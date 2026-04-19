# Chef iQ BLE

Native Home Assistant integration for the **Chef iQ CQ60** wireless meat thermometer. Local push, no cloud, works with any HA Bluetooth source (local HCI, ESPHome BT proxy, SLZB-06, …).

* Auto-discovered from manufacturer ID `0x05CD`.
* One device per physical probe; six temperature entities + battery + RSSI.
* Masks the firmware "not-measured" sentinel (`0x7FFB`) so disconnected rings show as **unavailable** instead of `3,276 °C`.
* Battery byte properly scaled to 0–100 %.
