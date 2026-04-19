"""Constants for the Chef iQ BLE integration."""
from __future__ import annotations

DOMAIN = "chefiq_ble"

# Bluetooth SIG manufacturer ID assigned to Chef iQ
MFR_ID = 1485  # 0x05CD

# Dispatcher signal — payload is the address (no colons, lowercased)
SIGNAL_NEW = f"{DOMAIN}_new_data"

# Sentinel values used by the CQ60 firmware when a probe ring is not in
# contact with anything. Anything at or above this value is treated as
# "not measured" and surfaces in HA as `unavailable` rather than a bogus
# 3000+ °C reading.
TEMP_SENTINEL_MIN = 0x7FF0
