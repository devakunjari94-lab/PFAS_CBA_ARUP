import os
import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="PFAS Decision Tool", layout="wide")

# ======================
# LOGO
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "arup_logo.png")

if os.path.exists(logo_path):
    st.image(logo_path, width=140)

st.title("PFAS Polluter-Pays Cost & Decision Tool")

# ======================
# DISCLAIMER
# ======================
with st.expander("⚠️ Model Scope & Limitations"):
    st.markdown("""
This tool provides **screening-level PFAS cost and performance estimates**.

✔ Suitable for:
- Early-stage decision making  
- Technology comparison  
- Order-of-magnitude cost estimation  

❌ Not suitable for:
- Detailed engineering design  
- Contractor pricing  
- Regulatory submission  

Costs follow **P50 (expected)** and **P90 (conservative)** scenarios  
based on EPA modelling approaches.
""")

# ======================
# COST EXPLANATION
# ======================
with st.expander("📊 Why P50 / P90 is used"):
    st.markdown("""
PFAS treatment costs vary significantly due to:

- PFAS chemistry (short vs long chain)
- Site-specific water quality
- Waste disposal requirements
- Regulatory targets

**P50 = expected cost (median)**  
**P90 = conservative cost (risk-averse)**  

This reflects *industry practice and EPA cost modelling*,  
which uses ranges and assumptions rather than fixed values.  
""")

# ======================
# COST DATABASE SOURCE
# ======================
with st.expander("📚 Cost Data Sources (EPA / ITRC)"):
    st.markdown("""
Cost ranges are based on:

• US EPA PFAS treatment cost reports (2023–2024)  
• EPA Work Breakdown Structure (WBS) cost models  
• ITRC PFAS Guidance (2026)  
• Industry case studies and utility data  

EPA shows treatment costs vary significantly depending on system design and O&M factors [1](https://www.epa.gov/sdwa/drinking-water-treatment-technology-unit-cost-models)  
PFAS cost estimation depends strongly on influent quality, flow, and treatment targets [2](https://www.waterandwastewater.com/cost-pfas-removal-systems-capital-lifecycle-factors/)  

These values represent **screening-level engineering estimates**.
""")

# ======================
# STEP 1: SITE INFO
# ======================
st.header("Step 1: Site Information")

c1, c2, c3 = st.columns(3)
with c1:
    site_name = st.text_input("Site Name", "PFAS Site")
with c2:
    water_volume = st.number_input("Water Volume (m³)", value=1_000_000.0)
with c3:
    soil_mass = st.number_input("Soil Mass (tonnes)", value=10000.0)

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
st.header("Step 2: PFAS Data")

with st.expander("🌍 PFAS Map"):
    if jurisdiction in ["UK", "EU"]:
        components.iframe("https://pdh.cnrs.fr/en/map/", height=500)
    elif jurisdiction == "USA":
        components.iframe("https://www.epa.gov/pfas/pfas-data-dashboard", height=500)
    else:
        components.iframe("https://www.pfasportal.org.au/", height=500)

unit = st.selectbox("Concentration Unit", ["ng/L","µg/L","mg/L"], index=1)
conv = {"ng/L":0.001,"µg/L":1,"mg/L":1000}

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

flow_rate = st.number_input("Flow Rate (m³/day)", value=5000.0)

duration = water_volume / flow_rate if flow_rate > 0 else 0
st.info(f"Estimated treatment duration: {duration:,.0f} days")

# ======================
# COST SCENARIO
# ======================
scenario = st.radio(
    "Cost Scenario",
    ["P50 (Expected)", "P90 (Conservative)"]
)

cost_key = "P50" if "P50" in scenario else "P90"
eff_key = 0 if cost_key == "P50" else 1

