# Chef iQ — Full “Smart Kitchen” Dashboard

This is the rich, multi‑feature Lovelace dashboard shown in the project screenshots. It turns the
Chef iQ probe into a **mode‑aware cooking, food‑safety, fridge/cold‑chain, fermentation and
chocolate‑tempering coach**, with an optional **AI cook assistant** and **Sonos announcements**.

> Looking for the simple starter dashboards instead? See
> [`examples/dashboard.yaml`](../examples/dashboard.yaml) (single probe) and
> [`examples/dashboard_multi_probe.yaml`](../examples/dashboard_multi_probe.yaml).

The full dashboard, the derived template sensors it reads, the helpers, the automations and the
Sonos announce script are all bundled in [`examples/`](../examples/):

| File | What it is |
|---|---|
| [`examples/dashboard_full.yaml`](../examples/dashboard_full.yaml) | The complete Lovelace dashboard (this page). |
| [`examples/cooking_physics_package.yaml`](../examples/cooking_physics_package.yaml) | All the derived **template sensors** (pasteurization, juiciness, carryover, fridge, ferment, proof, temper, …). |
| [`examples/chefiq_automations.yaml`](../examples/chefiq_automations.yaml) | All **27 automations** — see [AUTOMATIONS.md](AUTOMATIONS.md). |
| [`examples/chefiq_scripts.yaml`](../examples/chefiq_scripts.yaml) | The `chefiq_start_cook` + `chefiq_kitchen_announce` scripts. |
| [`examples/ai_cook_setup.yaml`](../examples/ai_cook_setup.yaml) | “Describe your cook → AI configures the probe” + session lifecycle. |
| [`examples/ai_cook_coach.yaml`](../examples/ai_cook_coach.yaml) | The 5‑minute AI cook‑coach poll. |
| [`examples/kitchen_announce.yaml`](../examples/kitchen_announce.yaml) | The Sonos TTS announce script (relative‑volume, restores music). |

---

## Screenshots

### 1 · Cooking overview
The default view while cooking: probe‑mode picker, the AI Cook Setup/Coach cards, a live 2‑hour
trend of every ring, and the big doneness gauge with target, rate‑of‑rise and ETA.

![Cooking overview](screenshots/dashboard-1-cooking-overview.png)

### 2 · Cook setup, food safety & cooking intelligence
Preset/target controls, a per‑ring **Probe Thermal Map**, the **Food Safety** column
(pasteurization, lethality, danger‑zone, hot‑hold, rapid‑cooling) and the **Cooking Intelligence**
column (Newton’s‑law ETA, carryover, juiciness, cook phase, rested temp, doneness spread, braise
tenderness).

![Food safety and cooking intelligence](screenshots/dashboard-2-food-safety-intelligence.png)

### 3 · Fridge / cold‑chain mode
Switch **Probe Mode → Fridge** and the dashboard re‑skins into a cold‑chain monitor: bacterial
growth factor (Ratkowsky), shelf‑life multiplier and FSIS danger‑zone timing.

![Fridge cold-chain mode](screenshots/dashboard-3-fridge-cold-chain.png)

### 4 · Fermenting / proofing mode
**Probe Mode → Fermenting** turns it into a culture‑temperature coach (yogurt, sourdough, bread &
pizza dough, beer, tempeh, natto) with a temperature‑compensated proof tracker.

![Fermenting proofing mode](screenshots/dashboard-4-fermenting-proofing.png)

---

## Prerequisites

**1. Frontend cards (install via HACS → Frontend):**

