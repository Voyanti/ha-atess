# Changelog

## 0.5.8

### Added
- BMS max/min temperature locators from input registers 167 and 170: `BMS Max Temp Group Nr` / `BMS Min Temp Group Nr` (167 high/low byte) and `BMS Max Temp Box Nr` / `BMS Min Temp Box Nr` (170 high/low byte). These say *where* the existing `BMS Max./Min. Temperature` (171) readings were measured, so a hot pack can be identified rather than only detected. "all model" per the protocol PDF.
### Changed
- BMS Max./Min. Temperature (input register 171) and BMS Max./Min. Cell Voltage (174, 175) now have the `measurement` state class, so Home Assistant keeps long-term statistics for them beyond recorder retention.

## 0.5.6

### Changed
- Reactive Power Regulation Mode (250) is now a select rather than a number. The protocol PDF gives no legend for the values; the PCS user manual supplies one and all three modes were confirmed live on an HPS. Options are `Fixed Power Factor` (1), `Power Factor Curve (unsafe)` (2) and `Fixed Reactive Power` (3). Both templates fall through to the raw value, so an undocumented reading of 0 or 4 renders as a number rather than going unknown.
- Power Factor Reference Sign (251) and Reactive Reference Sign (263) are now selects, `Lagging (absorb)` (0) and `Leading (supply)` (1), confirmed against measured bypass reactive power.
- `Reactive Power Control` in DOCS.md rewritten from field results: the write-ordering rule for registers 250 and 264, why mode 2 is unsafe with undefined curve points, the sign convention, the non-linear response of register 264 and its resolution floor, the feedback registers, and the bypass constraint.

### Note
- The three registers above now take their label string as the MQTT payload, not the integer. Any external script writing them directly needs updating.

## 0.5.5

### Fixed
- Power factor (input register 23) rendered incorrectly in Home Assistant. It was declared with the `enum` device class, which only accepts a state drawn from a fixed options list, so the 0.001-scaled float it publishes could not be rendered. Now uses the `power_factor` device class with `measurement` state class, matching Load Power Factor (52).
- Power factor symbol (input register 22) no longer claims the `enum` device class either. It carries the sign of register 23, and the protocol does not say which of 0/1 means leading, so it publishes with no device class rather than a guessed labelling.

### Changed
- `device_class` is now optional on read parameters; discovery omits the field when a register has no natural Home Assistant device class.

### Known issue
- 32 further read registers still declare the `enum` device class without a `value_template` or options list (fault alarm words, BMS status, running state, serial number). These are integer-valued so they misrender less obviously, but they need the same treatment.

## 0.5.4

### Added
- Reactive power control registers: Reactive Power Regulation Enable (11), Reactive Power Regulation Mode (250), Power Factor Reference Sign/Value (251/252), Reactive Reference Sign/Value (263/264) and Reactive Lock Enable (267). Together with the existing Output/Load Reactive Power sensors these allow power-factor correction at the point of common coupling.
- Optional `step` on write parameters, published in MQTT discovery for number entities.
- `Reactive Power Control` section in DOCS.md, recording which parts of the 250-267 block the protocol leaves undocumented.

### Fixed
- Power Factor Reference rendered as an integer-only control in Home Assistant. MQTT number entities default to a step of 1, so a register with range 0-1 offered only those two values. It now declares `step: 0.001`.
- Writes to any register with a fractional multiplier could land one count low. The encoder truncated instead of rounding, so dividing by the multiplier left float error and 0.999/0.001 was written as 998. Affects Grid Power Compensation, Max Grid Charge Power, the current limits and the PBD voltage settings.

## Unreleased

### Added
- PCS fault alarm bit decoding (registers 181-188). Fault Alarm 1-8 raw register values are replaced by a single "PCS Active Faults" sensor entity that publishes a JSON array of active fault strings (e.g. `["G1D0_PV_Inverse_Failure", "G2D3_BMS_Communication_Fault"]`).
- Fault bit maps for all 8 PCS fault alarm groups (Atess Modbus RTU v3.22, Figures 4.3.2-4.3.9).
- High/low byte swap applied to fault registers before bit decoding, as required by the protocol.
- `json_attributes_topic` on the fault entity exposes `active_faults` list and `count` as HA attributes.

### Changed
- Removed individual Fault Alarm 1-8 sensor entities from PCS parameters. These are now decoded and combined into the single "PCS Active Faults" entity.

## 0.5.3

### Fixed
- Unrecoverable reconnect loop after the device closed the TCP connection: the stale socket was never closed, so every retry reused it and only a manual addon restart recovered. Connection errors now force a fresh socket and retry once before escalating.
- Modbus timeouts (slow device) no longer tear down the transport; they get one in-place retry before escalating, preventing availability flapping and serial-port churn on RTU.
- Reconnect attempts to offline devices are paced by a 30s cooldown instead of retrying every loop.
- MQTT discovery is republished when a server reconnects, so devices that were offline at addon startup now get their Home Assistant entities.
- A failed reconnect during the retry sweep can no longer crash the addon; the addon also starts (and keeps retrying) when all devices are offline at boot.
- Write commands arriving on a dead connection no longer trigger the addon's self-restart: the transport is repaired and the write is retried at the server layer (new `with_retries` helper).
- Modbus access is serialised between the read loop and the MQTT command thread.
