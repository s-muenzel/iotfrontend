"""modbus_handler.py: Modbus communication for Solaranlagen (solar systems)."""
import logging
import pymodbus.client as ModbusClient
from pymodbus import ModbusException


def get_power_status():
    """Read power information from Modbus (Solar and House).
    
    Returns:
        dict: Dictionary with 'p_solar' and 'p_haus' in Watts
              Returns None if connection fails
    """
    try:
        modclient = ModbusClient.ModbusTcpClient(
            host="192.168.2.56",
            port="1502"
        )
        
        if not modclient.connect():
            logging.error("Unable to connect to modbus server")
            return None
        
        try:
            # Read solar power
            rr = modclient.read_holding_registers(0x9c93, count=2)
            values = modclient.convert_from_registers(rr.registers, data_type=modclient.DATATYPE.INT16)
            p_solar = values[0] * (10 ** values[1])
            
            # Read house power
            rr = modclient.read_holding_registers(0x9d0e, count=5)
            values = modclient.convert_from_registers(rr.registers, data_type=modclient.DATATYPE.INT16)
            p_haus = values[0] * (10 ** values[4])
            
            return {
                'p_solar': p_solar,
                'p_haus': p_haus,
                'p_grid': p_haus - p_solar,
                'p_battery': 0
            }
        except ModbusException as exc:
            logging.error("Received ModbusException: %s", exc)
            return None
        finally:
            modclient.close()
    except Exception as err:
        logging.error("Error reading modbus data: %s", err)
        return None
