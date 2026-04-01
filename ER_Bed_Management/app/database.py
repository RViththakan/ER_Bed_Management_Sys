import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "hospital_management1.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Patients Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY, age INTEGER, condition TEXT, ctas_level TEXT,
        region TEXT, hospital TEXT, nurse_ratio INTEGER, specialist_availability INTEGER,
        discharge_prob REAL, est_wait_time REAL, timestamp TEXT)''')
    
    # Staff Table (Tracking hours toward 40h goal)
    cursor.execute('''CREATE TABLE IF NOT EXISTS cleaning_staff (
        name TEXT PRIMARY KEY, hours_worked REAL DEFAULT 0.0)''')
    
    # Seed Staff Data
    cursor.execute("SELECT count(*) FROM cleaning_staff")
    if cursor.fetchone()[0] == 0:
        import random
        for name in ["John Smith", "Sarah Lee", "Mike Ross", "Elena Rodriguez"]:
            cursor.execute("INSERT INTO cleaning_staff VALUES (?, ?)", (name, round(random.uniform(10, 32), 1)))

    # Tickets Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY, patient_id TEXT, hospital TEXT,
        staff_assigned TEXT DEFAULT 'Unassigned', status TEXT DEFAULT 'Pending',
        cleaning_start_time TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def save_patient_to_db(data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                    (data['patient_id'], data['age'], data['condition'], data['ctas_level'], 
                     data['region'], data['hospital'], data['nurse_ratio'], data['specialist_availability'], 
                     data['discharge_prob'], data['est_wait_time'], now))
    conn.commit()
    conn.close()

def discharge_patient_and_create_ticket(p_id, hospital):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM patients WHERE patient_id = ?', (p_id,))
        t_id = f"TKT-{p_id[-4:]}"
        cursor.execute('INSERT INTO tickets (ticket_id, patient_id, hospital) VALUES (?,?,?)', (t_id, p_id, hospital))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def assign_staff_to_ticket(t_id, staff_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Step 1: Manager assigns, but staff hasn't accepted yet
    cursor.execute('UPDATE tickets SET staff_assigned = ?, status = "Pending Acceptance" WHERE ticket_id = ?', 
                   (staff_name, t_id))
    conn.commit()
    conn.close()

def accept_ticket_task(t_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    # Step 2: Staff accepts, timer starts NOW
    cursor.execute('UPDATE tickets SET status = "In Progress", cleaning_start_time = ? WHERE ticket_id = ?', 
                   (now, t_id))
    conn.commit()
    conn.close()

def complete_ticket_and_add_hours(t_id, staff_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE cleaning_staff SET hours_worked = hours_worked + 0.5 WHERE name = ?', (staff_name,))
    cursor.execute('DELETE FROM tickets WHERE ticket_id = ?', (t_id,))
    conn.commit()
    conn.close()

def get_all_patients():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM patients", conn)
    conn.close()
    return df

def get_staff_by_hours():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cleaning_staff ORDER BY hours_worked ASC", conn)
    conn.close()
    return df

def get_all_tickets():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM tickets", conn)
    conn.close()
    return df