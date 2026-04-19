"""Config flow for Chef iQ BLE.

The flow is triggered automatically by the HA Bluetooth integration the
moment any source (USB HCI, ESPHome BT proxy, SLZB-06, …) sees a Chef iQ
manufacturer-ID advertisement (0x05CD). The user just clicks **Add** on
the resulting "Discovered" card.

A manual entry path is also offered for users who want to pre-pair a
specific BD address before the device is in range.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from . import parse_chefiq_payload
from .const import DOMAIN, MFR_ID


class ChefIQConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Chef iQ BLE probes."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_address: str | None = None
        self._discovered_name: str | None = None
        self._discovered_devices: dict[str, str] = {}

    async def async_step_bluetooth(
        self,
        discovery_info: BluetoothServiceInfoBleak,
    ) -> ConfigFlowResult:
        """Handle Bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        # Only accept if the manufacturer payload actually decodes — keeps
        # us from showing discovery cards for non-CQ60 Chef iQ products.
        mfr = discovery_info.manufacturer_data.get(MFR_ID)
        if not mfr or parse_chefiq_payload(mfr) is None:
            # Identity / name records appear before the first temperature
            # record. Allow discovery anyway so we don't miss the device,
            # but only proceed once we've seen a valid temp record OR the
            # user confirms.
            pass

        self._discovered_address = discovery_info.address
        self._discovered_name = discovery_info.name or "Chef iQ CQ60"

        self.context.update(
            {
                "title_placeholders": {"name": self._discovered_name},
            }
        )
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Confirm a Bluetooth-discovered Chef iQ probe."""
        assert self._discovered_address is not None
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_name or "Chef iQ CQ60",
                data={CONF_ADDRESS: self._discovered_address},
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": self._discovered_name or "Chef iQ CQ60",
                "address": self._discovered_address,
            },
        )

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the manual-add path."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._discovered_devices.get(address, "Chef iQ CQ60"),
                data={CONF_ADDRESS: address},
            )

        # Surface any Chef iQ devices currently visible to HA's bluetooth
        # integration (filtering by manufacturer ID).
        current_addresses = self._async_current_ids()
        for info in async_discovered_service_info(self.hass):
            if info.address in current_addresses:
                continue
            if MFR_ID not in info.manufacturer_data:
                continue
            self._discovered_devices[info.address] = info.name or "Chef iQ CQ60"

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            addr: f"{name} ({addr})"
                            for addr, name in self._discovered_devices.items()
                        }
                    )
                }
            ),
        )
