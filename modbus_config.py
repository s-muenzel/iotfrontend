"""modbus_config.py: Configuration for Modbus registers.

Contains definitions for Inverter and Meter Modbus registers
"""
import enum


class RegisterTyp(enum.Enum):
    """Enum for Modbus register types."""
    UINT16 = 1
    UINT32 = 2
    UINT64 = 3
    INT16 = 4
    SCALE = 5
    ACC32 = 6
    FLOAT32 = 7
    SEFLOAT = 8
    INT32 = 9
    STRING = 10


INVERTER_STATUS_MAP = [
    "Undefined",
    "Off",
    "Sleeping",
    "Grid Monitoring",
    "Producing",
    "Producing (Throttled)",
    "Shutting Down",
    "Fault",
    "Standby"
]

INVERTER_REGISTERS = {
    # name, address, length, type, description, unit, scaling
    "power_ac": (0x9c93, 1, RegisterTyp.INT16, "Power", "W", True),
    "power_ac_scale": (0x9c94, 1, RegisterTyp.SCALE, "Power Scale Factor", "", True),
    "energy_total": (0x9c9d, 2, RegisterTyp.ACC32, "Total Energy", "Wh", True),
    "energy_total_scale": (0x9c9f, 1, RegisterTyp.SCALE, "Total Energy Scale Factor", "", True),
    "temperature": (0x9ca7, 1, RegisterTyp.INT16, "Temperature", "°C", True),
    "temperature_scale": (0x9caa, 1, RegisterTyp.SCALE, "Temperature Scale Factor", "", True),
    "status": (0x9cab, 1, RegisterTyp.UINT16, "Status", INVERTER_STATUS_MAP, False),
}

METER_REGISTERS = {
    "power": (0x9d0e, 1, RegisterTyp.INT16, "Power", "W", True),
    "power_scale": (0x9d12, 1, RegisterTyp.SCALE, "Power Scale Factor", "", True),
    "power_apparent": (0x9d13, 1, RegisterTyp.INT16, "Power (Apparent)", "VA", True),
    "power_apparent_scale": (0x9d17, 1, RegisterTyp.SCALE, "Power (Apparent) Scale Factor", "", True),
    "power_reactive": (0x9d18, 1, RegisterTyp.INT16, "Power (Reactive)", "VAr", True),
    "power_reactive_scale": (0x9d1c, 1, RegisterTyp.SCALE, "Power (Reactive) Scale Factor", "", True),
    "power_factor": (0x9d1d, 1, RegisterTyp.INT16, "Power Factor", "", True),
    "power_factor_scale": (0x9d21, 1, RegisterTyp.SCALE, "Power Factor Scale Factor", "", True),
    "export_energy_active": (0x9d22, 2, RegisterTyp.UINT32, "Total Exported Energy (Active)", "Wh", True),
    "energy_active_scale1": (0x9d32, 1, RegisterTyp.SCALE, "Energy (Active) Scale Factor", "", True),
    "import_energy_active": (0x9d2a, 2, RegisterTyp.UINT32, "Total Imported Energy (Active)", "Wh", True),
    "energy_active_scale": (0x9d32, 1, RegisterTyp.SCALE, "Energy (Active) Scale Factor", "", True),
    "export_energy_apparent": (0x9d33, 2, RegisterTyp.UINT32, "Total Exported Energy (Apparent)", "VAh", True),
    "energy_apparent_scale2": (0x9d43, 1, RegisterTyp.SCALE, "Energy (Apparent) Scale Factor", "", True),
    "import_energy_apparent": (0x9d3b, 2, RegisterTyp.UINT32, "Total Imported Energy (Apparent)", "VAh", True),
    "energy_apparent_scale": (0x9d43, 1, RegisterTyp.SCALE, "Energy (Apparent) Scale Factor", "", True),
}
