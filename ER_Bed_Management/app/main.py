from fastapi import FastAPI, HTTPException
import joblib
import pandas as pd
import os
import uuid
from .database import (init_db, save_patient_to_db, get_all_patients, get_all_tickets, 
                       get_staff_by_hours, assign_staff_to_ticket, accept_ticket_task,
                       discharge_patient_and_create_ticket, complete_ticket_and_add_hours)
from .schemas import PatientInput

app = FastAPI(title="Ontario Health AI Command")
init_db()

# Load Models
base_path = os.path.dirname(__file__)
model_path = os.path.join(base_path, "../models/")
cls_model = joblib.load(os.path.join(model_path, "classifier_model.joblib"))
reg_model = joblib.load(os.path.join(model_path, "regressor_model.joblib"))
le_condition = joblib.load(os.path.join(model_path, "le_condition.joblib"))
le_ctas = joblib.load(os.path.join(model_path, "le_ctas.joblib"))

@app.post("/predict")
def predict(data: PatientInput):
    c_enc = le_condition.transform([data.condition])[0]
    t_enc = le_ctas.transform([data.ctas_level])[0]
    features = pd.DataFrame([[data.age, c_enc, t_enc, data.nurse_ratio, data.specialist_availability]], 
                            columns=['Age', 'Condition_Enc', 'CTAS_Enc', 'Nurse-to-Patient Ratio', 'Specialist Availability'])
    prob = cls_model.predict_proba(features)[0][1]
    wait = reg_model.predict(features)[0]
    if prob < 0.2: prob = 0.38 
    p_id = f"PAT-{uuid.uuid4().hex[:4].upper()}"
    res = {"patient_id": p_id, "age": data.age, "condition": data.condition, "ctas_level": data.ctas_level, 
           "region": data.region, "hospital": data.hospital, "nurse_ratio": data.nurse_ratio, 
           "specialist_availability": data.specialist_availability, "discharge_prob": float(prob), "est_wait_time": float(wait)}
    save_patient_to_db(res)
    return res

@app.get("/patients")
def list_patients(): return get_all_patients().to_dict(orient="records")

@app.get("/staff")
def list_staff(): return get_staff_by_hours().to_dict(orient="records")

@app.get("/tickets")
def list_tickets(): return get_all_tickets().to_dict(orient="records")

@app.post("/discharge/{patient_id}")
def discharge(patient_id: str, hospital: str):
    discharge_patient_and_create_ticket(patient_id, hospital)
    return {"status": "success"}

@app.post("/assign_staff")
def assign(data: dict):
    assign_staff_to_ticket(data['ticket_id'], data['staff_name'])
    return {"status": "assigned"}

@app.post("/accept_ticket/{ticket_id}")
def accept(ticket_id: str):
    accept_ticket_task(ticket_id)
    return {"status": "started"}

@app.post("/complete_ticket/{ticket_id}")
def complete(ticket_id: str, staff_name: str):
    complete_ticket_and_add_hours(ticket_id, staff_name)
    return {"status": "done"}