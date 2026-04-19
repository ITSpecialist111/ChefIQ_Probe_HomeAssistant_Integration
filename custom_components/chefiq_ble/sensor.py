"""Sensor platform for Chef iQ BLE.

Each config entry corresponds to exactly one physical CQ60 probe (keyed
by BD address). For each entry we register a fixed bundle of sensors:

* meat / probe-tip / probe-1 / probe-2 / probe-3 / ambient temperatures
* battery
* signal strength (disabled by default)

Values come in via the dispatcher signal raised by ``__init__.py`` every
time we see a fresh manufacturer-data advert. ``None`` values surface as
*unavailable* in HA — that includes both "no advert seen yet" and
"sensor ring is reading the not-measured sentinel".
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ADDRESS,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_NEW

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class ChefIQSensorDescription(SensorEntityDescription):
    """Describes a single Chef iQ sensor."""

    field: str = ""


SENSORS: tuple[ChefIQSensorDescription, ...] = (
    ChefIQSensorDescription(
        key="meat",
        field="meat_temperature",
        translation_key="meat_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:food-steak",
    ),
    ChefIQSensorDescription(
        key="probe_tip",
        field="probe_tip_temperature",
        translation_key="probe_tip_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:thermometer",
    ),
    ChefIQSensorDescription(
        key="probe_1",
        field="probe_1_temperature",
        translation_key="probe_1_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:thermometer",
    ),
    ChefIQSensorDescription(
        key="probe_2",
        field="probe_2_temperature",
        translation_key="probe_2_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:thermometer",
    ),
    ChefIQSensorDescription(
        key="probe_3",
        field="probe_3_temperature",
        translation_key="probe_3_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:thermometer",
    ),
    ChefIQSensorDescription(
        key="ambient",
        field="ambient_temperature",
        translation_key="ambient_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:fire-circle",
    ),
    ChefIQSensorDescription(
        key="battery",
        field="battery",
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    ChefIQSensorDescription(
        key="rssi",
        field="rssi",
        translation_key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        suggested_display_precision=0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Chef iQ sensors for a single config entry (one probe)."""
    address: str = entry.data[CONF_ADDRESS]
    addr_slug = address.replace(":", "").lower()
    store = hass.data[DOMAIN][addr_slug]
    async_add_entities(
        ChefIQSensor(addr_slug, store, desc, address, entry.title)
        for desc in SENSORS
    )


class ChefIQSensor(SensorEntity):
    """Single sensor for one CQ60 attribute."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        addr_slug: str,
        store: dict[str, Any],
        description: ChefIQSensorDescription,
        address: str,
        title: str,
    ) -> None:
        self.entity_description = description
        self._addr_slug = addr_slug
        self._store = store
        self._field = description.field
        self._attr_unique_id = f"{DOMAIN}_{addr_slug}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, addr_slug)},
            connections={("bluetooth", address)},
            name=title or "Chef iQ CQ60",
            manufacturer="Chef iQ",
            model="CQ60",
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to dispatcher updates for our address."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_NEW, self._handle_signal)
        )

    @callback
    def _handle_signal(self, addr_slug: str) -> None:
        if addr_slug != self._addr_slug:
            return
        self.async_write_ha_state()

    @property
    def native_value(self) -> Any:
        return self._store.get(self._field)

    @property
    def available(self) -> bool:
        return self._store.get(self._field) is not None