# ======================
# COST DATABASE
# ======================
water_methods = {
    "GAC": {"P50":0.04,"P90":0.08,"eff":(0.7,0.9),"type":"Removal","waste":True},
    "Ion Exchange": {"P50":0.06,"P90":0.12,"eff":(0.75,0.95),"type":"Removal","waste":True},
    "RO": {"P50":0.12,"P90":0.25,"eff":(0.9,0.99),"type":"Removal","waste":True},
    "Foam Fractionation": {"P50":0.04,"P90":0.08,"eff":(0.3,0.6),"type":"Removal","waste":True},
    "AOP": {"P50":0.50,"P90":1.20,"eff":(0.7,0.99),"type":"Destruction","waste":False},
    "SCWO": {"P50":8.0,"P90":20.0,"eff":(0.95,1.0),"type":"Destruction","waste":False},
    "Electrochemical": {"P50":0.20,"P90":0.60,"eff":(0.6,0.95),"type":"Destruction","waste":False}
}

# ======================
# STEP 4: TREATMENT TRAIN
# ======================
st.header("Step 4: Treatment Train")

selected = st.multiselect(
    "Select treatment methods (sequential)",
    list(water_methods.keys())
)

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

    cost = data[cost_key] * water_volume
    eff = data["eff"][eff_key]

    for k in remaining:
        removed_mass = remaining[k] * eff
        remaining[k] -= removed_mass

    if data["waste"]:
        waste = 250 * (water_volume * 0.05)
    else:
        waste = 0

    treatment_cost += cost
    waste_cost += waste

    st.write(f"""
    **{m}**
    - Cost: £{cost:,.0f}
    - Efficiency: {eff*100:.1f}%
    - Waste cost: £{waste:,.0f}
    """)

# ======================
# RESULTS
# ======================
st.header("Step 5: Results")

total_in = sum(mass_in.values())
total_out = sum(remaining.values())
removed = total_in - total_out

final_conc = (total_out * 1e9) / water_volume

c1, c2, c3 = st.columns(3)
c1.metric("PFAS Input (kg)", f"{total_in:.2f}")
c2.metric("Remaining (kg)", f"{total_out:.2f}")
c3.metric("Removed (kg)", f"{removed:.2f}")

st.metric("Final Concentration (µg/L)", f"{final_conc:.4f}")

# ======================
# COMPLIANCE
# ======================
st.header("Step 6: Compliance")

THRESH = {
    "UK":{
        "Drinking water":{"PFOA":0.4,"PFOS":0.015,"PFHxS":0.2,"PFNA":0.3,"General PFAS":0.4},
        "Surface water":{"PFOA":2,"PFOS":0.2,"PFHxS":0.5,"PFNA":0.6,"General PFAS":2},
        "Wastewater":{"PFOA":1,"PFOS":0.5,"PFHxS":1,"PFNA":1,"General PFAS":2}
    }
}

thresholds = THRESH["UK"][receptor]

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
st.header("Step 7: Cost Summary")

total_cost = treatment_cost + waste_cost

c1, c2, c3 = st.columns(3)
c1.metric("Treatment Cost", f"£{treatment_cost:,.0f}")
c2.metric("Waste Cost", f"£{waste_cost:,.0f}")
c3.metric("Total Cost (Estimate)", f"£{total_cost:,.0f}")

if removed > 0:
    st.metric("Cost per kg PFAS removed", f"£{total_cost/removed:,.0f}/kg")

# ======================
# VISUAL
# ======================
df = pd.DataFrame({
    "Category":["Treatment","Waste"],
    "Cost":[treatment_cost,waste_cost]
})

fig = px.bar(df, x="Category", y="Cost", text="Cost")
st.plotly_chart(fig, use_container_width=True)

# ======================
# INSIGHTS
# ======================
st.header("Decision Insight")

if final_conc > max(thresholds.values()):
    st.error("❌ Not compliant")
elif any(water_methods[m]["type"]=="Removal" for m in selected):
    st.warning("⚠ PFAS transferred to waste — long-term liability")
else:
    st.success("✅ Destruction pathway reduces long-term risk")
