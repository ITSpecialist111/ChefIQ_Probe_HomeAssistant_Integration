# Chef iQ — Automations & Scripts

The full “smart kitchen” build ships **27 automations** and **2 scripts**. They drive the cook
lifecycle (auto start/stop, rest), the alerts (pull point, pre‑alert, stall, low battery, signal
lost), the food‑safety coaching, the fridge / fermentation / chocolate modes, and the optional
**AI** + **Sonos** behaviour.

* Import them from [`examples/chefiq_automations.yaml`](../examples/chefiq_automations.yaml) and
  [`examples/chefiq_scripts.yaml`](../examples/chefiq_scripts.yaml).
* They read the derived sensors from
  [`examples/cooking_physics_package.yaml`](../examples/cooking_physics_package.yaml) and the
  helpers listed in [DASHBOARD.md](DASHBOARD.md#helpers-it-uses).

> **Notify target:** every notification uses `notify.mobile_app_your_phone` as a placeholder —
> find‑and‑replace it with your own mobile‑app notify service. Voice lines call
> `script.chefiq_kitchen_announce` (your Sonos / TTS — see
> [`kitchen_announce.yaml`](../examples/kitchen_announce.yaml)).

---

## Cook lifecycle

| Automation (`id`) | Trigger | Condition | What it does |
|---|---|---|---|
| **Auto‑start Cook** (`chefiq_auto_start`) | meat rate **> 0.5 °C/min** for 2 min | cook not already active & probe present | Stamps `chefiq_cook_start`, turns on `chefiq_cook_active`, clears the alert flag, notifies “Cook started”. |
| **Auto‑stop Cook** (`chefiq_auto_stop`) | rate **< −2 °C/min** for 2 min · **or** probe unavailable 15 min · **or** core **< 30 °C** for 30 min | cook active | Ends the session, clears flags, notifies with the reason (pulled / offline / settled). |
| **End Cook Session** (`chefiq_cook_end`) | press `input_button.chef_iq_cook_end` | — | Manual end: stops the timer, clears all flags, stops the AI coach polling. |
| **Cook‑start Safety Briefing** (`chefiq_cook_briefing`) | `chefiq_cook_active` → on | — | Speaks + notifies a short food‑safety briefing for the chosen meat type. |
| **Rest Started** (`chefiq_rest_start`) | `chefiq_cook_active` → off | template (pulled hot, not cooling) | Stamps `chef_iq_rest_start`, sets the resting flag, announces “resting”. |
| **Rest Complete** (`chefiq_rest_done`) | every 1 min | resting & rest minutes elapsed | Clears the resting flag and announces the rest is done. |

## Doneness & probe alerts

| Automation | Trigger | Condition | What it does |
|---|---|---|---|
| **Almost There Pre‑alert** (`chefiq_prealert`) | meat temperature changes | cook active, not yet pre‑alerted, within *pre‑alert lead* of pull point | One‑shot “almost there” voice + push. |
| **Pull Point Reached** (`chefiq_target_reached`) | meat temperature changes | cook active, not yet alerted, core ≥ (target − carryover) | Announces the **pull point**, pushes a notification + a persistent notification. |
| **BBQ Stall Detected** (`chefiq_stall`) | rate **< 0.15 °C/min** for 20 min | cook active, hot enough, not already flagged | Flags the stall and notifies (the classic brisket/pork‑shoulder plateau). |
| **Stall Broken** (`chefiq_stall_break`) | rate **> 0.4 °C/min** for 5 min | cook active & stall was flagged | Clears the stall flag and notifies the cook is climbing again. |
| **Probe Signal Lost** (`chefiq_probe_lost`) | meat temp → unavailable/unknown | cook active | Push + persistent notification that the probe dropped out mid‑cook. |
| **Low Battery** (`chefiq_low_battery`) | battery **< 20 %**, and **< 8 %** | — | Tiered warning so the probe doesn’t die mid‑cook. |

## Food safety

| Automation | Trigger | Condition | What it does |
|---|---|---|---|
| **Pasteurized** (`chefiq_pasteurized`) | `chef_iq_safe_to_eat` → Pasteurized | cook active | Announces the food is now pasteurised/safe. |
| **Danger Zone Warning** (`chefiq_danger_zone`) | `chef_iq_danger_zone_time` **> 240 min** | cook active | Warns the food has spent > 4 h in the 5–57 °C danger zone. |
| **Hot‑hold Dropped** (`chefiq_hold_dropped`) | core **< 54 °C** for 2 min | cooked food, not cooling, still warm | Warns it has fallen out of safe hot‑holding (chill or reheat). |
| **Cooling Started** (`chefiq_cool_start`) | core **< 55 °C** for 1 min | not actively cooking, cooling, rate falling | Begins FDA 2‑stage cool tracking (stamps `chef_iq_cool_start`). |
| **Cooling Reset** (`chefiq_cool_reset`) | core **< 5 °C** (chilled) **or > 57 °C** (reheated) | cooling flag on | Ends cool tracking. |

## Fridge / cold‑chain (Probe Mode = Fridge)

| Automation | Trigger | Condition | What it does |
|---|---|---|---|
| **Fridge Warm** (`chefiq_fridge_warm`) | core **> 5 °C** for 30 min | mode = Fridge | Warns the fridge has been warm for half an hour. |
| **Cold‑chain Breach** (`chefiq_fridge_breach`) | `chef_iq_fridge_warm_duration` **> 120 min** | mode = Fridge | Escalates to a cold‑chain breach (discard‑risk) alert. |
| **Fridge Rapid Warming** (`chefiq_fridge_door`) | rate **> 0.3 °C/min** for 3 min | mode = Fridge | “Door left open?” rapid‑warming notification. |

## Fermenting & proofing (Probe Mode = Fermenting)

| Automation | Trigger | Condition | What it does |
|---|---|---|---|
| **Ferment At Temp** (`chefiq_ferment_ready`) | template (in ideal band) | mode = Fermenting | Announces the culture has reached its ideal temperature. |
| **Ferment Too Hot** (`chefiq_ferment_hot`) | template (above band) | mode = Fermenting | Warns the culture is too hot (risk of killing it). |
| **Proof Ready** (`chefiq_proof_ready`) | `chef_iq_proof_percent` **> 99 %** | ferment type = Pizza dough | Announces the dough is proofed (temperature‑compensated). |
| **Proof Start/Reset** (`chefiq_proof_reset`) | press `input_button.chef_iq_proof_start` | — | Baselines the proof tracker and stamps the start time. |

## Chocolate (Probe Mode = Tempering chocolate)

| Automation | Trigger | Condition | What it does |
|---|---|---|---|
| **Chocolate In Temper** (`chefiq_choc_temper`) | `chef_iq_in_temper` → Yes | mode = Tempering chocolate | Announces the chocolate has reached its working/temper window. |

## AI assistant

| Automation | Trigger | Condition | What it does |
|---|---|---|---|
| **AI Cook Setup** (`chefiq_ai_cook_setup`) | press `input_button.chef_iq_cook_setup` | — | Sends your plain‑English request to HA **AI Task**, which returns structured settings; applies probe mode, meat‑safety type, target, carryover, pre‑alert, rest (and proof hours), then starts the session. See [`ai_cook_setup.yaml`](../examples/ai_cook_setup.yaml). |
| **AI Coach (5 min)** (`chefiq_ai_coach_poll`) | every 5 min | cook active **and** not resting/cooling **and** still actively heating | Sends the live cook state to AI Task for one short expert insight, stores it in `input_text.chef_iq_ai_coach`, optionally speaks it. Skips rest/idle to save tokens. See [`ai_cook_coach.yaml`](../examples/ai_cook_coach.yaml). |

---

## Scripts

| Script | Purpose |
|---|---|
| **`chefiq_start_cook`** | Manual “start a cook”: stamps the start time, turns on `chefiq_cook_active`, clears the alert flag. |
| **`chefiq_kitchen_announce`** | Speaks a message on Sonos over the top of music and **restores the music + volume afterwards**. Volume is **relative** to the current music level (music + the `chef_iq_announce_boost` slider), with the per‑call `volume` acting as a minimum floor for urgent alerts. Robust against overlapping/cancelled announcements. See [`kitchen_announce.yaml`](../examples/kitchen_announce.yaml). |

---

## Notes

* **Single‑probe.** These automations target one probe (`sensor.chefiq_*`). For multiple probes,
  duplicate and re‑point the entity IDs per device.
* **Idempotent flags.** The `input_boolean` flags (`chefiq_alert_sent`, `chef_iq_pre_alert_sent`,
  `chef_iq_stall_notified`, …) make the one‑shot alerts fire once per cook; the lifecycle
  automations reset them at start/stop.
* **Guidance only.** The food‑safety logic follows widely‑published USDA/FSIS and FDA 2‑stage
  cooling guidance, but it is advisory — always follow your local food‑safety rules for at‑risk
  diners.
