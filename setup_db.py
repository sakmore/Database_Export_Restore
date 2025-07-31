import psycopg2
from dotenv import load_dotenv
import os
from faker import Faker
import random
from datetime import datetime, timedelta

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

conn = None
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        dbname=os.getenv('DB_NAME')
    )
    print("Connected to the database successfully")

    with conn.cursor() as cur:
        with open('schema.sql', 'r') as file:
            ddl = file.read()
            cur.execute(ddl)
            conn.commit()
            print("Schema applied successfully")

        fake = Faker()

        print("Populating agents table with fake data")
        agents_data = []
        num_agents = random.randint(5, 8)
        for _ in range(num_agents):
            name = fake.name()
            email = fake.unique.email()
            cur.execute("INSERT INTO agents (name, email) VALUES (%s, %s) RETURNING id;", (name, email))
            agent_id = cur.fetchone()[0]
            agents_data.append({'id': agent_id, 'name': name, 'email': email})
        conn.commit()
        print(f"Populated {len(agents_data)} agents.")

        print("Populating leads table with fake data")
        leads_data = []
        num_leads = random.randint(20, 30) # 20-30 leads
        lead_statuses = ['new', 'contacted', 'converted', 'rejected']
        for _ in range(num_leads):
            full_name = fake.name()
            email = fake.unique.email()
            phone = fake.phone_number()
            status = random.choice(lead_statuses)
            created_at = fake.date_time_between(start_date='-6m', end_date='now')

            assigned_agent_id = None
            if agents_data and random.random() > 0.3:
                assigned_agent_id = random.choice(agents_data)['id']

            cur.execute(
                "INSERT INTO leads (full_name, email, phone, status, created_at, assigned_agent_id) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;",
                (full_name, email, phone, status, created_at, assigned_agent_id)
            )
            lead_id = cur.fetchone()[0]
            leads_data.append({'id': lead_id, 'status': status, 'assigned_agent_id': assigned_agent_id})
        conn.commit()
        print(f"Populated {len(leads_data)} leads.")

        print("Populating feedback table with fake data")
        num_feedback = random.randint(10, 15) # 10-15 feedback entries
        for _ in range(num_feedback):
            if not leads_data or not agents_data:
                print("No feedback created: No leads or agents available.")
                break

            lead_entry = random.choice(leads_data)
            lead_id = lead_entry['id']

            agent_entry = random.choice(agents_data)
            agent_id = agent_entry['id']

            rating = random.randint(1, 5) # Rating between 1 and 5
            comments = fake.paragraph(nb_sentences=2)

            submitted_at = fake.date_time_between(start_date='-3m', end_date='now')

            cur.execute(
                "INSERT INTO feedback (lead_id, agent_id, rating, comments, submitted_at) VALUES (%s, %s, %s, %s, %s);",
                (lead_id, agent_id, rating, comments, submitted_at)
            )
        conn.commit()
        print(f"Populated {num_feedback} feedback entries.")

    print("Database setup and data population completed successfully.")
    
except psycopg2.Error as e:
    print(f"Database error: {e}")
    if conn:
        conn.rollback() 
except Exception as e:
    print(f"An unexpected error occurred: {e}")

finally:
    if conn:
        conn.close()
        print("Connection is closed")

