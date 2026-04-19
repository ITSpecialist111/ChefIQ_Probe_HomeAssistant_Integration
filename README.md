# Chef iQ BLE for Home Assistant

A native Home Assistant integration for the **Chef iQ CQ60 Smart Wireless Meat Thermometer** (and any other probe that broadcasts on manufacturer ID `0x05CD` / `1485`).

* **No cloud.** No Chef iQ account, no MQTT bridge, no BLE Monitor required.
* **Local push** via the Home Assistant Bluetooth integration. Works with any source HA already knows about — local USB HCI, ESPHome BT proxy, SLZB‑06 (LAN), Shelly BLE Gateway, etc.
* **Sentinel‑aware.** When a probe ring isn't in contact with anything (only the tip is inserted, ambient is exposed, etc.) the firmware emits a "not‑measured" value of `0x7FFB`. This integration masks those to **unavailable** instead of letting `3,276 °C` end up on your graphs.
* **Battery is properly scaled.** Raw 0–255 byte → 0–100 %.
* **Per‑probe config entries.** Each physical probe gets its own device card with all six rings, battery and signal as separate entities — auto‑discovered the moment HA sees a Chef iQ advert.

## Sensors per probe

| Entity | Description |
|---|---|
| `Meat temperature` | The deepest ring (the "meat" reading) |
| `Probe tip` | Tip of the probe |
| `Probe ring 1` / `2` / `3` | Other rings up the shaft |
| `Ambient temperature` | Handle‑end ring (use this for grill/oven temp) |
| `Battery` | 0–100 % |
| `Signal strength` | RSSI of the nearest BT source (disabled by default) |

Any ring that isn't in contact with anything reports as **unavailable** rather than a bogus number.

## Install (HACS — recommended)

1. In HACS → ⋮ → **Custom repositories**, add:
   * Repository: `https://github.com/ITSpecialist111/ChefIQ_Probe_HomeAssistant_Integration`
   * Type: **Integration**
2. Install **Chef iQ BLE**.
3. Restart Home Assistant.
4. Wake the probe (touch the capacitive button on the charger). HA's Bluetooth integration will surface a "Discovered" card — click **Configure → Submit**.

## Install (manual)

Copy `custom_components/chefiq_ble/` into your HA `config/custom_components/` directory and restart HA.

## Why not just use BLE Monitor?

BLE Monitor is brilliant, but its bundled Chef iQ parser:

* surfaces probe rings that aren't in contact as `~3,276 °C`,
* doesn't scale battery from raw byte to percentage,
* and on Home Assistant OS only supports the **local** HCI adapter — it can't ingest from an SLZB‑06 or any other remote scanner that HA's first‑party Bluetooth integration knows about.

This integration is an end run around all three of those — it sits directly on `homeassistant.components.bluetooth`, so any source that integration sees, this one sees too.

(There is a [companion PR open against BLE Monitor](https://github.com/custom-components/ble_monitor/pull/1538) that fixes the sentinel issue there too, for users who prefer to stay on BLE Monitor.)

## Example dashboard / automation

A ready‑made Lovelace dashboard with a "doneness" gauge, ring chart and cook‑state banner is published as a separate Python script in the [HASS MCP repo](https://github.com/ITSpecialist111/HASS-MCP) — point it at your HA URL + LLT and it republishes the dashboard idempotently.

A minimal example is included in [`examples/dashboard.yaml`](examples/dashboard.yaml).

## Compatibility

* Home Assistant **2024.4** or newer.
* Tested with Chef iQ **CQ60** firmware as shipped in late 2024 / 2025. Other Chef iQ probes that share the manufacturer ID may partially work — please open an issue with a packet capture if you have one.

## Credits

Manufacturer‑data layout reverse‑engineered from on‑device captures and cross‑referenced with the parser in [`custom-components/ble_monitor`](https://github.com/custom-components/ble_monitor/blob/master/custom_components/ble_monitor/ble_parser/chefiq.py).

## License

[MIT](LICENSE).
