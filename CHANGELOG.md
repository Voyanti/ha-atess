# Changelog

## Unreleased

### Added
- PCS fault alarm bit decoding (registers 181-188). Fault Alarm 1-8 raw register values are replaced by a single "PCS Active Faults" sensor entity that publishes a JSON array of active fault strings (e.g. `["G1D0_PV_Inverse_Failure", "G2D3_BMS_Communication_Fault"]`).
- Fault bit maps for all 8 PCS fault alarm groups (Atess Modbus RTU v3.22, Figures 4.3.2-4.3.9).
- High/low byte swap applied to fault registers before bit decoding, as required by the protocol.
- `json_attributes_topic` on the fault entity exposes `active_faults` list and `count` as HA attributes.

### Changed
- Removed individual Fault Alarm 1-8 sensor entities from PCS parameters. These are now decoded and combined into the single "PCS Active Faults" entity.
