"""Chef iQ CQ60 BLE — direct integration with Home Assistant Bluetooth.

Listens for manufacturer-id 0x05CD (1485) advertisements from any
Bluetooth source the HA Bluetooth integration knows about — local USB
HCI dongle, ESPHome BT proxy, SLZB-06, Shelly BLE Gateway, etc. — and
exposes the CQ60 probe data as native Home Assistant sensors. No cloud,
no MQTT bridge, no BLE Monitor required.

Repo: https://github.com/ITSpecialist111/ChefIQ_Probe_HomeAssistant_Integration
"""
from __future__ import annotations

import logging
from struct import unpack
from typing import Any

from homeassistant.components.bluetooth import (
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.components.bluetooth.match import BluetoothCallbackMatcher
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, MFR_ID, SIGNAL_NEW, TEMP_SENTINEL_MIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


def _decode_temp(raw: int) -> float | None:
    """Decode a little-endian uint16 temperature in tenths of °C.

    The CQ60 emits 0x7FFB / 0x7FFE / 0x7FFF when a ring sensor has nothing
    to read (probe partially inserted, broken probe wire, etc.). We mask
    anything ≥ 0x7FF0 to ``None`` so HA shows the entity as *unavailable*
    rather than a meaningless 3,276 °C reading.
    """
    if raw >= TEMP_SENTINEL_MIN:
        return None
    return round(raw / 10, 1)


def parse_chefiq_payload(payload: bytes) -> dict[str, Any] | None:
    """Decode a Chef iQ CQ60 manufacturer payload (the bytes that follow
    the manufacturer-ID prefix).

    Layout (18 bytes, all little-endian):

    ``[0]``    record-type (``0x01`` = temperature, ``0x03`` = identity,
               ``0x00`` = name)
    ``[1]``    sub-type / sequence
    ``[2]``    battery (raw 0-255 → scaled to 0-100 %)
    ``[3]``    probe-ring 3 (8-bit °C, integer)
    ``[4-5]``  reserved
    ``[6-7]``  meat (tip-most ring) °C × 10
    ``[8-9]``  probe tip °C × 10
    ``[10-11]`` probe ring 1 °C × 10
    ``[12-13]`` probe ring 2 °C × 10
    ``[14-15]`` ambient (handle-end) °C × 10
    ``[16-17]`` checksum / sequence

    Returns ``None`` for any non-temperature record so callers can ignore
    them silently.
    """
    if len(payload) != 18 or payload[0] != 0x01:
        return None
    try:
        msg = payload[2:]
        (
            batt,
            t_probe_3,
            _reserved,
            t_meat,
            t_tip,
            t_p1,
            t_p2,
            t_amb,
            _last,
        ) = unpack("<BBHHHHHHh", msg)
    except Exception:  # noqa: BLE001
        return None

    return {
        "battery": max(0, min(100, round(batt * 100 / 255))),
        "meat_temperature": _decode_temp(t_meat),
        "probe_tip_temperature": _decode_temp(t_tip),
        "probe_1_temperature": _decode_temp(t_p1),
        "probe_2_temperature": _decode_temp(t_p2),
        "probe_3_temperature": float(t_probe_3) if t_probe_3 < 0xFE else None,
        "ambient_temperature": _decode_temp(t_amb),
    }


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Top-level setup — nothing to do; everything happens per config-entry."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a single Chef iQ CQ60 probe (one config entry per probe)."""
    address: str = entry.unique_id  # uppercased BD address from discovery
    addr_slug = address.replace(":", "").lower()

    store = hass.data[DOMAIN].setdefault(
        addr_slug,
        {
            "address": address,
            "name": entry.title or "Chef iQ CQ60",
            "rssi": None,
        },
    )

    @callback
    def _on_advert(
        service_info: BluetoothServiceInfoBleak,
        change: BluetoothChange,
    ) -> None:
        mfr = service_info.manufacturer_data.get(MFR_ID)
        if not mfr:
            return
        data = parse_chefiq_payload(mfr)
        if data is None:
            return
        store.update(data)
        store["rssi"] = service_info.rssi
        store["name"] = service_info.name or store["name"]
        async_dispatcher_send(hass, SIGNAL_NEW, addr_slug)
        _LOGGER.debug("Chef iQ %s: %s", service_info.address, data)

    cancel = async_register_callback(
        hass,
        _on_advert,
        BluetoothCallbackMatcher(
            manufacturer_id=MFR_ID,
            address=address,
        ),
        BluetoothScanningMode.PASSIVE,
    )

    @callback
    def _on_stop(_event):
        cancel()

    entry.async_on_unload(cancel)
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _on_stop)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        addr_slug = entry.unique_id.replace(":", "").lower()
        hass.data[DOMAIN].pop(addr_slug, None)
    return unloaded
