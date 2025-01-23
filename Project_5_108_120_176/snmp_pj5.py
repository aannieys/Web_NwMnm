import psycopg2
from pysnmp.hlapi import *
import time

# Database connection parameters
DB_NAME = "mib"
DB_USER = "user_management"
DB_PASSWORD = "management"
DB_HOST = "localhost"
DB_PORT = "5432"


def get_dynamic_oids(base_oid, num_interfaces):
    return [f"{base_oid}.{i}" for i in range(1, num_interfaces + 1)]

# Dynamically fetch number of interfaces
NUM_INTERFACES = 10  # Replace with dynamic detection if possible

CRITICAL_METRICS = {
    "Bandwidth In": get_dynamic_oids("1.3.6.1.2.1.2.2.1.10", NUM_INTERFACES),
    "Bandwidth Out": get_dynamic_oids("1.3.6.1.2.1.2.2.1.16", NUM_INTERFACES),
    "Input Errors": get_dynamic_oids("1.3.6.1.2.1.2.2.1.14", NUM_INTERFACES),
    "Output Errors": get_dynamic_oids("1.3.6.1.2.1.2.2.1.20", NUM_INTERFACES),
    "System Uptime": ["1.3.6.1.2.1.1.3.0"],
    "IP Packets Received": ["1.3.6.1.2.1.4.3.0"],
    "UDP Datagrams Sent": ["1.3.6.1.2.1.7.4.0"],
    "TCP Connections": ["1.3.6.1.2.1.6.9.0"],
    "Incoming IP Errors": ["1.3.6.1.2.1.4.5.0"],
}


# Function to connect to the database
def connect_to_database():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

# Function to insert data into the database
def insert_metric(connection, metric_name, oid, value, value_type, ip_port):
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO snmp_critical_metrics (metric_name, oid, value, value_type, ip_port)
            VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(query, (metric_name, oid, value, value_type, ip_port))
        connection.commit()
        cursor.close()
        print(f"Recorded {metric_name}: {value} from {ip_port}")
    except Exception as e:
        print(f"Error inserting data: {e}")

# Function to fetch SNMP data
def fetch_snmp_data(target, community, oid):
    try:
        for errorIndication, errorStatus, errorIndex, varBinds in getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((target, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        ):
            if errorIndication:
                print(f"SNMP Error: {errorIndication}")
                return None
            elif errorStatus:
                print(f"SNMP Error: {errorStatus.prettyPrint()}")
                return None
            else:
                for varBind in varBinds:
                    oid, value = varBind
                    return oid.prettyPrint(), str(value), type(value).__name__
    except Exception as e:
        print(f"Error fetching SNMP data: {e}")
        return None

# Main function to collect and record data
def main():
    target = "127.0.0.1"
    community = "public"

    # Connect to the database
    connection = connect_to_database()

    try:
        while True:
            for metric_group, oids in CRITICAL_METRICS.items():  # `oids` is a list
                for oid in oids:  # Iterate over the list
                    snmp_data = fetch_snmp_data(target, community, oid)

                    # Debugging: Count rows in the database
                    cursor = connection.cursor()
                    cursor.execute("SELECT COUNT(*) FROM snmp_critical_metrics;")
                    row_count = cursor.fetchone()[0]
                    print(f"Total rows in snmp_critical_metrics: {row_count}")
                    cursor.close()

                    if snmp_data:
                        oid, value, value_type = snmp_data
                        insert_metric(
                            connection,
                            f"{metric_group}",
                            oid,
                            value,
                            value_type,
                            f"{target}:161"
                        )
                    else:
                        print(f"Skipped metric {metric_group} for OID {oid} due to missing data.")
            # Wait 60 seconds before the next round
            time.sleep(60)
    except KeyboardInterrupt:
        print("Exiting program...")
    finally:
        connection.close()

if __name__ == "__main__":
    main()
