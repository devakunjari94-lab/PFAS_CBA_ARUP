import os
import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# ======================
# 🔐 PASSWORD
# ======================
APP_PASSWORD = "PFAS2026"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pw = st.text_input("Enter password", type="password")
    if pw:
        if pw == APP_PASSWORD:
            st.session_state.auth = True
            st.success("✅ Access granted")
        else:
            st.error("❌ Wrong password")
            st.stop()
    else:
        st.stop()

# ======================
# CONFIG + LOGO
# ======================
st.set_page_config(page_title="PFAS Decision Tool", layout="wide")

st.title("PFAS Polluter-Pays Cost & Decision Tool")

# ======================
# DISCLAIMER
# ======================
with st.expander("⚠️ Model Scope"):
    st.markdown("""
This tool provides **screening-level estimates**.

✔ Early-stage decision  
✔ Technology comparison  

❌ Not for detailed design or contractor pricing  

Uses P50 (expected) and P90 (conservative) scenarios based on EPA-style modelling.
""")

# ======================
# STEP 1: SITE INFO
# ======================
st.header("Step 1: Site Information")

c1,c2,c3 = st.columns(3)
site = c1.text_input("Site Name","PFAS Site")
water_volume = c2.number_input("Water Volume (m³)", value=1_000_000.0)
soil_mass = c3.number_input("Soil Mass (t)", value=10000.0)

receptor = st.selectbox("Receptor", ["Drinking water","Surface water","Wastewater"])

# ======================
# STEP 2: PFAS DATA
# ======================
st.header("Step 2: PFAS Data")

with st.expander("🌍 PFAS Map"):
    components.iframe("https://pdh.cnrs.fr/en/map/", height=500)

unit = st.selectbox("Unit",["ng/L","µg/L","mg/L"], index=1)
conv = {"ng/L":0.001,"µg/L":1,"mg/L":1000}

use_general = st.checkbox("Use General PFAS only")

chains = ["General PFAS"] if use_general else ["PFOA","PFOS","PFHxS","PFNA"]

influent = {}
for c in chains:
    val = st.number_input(f"{c} ({unit})", value=10.0)
    influent[c] = val * conv[unit]

# ======================
# STEP 3: FLOW
# ======================
st.header("Step 3: Flow Rate")

flow_rate = st.number_input("Flow rate (m³/day)", value=5000.0)
duration = water_volume / flow_rate if flow_rate>0 else 0

st.info(f"Duration = Volume / Flow = {water_volume:,} / {flow_rate:,} = {duration:.0f} days")

with st.expander("ℹ What is Flow Rate?"):
    st.markdown("""
Flow rate defines how fast water is treated (m³/day).  
It determines plant size and cost.

Higher flow = higher CAPEX  
Lower flow = longer treatment time  
""")

# ======================
# COST SCENARIO
# ======================
scenario = st.radio("Scenario",["P50 (Expected)","P90 (Conservative)"])
cost_key = "P50" if "P50" in scenario else "P90"
eff_idx = 0 if cost_key=="P50" else 1

# ======================
# METHODS
# ======================
water_methods = {
    "GAC":{"P50":0.04,"P90":0.08,"eff":(0.7,0.9),"type":"Removal"},
    "Ion Exchange":{"P50":0.06,"P90":0.12,"eff":(0.75,0.95),"type":"Removal"},
    "RO":{"P50":0.12,"P90":0.25,"eff":(0.9,0.99),"type":"Removal"},
    "AOP":{"P50":0.5,"P90":1.2,"eff":(0.7,0.99),"type":"Destruction"},
    "SCWO":{"P50":8,"P90":20,"eff":(0.95,1.0),"type":"Destruction"}
}

soil_methods = {
    "Incineration":{"P50":150,"P90":300,"eff":(0.9,1.0)},
    "Landfill":{"P50":80,"P90":200,"eff":(0.3,0.5)},
    "Soil Washing":{"P50":50,"P90":120,"eff":(0.5,0.8)}
}

# ======================
# STEP 4: METHODS
# ======================
st.header("Step 4: Treatment Selection")

