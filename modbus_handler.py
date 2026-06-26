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
    p_solar = None
    p_grid = None
    p_battery = None
    soc = None
    # Read Solaredge inverter power and grid power from Modbus
    try:
        modclient = ModbusClient.ModbusTcpClient(
            host="192.168.2.56",
            port="1502"
        )
        
        if not modclient.connect():
            logging.error("Unable to connect to Solaredge server")
            return None
        
        try:
            # Read solar power
            rr = modclient.read_holding_registers(0x9c93, count=2)
            values = modclient.convert_from_registers(rr.registers, data_type=modclient.DATATYPE.INT16)
            p_solar = values[0] * (10 ** values[1])
            
            # Read grid power
            rr = modclient.read_holding_registers(0x9d0e, count=5)
            values = modclient.convert_from_registers(rr.registers, data_type=modclient.DATATYPE.INT16)
            p_grid = - values[0] * (10 ** values[4])
            
        except ModbusException as exc:
            logging.error("Received ModbusException: %s", exc)
        finally:
            modclient.close()
    except Exception as err:
        logging.error("Error reading modbus data: %s", err)
        return None

    # # Read Growatt battery power and state of charge (not implemented in this example, so we use placeholders)   
    # try:
    #     modclient = ModbusClient.ModbusTcpClient(
    #         host="192.168.2.57",
    #         port="502"
    #     )
        
    #     if not modclient.connect():
    #         logging.error("Unable to connect to Growatt server")
    #         return None
        
    #     # read charge power
    #     rr = modclient.read_holding_registers(1128,count=2)
    #     values_c = modclient.convert_from_registers(rr.registers, data_type=modclient.DATATYPE.INT32)
    #     # read discharge power
    #     rr = modclient.read_holding_registers(2035,count=2)
    #     values_d = modclient.convert_from_registers(rr.registers, data_type=modclient.DATATYPE.INT32)
    #     p_battery = values_c - values_d
    #     # read soc
    #     rr = modclient.read_holding_registers(1014,count=1)
    #     soc = modclient.convert_from_registers(rr.registers, data_type=modclient.DATATYPE.INT16)
            
    #     except ModbusException as exc:
    #         logging.error("Received ModbusException: %s", exc)
    # finally:
    #     modclient.close()
    # except Exception as err:
    #     logging.error("Error reading modbus data: %s", err)
    p_battery = 0  # Placeholder for battery power, as it's not read from Modbus in this example
    soc = 50  # Placeholder for state of charge, as it's not read from Modbus in this example

    return {
        'p_solar': p_solar,
        'p_haus': p_solar + p_grid - p_battery,
        'p_grid': p_grid,
        'p_battery': p_battery,
        'soc': soc
    }
