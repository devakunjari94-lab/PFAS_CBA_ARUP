import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# ======================
# 🔐 PASSWORD PROTECTION
# ======================
PASSWORD = "PFAS2026"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pw = st.text_input("Enter password to access the tool", type="password")
    if pw:
        if pw == PASSWORD:
            st.session_state.authenticated = True
            st.success("✅ Access granted")
        else:
            st.error("❌ Incorrect password")
            st.stop()
    else:
        st.stop()

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(layout="wide")
st.title("PFAS Polluter-Pays Decision Support Tool")

# ======================
# 🔴 MODEL EXPLANATION
# ======================
with st.expander("📚 Cost Methodology (EPA Adaptation)"):
    st.markdown("""
This tool uses:

- US EPA Work Breakdown Structure (WBS) cost models  
- Industry PFAS treatment data  
- Engineering scaling assumptions  

EPA does not provide fixed £/m³ costs — instead, it calculates costs based on:
- flow rate
- system design
- operating conditions [1](https://sustainabilityservices.eurofins.com/news/2025-pfas-regulations-the-global-landscape/)  

PFAS costs vary widely depending on site-specific factors [2](https://www.lathropgpm.com/insights/epa-moves-to-address-pfas-discharges-under-clean-water-act-ahead-of-new-administration/)  

This tool converts that into:
- P50 (expected)
- P90 (conservative)

✅ For screening-level decision making  
❌ Not for detailed design or regulatory submissions  
""")

# ======================
# STEP 1: SITE DATA
# ======================
st.header("Step 1: Site Information")

col1, col2 = st.columns(2)
water_volume = col1.number_input("Water Volume (m³)", value=1_000_000.0)
soil_mass = col2.number_input("Soil Mass (tonnes)", value=10_000.0)

# ======================
# STEP 2: PFAS DATA
# ======================
st.header("Step 2: PFAS Contamination")

with st.expander("🌍 PFAS Map"):
    components.iframe("https://pdh.cnrs.fr/en/map/", height=400)

chains = ["PFOA","PFOS","PFHxS","PFNA"]

influent = {}
for c in chains:
    influent[c] = st.number_input(f"{c} (µg/L)", value=10.0)

# ======================
# STEP 3: FLOW
# ======================
st.header("Step 3: Flow Rate")

flow_rate = st.number_input("Flow rate (m³/day)", value=5000.0)
duration = water_volume / flow_rate if flow_rate > 0 else 0

st.info(f"Duration = Volume / Flow = {duration:.0f} days")

# ======================
# SCENARIO
# ======================
scenario = st.radio("Cost Scenario", ["P50 (Expected)", "P90 (Conservative)"])
cost_key = "P50" if "P50" in scenario else "P90"
eff_idx = 0 if cost_key == "P50" else 1

# ======================
# METHODS
# ======================
water_methods = {
    "GAC": {"P50":0.04,"P90":0.08,"eff":(0.7,0.9),"type":"Removal"},
    "Ion Exchange": {"P50":0.06,"P90":0.12,"eff":(0.75,0.95),"type":"Removal"},
    "RO": {"P50":0.12,"P90":0.25,"eff":(0.9,0.99),"type":"Removal"},
    "AOP": {"P50":0.5,"P90":1.2,"eff":(0.7,0.99),"type":"Destruction"},
    "SCWO": {"P50":8,"P90":20,"eff":(0.95,1.0),"type":"Destruction"}
}

soil_methods = {
    "Incineration": {"P50":150,"P90":300},
    "Landfill": {"P50":80,"P90":200}
}

# ======================
# STEP 4: SELECT METHODS
# ======================
st.header("Step 4: Treatment Selection")

water_sel = st.multiselect("Water Treatment Methods", list(water_methods.keys()))
soil_sel = st.multiselect("Soil Treatment Methods", list(soil_methods.keys()))

# ======================
# MASS BALANCE
# ======================
mass_in = {k:(v*water_volume)/1e9 for k,v in influent.items()}
remaining = mass_in.copy()

treatment_cost = 0

st.header("🔧 Method Calculations (Full Transparency)")

