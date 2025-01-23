import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Define connection parameters for the default PostgreSQL database
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "<PASSWORD>"  # Replace with your postgres user's password
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"

# Define parameters for the new database and user
NEW_DB_NAME = "mib"
NEW_USER_NAME = "user_management"
NEW_USER_PASSWORD = "management"

# Define the table schema
TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS snmp_critical_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    oid VARCHAR(255) NOT NULL,
    value TEXT,
    value_type VARCHAR(50),
    ip_port VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

try:
    # Step 1: Connect to the default PostgreSQL database
    connection = psycopg2.connect(
        dbname="postgres",
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # Allow database creation
    cursor = connection.cursor()

    # Step 2: Check if the database exists
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{NEW_DB_NAME}';")
    db_exists = cursor.fetchone()
    if not db_exists:
        # Create the new database if it doesn't exist
        cursor.execute(f"CREATE DATABASE {NEW_DB_NAME};")
        print(f"Database '{NEW_DB_NAME}' created successfully.")
    else:
        print(f"Database '{NEW_DB_NAME}' already exists.")

    # Step 3: Check if the user exists
    cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname = '{NEW_USER_NAME}';")
    user_exists = cursor.fetchone()
    if not user_exists:
        # Create the new user if it doesn't exist
        cursor.execute(f"CREATE USER {NEW_USER_NAME} WITH PASSWORD '{NEW_USER_PASSWORD}';")
        print(f"User '{NEW_USER_NAME}' created successfully.")
    else:
        print(f"User '{NEW_USER_NAME}' already exists.")

    # Step 4: Grant permissions to the new user on the database
    cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {NEW_DB_NAME} TO {NEW_USER_NAME};")
    print(f"Granted all privileges on '{NEW_DB_NAME}' to '{NEW_USER_NAME}'.")

    # modify steps 4 to fix the error of permission denied for schema public
    #####################################################################################
    # Grant privileges on the public schema to the new user
    connection = psycopg2.connect(
        dbname=NEW_DB_NAME,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()

    cursor.execute(f"GRANT USAGE ON SCHEMA public TO {NEW_USER_NAME};")
    cursor.execute(f"GRANT CREATE ON SCHEMA public TO {NEW_USER_NAME};")
    cursor.execute(f"ALTER SCHEMA public OWNER TO {NEW_USER_NAME};")
    print(f"Granted privileges and ownership of schema 'public' to '{NEW_USER_NAME}'.")
    #####################################################################################

    # Close the cursor and connection to the default database
    cursor.close()
    connection.close()

    # Step 5: Connect to the newly created database as the new user
    connection = psycopg2.connect(
        dbname=NEW_DB_NAME,
        user=NEW_USER_NAME,
        password=NEW_USER_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()

    # Step 6: Create the new table
    cursor.execute(TABLE_SCHEMA)
    print(f"Table 'snmp_critical_metrics' created successfully in database '{NEW_DB_NAME}'.")

    # Close the cursor and connection
    cursor.close()
    connection.close()

except Exception as e:
    print(f"An error occurred: {e}")
