import json
import sqlite3
import os

def migrate_json_to_sqlite():
    """
    Reads instance data from a JSON file and migrates it into a structured SQLite database.
    This is a one-time operation to set up the database for the main application.
    It correctly maps the flat JSON structure to the database schema.
    """
    json_path = os.path.join(os.path.dirname(__file__), 'instances.json')
    db_path = os.path.join(os.path.dirname(__file__), 'instances.db')

    # Delete existing DB file to ensure a fresh migration
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")

    # Check if JSON file exists
    if not os.path.exists(json_path):
        print(f"Error: instances.json not found at {json_path}")
        return

    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the instances table
    cursor.execute('''
    CREATE TABLE instances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        provider TEXT NOT NULL,
        cost_per_month REAL NOT NULL,
        vcpu INTEGER NOT NULL,
        ram INTEGER NOT NULL,
        network_gbps REAL,
        storage_gb INTEGER,
        web_serving REAL DEFAULT 0,
        database REAL DEFAULT 0,
        caching REAL DEFAULT 0,
        analytics REAL DEFAULT 0
    )
    ''')

    # Load data from JSON file
    with open(json_path, 'r') as f:
        instances_data = json.load(f)

    # Insert data into the table
    for inst in instances_data:
        if not isinstance(inst, dict) or 'instance_id' not in inst or 'vcpus' not in inst or 'memory_gb' not in inst:
            continue

        # Calculate cost per month (assuming 730 hours/month)
        cost_per_month = inst.get('hourly_on_demand_price_usd', 0) * 730

        # For suitability, we'll assign some basic scores based on category for demonstration
        suitability = { "web_serving": 0, "database": 0, "caching": 0, "analytics": 0 }
        category = inst.get("category", "").lower()
        if "general purpose" in category:
            suitability = { "web_serving": 1.0, "database": 0.8, "caching": 0.7, "analytics": 0.5 }
        elif "compute optimized" in category:
            suitability = { "web_serving": 1.2, "database": 0.6, "caching": 0.6, "analytics": 1.0 }
        elif "memory optimized" in category:
            suitability = { "web_serving": 0.8, "database": 1.2, "caching": 1.1, "analytics": 0.7 }


        cursor.execute('''
        INSERT INTO instances (
            name, provider, cost_per_month, vcpu, ram, network_gbps, storage_gb,
            web_serving, database, caching, analytics
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            inst.get('instance_id'),
            inst.get('provider'),
            cost_per_month,
            inst.get('vcpus'),
            inst.get('memory_gb'),
            inst.get('network_performance_gbps'),
            inst.get('storage_size_gb'),
            suitability['web_serving'],
            suitability['database'],
            suitability['caching'],
            suitability['analytics']
        ))

    conn.commit()
    conn.close()
    print(f"Successfully migrated data from instances.json to {db_path}")

if __name__ == '__main__':
    migrate_json_to_sqlite()