water_sel = st.multiselect("Water Treatment", list(water_methods.keys()))
soil_sel = st.multiselect("Soil Treatment", list(soil_methods.keys()))

# ======================
# MASS BALANCE
# ======================
mass_in = {k:(v*water_volume)/1e9 for k,v in influent.items()}
remaining = mass_in.copy()

treatment_cost = 0

for m in water_sel:
    data = water_methods[m]
    cost = data[cost_key] * water_volume
    eff = data["eff"][eff_idx]
    treatment_cost += cost

    for k in remaining:
        remaining[k] *= (1-eff)

soil_cost = sum(soil_methods[m][cost_key]*soil_mass for m in soil_sel)

# ======================
# COST MODEL
# ======================
capex = flow_rate * 200
opex = treatment_cost * duration * 0.01
waste_cost = water_volume * 0.05 * 250
monitoring = 50000

total_cost = capex + opex + waste_cost + monitoring + soil_cost

# ======================
# RESULTS
# ======================
st.header("Step 5: Results")

total_in = sum(mass_in.values())
total_out = sum(remaining.values())
removed = total_in - total_out

final_conc = (total_out * 1e9)/water_volume

st.metric("PFAS In (kg)", f"{total_in:.2f}")
st.metric("Remaining (kg)", f"{total_out:.2f}")
st.metric("Removed (kg)", f"{removed:.2f}")
st.metric("Final Concentration (µg/L)", f"{final_conc:.4f}")

# ======================
# HAZARD INDEX
# ======================
thresholds = {c:0.5 for c in chains}

hazard = 0
rows=[]
for c in chains:
    conc = remaining[c]*1e9/water_volume
    th = thresholds[c]
    hazard += conc/th
    rows.append([c, conc, th])

st.table(pd.DataFrame(rows, columns=["PFAS","Value","Limit"]))

st.metric("Hazard Index", f"{hazard:.2f}")

with st.expander("ℹ Hazard Index"):
    st.markdown("""
Hazard Index = Σ (Concentration / Limit)

≤1 = Compliant  
>1 = Risk  

Used to assess cumulative PFAS risk.
""")

# ======================
# COST RESULTS
# ======================
st.header("Step 6: Costs")

st.metric("CAPEX", f"£{capex:,.0f}")
st.metric("OPEX", f"£{opex:,.0f}")
st.metric("Waste", f"£{waste_cost:,.0f}")
st.metric("Monitoring", f"£{monitoring:,.0f}")
st.metric("Soil Cost", f"£{soil_cost:,.0f}")
st.metric("Total Cost", f"£{total_cost:,.0f}")

if removed>0:
    st.metric("£/kg removed", f"£{total_cost/removed:,.0f}")

# ======================
# CALCULATION PROOF
# ======================
with st.expander("📐 Calculation Breakdown"):
    st.markdown(f"""
Mass = Conc × Volume / 1e9  

CAPEX = Flow × 200 = {flow_rate} × 200 = £{capex:,.0f}  

OPEX ≈ Treatment × Duration × 1% = £{opex:,.0f}  

Waste = 5% × Volume × 250 = £{waste_cost:,.0f}  

Total = CAPEX + OPEX + Waste + Monitoring + Soil  

= £{total_cost:,.0f}
""")

# ======================
# VISUAL
# ======================
df = pd.DataFrame({
    "Type":["CAPEX","OPEX","Waste","Monitoring","Soil"],
    "Cost":[capex,opex,waste_cost,monitoring,soil_cost]
})

st.plotly_chart(px.bar(df,x="Type",y="Cost",text="Cost"))

# ======================
# REFERENCES
# ======================
with st.expander("📚 References"):
    st.markdown("""
• US EPA PFAS Cost Models (2023–2024)  
• EPA WBS Engineering Cost Framework  
• ITRC PFAS Guidance  

EPA shows costs depend heavily on flow, influent, and design assumptions [1](https://www.epa.gov/sdwa/drinking-water-treatment-technology-unit-cost-models)  
PFAS treatment costs vary significantly due to site-specific conditions [2](https://www.waterandwastewater.com/cost-pfas-removal-systems-capital-lifecycle-factors/)  
""")

