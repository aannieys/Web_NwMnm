# Web Interface for Network Management

## Overview
This project implements a centralized web interface for monitoring and managing network traffic. Using SNMP, Flask, and PostgreSQL, the system provides real-time data visualization, metrics analysis, and device management features for efficient network performance monitoring.

## Core Features
- **Real-Time Data Visualization**:
  - View live bandwidth usage and network performance with line charts.
  - Customizable time range filters (hour, day, week).
- **Network Metrics Dashboard**:
  - Displays key statistics (current, average, max, and min) for bandwidth metrics.
- **Interactive User Interface**:
  - Responsive design with easy navigation and dynamic visualizations.
- **Device Management**:
  - Supports monitoring SNMP-enabled devices and integrating multiple devices.
- **Database Integration**:
  - Stores historical and real-time data in PostgreSQL for efficient querying.

## Technologies Used
- **Frontend**:
  - HTML, CSS, JavaScript, Chart.js (for data visualizations).
- **Backend**:
  - Python Flask (handles API communication and data processing).
  - PySNMP (fetches SNMP data from devices).
  - SQLAlchemy (ORM for database interaction).
- **Database**:
  - PostgreSQL for storing network metrics and historical data.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/network-management-tool.git
2. Install dependencies:
   ```bash
   pip install flask psycopg2 pysnmp chart.js
3. Configure PostgreSQL:
   - Create a database named mib.
   - Create a user with the following credentials:
      - Username: user_management
      - Password: management
   - Run the database schema setup in db_pj5.py.
4. Run snmp_pj5.py to start recording SNMP data to the database:
   ```bash
   python snmp_pj5.py

5. Start the Flask application:
   ```bash
   python app.py
6. Open the application in your browser at http://localhost:5000.

## How It Works
1. **Data Collection**:
  - SNMP data is periodically fetched from devices and stored in the database.
2. **Data Visualization**:
  - Real-time and historical metrics are rendered using Chart.js and tables.
3. **Interactive Dashboard**:
  - Users can select time ranges, view bandwidth metrics, and navigate between different pages.

## Team Members
- Sirapath Thainiyom - ID: 6488108
- Suphavadee Cheng - ID: 6488120
- Jidapa Moolkaew - ID: 6488176
