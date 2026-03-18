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
    serialnum: "A2340700442"
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

| Name | Addr | Type | Count | Multiplier | Unit | Min | Max | Group |
|------|------|------|-------|------------|------|-----|-----|-------|
| Device On/Off | 0 | U16 | 1 | 1 | | | | All |
| Grid And PV Charge Together | 8 | U16 | 1 | 1 | | | | Writable (All) |
| Bypass Cabinet Enable | 13 | U16 | 1 | 1 | | | | Writable (All) |
| BMS Communication Enable | 14 | U16 | 1 | 1 | | | | Writable (All) |
| Anti Reflux Enable | 16 | U16 | 1 | 1 | | | | Writable (All) |
| Mode selection | 26 | U16 | 1 | 1 | | | | Writable (All) |
| Device Type Code | 43 | U16 | 1 | 1 | | | | All |
| Grid Power Compensation | 44 | U16 | 1 | 0.1 | kW | 0 | 100 | Writable (All) |
| Discharge Cutoff SOC | 47 | U16 | 1 | 1 | % | 0 | 100 | Writable (All) |
| Output Power Limit | 58 | U16 | 1 | 1 | % | 0 | 120 | Writable (All) |
| CP Nominal Power | 118 | U16 | 1 | 1 | kW | 0 | 1000 | Writable (All) |
| PV Start Voltage | 60 | U16 | 1 | 0.1 | V | 300 | 850 | Writable (PBD) |
| Max MPPT Voltage | 61 | U16 | 1 | 0.1 | V | 300 | 1500 | Writable (PBD) |
| Min MPPT Voltage | 62 | U16 | 1 | 0.1 | V | 300 | 1500 | Writable (PBD) |
| PV Start Power | 63 | U16 | 1 | 0.1 | kW | 0 | 500 | Writable (PBD) |
| Grid Power UP Limit | 65 | U16 | 1 | 1 | kW | 0 | 500 | Writable (All) |
| Generator Start SOC | 66 | U16 | 1 | 1 | % | 0 | 100 | Writable (All) |
| Generator Stop SOC | 67 | U16 | 1 | 1 | % | 0 | 100 | Writable (All) |
| Frequency Shift Enable | 79 | U16 | 1 | 1 | | | | PCS |
| PV Voltage | 80 | U16 | 1 | 0.1 | V | | | All |
| PV Current | 83 | U16 | 1 | 0.1 | A | | | All |
| Battery Charging Saturation | 150 | U16 | 1 | 1 | | 0 | 10 | Writable (All) |
| Charge Current Limit | 154 | U16 | 1 | 0.1 | A | 0 | 10000 | Writable (All) |
| Discharge current limit | 155 | U16 | 1 | 0.1 | A | 0 | 1000 | Writable (All) |
| Float Charging Voltage | 156 | U16 | 1 | 1 | mV | | | All |
| Single PV to Off-grid | 161 | U16 | 1 | 1 | mV | | | All |
| Float Charging Current | 163 | U16 | 1 | 10 | mA | | | All |
| Battery Power Export to Grid Set | 174 | U16 | 1 | 1 | kW | 0 | 150 | Writable (All) |
| Charge Cutoff SOC | 178 | U16 | 1 | 1 | % | 0 | 100 | PCS / Writable (All) |
| Serial Number | 180 | UTF8 | 5 | 1 | | | | All |
| Max Grid Charge Power | 225 | U16 | 1 | 0.1 | kW | 0 | 150 | Writable (All) |
| Forced Charge Enable | 229 | U16 | 1 | 1 | | | | Writable (All) |
| Grid Charge Cutoff SOC | 340 | U16 | 1 | 1 | % | 0 | 100 | Writable (All) |

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
| Power factor symbol | 22 | U16 | 1 | 1 | | PCS |
| Power factor | 23 | U16 | 1 | 0.001 | | PCS |
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
