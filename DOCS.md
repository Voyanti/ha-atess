# Quick Start

Install required add-ons:

- MQTT broker e.g. [Mosquitto](https://github.com/home-assistant/addons/blob/master/mosquitto/DOCS.md)
- [Homeassistant MQTT integration](https://www.home-assistant.io/integrations/mqtt/) to enable discovering the MQTT devices and entities
- Configure
  - Clients(Modbus Hubs/USB to Serial Converters) and Servers(Devices/RTUs) See Configuration section for details.
  - MQTT host, port, username and password

# Configuration

## Server

Each server should be defined as

```
  - name: "SG1"
    serialnum: "SERIAL0001"
    server_type: "SUNGROW_INVERTER"
    connected_client: "Client1"
    modbus_id: 1
```

- `name` is used to create the HA entity unique_id, and device name. Use alphanumeric characters only. Keep it unique.
- `serialnum` is verified upon add-on startup.
- `server_type` is used to select the class of server to instantiate. This add-on supports only PANELTRACK.
- `connected_client` specifies on which client bus (abstraction of serial port or tcp ip) the server is connected. Most systems use a single client.
- `modbus_id`: Modbus slave address of the device/server.

## Client

Each client should be defined as

```
  - name: "ModbusTCP"
    type: "TCP"
    host: "10.0.0.15"
    port: 502
```

or

```
  - name: "ModbusTCP"
    ha_display_name: "Client2"
    type: "RTU"
    port: "/dev/tty1"
    baudrate: 9600
    bytesize: 8
    parity: false
    stopbits: 1
```

- `name` see Server config above
- `type` can be one of "RTU" or "TCP"
- `port` is the com port if `type` is "RTU", TCP port if `type` is "TCP"

## Rounding

Decoded values are rounded before publishing, to the number of decimals configured for
their Home Assistant device class. `rounding_overrides` overrides the built-in defaults
in `enums.device_class_to_rounding`:

```
  rounding_overrides:
    - ha_device_class: power
      n_decimals: 0
    - ha_device_class: energy
      n_decimals: 1
```

- `ha_device_class` must be a valid [HA sensor device class](https://www.home-assistant.io/integrations/sensor/#device-class) string, e.g. `power`, `energy`, `voltage`, `current`, `frequency`, `apparent_power`, `reactive_power`, `power_factor`. Unknown values fail validation at startup.
- `n_decimals` must be between 0 and 6.
- Device classes not listed keep their built-in default; anything with no default at all is rounded to 2 decimals.
- Changes take effect on add-on restart. This rounds at the source, so it also reduces
  recorder churn for noisy sensors — unlike the per-entity **Display precision** setting
  in the HA UI, which only affects how the value is displayed.

# Custom Sensors

On first run the add-on creates `/share/ha-atess/mysensors.py` containing a
commented template. Add `ParamWrapped` entries to the `MY_SENSORS` list in that
file to register extra read or write registers; they are merged into the
built-in register map for every Atess device on the next add-on restart. The
template lists the names pre-injected into the file's namespace (group aliases,
`DataType`, `Parameter`, `WriteParameter`, etc.) so no imports are needed.

# Development

## Running locally

`devcontainer.json` can be used in vs code (Rebuild and reopen in container), followed by the task start Home assistant from `tasks.json` as outlined [here](https://developers.home-assistant.io/docs/add-ons/testing/).

`run_locally.sh` starts the app with default configuration, and creates a temporary local mosquitto broker

`run_tests.sh` runs all python unit test after setting the appropriate environment variables

Both make use of a spoofClient class which returns fake readings.

## Tests

- Completed tests
  - loader
  - some app functionality
- TODO tests
  - rest of app functionality
  - server
  - client
  - modbus_mqtt

### Defining a new Server type (for new add-on)

Abstract class Server in `server.py` can be implemented. See abstractmethod docstrings for information.

Add the new type to the enum in `implemented_servers.py` and use this string when declaring the `server_type` in config.yaml

# Register Map

All addresses are 0-indexed. Group indicates which device types the register applies to.

## Holding Registers

| Name | Addr | Type | Count | Multiplier | Unit | Min | Max | Group | Notes |
|------|------|------|-------|------------|------|-----|-----|-------|-------|
| Device On/Off | 0 | U16 | 1 | 1 | | | | All | |
| Grid And PV Charge Together | 8 | U16 | 1 | 1 | | | | Writable (All) | |
| Active Power Regulation Enable | 10 | U16 | 1 | 1 | | | | Writable (HPS/PCS/HPSTL) | |
| Manual Adjustment Enable | 12 | U16 | 1 | 1 | | | | Writable (HPS/PCS/HPSTL) | |
| Bypass Cabinet Enable | 13 | U16 | 1 | 1 | | | | Writable (All) | |
| BMS Communication Enable | 14 | U16 | 1 | 1 | | | | Writable (All) | |
| Anti Reflux Enable | 16 | U16 | 1 | 1 | | | | Writable (All) | |
| Reactive Power Regulation Enable | 11 | U16 | 1 | 1 | | | | Writable (HPS/PCS/HPSTL) | Gates registers 250-267 |
| Mode selection | 26 | U16 | 1 | 1 | | | | Writable (All) | |
| PV Power Setting | 33 | U16 | 1 | 1 | kW | 0 | 500 | Writable (All) | Illegal Address Exception on AtessPCS when 10 off , 12, on |
| Device Type Code | 43 | U16 | 1 | 1 | | | | All | |
| Grid Power Compensation | 44 | U16 | 1 | 0.1 | kW | 0 | 100 | Writable (All) | |
| Discharge Cutoff SOC | 47 | U16 | 1 | 1 | % | 0 | 100 | Writable (All) | |
| Output Power Limit | 58 | U16 | 1 | 1 | % | 0 | 120 | Writable (All) | Sets PV generated on PBD. PCS working not confirmed. |
| Output Power Setting | 59 | U16 | 1 | 1 | kW | 0 | 500 | Writable (All) | |
| CP Nominal Power | 118 | U16 | 1 | 1 | kW | 0 | 1000 | Writable (All) | |
| PV Start Voltage | 60 | U16 | 1 | 0.1 | V | 300 | 850 | Writable (PBD) | |
| Max MPPT Voltage | 61 | U16 | 1 | 0.1 | V | 300 | 1500 | Writable (PBD) | |
| Min MPPT Voltage | 62 | U16 | 1 | 0.1 | V | 300 | 1500 | Writable (PBD) | |
| PV Start Power | 63 | U16 | 1 | 0.1 | kW | 0 | 500 | Writable (PBD) | |
| Grid Power UP Limit | 65 | U16 | 1 | 1 | kW | 0 | 500 | Writable (All) | |
| Generator Start SOC | 66 | U16 | 1 | 1 | % | 0 | 100 | Writable (All) | |
| Generator Stop SOC | 67 | U16 | 1 | 1 | % | 0 | 100 | Writable (All) | |
| Frequency Shift Enable | 79 | U16 | 1 | 1 | | | | PCS | |
| PV Voltage | 80 | U16 | 1 | 0.1 | V | | | All | |
| PV Current | 83 | U16 | 1 | 0.1 | A | | | All | |
| Battery Charging Saturation | 150 | U16 | 1 | 1 | | 0 | 10 | Writable (All) | |
| Battery Group Number | 151 | U16 | 1 | 1 | | 0 | 100 | Writable (All) ||
| Battery Unit Number | 152 | U16 | 1 | 1 | | 0 | 50000 | Writable (All) | |
| Battery Capacity | 153 | U16 | 1 | 1 | Ah | 0 | 50000 | Writable (All) |  |
| Charge Current Limit | 154 | U16 | 1 | 0.1 | A | 0 | 10000 | Writable (All) | |
| Discharge current limit | 155 | U16 | 1 | 0.1 | A | 0 | 1000 | Writable (All) | |
| Float Charging Voltage | 156 | U16 | 1 | 1 | mV | 0 | 50000 | Writable (All) |  |
| Battery Low Voltage Warning | 157 | U16 | 1 | 1 | mV | 0 | 50000 | Writable (All) |  |
| Battery Low Voltage Fault | 158 | U16 | 1 | 1 | mV | 0 | 50000 | Writable (All) |  |
| Battery High Voltage Fault | 159 | U16 | 1 | 1 | mV | 0 | 50000 | Writable (All) |  |
| Battery Start Voltage | 160 | U16 | 1 | 1 | mV | 0 | 50000 | Writable (All) |   |
| Single PV to Off-grid | 161 | U16 | 1 | 1 | mV | 0 | 50000 | Writable (All) |   |
| Discharge Cutoff Voltage | 162 | U16 | 1 | 1 | mV | 0 | 50000 | Writable (All) |   |
| Float Charging Current | 163 | U16 | 1 | 10 | mA | | | All | |
| Battery Discharging Current Setpoint | 172 | U16 | 1 | 1 | A | 0 | 1000 | Writable (HPS) | |
| Battery Power Export to Grid Set | 174 | U16 | 1 | 1 | kW | 0 | 150 | Writable (All) | |
| BMS Voltage Judge Enable | 176 | U16 | 1 | 1 | | 0 | 1 | Writable (HPS/PCS) | |
| Discharge Recover SOC | 177 | U16 | 1 | 1 | % | 0 | 100 | Writable (HPS/PCS) | |
| Charge Cutoff SOC | 178 | U16 | 1 | 1 | % | 0 | 100 | PCS / Writable (All) | |
| Grid Charge SOC Enable | 179 | U16 | 1 | 1 | | 0 | 1 | Writable (HPS) | |
| Serial Number | 180 | UTF8 | 5 | 1 | | | | All | |
| Max Grid Charge Power | 225 | U16 | 1 | 0.1 | kW | 0 | 150 | Writable (All) | |
| Forced Charge Enable | 229 | U16 | 1 | 1 | | | | Writable (All) | |
| Reactive Power Regulation Mode | 250 | U16 | 1 | 1 | | 1 | 3 | Writable (HPS/PCS/HPSTL) | Select. 1 = fixed PF, 2 = PF(P) curve (unsafe), 3 = fixed reactive |
| Power Factor Reference Sign | 251 | U16 | 1 | 1 | | 0 | 1 | Writable (HPS/PCS/HPSTL) | Select. 0 = lagging (absorb), 1 = leading (supply) |
| Power Factor Reference | 252 | U16 | 1 | 0.001 | | 0 | 1 | Writable (HPS/PCS/HPSTL) | step 0.001 |
| Reactive Reference Sign | 263 | U16 | 1 | 1 | | 0 | 1 | Writable (HPS/PCS/HPSTL) | Select. Same convention as 251 |
| Reactive Reference | 264 | U16 | 1 | 1 | kVar | 0 | 300 | Writable (HPS/PCS/HPSTL) | |
| Reactive Lock Enable | 267 | U16 | 1 | 1 | | | | Writable (HPS/PCS/HPSTL) | Pins Q, overrides the setpoint |
| Grid Charge Cutoff SOC | 340 | U16 | 1 | 1 | % | 0 | 100 | Writable (All) | |

### Battery Config — interpretation

Sourced from the ATESS Modbus RTU V3.22 protocol (section 3 / 5, register block 150–179). 

- **Battery Group Number (151)** — number of battery strings (groups) wired in parallel. Used by the inverter to scale per-string current limits.
- **Battery Unit Number (152)** — number of battery units (modules) per string. Together with the group count this defines the total pack topology.
- **Battery Capacity (153)** — nominal capacity per string in Ah; drives charge/discharge C-rate calculations.
- **Float Charging Voltage (156)** — per-cell float voltage target once the pack is fully charged. Inverter holds this voltage to keep the pack topped up.
- **Battery Low Voltage Warning (157)** — per-cell threshold at which a soft low-voltage alarm is raised (no shutdown).
- **Battery Low Voltage Fault (158)** — per-cell threshold for a hard under-voltage fault; the inverter will trip discharge.
- **Battery High Voltage Fault (159)** — per-cell threshold for a hard over-voltage fault; the inverter will trip charging.
- **Battery Start Voltage (160)** — minimum per-cell voltage required before the inverter is allowed to begin discharging from a stopped state.
- **Single PV to Off-grid (161)** — per-cell battery voltage above which "single PV" mode (PV-only off-grid backup with no battery use) is permitted to switch to using the battery.
- **Discharge Cutoff Voltage (162)** — per-cell voltage at which discharge is forced to stop, independent of SOC.
- **Battery Discharging Current Setpoint (172, HPS only)** — commanded discharge current limit in A. Used to cap battery output current irrespective of inverter rating.
- **BMS Voltage Judge Enable (176, HPS/PCS)** — when on, the inverter ignores the SOC-based start/stop logic and instead gates charge/discharge on BMS-reported cell voltages (157–162).
- **Discharge Recover SOC (177, HPS/PCS)** — once discharge has stopped on a low-SOC trip, this is the SOC at which discharging is permitted to resume (hysteresis recovery point).
- **Grid Charge SOC Enable (179, HPS only)** — boolean enable for grid-charge-by-SOC control. Documented as "Freedom customisation" with range 0~1; modelled here as a switch but worth verifying on a real unit before relying on it.

## Input Registers

| Name | Addr | Type | Count | Multiplier | Unit | Group |
|------|------|------|-------|------------|------|-------|
| PV1 Voltage | 0 | I16 | 1 | 0.1 | V | All (except PCS) |
| Battery Voltage | 1 | I16 | 1 | 0.1 | V | All |
| Battery Current | 2 | I16 | 1 | 0.1 | A | All |
| PV1 DC Current | 3 | I16 | 1 | 0.1 | A | All (except PCS) |
| Output Voltage UV | 4 | U16 | 1 | 0.1 | V | PCS |
| Output Voltage VW | 5 | U16 | 1 | 0.1 | V | PCS |
| Output Voltage WU | 6 | U16 | 1 | 0.1 | V | PCS |
| Bypass Current U | 7 | U16 | 1 | 0.1 | A | PCS |
| Bypass Current V | 8 | U16 | 1 | 0.1 | A | PCS |
| Bypass Current W | 9 | U16 | 1 | 0.1 | A | PCS |
| Inductance Current A | 10 | U16 | 1 | 0.1 | A | PCS |
| Inductance Current B | 11 | U16 | 1 | 0.1 | A | PCS |
| Inductance Current C | 12 | U16 | 1 | 0.1 | A | PCS |
| Grid Bypass Voltage UV | 13 | U16 | 1 | 0.1 | V | PCS |
| Grid Bypass Voltage VW | 14 | U16 | 1 | 0.1 | V | PCS |
| Grid Bypass Voltage WU | 15 | U16 | 1 | 0.1 | V | PCS |
| Output Frequency | 16 | U16 | 1 | 0.01 | Hz | PCS |
| Battery Power | 17 | I16 | 1 | 0.1 | kW | All |
| Bypass Apparent Power | 18 | U16 | 1 | 0.1 | | PCS |
| Bypass Active Power | 19 | I16 | 1 | 0.1 | kW | PCS |
| Bypass Reactive Power | 20 | I16 | 1 | 0.1 | | PCS |
| Grid Frequency | 21 | U16 | 1 | 0.01 | Hz | PCS |
| Power factor symbol | 22 | U16 | 1 | 1 | | PCS | Sign of register 23. No device class: polarity undocumented |
| Power factor | 23 | U16 | 1 | 0.001 | | PCS | Magnitude only, always positive |
| Grid State | 28 | U16 | 1 | 1 | | PCS |
| Transformer temperature | 35 | I16 | 1 | 0.1 | °C | PCS |
| Ambient temperature | 36 | I16 | 1 | 0.1 | °C | All |
| Battery SOC | 47 | U16 | 1 | 1 | % | All |
| Load Apparent Power | 48 | U16 | 1 | 0.1 | | PCS |
| Load Active Power | 49 | U16 | 1 | 0.1 | kW | PCS |
| Load Reactive Power | 50 | I16 | 1 | 0.1 | | PCS |
| PV1 Power | 51 | I16 | 1 | 0.1 | kW | All (except PCS) |
| Load Power Factor | 52 | U16 | 1 | 0.001 | | PCS |
| Load Current U | 53 | I16 | 1 | 0.1 | A | PCS |
| Load Current V | 54 | I16 | 1 | 0.1 | A | PCS |
| Load Current W | 55 | I16 | 1 | 0.1 | A | PCS |
| Output Voltage U | 56 | U16 | 1 | 0.1 | V | PCS |
| Output Voltage V | 57 | U16 | 1 | 0.1 | V | PCS |
| Output Voltage W | 58 | U16 | 1 | 0.1 | V | PCS |
| PV Daily Power Generation | 62 | U16 | 1 | 0.1 | kWh | All (except PCS) |
| Total PV Generation | 64 | U32 | 2 | 0.1 | kWh | All (except PCS) |
| Total Battery Discharge Energy | 68 | U32 | 2 | 0.1 | kWh | All |
| Total Battery Charge Energy | 72 | U32 | 2 | 0.1 | kWh | All |
| Output Apparent Power | 78 | U16 | 1 | 0.1 | | PCS |
| Output Active Power | 79 | I16 | 1 | 0.1 | kW | PCS |
| Output Reactive Power | 80 | I16 | 1 | 0.1 | | PCS |
| Bypass Frequency | 81 | U16 | 1 | 0.01 | Hz | PCS |
| Daily Power Consumption | 82 | U16 | 1 | 0.1 | kWh | PCS |
| Total Load Energy | 84 | U32 | 2 | 0.1 | kWh | PCS |
| Daily Power From Grid | 88 | U16 | 1 | 0.1 | kWh | PCS |
| Total Grid Import | 90 | U32 | 2 | 0.1 | kWh | PCS |
| Daily Power To Grid | 94 | U16 | 1 | 0.1 | kWh | PCS |
| Total Grid Export | 96 | U32 | 2 | 0.1 | kWh | PCS |
| BMS Max Charge Current | 100 | U16 | 1 | 0.1 | A | All |
| BMS Max Discharge Current | 101 | U16 | 1 | 0.1 | A | All |
| PV2 Voltage | 105 | I16 | 1 | 0.1 | V | PBD |
| PV2 DC Current | 106 | I16 | 1 | 0.1 | A | PBD |
| PV2 Power | 107 | I16 | 1 | 0.1 | kW | PBD |
| PV Total Power | 108 | I16 | 1 | 0.1 | kW | PBD |
| Output Voltage | 109 | I16 | 1 | 0.1 | V | PBD |
| Output Current | 110 | I16 | 1 | 0.1 | A | PBD |
| Output Power | 113 | I16 | 1 | 0.1 | kW | PBD |
| PV Module Temperature | 114 | U16 | 1 | 0.1 | °C | PBD |
| PV3 Voltage | 123 | I16 | 1 | 0.1 | V | PBD |
| PV4 Voltage | 124 | I16 | 1 | 0.1 | V | PBD |
| PV5 Voltage | 125 | I16 | 1 | 0.1 | V | PBD |
| PV3 DC Current | 126 | I16 | 1 | 0.1 | A | PBD |
| PV4 DC Current | 127 | I16 | 1 | 0.1 | A | PBD |
| PV5 DC Current | 128 | I16 | 1 | 0.1 | A | PBD |
| PV3 Power | 132 | I16 | 1 | 0.1 | kW | PBD |
| PV4 Power | 133 | I16 | 1 | 0.1 | kW | PBD |
| PV5 Power | 134 | I16 | 1 | 0.1 | kW | PBD |
| Output Current U | 135 | I16 | 1 | 0.1 | A | PCS |
| Output Current V | 136 | I16 | 1 | 0.1 | A | PCS |
| Output Current W | 137 | I16 | 1 | 0.1 | A | PCS |
| System battery current | 162 | I16 | 1 | 0.1 | A | PCS |
| BMS Total Voltage | 164 | I16 | 1 | 0.1 | V | PCS |
| BMS Total Current | 165 | I16 | 1 | 0.1 | A | PCS |
| BMS Max V Group Nr | 168 | U8H | 1 | 1 | | PCS |
| BMS Min V Group Nr | 168 | U8L | 1 | 1 | | PCS |
| BMS Max. Temperature | 171 | I8H | 1 | 1 | °C | All |
| BMS Min. Temperature | 171 | I8L | 1 | 1 | °C | All |
| BMS Min V Unit Nr | 172 | U8H | 1 | 1 | | PCS |
| BMS Min V Unit Box Nr | 172 | U8L | 1 | 1 | | PCS |
| BMS Max V Unit Nr | 173 | U8H | 1 | 1 | | PCS |
| BMS Max V Unit Box Nr | 173 | U8L | 1 | 1 | | PCS |
| BMS Max. Cell Voltage | 174 | U16 | 1 | 1 | mV | All |
| BMS Min. Cell Voltage | 175 | U16 | 1 | 1 | mV | All |
| BMS Battery Status | 176 | U8H | 1 | 1 | | PCS |
| BMS System Status | 176 | U8L | 1 | 1 | | PCS |
| BMS Level 1 Alarm | 177 | U16 | 1 | 1 | | PCS |
| BMS Level 2 Alarm | 178 | U16 | 1 | 1 | | PCS |
| BMS Level 3 Protection | 179 | U16 | 1 | 1 | | PCS |
| Running State | 180 | U16 | 1 | 1 | | PCS |
| Fault Alarm 1 | 181 | U16 | 1 | 1 | | PCS |
| Fault Alarm 2 | 182 | U16 | 1 | 1 | | PCS |
| Fault Alarm 3 | 183 | U16 | 1 | 1 | | PCS |
| Fault Alarm 4 | 184 | U16 | 1 | 1 | | PCS |
| Fault Alarm 5 | 185 | U16 | 1 | 1 | | PCS |
| Fault Alarm 6 | 186 | U16 | 1 | 1 | | PCS |
| Fault Alarm 7 | 187 | U16 | 1 | 1 | | PCS |
| Fault Alarm 8 | 188 | U16 | 1 | 1 | | PCS |
| Running State Bitwise | 190 | U16 | 1 | 1 | | PCS |
| Operation Mode | 192 | U16 | 1 | 1 | | All |
| PBD Running State | 206 | U16 | 1 | 1 | | PBD |
| PBD Fault Alarm 1 | 207 | U16 | 1 | 1 | | PBD |
| PBD Fault Alarm 2 | 208 | U16 | 1 | 1 | | PBD |
| PBD Fault Alarm 3 | 209 | U16 | 1 | 1 | | PBD |
| PBD Fault Alarm 4 | 210 | U16 | 1 | 1 | | PBD |
| PBD Fault Alarm 5 | 211 | U16 | 1 | 1 | | PBD |
| PBD Fault Alarm 6 | 212 | U16 | 1 | 1 | | PBD |
| PBD Running State Bitwise | 213 | U16 | 1 | 1 | | PBD |
| PBD Operation Mode | 215 | U16 | 1 | 1 | | PBD |
| System battery power | 228 | I16 | 1 | 0.1 | kW | PCS |
| CP Power Limit | 229 | I16 | 1 | 0.1 | kW | PCS |
| Hardware Version | 270 | UTF8 | 10 | 1 | | All |


# Active Power Control

## PCS +PBD config
State: Working

Control the Active Power generated by writing to the Output Power Limit on the PBD devices. 

## HPS config
State: Unknown

- 33 PV Power Setting write -> Illegal data address/ illegal data value error (tested with 10 Active Power regulation ON & 12 Manual adjustment enable ON / OFF )
- 32 EMS Enable -> ON - can write, but disrupts peak shaving mode. Seems to throttle PV.
# Reactive Power Control

State: Confirmed on an HPS in the field. The mode legend is corroborated by the
PCS100/250/500/630 user manual, 2023-05-06.

## Register block

| Register | Function | Notes |
|---|---|---|
| 11 | Reactive power regulation enable | Gates the entire block. Nothing below takes effect while this is 0. |
| 250 | Mode selection | 1 = fixed power factor, 2 = power factor curve, 3 = fixed reactive power. |
| 251 / 252 | Power factor sign / reference | Consumed by mode 1 only. |
| 253-262 | Five-point cos-phi(P) curve | Consumed by mode 2. Not defined in this add-on. See the warning below. |
| 263 / 264 | Reactive sign / reference | Consumed by mode 3 only. |
| 267 | Reactive lock enable | Must be off. When on it pins Q and overrides the setpoint. |
| 286 / 287 | Reactive flow Kp / Ki | Not defined in this add-on. The manufacturer's manual states these must not be changed without ATESS authorisation. |

## Write ordering

**Register 250 must be written before register 264, and the mode must be 3 for the
reactive reference to be accepted.**

While register 250 holds any value other than 3, a write to 264 completes normally at the
Modbus layer. Function code 0x06 returns a valid echo response, the add-on logs no error,
and the value is discarded by the firmware. The readback of 264 stays at its previous
value, which is the only signal that the write did not take.

This was observed directly: three successive writes of 3 kVAr to register 264 with the
mode at 1 produced no change in either the readback or in bypass reactive power. The same
write after setting mode 3 took effect immediately.

Consequences for any controller:

1. Write 250 = 3 once at start-up, and verify by readback before writing 264.
2. Treat a 264 readback that does not track the commanded value as a mode fault, not as a
   communications fault. Re-assert the mode rather than retrying the setpoint.
3. Re-assert the mode after any inverter restart, since persistence across a power cycle
   has not been established.

The same ordering is assumed to apply to registers 251/252 under mode 1, though this has
not been tested.

## Mode 2 is unsafe with undefined curve points

Mode 2 interpolates the five-point power-factor-versus-power curve held in registers
253-262. This add-on does not define those registers, so on a unit that has never had them
configured they read zero, and a curve of all zeroes requests power factor 0 — that is,
pure reactive output.

Selecting mode 2 on an uncommissioned unit drove roughly 86 kVAr and 115-120 A per phase
within two seconds. The unit recovered cleanly when the mode was set back to 1, but a
sustained excursion of this size inside one demand interval is enough to set a monthly
maximum-demand peak on its own.

The mode is exposed in the entity list, labelled `Power Factor Curve (unsafe)`, rather
than hidden. Hiding it would not prevent a direct register write, and the label carries
the warning to the point of use. Do not select it unless 253-262 have been configured.

The PCS manual states that only modes 1 and 3 take effect. That is not true of the HPS
firmware tested here.

## Sign convention

For both 251 and 263: 0 = lagging (the unit absorbs reactive power), 1 = leading (the unit
supplies it). Confirmed against measured bypass reactive power, and consistent with the
manual.

Supplying reactive power is the direction that cancels an inductive site load. Getting the
sign wrong does not fault — it adds to the load instead of offsetting it, roughly doubling
the reactive component at the meter.

## Mode 1 follows the unit's own active output

Fixed-PF mode regulates the power factor at the inverter's own terminals, not at the point
of common coupling. A regression of output reactive power against the unit's own active
output gives a slope of 0.374 against a theoretical 0.484 for the commanded PF of 0.90;
the same regression against site load does not hold.

This matters when the objective is site power factor. The unit's active output is smallest
exactly when the load's reactive demand is largest — during a peak-shaving half-hour where
the battery does not hold, active output approaches zero, and mode 1 delivers close to no
correction at the half-hour that sets the demand charge. The nameplate limit of 0.8
leading also caps mode 1 at Q <= 0.75 x P of the unit's own output.

Mode 3 has no such coupling and is the correct choice for site-level correction.

## Register 264 is an injection command, not a target

Register 264 commands the reactive power the unit injects. It is not a setpoint for
reactive power at the grid, and the unit does not regulate to it in closed loop.

The evidence is a slope test below 60 kW of site load, where the site's reactive demand is
still proportional to load. Site reactive power against load gave a slope of -0.476 at
setpoint 0 and -0.606 at setpoint 15, a difference of -0.130. A grid-referenced regulator
would have produced a slope near +0.6, since it would have cancelled the load-proportional
term. Commanded and measured signs also disagree in a way a regulator would not permit.

### Response is non-linear

Measured steady-state injection against commanded value, at constant site load:

| Commanded (kVAr) | Measured injection (kVAr) |
|---|---|
| 10 | ~23 |
| 15 | ~23 |
| 20 | ~31 |
| 30 | ~56 |

The response has both a floor and a gain well above unity, and it is not monotonic in a
useful sense between 10 and 15. **Command values are not kVAr.** Any control law that
assumes they are will over-inject: a command of 55, within the register's declared range
of 0-300, would ask for roughly 100 kVAr of real injection.

These four points come from one site, one unit and one load condition, and are steady-state
only. They are sufficient to establish that the relationship is non-linear and to bound a
safe command range; they are not sufficient to fit a transfer function. Characterising it
properly needs a sweep across the full command range at several load levels, with the
transient response logged.

### Resolution floor

The unit cannot hold a small reactive output. When the commanded injection nearly cancels
the site's reactive demand, the measured grid reactive power oscillates about zero,
changing sign roughly every four seconds. Only 6.4% of ten-day samples fall within
+/-9 kVAr of zero, and the distribution of grid reactive power at a fixed setpoint is
unimodal at high load but bimodal at low load.

A controller should therefore aim for a non-zero residual rather than for zero, and should
not use a small deadband around zero as its steady-state target.

## Feedback registers

| Input register | Quantity | Scaling |
|---|---|---|
| 18 | Bypass apparent power | 0.1 kVA |
| 19 | Bypass active power | 0.1 kW, positive = import |
| 20 | Bypass reactive power | 0.1 kVAr |
| 50 | Load reactive power | |
| 52 | Load power factor | |
| 80 | Output reactive power | |

The bypass registers are the grid-side quantities and are the correct feedback for
site-level correction. There is no grid power factor register; compute it as 19 / 18.

Registers 22 and 23 report the unit's own output power factor, not the grid's, and read
zero while the unit is in bypass. They must not be used as a site power factor measurement.

## Bypass

In Battery First with PV down and the battery idle, the load transfers to the bypass
contactor and the inverter stands aside. A bypassed unit injects no reactive power at all.
Correction is available only while the unit is inverting, so a controller should gate on
inverter state and must not interpret an absent reactive response in bypass as a fault.
