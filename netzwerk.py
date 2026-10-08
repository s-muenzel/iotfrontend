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


def get_zone_a_records(filename="/tmp/dns/ar14.s-muenzel.de."):
    """Read owner and address pairs from A records in a DNS zone file."""
    records = []
    try:
        with open(filename, encoding="utf-8") as zone_file:
            for line in zone_file:
                line = line.split(";", 1)[0].split("#", 1)[0].strip()
                if not line:
                    continue
                fields = line.split()
                try:
                    record_type_index = fields.index("A")
                except ValueError:
                    continue
                if record_type_index == 0 or record_type_index + 1 >= len(fields):
                    continue
                records.append((fields[0], fields[record_type_index + 1]))
    except OSError as err:
        logging.warning("failed to read DNS zone file: %s", err)

    return records


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
            if type(db_device[2]) == bytes:
                db_mac = db_device[2].decode("ascii").lower()
            else:
                db_mac = str(db_device[2]).lower()
            # Gutfall: Name in DB und DHCP und MACs gleich
            if db_device[0] == dhcp_device["hostname"]:
                # 1. Fehlerfall: Name in DB und DHCP und MACs gleich, aber MACs unterschiedlich
                if db_mac != dhcp_device["mac"]:
                    Netzwerkfehler.append(
                        {"device": db_device[0], "fehler": "DHCP falsche MAC", "soll": db_device[2], "ist": dhcp_device["mac"]})
                found = True
                break
            # 2. Fehlerfall: MAC in DCHP, aber Name in DB und DHCP unterschiedlich
            if db_mac == dhcp_device["mac"]:
                Netzwerkfehler.append(
                    {"device": db_device[0], "fehler": "DHCP falscher Name", "soll": db_device[2], "ist": dhcp_device["hostname"]})
                found = True
                break
        if not found:
            # 3. Fehlerfall: Name in DB, aber kein Eintrag in DHCP
            Netzwerkfehler.append(
                {"device": db_device[0], "fehler": "DHCP kein Eintrag", "soll": db_device[2], "ist": ""})
    # 4. Fehlerfall: Name in DHCP, aber kein Eintrag in DB
    for dhcp_device in dhcp_devices:
        found = False
        for db_device in db_devices:
            if type(db_device[2]) == bytes:
                db_mac = db_device[2].decode("ascii").lower()
            else:
                db_mac = str(db_device[2]).lower()
            if dhcp_device["hostname"] == db_device[0]:
                found = True
                break
        if not found:
            Netzwerkfehler.append(
                {"device": dhcp_device["hostname"], "fehler": "DB kein Eintrag", "soll": "", "ist": dhcp_device["mac"]})
    # prüfe die DNS Einträge der Devices
    for db_device in db_devices:
        db_ip = db_device[1]
        try:
            import socket
            dns_ips = socket.gethostbyname_ex(
                db_device[0] + ".ar14.s-muenzel.de")[2]
            # 5. Fehlerfall: Name in DB, aber DNS Eintrag hat andere IP
            if db_ip not in dns_ips:
                Netzwerkfehler.append(
                    {"device": db_device[0], "fehler": "DNS falsche IP", "soll": db_ip, "ist": dns_ips})
                logging.warning(
                    "DB-Device %s DNS falsche IP %s - %s", db_device[0], db_ip, dns_ips)
        except socket.gaierror:
            # 6. Fehlerfall: Name in DB, aber kein DNS Eintrag
            Netzwerkfehler.append(
                {"device": db_device[0], "fehler": "DNS kein Eintrag", "soll": db_ip, "ist": ""})
            logging.warning("DB-Device %s DNS kein Eintrag", db_device[0])
    # Prüfe, ob für jeden A-Eintrag der DNS-Zone ein passender DB-Eintrag existiert.
    # auf der Synology NAS ist die Zone unter /volume1/@appstore/DNSServer/named/etc/zone/master/ar14.s-muenzel.de gespeichert
    # im Docker-Container ist die Zone auf /tmp/dns/ar14.s-muenzel.de gemappt
    zonefile = "/tmp/dns/ar14.s-muenzel.de"
    db_devices_by_name = {}
    for db_device in db_devices:
        name = str(db_device[0]).lower().rstrip(".")
        if name.endswith(".ar14.s-muenzel.de"):
            name = name[:-len(".ar14.s-muenzel.de")]
        db_devices_by_name[name] = str(db_device[1]).strip()

    for record_name, record_ip in get_zone_a_records(zonefile):
        normalized_name = record_name.lower().rstrip(".")
        if normalized_name == "@":
            normalized_name = "ar14.s-muenzel.de"
        elif normalized_name.endswith(".ar14.s-muenzel.de"):
            normalized_name = normalized_name[:-len(".ar14.s-muenzel.de")]
        db_ip = db_devices_by_name.get(normalized_name)
        if db_ip != record_ip:
            Netzwerkfehler.append(
                {"device": normalized_name, "fehler": "DNS A kein passender DB-Eintrag",
                 "soll": db_ip or "", "ist": record_ip})

    return Netzwerkfehler
