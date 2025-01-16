# Configuration
Before using, state all the modbus devices in `config.yaml`. Multiple servers and clients can be added

## Server 
Each server should be defined as 
```
  - name: "SunGrow Inverter 1"
    nickname: "SG1"
    serialnum: "12345678"
    server_type: "SunGrow Logger"
    connected_client: "Client1"  
    device_addr: 1
```
- `server_type` is used to select the class of server to instantiate. A Sungrow_Inverter and Sungrow_Logger, with their register maps are pre-defined, but additional classes can be added. See adding custom server types
- `connected_client` specifies on which client bus (abstraction of serial port or tcp ip) the server is connected. Most systems use a single client.
- `device_addr` specifies the Modbus slave address of tthe server

## Client
Each client should be defined as
```
- name: "ModebusTCP"
    nickname: "Client1"
    type: "TCP"
    connection_specs: "Sungrow_Logger"
    port: "/dev/tty1"
```
- `port` is only required if `type` is "RTU" 
- `type` can be one of "RTU" or "TCP"
- `connection_specs` defines the name of the entry under `connection_specs` for the relevant client where e.g. baudrate or ip is defined

## Connection specs
TODO
## Adding custom server types

## Client
### Defini
`config.yaml` contains a template for Modbus RTT as defined for SunGrow inverters under options>connection_specs. Add a custom entry and specify it for each client in `config.yaml`
## Server
### Defining a new Server type
Inherit from server class in `server.py`. 
<!-- TODO -->
