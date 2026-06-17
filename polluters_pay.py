import os
import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

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
            st.success("✅ Access granted")
        else:
            st.error("❌ Incorrect password")
            st.stop()
    else:
        st.stop()

# ======================
# PAGE CONFIG + LOGO
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "arup_logo.png")

st.set_page_config(page_title="PFAS Decision Tool", layout="wide")

if os.path.exists(logo_path):
    st.image(logo_path, width=140)
else:
    st.warning("Logo not found. Add arup_logo.png to folder.")

st.title("PFAS Polluter-Pays Decision Support Tool")

# ======================
# DISCLAIMER
# ======================
with st.expander("⚠️ Model Assumptions & Limitations"):
    st.markdown("""
This tool provides **screening-level estimates** only.

✔ Suitable for:
- Early decision-making  
- Cost comparison  
- Scenario analysis  

❌ Not suitable for:
- Detailed design  
- Regulatory submission  
- Contractor pricing  

Always validate with site-specific data.
""")

# ======================
# STEP 1: SITE INFO
# ======================
st.header("Step 1: Site Information")

col1, col2, col3 = st.columns(3)
with col1:
    site_name = st.text_input("Site name", "PFAS Site")
with col2:
    water_volume = st.number_input("Water volume (m³)", value=1_000_000.0)
with col3:
    soil_mass = st.number_input("Soil mass (tonnes)", value=10_000.0)

receptor = st.selectbox(
    "Receptor Type",
    ["Drinking water", "Surface water", "Wastewater"]
)

jurisdiction = st.selectbox(
    "Jurisdiction",
    ["UK", "EU", "USA", "Australia"]
)

# ======================
# STEP 2: PFAS INPUT
# ======================
st.header("Step 2: PFAS Contamination")

# ✅ MAP
with st.expander("🌍 PFAS Map"):
    if jurisdiction in ["UK", "EU"]:
        components.iframe("https://pdh.cnrs.fr/en/map/", height=600)
    elif jurisdiction == "USA":
        components.iframe("https://www.epa.gov/pfas/pfas-data-dashboard", height=600)
    else:
        components.iframe("https://www.pfasportal.org.au/", height=600)

# ✅ UNIT
unit = st.selectbox("Unit", ["ng/L","µg/L","mg/L"], index=1)
conv = {"ng/L":0.001, "µg/L":1, "mg/L":1000}

# ✅ GENERAL PFAS OPTION
use_general = st.checkbox("Use General PFAS only")

if use_general:
    chains = ["General PFAS"]
else:
    chains = ["PFOA","PFOS","PFHxS","PFNA"]

influent = {}

cols = st.columns(len(chains))
for col, c in zip(cols, chains):
    with col:
        val = st.number_input(f"{c} ({unit})", value=10.0)
        influent[c] = val * conv[unit]

# ======================
# STEP 3: FLOW
# ======================
st.header("Step 3: Flow & Duration")

flow_rate = st.number_input("Flow rate (m³/day)", value=5000.0)
duration = water_volume / flow_rate if flow_rate > 0 else 0

st.info(f"Estimated treatment duration: {duration:,.0f} days")

# ======================
# METHODS
# ======================
water_methods = {
    "GAC": {"cost":(0.02,0.08),"eff":(0.6,0.9),"type":"Removal","waste":True},
    "Ion Exchange": {"cost":(0.03,0.12),"eff":(0.7,0.95),"type":"Removal","waste":True},
    "RO": {"cost":(0.05,0.2),"eff":(0.8,0.99),"type":"Removal","waste":True},
    "Foam Fractionation": {"cost":(0.01,0.05),"eff":(0.3,0.6),"type":"Removal","waste":True},
    "AOP": {"cost":(0.15,1.0),"eff":(0.7,0.99),"type":"Destruction","waste":False},
    "SCWO": {"cost":(6.8,25.5),"eff":(0.9,1.0),"type":"Destruction","waste":False}
}

scenario = st.radio("Cost Scenario", ["Moderate","Conservative"])
idx = 0 if scenario=="Moderate" else 1

# ======================
# STEP 4: TREATMENT TRAIN
# ======================
st.header("Step 4: Treatment Train")

selected = st.multiselect("Select methods (sequential)", list(water_methods.keys()))

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

    cost = data["cost"][idx]*water_volume
    eff = data["eff"][idx]

    for k in remaining:
        removed = remaining[k]*eff
        remaining[k] -= removed

    if data["waste"]:
        waste = 250*(water_volume*0.05)
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

c1,c2,c3 = st.columns(3)
c1.metric("PFAS In (kg)", f"{total_in:.2f}")
c2.metric("Remaining (kg)", f"{total_out:.2f}")
c3.metric("Removed (kg)", f"{removed:.2f}")

st.metric("Final Concentration (µg/L)", f"{final_conc:.4f}")

# ======================
# COMPLIANCE
# ======================
st.header("Step 6: Compliance")

THRESH = {
    "UK": {
        "Drinking water":{"PFOA":0.4,"PFOS":0.015,"PFHxS":0.2,"PFNA":0.3,"General PFAS":0.4},
        "Surface water":{"PFOA":2,"PFOS":0.2,"PFHxS":0.5,"PFNA":0.6,"General PFAS":2},
        "Wastewater":{"PFOA":1,"PFOS":0.5,"PFHxS":1,"PFNA":1,"General PFAS":2}
    },
    "EU": {"Drinking water":{c:0.1 for c in chains},"Surface water":{c:0.5 for c in chains},"Wastewater":{c:1 for c in chains}},
    "USA": {"Drinking water":{"PFOA":0.004,"PFOS":0.004,"PFHxS":0.02,"PFNA":0.02,"General PFAS":0.01},
            "Surface water":{c:0.05 for c in chains},"Wastewater":{c:0.1 for c in chains}},
    "Australia":{"Drinking water":{"PFOA":0.56,"PFOS":0.56,"PFHxS":0.1,"PFNA":0.07,"General PFAS":0.5},
                  "Surface water":{c:0.5 for c in chains},"Wastewater":{c:1 for c in chains}}
}

thresholds = THRESH[jurisdiction][receptor]

rows=[]
hazard=0

for k in chains:
    conc = remaining[k]*1e9/water_volume
    th = thresholds.get(k, list(thresholds.values())[0])
    hazard += conc/th
    rows.append([k, conc, th, "✅" if conc<=th else "❌"])

st.table(pd.DataFrame(rows, columns=["PFAS","Value","Limit","Status"]))

if hazard <= 1:
    st.success(f"Hazard Index {hazard:.2f} — Compliant")
else:
    st.error(f"Hazard Index {hazard:.2f} — Exceeds")

# ======================
# COSTS
# ======================
st.header("Step 7: Costs")

total_cost = treatment_cost + waste_cost

c1,c2,c3 = st.columns(3)
c1.metric("Treatment Cost", f"£{treatment_cost:,.0f}")
c2.metric("Waste Cost", f"£{waste_cost:,.0f}")
c3.metric("Total Cost (Estimate)", f"£{total_cost:,.0f}")

if removed > 0:
    st.metric("£ per kg PFAS removed", f"£{total_cost/removed:,.0f}/kg")

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
st.header("Decision Insights")

if final_conc > max(thresholds.values()):
    st.error("❌ System not compliant")
elif any(water_methods[m]["type"]=="Removal" for m in selected):
    st.warning("⚠ PFAS transferred to waste — long-term liability remains")
else:
    st.success("✅ Destruction pathway reduces long-term risk")
