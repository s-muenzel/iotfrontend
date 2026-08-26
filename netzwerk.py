"""dhcp.py: Reads DHCP configuration for IoT Frontend.

Handles all DHCP operations
"""
import logging

def get_dhcp_devices(filename="/tmp/dhcp/dhcpd-eth0-static.conf"):
    """Liest MAC-Adressen und Hostnamen aus der DHCP-Konfiguration."""
    dhcp_devices = []
    try:
        with open(filename, encoding="utf-8") as dhcp_file:
            for line in dhcp_file:
                line = line.split("#", 1)[0].strip()
                if not line.startswith("dhcp-host="):
                    continue

                host_data = line[len("dhcp-host="):].split(",")
                if len(host_data) < 2:
                    continue
                dhcp_devices.append({"mac": host_data[0].strip().replace(":", "").lower(),
                                     "hostname": host_data[1].strip()})
    except OSError as err:
        logging.warning("failed to read DHCP device data: %s", err)

    return dhcp_devices


def check_netzwerkfehler(db_devices):
    """check_netzwerkfehler prüft die Devices in der DB und vergleicht sie mit den DHCP-Einträgen
    und prüft die DNS Einträge
    """
    Netzwerkfehler = []
    # hole und prüfe die Liste der Devices aus der DHCP-Konfiguration
    dhcp_devices = get_dhcp_devices()
    for db_device in db_devices:
        found = False
        for dhcp_device in dhcp_devices:
            if type(db_device[6]) == bytes:
                db_mac = db_device[6].decode("ascii").lower()
            else:
                db_mac = str(db_device[6]).lower()
            # Gutfall: Name in DB und DHCP und MACs gleich
            if db_device[0] == dhcp_device["hostname"]:
                # 1. Fehlerfall: Name in DB und DHCP und MACs gleich, aber MACs unterschiedlich
                if db_mac != dhcp_device["mac"]:
                    Netzwerkfehler.append({"device": db_device[0],"fehler": "DHCP falsche MAC", "soll": db_device[6], "ist": dhcp_device["mac"]})
                found = True
                break
            # 2. Fehlerfall: MAC in DCHP, aber Name in DB und DHCP unterschiedlich
            if db_mac == dhcp_device["mac"]:
                Netzwerkfehler.append({"device": db_device[0],"fehler": "DHCP falscher Name", "soll": db_device[6], "ist": dhcp_device["hostname"]})
                found = True
                break
        if not found:
            # 3. Fehlerfall: Name in DB, aber kein Eintrag in DHCP
            Netzwerkfehler.append({"device": db_device[0],"fehler": "DHCP kein Eintrag", "soll": db_device[6], "ist": ""})
    # prüfe die DNS Einträge der Devices
    for db_device in db_devices:
        db_ip = f"{db_device[2]}.{db_device[3]}.{db_device[4]}.{db_device[5]}"
        try:
            import socket
            dns_ips = socket.gethostbyname_ex(
                db_device[0] + ".ar14.s-muenzel.de")[2]
            # 4. Fehlerfall: Name in DB, aber DNS Eintrag hat andere IP
            if db_ip not in dns_ips:
                Netzwerkfehler.append({"device": db_device[0],"fehler": "DNS falsche IP", "soll": db_ip, "ist": dns_ips})
                logging.warning("DB-Device %s DNS falsche IP %s - %s", db_device[0], db_ip, dns_ips)
        except socket.gaierror:
            # 5. Fehlerfall: Name in DB, aber kein DNS Eintrag
            Netzwerkfehler.append({"device": db_device[0],"fehler": "DNS kein Eintrag", "soll": db_ip, "ist": ""})
            logging.warning("DB-Device %s DNS kein Eintrag", db_device[0])
    return Netzwerkfehler
    
