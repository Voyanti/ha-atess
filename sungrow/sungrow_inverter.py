class SungrowInverter(Server):
    """
    Sungrow
        SG110CX
        SGKTL-20        not found
        SG33CX
        SG80KTL-20
    """

    output_types = ["Two Phase", "3P4L", "3P3L"] # register 3x  5002

    # ROM 3x registers
    self.registers = {
        {"name": "Serial Number", "addr": 4990, "count": 10, "dtype": "UTF-8", "multiplier": 1, "unit": ""},
        {"name": "Device Type Code", "addr": 5000, "count": 1, "dtype": "U16", "multiplier": 1, "unit": ""},
        {"name": "Nominal Active Power", "addr": 5001, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "kW"},
        {"name": "Output Type", "addr": 5002, "count": 1, "dtype": "U16", "multiplier": 1, "unit": ""},
        {"name": "Daily Power Yields", "addr": 5003, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "kWh"},
        {"name": "Total Power Yields", "addr": 5004, "count": 2, "dtype": "U32", "multiplier": 1, "unit": "kWh"},
        {"name": "Total Running Time", "addr": 5006, "count": 2, "dtype": "U32", "multiplier": 1, "unit": "h"},
        {"name": "Internal Temperature", "addr": 5008, "count": 1, "dtype": "S16", "multiplier": 0.1, "unit": "°C"},
        {"name": "Total Apparent Power", "addr": 5009, "count": 2, "dtype": "U32", "multiplier": 1, "unit": "VA"},                  # only valid for specific models
        {"name": "MPPT 1 Voltage", "addr": 5011, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "MPPT 1 Current", "addr": 5012, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "MPPT 2 Voltage", "addr": 5013, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "MPPT 2 Current", "addr": 5014, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "MPPT 3 Voltage", "addr": 5015, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "MPPT 3 Current", "addr": 5016, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "Total DC Power", "addr": 5017, "count": 2, "dtype": "U32", "multiplier": 1, "unit": "W"},
        {"name": "A-B Line Voltage/Phase A Voltage", "addr": 5019, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},     # 5019-5021 two output types check TODO
        {"name": "B-C Line Voltage/Phase B Voltage", "addr": 5020, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "C-A Line Voltage/Phase C Voltage", "addr": 5019, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "Phase A Current", "addr": 5022, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "Phase B Current", "addr": 5023, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "Phase C Current", "addr": 5024, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "Total Active Power", "addr": 5031, "count": 2, "dtype": "U32", "multiplier": 1, "unit": "W"},
        {"name": "Total Reactive Power", "addr": 5033, "count": 2, "dtype": "U32", "multiplier": 1, "unit": "Var"},
        {"name": "Power Factor", "addr": 5035, "count": 1, "dtype": "S16", "multiplier": 0.001, "unit": ""},                        # >0: leading, <0 lagging
        {"name": "Grid Frequency", "addr": 5036, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "Hz"},
        {"name": "Work State", "addr": 5038, "count": 1, "dtype": "U16", "multiplier": 1, "unit": ""},                              
        {"name": "Fault/Alarm Code 1", "addr": 5045, "count": 1, "dtype": "U16", "multiplier": 1, "unit": ""},                      # can also get fault time registers 5039-5045
        {"name": "Nominal Reactive Power", "addr": 5049, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "kVar"},
        {"name": "Nominal Reactive Power", "addr": 5049, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "kVar"},
        {"name": "Array Insulation Resistance", "addr": 5071, "count": 1, "dtype": "U16", "multiplier": 1, "unit": "kΩ"},
        {"name": "Active Power Regulation Setpoint", "addr": 5077, "count": 2, "dtype": "U32", "multiplier": 1, "unit": "W"},
        {"name": "Reactive Power Regulation Setpoint", "addr": 5079, "count": 2, "dtype": "S32", "multiplier": 1, "unit": "Var"},
        {"name": "Work State (Extended)", "addr": 5081, "count": 2, "dtype": "U32", "multiplier": 1, "unit": ""},
        {"name": "Meter Power", "addr": 5083, "count": 2, "dtype": "S32", "multiplier": 1, "unit": "W"},
        {"name": "Meter A Phase Power", "addr": 5085, "count": 2, "dtype": "S32", "multiplier": 1, "unit": "W"},
        {"name": "Meter B Phase Power", "addr": 5087, "count": 2, "dtype": "S32", "multiplier": 1, "unit": "W"},
        {"name": "Meter C Phase Power", "addr": 5089, "count": 2, "dtype": "S32", "multiplier": 1, "unit": "W"},
        {"name": "Load Power", "addr": 5091, "count": 2, "dtype": "S32", "multiplier": 1, "unit": "W"},
        {"name": "Daily Export Energy", "addr": 5093, "count": 2, "dtype": "U32", "multiplier": 0.1, "unit": "kWh"},
        {"name": "Total Export Energy", "addr": 5095, "count": 2, "dtype": "U32", "multiplier": 0.1, "unit": "kWh"},
        {"name": "Daily Import Energy", "addr": 5097, "count": 2, "dtype": "U32", "multiplier": 0.1, "unit": "kWh"},
        {"name": "Total Import Energy", "addr": 5099, "count": 2, "dtype": "U32", "multiplier": 0.1, "unit": "kWh"},
        {"name": "Daily Direct Energy Consumption", "addr": 5101, "count": 2, "dtype": "U32", "multiplier": 0.1, "unit": "kWh"},
        {"name": "Total Direct Energy Consumption", "addr": 5103, "count": 2, "dtype": "U32", "multiplier": 0.1, "unit": "kWh"},
        {"name": "Daily Running Time", "addr": 5113, "count": 1, "dtype": "U16", "multiplier": 1, "unit": "min"},
        {"name": "Present Country", "addr": 5114, "count": 1, "dtype": "U16", "multiplier": 1, "unit": ""},
        {"name": "MPPT 4 Voltage", "addr": 5115, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "MPPT 4 Current", "addr": 5116, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "MPPT 5 Voltage", "addr": 5117, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "MPPT 5 Current", "addr": 5118, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "MPPT 6 Voltage", "addr": 5119, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "MPPT 6 Current", "addr": 5120, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "MPPT 7 Voltage", "addr": 5121, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "MPPT 7 Current", "addr": 5122, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "MPPT 8 Voltage", "addr": 5123, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "MPPT 8 Current", "addr": 5124, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "Monthly Power Yields", "addr": 5128, "count": 2, "dtype": "U32", "multiplier": 0.1, "unit": "kWh"},
        {"name": "MPPT 9 Voltage", "addr": 5130, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "MPPT 9 Current", "addr": 5131, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "MPPT 10 Voltage", "addr": 5132, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "MPPT 10 Current", "addr": 5133, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "MPPT 11 Voltage", "addr": 5134, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "MPPT 11 Current", "addr": 5135, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "MPPT 12 Voltage", "addr": 5136, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "MPPT 12 Current", "addr": 5137, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "A"},
        {"name": "Total Power Yields (Increased Accuracy)", "addr": 5144, "count": 2, "dtype": "U32", "multiplier": 0.1, "unit": "kWh"},
        {"name": "Negative Voltage to the Ground", "addr": 5146, "count": 1, "dtype": "S16", "multiplier": 0.1, "unit": "V"},
        {"name": "Bus Voltage", "addr": 5147, "count": 1, "dtype": "U16", "multiplier": 0.1, "unit": "V"},
        {"name": "Grid Frequency (Increased Accuracy)", "addr": 5148, "count": 1, "dtype": "U16", "multiplier": 0.01, "unit": "Hz"},
        {"name": "PID Work State", "addr": 5150, "count": 1, "dtype": "U16", "multiplier": 1, "unit": ""},
        {"name": "PID Alarm Code", "addr": 5151, "count": 1, "dtype": "U16", "multiplier": 1, "unit": ""}
        # TODO Combiner Board information p12 - need to check availability before reading?
    }

    # Params 4x register (write)
    settable_params = {}

    # Device Work state (Appendix 1) register 5038
    device_work_state = {
        0x0000: "Run",  # Grid-connected power generation, normal operation mode
        0x8000: "Stop",  # Inverter is stopped
        0x1300: "Key stop",  # Manual stop via app, internal DSP stops
        0x1500: "Emergency Stop",  
        0x1400: "Standby",  # Insufficient DC side input, waiting within standby duration
        0x1200: "Initial standby",  # Initial power-on standby state
        0x1600: "Starting",  # Initializing and synchronizing with grid
        0x9100: "Alarm run",  # Warning information detected
        0x8100: "Derating run",  # Active derating due to environmental factors
        0x8200: "Dispatch run",  # Running according to monitoring background scheduling
        0x5500: "Fault",  # Automatic stop and AC relay disconnect on fault
        0x2500: "Communicate fault"  # Unconfirmed state
    }
    # Device Work state (Appendix 2) register 5081-5082 
    # deive_work_state_2 = {}
    # Fault Codes (Appendix 3)
    fault_codes = {}
    # Country Info (Appendix 4)
    # countr_info = {}
    # PID Alarm COdes (Appendix 5)
    # pid_alarm_code = {}
    # Device Information (Appendix 6)
    device_info = {
        # TODO what are power limited ranges in appendix 6
        # verified from doc
        'SG33CX': {'type_code': '0x2C00', 'mppt': 3, 'string_per_mppt': 2},
        'SG110CX': {'type_code': '0x2C06', 'mppt': 9, 'string_per_mppt': 2},
        'SG80KTL-20': {'type_code': '0x0138', 'mppt': 1, 'string_per_mppt': 18},
        # not verified yet
        'SG30KTL': {'type_code': '0x27', 'mppt': 2, 'string_per_mppt': 4},
        'SG10KTL': {'type_code': '0x26', 'mppt': 2, 'string_per_mppt': 3},
        'SG12KTL': {'type_code': '0x29', 'mppt': 2, 'string_per_mppt': 3},
        'SG15KTL': {'type_code': '0x28', 'mppt': 2, 'string_per_mppt': 3},
        'SG20KTL': {'type_code': '0x2A', 'mppt': 2, 'string_per_mppt': 3},
        'SG30KU': {'type_code': '0x2C', 'mppt': 2, 'string_per_mppt': 5},
        'SG36KTL': {'type_code': '0x2D', 'mppt': 2, 'string_per_mppt': 5},
        'SG36KU': {'type_code': '0x2E', 'mppt': 2, 'string_per_mppt': 5},
        'SG40KTL': {'type_code': '0x2F', 'mppt': 2, 'string_per_mppt': 4},
        'SG40KTL-M': {'type_code': '0x0135', 'mppt': 3, 'string_per_mppt': 3},
        'SG50KTL-M': {'type_code': '0x011B', 'mppt': 4, 'string_per_mppt': 3},
        'SG60KTL-M': {'type_code': '0x0131', 'mppt': 4, 'string_per_mppt': 4},
        'SG60KU': {'type_code': '0x0136', 'mppt': 1, 'string_per_mppt': 8},
        'SG30KTL-M': {'type_code': '0x0141', 'mppt': 3, 'string_per_mppt': '3;3;2'},
        'SG30KTL-M-V31': {'type_code': '0x70', 'mppt': 3, 'string_per_mppt': '3;3;2'},
        'SG33KTL-M': {'type_code': '0x0134', 'mppt': 3, 'string_per_mppt': '3;3;2'},
        'SG36KTL-M': {'type_code': '0x74', 'mppt': 3, 'string_per_mppt': '3;3;2'},
        'SG33K3J': {'type_code': '0x013D', 'mppt': 3, 'string_per_mppt': 3},
        'SG49K5J': {'type_code': '0x0137', 'mppt': 4, 'string_per_mppt': 3},
        'SG34KJ': {'type_code': '0x72', 'mppt': 2, 'string_per_mppt': 4},
        'LP_P34KSG': {'type_code': '0x73', 'mppt': 1, 'string_per_mppt': 4},
        'SG50KTL-M-20': {'type_code': '0x011B', 'mppt': 4, 'string_per_mppt': 3},
        'SG60KTL': {'type_code': '0x010F', 'mppt': 1, 'string_per_mppt': 14},
        'SG80KTL': {'type_code': '0x0138', 'mppt': 1, 'string_per_mppt': 18},
        'SG60KU-M': {'type_code': '0x0132', 'mppt': 4, 'string_per_mppt': 4},
        'SG5KTL-MT': {'type_code': '0x0147', 'mppt': 2, 'string_per_mppt': 1},
        'SG6KTL-MT': {'type_code': '0x0148', 'mppt': 2, 'string_per_mppt': 1},
        'SG8KTL-M': {'type_code': '0x013F', 'mppt': 2, 'string_per_mppt': 1},
        'SG10KTL-M': {'type_code': '0x013E', 'mppt': 2, 'string_per_mppt': 1},
        'SG10KTL-MT': {'type_code': '0x2C0F', 'mppt': 2, 'string_per_mppt': 2},
        'SG12KTL-M': {'type_code': '0x013C', 'mppt': 2, 'string_per_mppt': 2},
        'SG15KTL-M': {'type_code': '0x0142', 'mppt': 2, 'string_per_mppt': 2},
        'SG17KTL-M': {'type_code': '0x0149', 'mppt': 2, 'string_per_mppt': 2},
        'SG20KTL-M': {'type_code': '0x0143', 'mppt': 2, 'string_per_mppt': 2},
        'SG80KTL-M': {'type_code': '0x0139', 'mppt': 4, 'string_per_mppt': 4},
        'SG111HV': {'type_code': '0x014C', 'mppt': 1, 'string_per_mppt': 1},
        'SG125HV': {'type_code': '0x013B', 'mppt': 1, 'string_per_mppt': 1},
        'SG125HV-20': {'type_code': '0x2C03', 'mppt': 1, 'string_per_mppt': 1},
        'SG30CX': {'type_code': '0x2C10', 'mppt': 3, 'string_per_mppt': 2},
        'SG36CX-US': {'type_code': '0x2C0A', 'mppt': 3, 'string_per_mppt': 2},
        'SG40CX': {'type_code': '0x2C01', 'mppt': 4, 'string_per_mppt': 2},
        'SG50CX': {'type_code': '0x2C02', 'mppt': 5, 'string_per_mppt': 2},
        'SG60CX-US': {'type_code': '0x2C0B', 'mppt': 5, 'string_per_mppt': 2},
        'SG250HX': {'type_code': '0x2C0C', 'mppt': 12, 'string_per_mppt': 2},
        'SG250HX-US': {'type_code': '0x2C11', 'mppt': 12, 'string_per_mppt': 2},
        'SG100CX': {'type_code': '0x2C12', 'mppt': 12, 'string_per_mppt': 2},
        'SG100CX-JP': {'type_code': '0x2C12', 'mppt': 12, 'string_per_mppt': 2},
        'SG250HX-IN': {'type_code': '0x2C13', 'mppt': 12, 'string_per_mppt': 2},
        'SG25CX-SA': {'type_code': '0x2C15', 'mppt': 3, 'string_per_mppt': 2},
        'SG75CX': {'type_code': '0x2C22', 'mppt': 9, 'string_per_mppt': 2},
        'SG3.0RT': {'type_code': '0x243D', 'mppt': 2, 'string_per_mppt': 1},
        'SG4.0RT': {'type_code': '0x243E', 'mppt': 2, 'string_per_mppt': 1},
        'SG5.0RT': {'type_code': '0x2430', 'mppt': 2, 'string_per_mppt': 1},
        'SG6.0RT': {'type_code': '0x2431', 'mppt': 2, 'string_per_mppt': 1},
        'SG7.0RT': {'type_code': '0x243C', 'mppt': 2, 'string_per_mppt': '2;1'},
        'SG8.0RT': {'type_code': '0x2432', 'mppt': 2, 'string_per_mppt': '2;1'},
        'SG10RT': {'type_code': '0x2433', 'mppt': 2, 'string_per_mppt': '2;1'},
        'SG12RT': {'type_code': '0x2434', 'mppt': 2, 'string_per_mppt': '2;1'},
        'SG15RT': {'type_code': '0x2435', 'mppt': 2, 'string_per_mppt': 2},
        'SG17RT': {'type_code': '0x2436', 'mppt': 2, 'string_per_mppt': 2},
        'SG20RT': {'type_code': '0x2437', 'mppt': 2, 'string_per_mppt': 2}
    }

    # Appendix 7, 8, 9?
    