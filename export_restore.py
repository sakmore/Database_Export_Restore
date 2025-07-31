import os
import sys
import csv
import argparse
import shutil 
import datetime
from io import StringIO

import psycopg2
from dotenv import load_dotenv

EXPORT_FOLDER="exports"
TABLE_NAMES = ['agents', 'leads','feedback']


def connect_to_database(env_file_path):
    
    load_dotenv(dotenv_path=env_file_path)
    db_config = {

        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'dbname': os.getenv('DB_NAME'), 
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    if not all(db_config.values()): 
        print(f"✗ Error: Missing database credentials in '{env_file_path}'. "
              "Please ensure DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD are set.", file=sys.stderr)
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(**db_config)
        print(f"Connected to database: {db_config['dbname']}")
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during connection: {e}", file=sys.stderr)
        sys.exit(1)

#export

def export_schema(conn):

    print("Exporting schema...")
    
    os.makedirs(EXPORT_FOLDER, exist_ok=True) 
    
    source_schema_path = 'schema.sql' 
    exported_schema_path = os.path.join(EXPORT_FOLDER, 'schema.sql')
    
    if not os.path.exists(source_schema_path):
        print(f"Error: 'schema.sql' not found at '{source_schema_path}'. "
              "Please ensure your primary schema definition file is in the root directory.", file=sys.stderr)
        sys.exit(1)

    try:
        shutil.copy(source_schema_path, exported_schema_path)
        print(f"Copied '{source_schema_path}' to '{exported_schema_path}' successfully!")
    except Exception as e:
        print(f"Failed to copy schema.sql: {e}", file=sys.stderr)
        sys.exit(1)
    
def export_table_data(conn, table_name):
    
    print(f"Exporting data from: '{table_name}'")
    
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY 1;")
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description] 
        
        csv_file = os.path.join(EXPORT_FOLDER, f'{table_name}.csv')
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(column_names) 
            writer.writerows([[str(item) if isinstance(item, (datetime.datetime, datetime.date, datetime.time)) else item for item in row] for row in rows])
        
        print(f"Exported {len(rows)} rows to '{csv_file}'")
    except psycopg2.Error as e:
        print(f"Database error during export of '{table_name}': {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred during export of '{table_name}': {e}", file=sys.stderr)
    finally:
        cursor.close()

def export_database(env_file_path):

    print("Starting database export...")
    conn = None
    try:
        conn = connect_to_database(env_file_path)
        export_schema(conn)
        
        for table in TABLE_NAMES:
            export_table_data(conn, table)
        
        print("Export completed successfully!")
    finally:
        if conn: 
            conn.close()
            print("Database connection closed.")
#restore


def restore_schema(conn):

    print("Restoring schema...")
    
    schema_file = os.path.join(EXPORT_FOLDER, 'schema.sql')
    
    if not os.path.exists(schema_file):
        print(f"✗ Schema file not found: '{schema_file}'. Please run export first.", file=sys.stderr)
        sys.exit(1)
    
    cursor = conn.cursor()
    try:
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        
        cursor.execute(schema_sql)
        conn.commit() 
        print("Schema restored successfully.")
    except psycopg2.Error as e:
        print(f"Database error during schema restore: {e}", file=sys.stderr)
        conn.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during schema restore: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        cursor.close()

def restore_table_data(conn, table_name):
    
    print(f"Restoring data to: '{table_name}'")
    
    csv_file = os.path.join(EXPORT_FOLDER, f'{table_name}.csv')
    
    if not os.path.exists(csv_file):
        print(f"CSV file not found for '{table_name}': '{csv_file}'. Data cannot be restored for this table.")
        return 
    
    cursor = conn.cursor()
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            headers = next(csv_reader) 
            
            temp_csv_file = StringIO()
            writer = csv.writer(temp_csv_file)
            for row in csv_reader:
            
                processed_row = [value if value != '' else None for value in row]
                writer.writerow(processed_row)
            temp_csv_file.seek(0)
              
            cursor.copy_from(temp_csv_file, table_name, sep=',', columns=headers, null='')
            conn.commit()
            print(f"Restored {len(list(csv.reader(StringIO(temp_csv_file.getvalue()))))} rows to '{table_name}'Successfully!")
            
    except psycopg2.Error as e:
        print(f"Database error during data restore for '{table_name}': {e}", file=sys.stderr)
        conn.rollback() 
    except Exception as e:
        print(f"An unexpected error occurred during data restore for '{table_name}': {e}", file=sys.stderr)
    finally:
        cursor.close()


#important to restore integrity
def adjust_sequences(conn):
    print("Adjusting sequences for SERIAL primary keys...")
    cursor = conn.cursor()
    try:
        for table_name in TABLE_NAMES:
            
            cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), COALESCE((SELECT MAX(id) FROM {table_name}), 1));")
            conn.commit()
            print(f"Sequence for '{table_name}' adjusted.")
    except Exception as e:
        print(f"An error occurred during sequence adjustment: {e}", file=sys.stderr)
        conn.rollback()
    finally:
        cursor.close()

def restore_database(env_file_path):

    print("Starting database restore...")
    conn = None
    try:
        conn = connect_to_database(env_file_path)
        
        restore_schema(conn)
        
        for table_name in TABLE_NAMES:
            restore_table_data(conn, table_name)
        
        adjust_sequences(conn) 
        
        print("Restore completed successfully!")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

#main function for CLI

def main():

    parser = argparse.ArgumentParser(
        description="Export or restore PostgreSQL database schema and data.",
        formatter_class=argparse.RawTextHelpFormatter 
    )
    
    parser.add_argument(
        'mode', 
        choices=['export', 'restore'], 
        help="Mode of operation: 'export' or 'restore'."
    )
    
    parser.add_argument(
        '--env-file', 
        required=True, 
        help="Path to the .env file containing database credentials.\n"
             "  - For 'export' mode, use a source environment file (e.g., source.env).\n"
             "  - For 'restore' mode, use a target environment file (e.g., target.env)."
    )
    
    args = parser.parse_args()
    
    if args.mode == 'export':
        export_database(args.env_file)
    elif args.mode == 'restore':
        restore_database(args.env_file)

if __name__ == "__main__":
    main()