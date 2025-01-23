from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func, cast, Float

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user_management:management@localhost/mib'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class SNMPCriticalMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(255), nullable=False)
    oid = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Text)
    value_type = db.Column(db.String(50))
    ip_port = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/values')
def values_dashboard():
    return render_template('values_dashboard.html')

@app.route('/api/network-values', methods=['GET'])
def network_values():
    try:
        scale = request.args.get('scale', 'hour')

        # Determine Time Threshold
        latest_record = db.session.query(func.max(SNMPCriticalMetrics.timestamp)).scalar()
        if not latest_record:
            return jsonify({"in": [], "out": []})

        if scale == 'hour':
            time_threshold = latest_record - timedelta(hours=1)
        elif scale == 'day':
            time_threshold = latest_record - timedelta(days=1)
        elif scale == 'week':
            time_threshold = latest_record - timedelta(weeks=1)
        else:
            return jsonify({"error": "Invalid scale parameter"}), 400

        def fetch_values(metric_name):
            query = db.session.query(
                SNMPCriticalMetrics.timestamp,
                cast(func.trim(SNMPCriticalMetrics.value), Float).label('value')
            ).filter(
                func.trim(SNMPCriticalMetrics.metric_name) == metric_name,
                SNMPCriticalMetrics.timestamp >= time_threshold
            ).order_by(SNMPCriticalMetrics.timestamp.asc())

            results = query.all()

            values = [{"timestamp": r.timestamp.strftime('%Y-%m-%d %H:%M:%S'), "value": r.value} for r in results]
            return values

        values_in = fetch_values('Bandwidth In')
        values_out = fetch_values('Bandwidth Out')

        def calculate_stats(values):
            rates = [v['value'] for v in values if v['value'] >= 0]
            return {
                "current": rates[-1] if rates else 0,
                "average": sum(rates) / len(rates) if rates else 0,
                "max": max(rates) if rates else 0,
                "min": min(rates) if rates else 0
            }

        stats_in = calculate_stats(values_in)
        stats_out = calculate_stats(values_out)

        return jsonify({
            "in": values_in,
            "out": values_out,
            "stats": {"in": stats_in, "out": stats_out}
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to fetch network values data"}), 500



@app.route('/api/network-traffic', methods=['GET'])
def network_traffic():
    try:
        scale = request.args.get('scale', 'hour')

        # Determine Time Threshold
        latest_record = db.session.query(func.max(SNMPCriticalMetrics.timestamp)).scalar()
        if not latest_record:
            return jsonify({"in": [], "out": []})

        if scale == 'hour':
            time_threshold = latest_record - timedelta(hours=1)
        elif scale == 'day':
            time_threshold = latest_record - timedelta(days=1)
        elif scale == 'week':
            time_threshold = latest_record - timedelta(weeks=1)
        else:
            return jsonify({"error": "Invalid scale parameter"}), 400

        def fetch_bandwidth_data(metric_name):
            """Fetch and calculate bandwidth rates (bps)."""
            query = db.session.query(
                SNMPCriticalMetrics.timestamp,
                cast(func.trim(SNMPCriticalMetrics.value), Float).label('value')
            ).filter(
                func.trim(SNMPCriticalMetrics.metric_name) == metric_name,
                cast(func.trim(SNMPCriticalMetrics.value), Float) > 0,
                SNMPCriticalMetrics.timestamp >= time_threshold
            ).order_by(SNMPCriticalMetrics.timestamp.asc())

            results = query.all()

            # Calculate rates (bps) between consecutive timestamps
            rates = []
            for i in range(1, len(results)):
                prev = results[i - 1]
                curr = results[i]
                time_diff = (curr.timestamp - prev.timestamp).total_seconds()
                value_diff = curr.value - prev.value

                # Handle SNMP counter resets
                if value_diff < 0:
                    value_diff = curr.value

                # Validate positive differences and non-zero time intervals
                if value_diff >= 0 and time_diff > 0:
                    rate = (value_diff * 8) / time_diff
                    rates.append({"timestamp": curr.timestamp.strftime('%Y-%m-%d %H:%M:%S'), "rate": rate})

            return rates

        rates_in = fetch_bandwidth_data('Bandwidth In')
        rates_out = fetch_bandwidth_data('Bandwidth Out')

        def calculate_stats(rates):
            """Calculate current, average, max, and min rates."""
            if not rates:
                return {"current": 0, "average": 0, "max": 0, "min": 0}

            values = [r['rate'] for r in rates if r['rate'] >= 0]

            if not values:
                return {"current": 0, "average": 0, "max": 0, "min": 0}

            return {
                "current": values[-1],
                "average": sum(values) / len(values),
                "max": max(values),
                "min": min(values)
            }

        stats_in = calculate_stats(rates_in)
        stats_out = calculate_stats(rates_out)

        response = {
            "in": rates_in,
            "out": rates_out,
            "stats": {
                "in": stats_in,
                "out": stats_out
            }
        }

        return jsonify(response)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to fetch network traffic data"}), 500

if __name__ == '__main__':
    app.run(debug=True)

'''
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func, cast, Float
from pysnmp.hlapi import *
import threading
import time
import logging

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user_management:sql@localhost/mib'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Logging Configuration
logging.basicConfig(level=logging.INFO)

# Device summary cache (global)
device_summary_cache = {}

# ------------------- Database Model -------------------

class SNMPCriticalMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(255), nullable=False)
    oid = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Text)
    value_type = db.Column(db.String(50))
    ip_port = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------- Device Summary Logic -------------------

def fetch_device_data(ip, community):
    """
    Fetches SNMP device data dynamically using pysnmp.
    """
    device_summary = {}

    # Fetch IP Address (direct input)
    device_summary["IP Address"] = ip

    # Fetch DNS Name
    device_summary["DNS Name"] = get_snmp_value(ip, community, "1.3.6.1.2.1.1.5.0") or "N/A"

    # Fetch System Description
    device_summary["System Description"] = get_snmp_value(ip, community, "1.3.6.1.2.1.1.1.0") or "N/A"

    # Default status
    device_summary["Status"] = "Clear"
    device_summary["Poll Using"] = "IP Address"

    # Deduce type, vendor, and category
    system_description = device_summary["System Description"]
    if "Windows" in system_description:
        device_summary["Type"] = "Windows Server"
        device_summary["Vendor"] = "Microsoft"
        device_summary["Category"] = "Server"
    elif "Linux" in system_description:
        device_summary["Type"] = "Linux Server"
        device_summary["Vendor"] = "net-snmp"
        device_summary["Category"] = "Server"
    else:
        device_summary["Type"] = "Unknown"
        device_summary["Vendor"] = "Unknown"
        device_summary["Category"] = "Unknown"

    # Fetch RAM size
    ram_size = get_snmp_value(ip, community, "1.3.6.1.4.1.2021.4.6.0")  # UCD-SNMP-MIB for Linux
    device_summary["RAM size"] = f"{int(ram_size) / 1024:.2f} MB" if ram_size else "N/A"

    # Hard disk size and other details
    device_summary["Hard disk size"] = "N/A"
    device_summary["Monitoring (mins)"] = "1"
    device_summary["Uplink Dependency"] = "None"
    device_summary["Monitored via"] = "SNMP"

    return device_summary

def get_snmp_value(ip, community, oid):
    """
    Fetches a single SNMP value for a given OID.
    """
    try:
        for (errorIndication, errorStatus, errorIndex, varBinds) in getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip, 161), timeout=5, retries=3),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        ):
            if errorIndication:
                logging.error(f"SNMP error: {errorIndication}")
                return None
            elif errorStatus:
                logging.error(f"SNMP error: {errorStatus.prettyPrint()}")
                return None
            else:
                for varBind in varBinds:
                    return str(varBind[1])  # Extract the value
    except Exception as e:
        logging.error(f"Error fetching SNMP data: {e}")
        return None

def fetch_device_data_periodically(ip, community, interval=60):
    """
    Periodically fetches device data and updates the global cache.
    """
    global device_summary_cache
    while True:
        try:
            device_summary_cache = fetch_device_data(ip, community)
            logging.info("Device summary updated.")
        except Exception as e:
            logging.error(f"Error updating device summary: {e}")
        time.sleep(interval)

# ------------------- Routes -------------------

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/values')
def values_dashboard():
    return render_template('values_dashboard.html')

@app.route('/device-summary')
def device_summary():
    global device_summary_cache
    return render_template('index.html', device_summary=device_summary_cache)

@app.route('/api/device-summary', methods=['GET'])
def api_device_summary():
    global device_summary_cache
    return jsonify(device_summary_cache)

@app.route('/api/network-values', methods=['GET'])
def network_values():
    try:
        scale = request.args.get('scale', 'hour')
        latest_record = db.session.query(func.max(SNMPCriticalMetrics.timestamp)).scalar()
        if not latest_record:
            return jsonify({"in": [], "out": []})

        time_threshold = determine_time_threshold(scale, latest_record)

        def fetch_values(metric_name):
            query = db.session.query(
                SNMPCriticalMetrics.timestamp,
                cast(func.trim(SNMPCriticalMetrics.value), Float).label('value')
            ).filter(
                func.trim(SNMPCriticalMetrics.metric_name) == metric_name,
                SNMPCriticalMetrics.timestamp >= time_threshold
            ).order_by(SNMPCriticalMetrics.timestamp.asc())

            return [{"timestamp": r.timestamp.strftime('%Y-%m-%d %H:%M:%S'), "value": r.value} for r in query.all()]

        values_in = fetch_values('Bandwidth In')
        values_out = fetch_values('Bandwidth Out')

        return jsonify({"in": values_in, "out": values_out})

    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": "Failed to fetch network values data"}), 500

@app.route('/api/network-traffic', methods=['GET'])
def network_traffic():
    try:
        scale = request.args.get('scale', 'hour')
        latest_record = db.session.query(func.max(SNMPCriticalMetrics.timestamp)).scalar()
        if not latest_record:
            return jsonify({"in": [], "out": []})

        time_threshold = determine_time_threshold(scale, latest_record)

        def fetch_bandwidth_data(metric_name):
            query = db.session.query(
                SNMPCriticalMetrics.timestamp,
                cast(func.trim(SNMPCriticalMetrics.value), Float).label('value')
            ).filter(
                func.trim(SNMPCriticalMetrics.metric_name) == metric_name,
                cast(func.trim(SNMPCriticalMetrics.value), Float) > 0,
                SNMPCriticalMetrics.timestamp >= time_threshold
            ).order_by(SNMPCriticalMetrics.timestamp.asc())

            rates = []
            for i in range(1, len(query.all())):
                prev, curr = query.all()[i - 1], query.all()[i]
                time_diff = (curr.timestamp - prev.timestamp).total_seconds()
                value_diff = curr.value - prev.value
                if value_diff >= 0 and time_diff > 0:
                    rate = (value_diff * 8) / time_diff
                    rates.append({"timestamp": curr.timestamp.strftime('%Y-%m-%d %H:%M:%S'), "rate": rate})
            return rates

        rates_in = fetch_bandwidth_data('Bandwidth In')
        rates_out = fetch_bandwidth_data('Bandwidth Out')

        return jsonify({"in": rates_in, "out": rates_out})

    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": "Failed to fetch network traffic data"}), 500

def determine_time_threshold(scale, latest_record):
    if scale == 'hour':
        return latest_record - timedelta(hours=1)
    elif scale == 'day':
        return latest_record - timedelta(days=1)
    elif scale == 'week':
        return latest_record - timedelta(weeks=1)
    else:
        raise ValueError("Invalid scale parameter")

# ------------------- Main -------------------

if __name__ == '__main__':
    device_ip = "127.0.0.1"
    community_string = "public"

    threading.Thread(
        target=fetch_device_data_periodically,
        args=(device_ip, community_string),
        daemon=True
    ).start()

    app.run(debug=True)'''
