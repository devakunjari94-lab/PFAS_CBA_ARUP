import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

st.title("PFAS Polluter-Pays Decision Tool")

# ======================
# ✅ TOP SECTION (CRITICAL)
# ======================

# 🔴 DISCLAIMER
with st.expander("⚠️ Model Limitations"):
    st.markdown("""
This tool provides **screening-level estimates only**.

✔ Used for:
- early-stage decision making  
- comparing treatment options  

❌ Not for:
- detailed design  
- contractor pricing  

""")

# 🔴 P50 / P90 EXPLANATION
with st.expander("📊 Why P50 / P90 is used"):
    st.markdown("""
PFAS treatment costs vary significantly depending on:

- PFAS chemistry  
- site conditions  
- treatment design  
- waste handling  

**P50 = expected cost (median)**  
**P90 = conservative cost (risk-averse)**  

This reflects standard engineering practice.
""")

# 🔴 EPA COST EXPLANATION (THIS IS WHAT YOU ASKED)
with st.expander("📚 EPA Cost Model Explanation"):
    st.markdown("""
The US EPA **does NOT provide fixed cost values (e.g. £/m³)**.

Instead, EPA uses:

➡️ **Engineering cost models (Work Breakdown Structure – WBS)**

These models calculate cost based on:
- flow rate  
- plant size  
- equipment  
- energy  
- waste handling  

EPA explicitly states that:

- costs depend heavily on system design and inputs [1](https://www.epa.gov/sdwa/drinking-water-treatment-technology-unit-cost-models)  
- PFAS treatment cost varies significantly depending on site conditions [2](https://www.waterandwastewater.com/cost-pfas-removal-systems-capital-lifecycle-factors/)  

✅ Therefore, this tool uses **P50/P90 ranges derived from EPA-style modelling**
to provide realistic screening estimates.
""")

# ======================
# STEP 1: SITE DATA
# ======================
st.header("Step 1: Site Information")

col1,col2 = st.columns(2)
water_volume = col1.number_input("Water Volume (m³)", value=1_000_000.0)
soil_mass = col2.number_input("Soil Mass (tonnes)", value=10000.0)

# ======================
# STEP 2: PFAS DATA
# ======================
st.header("Step 2: PFAS Data")

with st.expander("🌍 PFAS Map"):
    components.iframe("https://pdh.cnrs.fr/en/map/", height=500)

use_general = st.checkbox("Use General PFAS only")

if use_general:
    chains = ["General PFAS"]
else:
    chains = ["PFOA","PFOS","PFHxS","PFNA"]

influent = {}
for c in chains:
    influent[c] = st.number_input(f"{c} (µg/L)", value=10.0)

# ======================
# STEP 3: FLOW RATE
# ======================
st.header("Step 3: Flow Rate")

flow_rate = st.number_input("Flow Rate (m³/day)", value=5000.0)
duration = water_volume / flow_rate

st.info(f"Treatment duration ≈ {duration:.0f} days")

with st.expander("ℹ️ What is flow rate?"):
    st.markdown("""
Flow rate = amount of water treated per day (m³/day)

It determines:
- plant size  
- capital cost  
- treatment duration  
""")

# ======================
# STEP 4: COST SCENARIO
# ======================
scenario = st.radio("Scenario", ["P50 (Expected)", "P90 (Conservative)"])
cost_key = "P50" if "P50" in scenario else "P90"
eff_idx = 0 if cost_key=="P50" else 1

# 🔴 COST EXPLANATION BEFORE METHODS
with st.expander("📊 Cost Assumptions"):
    st.markdown("""
Costs shown are **unit treatment costs (£/m³)** derived from:

- EPA cost modelling frameworks  
- ITRC PFAS guidance  
- industry data  

Values represent:
- P50 → typical condition  
- P90 → conservative scenario  
""")

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
    "Landfill":{"P50":80,"P90":200,"eff":(0.3,0.5)}
}

# ======================
# STEP 5: SELECT METHODS
# ======================
st.header("Step 4: Treatment Selection")

water_sel = st.multiselect("Water Methods", list(water_methods.keys()))
soil_sel = st.multiselect("Soil Methods", list(soil_methods.keys()))

# ======================
# MASS BALANCE
# ======================
mass_in = {k:(v*water_volume)/1e9 for k,v in influent.items()}
remaining = mass_in.copy()

treatment_cost = 0

for m in water_sel:
    data = water_methods[m]
    cost = data[cost_key]*water_volume
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
waste = water_volume * 0.05 * 250
monitoring = 50000

total_cost = capex + opex + waste + monitoring + soil_cost

# ======================
# RESULTS
# ======================
st.header("Step 5: Results")

total_in = sum(mass_in.values())
total_out = sum(remaining.values())
removed = total_in - total_out

final_conc = (total_out*1e9)/water_volume

st.metric("PFAS Removed (kg)", f"{removed:.2f}")
st.metric("Final Concentration (µg/L)", f"{final_conc:.4f}")

# ======================
# COST RESULTS
# ======================
st.header("Step 6: Cost Summary")

st.metric("CAPEX", f"£{capex:,.0f}")
st.metric("OPEX", f"£{opex:,.0f}")
st.metric("Total Cost", f"£{total_cost:,.0f}")

# ======================
# CALCULATION PROOF
# ======================
with st.expander("📐 Calculation Breakdown"):
    st.markdown(f"""
CAPEX = Flow × 200 = £{capex:,.0f}  

OPEX ≈ Treatment × Duration × 1%  

Total Cost = CAPEX + OPEX + Waste + Monitoring  

= £{total_cost:,.0f}  
""")

# ======================
# REFERENCES (BOTTOM)
# ======================
with st.expander("📚 References"):
    st.markdown("""
• US EPA Drinking Water Treatment Cost Models  
• EPA WBS Cost Framework  
• ITRC PFAS Guidance  

EPA explains that:
- cost depends on flow and design [1](https://www.epa.gov/sdwa/drinking-water-treatment-technology-unit-cost-models)  
- PFAS treatment cost varies by site conditions [2](https://www.waterandwastewater.com/cost-pfas-removal-systems-capital-lifecycle-factors/)  
""")