for m in water_sel:
    data = water_methods[m]

    unit_cost = data[cost_key]
    eff = data["eff"][eff_idx]

    cost = unit_cost * water_volume
    treatment_cost += cost

    for k in remaining:
        remaining[k] *= (1-eff)

    st.markdown(f"## {m}")

    with st.expander(f"📐 {m} Detailed Calculation"):
        st.markdown(f"""
### Cost Equation
Cost = Unit Cost × Volume  

= {unit_cost} × {water_volume:,}  
= **£{cost:,.0f}**

### PFAS Removal
Remaining = Initial × (1 − {eff*100:.1f}%)

### CAPEX Drivers
- Equipment sizing (depends on flow)
- Tanks / membranes / reactors

### OPEX Drivers
- Energy consumption
- Media replacement (GAC, IX)
- Maintenance

### Source
Derived from EPA WBS cost modelling approach  
(flow → design → cost) [1](https://sustainabilityservices.eurofins.com/news/2025-pfas-regulations-the-global-landscape/)  

PFAS costs vary based on site and design [2](https://www.lathropgpm.com/insights/epa-moves-to-address-pfas-discharges-under-clean-water-act-ahead-of-new-administration/)  
""")

# ======================
# SOIL COST
# ======================
soil_cost = 0

for m in soil_sel:
    unit = soil_methods[m][cost_key]
    cost = unit * soil_mass
    soil_cost += cost

    st.markdown(f"## {m} (Soil)")

    with st.expander(f"📐 {m} Calculation"):
        st.markdown(f"""
Cost = Unit × Soil Mass  

= {unit} × {soil_mass:,}  
= **£{cost:,.0f}**

Based on remediation cost ranges:
- excavation
- transport
- disposal
""")

# ======================
# COST MODEL
# ======================
capex = flow_rate * 200
opex = treatment_cost * duration * 0.01
waste_cost = water_volume * 0.05 * 250
monitoring_cost = 50000

total_cost = capex + opex + waste_cost + monitoring_cost + soil_cost

# ======================
# RESULTS
# ======================
total_in = sum(mass_in.values())
total_out = sum(remaining.values())
removed = total_in - total_out

final_conc = (total_out * 1e9) / water_volume

st.header("Step 5: Results")

st.metric("PFAS Removed (kg)", f"{removed:.2f}")
st.metric("Final Concentration (µg/L)", f"{final_conc:.4f}")

# ======================
# HAZARD INDEX
# ======================
hazard = 0
for k in chains:
    conc = remaining[k]*1e9/water_volume
    limit = 0.5
    hazard += conc/limit

st.metric("Hazard Index", f"{hazard:.2f}")

with st.expander("ℹ What is Hazard Index?"):
    st.markdown("""
Hazard Index = Σ (Concentration / Limit)

≤1 = compliant  
>1 = risk  

Used to assess combined PFAS impact.
""")

# ======================
# COST SUMMARY
# ======================
st.header("Step 6: Cost Summary")

col1,col2,col3 = st.columns(3)
col1.metric("CAPEX", f"£{capex:,.0f}")
col2.metric("OPEX", f"£{opex:,.0f}")
col3.metric("Total Cost", f"£{total_cost:,.0f}")

if removed > 0:
    st.metric("Cost per kg removed", f"£{total_cost/removed:,.0f}")

# ======================
# FULL CALCULATION PROOF
# ======================
with st.expander("📐 Full Calculation Breakdown"):
    st.markdown(f"""
Mass = Conc × Volume / 1e9  

CAPEX = Flow × 200 = £{capex:,.0f}  

OPEX ≈ Treatment × Duration × 1% = £{opex:,.0f}  

Waste = 5% × Volume × 250 = £{waste_cost:,.0f}  

Monitoring = £{monitoring_cost:,.0f}  

Total Cost = £{total_cost:,.0f}
""")

# ======================
# VISUAL
# ======================
df = pd.DataFrame({
    "Category":["CAPEX","OPEX","Waste","Soil"],
    "Cost":[capex,opex,waste_cost,soil_cost]
})

fig = px.bar(df, x="Category", y="Cost", text="Cost")
st.plotly_chart(fig, use_container_width=True)
