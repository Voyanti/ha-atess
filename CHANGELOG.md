# Changelog

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