| Card | Used for |
|---|---|
| [`apexcharts-card`](https://github.com/RomRider/apexcharts-card) | Live 2‑hour multi‑ring trend |
| [`mushroom`](https://github.com/piitaya/lovelace-mushroom) | Mode/preset pickers, the status tiles |
| [`bar-card`](https://github.com/custom-cards/bar-card) | Pizza‑dough proof progress bar |

**2. The derived template sensors** from
[`examples/cooking_physics_package.yaml`](../examples/cooking_physics_package.yaml). Add it to your
`configuration.yaml` (e.g. `homeassistant: packages: !include_dir_named packages/` or
`template: !include …`) and reload. These produce every `sensor.chef_iq_*` the cards read.

**3. The helpers** listed in [Helpers](#helpers-it-uses) below (auto‑created if you build via the
API, or create them under *Settings → Devices & Services → Helpers*).

**4. (Optional) AI + Sonos** — see [`ai_cook_setup.yaml`](../examples/ai_cook_setup.yaml),
[`ai_cook_coach.yaml`](../examples/ai_cook_coach.yaml) and
[`kitchen_announce.yaml`](../examples/kitchen_announce.yaml).

> **Entity names:** the dashboard reads the raw probe as `sensor.chefiq_*` (e.g.
> `sensor.chefiq_meat_temperature`) and the derived helpers as `sensor.chef_iq_*` (note the
> underscore). If your probe device is named differently, do a find‑and‑replace on the entity
> prefix once.

---

## Install

1. Install the prerequisite cards + the template‑sensor package and restart/reload.
2. *Settings → Dashboards → + Add Dashboard → New dashboard from scratch*, open it, then
   *⋮ → Edit Dashboard → ⋮ → Raw configuration editor*.
3. Paste the contents of [`examples/dashboard_full.yaml`](../examples/dashboard_full.yaml) and save.
4. Set **Probe Mode** to match what you’re doing (Cooking / Fridge / Freezer / Fermenting /
   Tempering chocolate). The relevant sections appear automatically.

---

## How it’s laid out

A single **Sections** view (3 columns max). The first sections are always visible; the last five
are **conditional** on the *Probe Mode* (and ferment‑type) selector, so the board re‑skins itself to
whatever you’re doing.

| # | Section | Shown when | Key cards |
|---|---|---|---|
| 0 | **Probe Mode + Live Trend** | always | `mushroom-select` mode picker · `apexcharts` 2 h trend of meat/ambient/ring1/ring2/target · cook‑activity logbook |
| 1 | **AI Cook Setup + Coach** | always | “Describe your cook” text box + **Apply with AI** / **End cook session** buttons · AI coach insight · *Announce on Sonos* toggle + *Announce loudness* slider |
| 2 | **Doneness gauge & status** | always | Battery / signal / device tiles · big **Meat Temperature** gauge · rate‑of‑rise · ETA · target / ambient / to‑target tiles |
| 3 | **Cook setup & thermal map** | always | Cook timer · **Preset** picker + **Custom Target** slider · **Start/Stop Cook** · **Probe Thermal Map** (tip / ring 1 / ring 2 / ambient) |
| 4 | **🛡️ Food Safety** | always | Meat‑type picker · overall verdict · pasteurization % · lethality (time × temp) · time‑in‑danger‑zone · hot‑hold · rapid‑cooling (FDA 2‑stage) |
| 5 | **🧪 Cooking Intelligence** | always | Smart ETA (Newton) · final‑after‑rest · carryover · settles‑to · juiciness · edge‑to‑edge spread · cook phase · braise tenderness |
| 6 | **❄️ Fridge / Cold‑Chain** | Probe Mode = Fridge | cold‑chain status · fridge status · bacteria‑growth factor (Ratkowsky) · food‑lasts (shelf‑life) |
| 7 | **Fermenting / Proofing** | Probe Mode = Fermenting | ferment‑type picker · ferment status · ferment speed × |
| 8 | **Pizza Dough Proof** | Ferment type = Pizza dough | proof target hours + start button · proof status · proof % (`bar-card`) · dough temp |
| 9 | **Chocolate Tempering** | Probe Mode = Tempering chocolate | chocolate‑type picker · temper stage · temper target |

---

## Sensors & helpers reference

### Probe sensors (`sensor.chefiq_*`)

| Entity | Meaning |
|---|---|
| `sensor.chefiq_meat_temperature` | Core / deepest ring (°C) |
| `sensor.chefiq_probe_tip` | Tip (°C) |
| `sensor.chefiq_probe_ring_1` / `_2` / `_3` | Rings up the shaft (°C) |
| `sensor.chefiq_ambient_temperature` | Handle‑end ring = oven/pit temp (°C) |
| `sensor.chefiq_meat_rate` | Rate of rise (°C/min) |
| `sensor.chefiq_battery` | Battery (%) |
| `sensor.chefiq_signal` | BLE RSSI (dBm) |

### Derived “intelligence” sensors (`sensor.chef_iq_*`)

These come from [`cooking_physics_package.yaml`](../examples/cooking_physics_package.yaml).

**Cooking & doneness:** `cook_phase`, `eta_to_target`, `predicted_final_temp`, `rested_temp`,
`dynamic_carryover`, `doneness_spread`, `juiciness`, `collagen_hours`, `collagen_rate`,
`braise_tenderness`.

**Food safety:** `food_safety`, `safe_to_eat`, `pasteurization`, `pasteurization_f60`,
`lethality_rate`, `danger_zone_time`, `hot_hold_safety`, `cooling_safety`.

**Fridge / cold‑chain:** `cold_chain`, `fridge_status`, `fridge_warm_duration`,
`bacteria_growth_factor`, `shelf_life_factor`.

**Fermenting / proofing:** `ferment_status`, `ferment_speed`, `ferment_target`, `dough_temp_tip`,
`proof_status`, `proof_percent`, `proof_progress`, `proof_hours_total`, `proof_rate`, `proof_eta`.

**Chocolate:** `temper_stage`, `temper_target`, `in_temper`.

### Helpers it uses

| Helper | Purpose |
|---|---|
| `input_select.chef_iq_probe_mode` | Cooking / Fridge / Freezer / Fermenting / Tempering chocolate / Other — drives the conditional sections |
| `input_select.chefiq_preset` | 16 doneness presets (Beef · Medium Rare, Chicken · Breast, …) |
| `input_select.chef_iq_meat_type` | Intact cut / Ground / Poultry / Fish — sets the safety target |
| `input_select.chef_iq_ferment_type` | Yogurt / Bread / Pizza dough / Sourdough / Beer / Tempeh / Natto |
| `input_select.chef_iq_chocolate_type` | Dark / Milk / White |
| `input_number.chefiq_target_temperature` | Core pull target (°C) |
| `input_number.chef_iq_carryover_offset` | Expected carryover rise (°C) |
| `input_number.chef_iq_pre_alert_lead` | Degrees before target to pre‑alert |
| `input_number.chef_iq_rest_minutes` | Rest time after pulling |
| `input_number.chef_iq_proof_target_hours` / `chef_iq_proof_baseline` | Proof‑tracker target / baseline |
| `input_number.chef_iq_announce_boost` | **Sonos announce loudness** above the music (dashboard slider) |
| `input_boolean.chefiq_cook_active` | Master “a cook is in progress” flag |
| `input_boolean.chef_iq_ai_announce` | Speak AI insights on Sonos |
| `input_text.chef_iq_cook_request` / `chef_iq_cook_plan` / `chef_iq_ai_coach` | AI request / plan / latest coach insight |
| `input_button.chef_iq_cook_setup` / `chef_iq_cook_end` / `chef_iq_proof_start` | Apply‑with‑AI / End session / Start‑proof |
| `input_datetime.chefiq_cook_start` / `chef_iq_rest_start` / `chef_iq_cool_start` / `chef_iq_proof_start_time` | Session timestamps |

---

## Re‑exporting your own dashboard

If you’ve customised the board and want to snapshot it back to YAML, open
*⋮ → Edit Dashboard → Raw configuration editor* and copy the whole document. The
[`examples/dashboard_full.yaml`](../examples/dashboard_full.yaml) in this repo was exported the same
way and only references portable entity IDs (no personal `media_player`, `notify` or `person`
entities — the Sonos label is just a card title).

See **[AUTOMATIONS.md](AUTOMATIONS.md)** for the 27 automations that drive the alerts, the cook
lifecycle and the AI/Sonos behaviour.
