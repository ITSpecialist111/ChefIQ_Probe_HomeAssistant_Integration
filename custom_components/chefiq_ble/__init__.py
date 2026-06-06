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
from homeassistant.const import CONF_ADDRESS, Platform
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

    The CQ60 broadcasts three record types, distinguished by byte ``[0]``:

    * ``0x01`` temperature (18 bytes) — byte ``[1]`` is a flags/sequence
      field, followed by seven little-endian ``uint16`` temperature slots
      (°C × 10) spanning bytes ``[2:16]``, then a 2-byte checksum. Slot 0
      mirrors the ambient slot (slot 6); the firmware emits ``0x7FFB`` /
      ``0x7FFE`` / ``0x7FFF`` for any ring that is not currently reading.

          slot 0  ([2:4])    ambient mirror (ignored — same as slot 6)
          slot 1  ([4:6])    probe ring 3
          slot 2  ([6:8])    meat (tip-most ring)
          slot 3  ([8:10])   probe tip
          slot 4  ([10:12])  probe ring 1
          slot 5  ([12:14])  probe ring 2
          slot 6  ([14:16])  ambient (handle-end)

    * ``0x03`` identity (17 bytes) — bytes ``[2:8]`` are the BD address and
      byte ``[8]`` is the battery percentage (0-100, already scaled by the
      firmware).
    * ``0x00`` name (16 bytes) — ignored.

    Returns a *partial* dict for temperature and identity records (callers
    merge them into a single per-device store), or ``None`` for any record
    we do not decode.
    """
    if not payload:
        return None

    if payload[0] == 0x01 and len(payload) == 18:
        try:
            slots = unpack("<7H", payload[2:16])
        except Exception:  # noqa: BLE001
            return None
        return {
            "meat_temperature": _decode_temp(slots[2]),
            "probe_tip_temperature": _decode_temp(slots[3]),
            "probe_1_temperature": _decode_temp(slots[4]),
            "probe_2_temperature": _decode_temp(slots[5]),
            "probe_3_temperature": _decode_temp(slots[1]),
            "ambient_temperature": _decode_temp(slots[6]),
        }

    if payload[0] == 0x03 and len(payload) >= 9:
        # Identity record: battery percentage sits just after the address.
        return {"battery": max(0, min(100, payload[8]))}

    return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a single Chef iQ CQ60 probe (one config entry per probe)."""
    hass.data.setdefault(DOMAIN, {})
    address: str = entry.data[CONF_ADDRESS]  # uppercased BD address from discovery
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

    # ``connectable=False`` ensures we still match the probe when the only
    # Bluetooth source is an advert-only / passive scanner (ESPHome BT
    # proxy, SLZB-06, Shelly gateway) that cannot make active connections.
    entry.async_on_unload(
        async_register_callback(
            hass,
            _on_advert,
            BluetoothCallbackMatcher(
                manufacturer_id=MFR_ID,
                address=address,
                connectable=False,
            ),
            BluetoothScanningMode.PASSIVE,
        )
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        addr_slug = entry.data[CONF_ADDRESS].replace(":", "").lower()
        hass.data[DOMAIN].pop(addr_slug, None)
    return unloaded
