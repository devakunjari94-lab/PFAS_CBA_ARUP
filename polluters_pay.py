import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ======================
# 🔐 PASSWORD
# ======================
APP_PASSWORD = "ARUPPFASSWS2026"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pw = st.text_input("Enter password", type="password")
    if pw:
        if pw == APP_PASSWORD:
            st.session_state.auth = True
            st.success("Access granted")
        else:
            st.error("Incorrect password")
            st.stop()
    else:
        st.stop()

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="PFAS Decision Tool", layout="wide")
st.title("PFAS Treatment Cost & Compliance Tool")

# ======================
# STEP 1: SITE DATA
# ======================
st.header("Step 1: Site Information")

col1, col2, col3 = st.columns(3)
with col1:
    site_name = st.text_input("Site name", "PFAS Site")
with col2:
    water_volume = st.number_input("Water volume (m³)", value=1_000_000.0)
with col3:
    soil_mass = st.number_input("Soil mass (tonnes)", value=10_000.0)

receptor = st.selectbox("Receptor", ["Drinking water", "Surface water"])

jurisdiction = st.selectbox("Regulation", [
    "UK", "EU", "USA", "Australia"
])

# ======================
# STEP 2: PFAS INPUT
# ======================
st.header("Step 2: PFAS Concentrations")

chains = ["PFOA","PFOS","PFHxS","PFNA"]
influent = {}

cols = st.columns(len(chains))
for col, c in zip(cols, chains):
    with col:
        influent[c] = st.number_input(f"{c} (µg/L)", value=10.0)

# ======================
# STEP 3: FLOW
# ======================
st.header("Step 3: System Flow")

flow_rate = st.number_input("Flow rate (m³/day)", value=5000.0)

duration = water_volume / flow_rate if flow_rate > 0 else 0
st.info(f"Estimated duration: {duration:.0f} days")

# ======================
# METHODS
# ======================
water_methods = {
    "GAC": {"cost":(0.02,0.08),"eff":(0.6,0.9),"type":"Removal","waste":True},
    "Ion Exchange": {"cost":(0.03,0.12),"eff":(0.7,0.95),"type":"Removal","waste":True},
    "RO": {"cost":(0.05,0.2),"eff":(0.8,0.99),"type":"Removal","waste":True},
    "Foam Fractionation": {"cost":(0.01,0.05),"eff":(0.3,0.6),"type":"Removal","waste":True},
    "AOP": {"cost":(0.15,1.0),"eff":(0.7,0.99),"type":"Destruction","waste":False},
    "SCWO": {"cost":(6.8,25.5),"eff":(0.9,1.0),"type":"Destruction","waste":False},
}

scenario = st.radio("Scenario", ["Moderate","Conservative"])
cost_idx = 0 if scenario=="Moderate" else 1

# ======================
# STEP 4: TREATMENT TRAIN
# ======================
st.header("Step 4: Treatment Train")

selected = st.multiselect("Select methods (in order)", list(water_methods.keys()))

# ======================
# MASS BALANCE
# ======================
mass_in = {k:(v*water_volume)/1e9 for k,v in influent.items()}
remaining = mass_in.copy()

treatment_cost = 0
waste_cost = 0

st.subheader("Treatment Performance")

for m in selected:
    data = water_methods[m]

    cost = data["cost"][cost_idx]*water_volume
    eff = data["eff"][cost_idx]

    for k in remaining:
        removed = remaining[k]*eff
        remaining[k] -= removed

    if data["waste"]:
        waste = 200*(water_volume*0.05)
        waste_cost += waste
    else:
        waste = 0

    treatment_cost += cost

    st.write(f"""
    **{m}**
    - Cost: £{cost:,.0f}
    - Efficiency: {eff*100:.0f}%
    - Waste cost: £{waste:,.0f}
    """)

# ======================
# RESULTS
# ======================
st.header("Step 5: Results")

total_in = sum(mass_in.values())
total_out = sum(remaining.values())
removed = total_in - total_out

final_conc = (total_out*1e9)/water_volume if water_volume>0 else 0

col1,col2,col3 = st.columns(3)

col1.metric("PFAS In (kg)", f"{total_in:.2f}")
col2.metric("Remaining (kg)", f"{total_out:.2f}")
col3.metric("Removed (kg)", f"{removed:.2f}")

st.metric("Final concentration (µg/L)", f"{final_conc:.4f}")

# ======================
# COMPLIANCE
# ======================
st.header("Compliance")

THRESH = {
    "UK":{"Drinking water":{"PFOA":0.4,"PFOS":0.015,"PFHxS":0.2,"PFNA":0.3}},
    "EU":{"Drinking water":{"PFOA":0.1,"PFOS":0.1,"PFHxS":0.1,"PFNA":0.1}},
    "USA":{"Drinking water":{"PFOA":0.004,"PFOS":0.004,"PFHxS":0.02,"PFNA":0.02}},
    "Australia":{"Drinking water":{"PFOA":0.56,"PFOS":0.56,"PFHxS":0.1,"PFNA":0.07}},
}

thresholds = THRESH[jurisdiction]["Drinking water"]

rows=[]
hazard=0

for k in chains:
    conc = remaining[k]*1e9/water_volume
    th = thresholds[k]
    hazard += conc/th
    rows.append([k, conc, th, "✅" if conc<=th else "❌"])

st.table(pd.DataFrame(rows, columns=["PFAS","Value","Limit","Status"]))

if hazard<=1:
    st.success(f"Hazard index {hazard:.2f} (Compliant)")
else:
    st.error(f"Hazard index {hazard:.2f} (Fail)")

# ======================
# COSTS
# ======================
st.header("Step 6: Costs")

total = treatment_cost + waste_cost

col1,col2,col3 = st.columns(3)

col1.metric("Treatment cost", f"£{treatment_cost:,.0f}")
col2.metric("Waste cost", f"£{waste_cost:,.0f}")
col3.metric("Total cost", f"£{total:,.0f}")

if removed>0:
    st.metric("£ / kg removed", f"£{total/removed:,.0f}/kg")

# ======================
# VISUAL
# ======================
df = pd.DataFrame({
    "Category":["Treatment","Waste"],
    "Cost":[treatment_cost, waste_cost]
})

fig = px.bar(df, x="Category", y="Cost", text="Cost")
st.plotly_chart(fig, use_container_width=True)

# ======================
# INSIGHT
# ======================
st.header("Decision Insight")

if final_conc > list(thresholds.values())[0]:
    st.error("System not compliant")
elif any(water_methods[m]["type"]=="Removal" for m in selected):
    st.warning("PFAS transferred to waste stream (liability remains)")
else:
    st.success("Destruction pathway reduces liability")
