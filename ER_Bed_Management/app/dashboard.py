import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime
import time

st.set_page_config(page_title="ER Operations Command", layout="wide")
API_URL = "http://127.0.0.1:8000"

# --- REFRESH DATA ---
try:
    patients = requests.get(f"{API_URL}/patients").json()
    tickets = requests.get(f"{API_URL}/tickets").json()
    staff_data = requests.get(f"{API_URL}/staff").json()
except: patients, tickets, staff_data = [], [], []

st.title("🏥 Regional ER Operations Command")

# --- KPI ROW ---
if patients:
    df_p = pd.DataFrame(patients)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Active Census", len(df_p))
    k2.metric("Avg Predicted Stay", f"{df_p['est_wait_time'].mean():.1f}m")
    k3.metric("Critical (CTAS 1/2)", len(df_p[df_p['ctas_level'].str.contains('1|2')]))
    k4.metric("Cleaning Queue", len(tickets))

# --- SIDEBAR ---
with st.sidebar:
    st.header("Patient Admission")
    with st.form("adm"):
        h = st.selectbox("Hospital", ['Hamilton General', 'North Bay Regional', 'Southlake Regional', 'The Ottawa Hospital', 'Toronto General'])
        age = st.number_input("Age", 0, 110, 45); c = st.selectbox("Condition", ['Abdominal Pain', 'Cardiac Arrest', 'Chest Pain', 'Stroke Symptoms'])
        ctas = st.selectbox("Triage", ['CTAS 1 (Resuscitation)', 'CTAS 2 (Emergent)', 'CTAS 3 (Urgent)'])
        n = st.slider("Nurse Ratio", 1, 10, 4); s = st.slider("Spec Availability", 0, 5, 2)
        if st.form_submit_button("Admit"):
            requests.post(f"{API_URL}/predict", json={"age": age, "condition": c, "ctas_level": ctas, "nurse_ratio": n, "specialist_availability": s, "region": "Toronto Region", "hospital": h})
            st.rerun()

tab1, tab2, tab3 = st.tabs(["📊 Live Census", "📈 Analytics", "🧹 Room Service"])

with tab1:
    if patients:
        df = pd.DataFrame(patients)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        now = datetime.now()
        df['mins'] = (now - df['timestamp']).dt.total_seconds() / 60
        df['live_wait'] = (df['est_wait_time'] - df['mins']).clip(lower=0).round(1)
        df['live_prob'] = (df['discharge_prob'] + (df['mins'] * 0.01)).clip(lower=0.1, upper=0.99)

        for _, row in df.iterrows():
            c1, c2, c3, c4, c5 = st.columns([1, 2, 1, 1, 1])
            c1.write(f"**{row['patient_id']}**")
            c2.write(f"{row['hospital']} | {row['condition']}")
            c3.write(f"⌛ {row['live_wait']}m left")
            p_val = row['live_prob']
            color = "green" if p_val > 0.75 else "orange" if p_val > 0.45 else "red"
            c4.markdown(f":{color}[**Prob: {p_val:.0%}**]")
            if c5.button("Discharge ✅", key=row['patient_id']):
                requests.post(f"{API_URL}/discharge/{row['patient_id']}?hospital={row['hospital']}")
                st.rerun()
            st.divider()
    else: st.info("No active patients.")

with tab2:
    if patients:
        df_a = pd.DataFrame(patients)
        col1, col2 = st.columns(2)
        fig_heat = px.density_heatmap(df_a, x="hospital", y="ctas_level", title="System Load Intensity", color_continuous_scale="Viridis")
        col1.plotly_chart(fig_heat, use_container_width=True)
        fig_pie = px.pie(df_a, names="condition", title="Current Condition Mix", hole=0.4)
        col2.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    st.subheader("🧹 Fair-Labor Sanitation Queue")
    if staff_data:
        sdf = pd.DataFrame(staff_data)
        cols = st.columns(len(sdf))
        for i, row in sdf.iterrows():
            with cols[i]:
                st.progress(min(row['hours_worked']/40, 1.0))
                st.write(f"**{row['name']}**")
                st.caption(f"{row['hours_worked']} / 40h")
    st.divider()

    if tickets:
        tdf = pd.DataFrame(tickets)
        for _, row in tdf.iterrows():
            t1, t2, t3, t4 = st.columns([1, 1.5, 2, 1.5])
            t1.write(row['ticket_id'])
            t2.write(row['hospital'])
            
            # --- PHASE 1: ACCEPTANCE ---
            if row['status'] == "Pending Acceptance":
                t3.info(f"📩 Sent to {row['staff_assigned']}")
                if t4.button("Staff: Accept ✅", key=f"acc_{row['ticket_id']}"):
                    requests.post(f"{API_URL}/accept_ticket/{row['ticket_id']}")
                    st.rerun()

            # --- PHASE 2: CLEANING TIMER ---
            elif row['status'] == "In Progress":
                start_time = pd.to_datetime(row['cleaning_start_time'], errors='coerce')
                elapsed = (datetime.now() - start_time).total_seconds() / 60
                rem = max(0, 0.5 - elapsed) 
                if rem > 0:
                    t3.warning(f"🕒 Cleaning... {rem:.1f}m")
                    t4.write(f"👷 {row['staff_assigned']}")
                else:
                    t3.success("✅ Cleaned")
                    if t4.button("Verify ✨", key=f"v_{row['ticket_id']}"):
                        requests.post(f"{API_URL}/complete_ticket/{row['ticket_id']}?staff_name={row['staff_assigned']}")
                        st.balloons(); st.rerun()
            
            # --- PHASE 3: ASSIGNMENT ---
            else:
                best_match = sdf.iloc[0]['name']
                t3.info(f"💡 Suggest: {best_match}")
                if t4.button(f"Assign {best_match.split()[0]}", key=f"a_{row['ticket_id']}"):
                    requests.post(f"{API_URL}/assign_staff", json={"ticket_id": row['ticket_id'], "staff_name": best_match})
                    st.rerun()
    else: st.info("No beds awaiting cleaning.")

time.sleep(5)
st.rerun()
