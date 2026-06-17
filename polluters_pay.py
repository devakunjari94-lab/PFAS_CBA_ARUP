import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# ======================
# 🔐 PASSWORD
# ======================
PASSWORD = "PFAS2026"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pw = st.text_input("Enter password", type="password")
    if pw:
        if pw == PASSWORD:
            st.session_state.auth = True
            st.success("✅ Access granted")
        else:
            st.error("❌ Incorrect password")
            st.stop()
    else:
        st.stop()

# ======================
# CONFIG
# ======================
st.set_page_config(layout="wide")
st.title("PFAS Polluter-Pays Decision Tool")

# ======================
# STEP 1
# ======================
st.header("Step 1: Site Information")

col1, col2 = st.columns(2)
water_volume = col1.number_input("Water Volume (m³)", value=1_000_000.0)
soil_mass = col2.number_input("Soil Mass (tonnes)", value=10000.0)

# ======================
# STEP 2: PFAS INPUT
# ======================
st.header("Step 2: PFAS Data")

with st.expander("🌍 PFAS Map"):
    components.iframe("https://pdh.cnrs.fr/en/map/", height=400)

use_general = st.checkbox("Use General PFAS only (no chain data)")

if use_general:
    chains = ["General PFAS"]
else:
    chains = ["PFOA","PFOS","PFHxS","PFNA"]

influent = {}
for c in chains:
    influent[c] = st.number_input(f"{c} (µg/L)", value=10.0)

with st.expander("ℹ General PFAS Mode"):
    st.markdown("""
Use when only total PFAS concentration is known.
Less accurate but suitable for screening assessments.
""")

# ======================
# STEP 3: FLOW
# ======================
st.header("Step 3: Flow")

flow_rate = st.number_input("Flow rate (m³/day)", value=5000.0)
duration = water_volume / flow_rate if flow_rate > 0 else 0

st.info(f"Estimated duration: {duration:.0f} days")

# ======================
# SCENARIO
# ======================
scenario = st.radio("Scenario", ["P50","P90"])
cost_key = scenario
eff_idx = 0 if scenario == "P50" else 1

# ======================
# METHODS
# ======================
water_methods = {
    "GAC":{"P50":0.04,"P90":0.08,"eff":(0.7,0.9)},
    "Ion Exchange":{"P50":0.06,"P90":0.12,"eff":(0.75,0.95)},
    "RO":{"P50":0.12,"P90":0.25,"eff":(0.9,0.99)},
    "AOP":{"P50":0.5,"P90":1.2,"eff":(0.7,0.99)},
    "SCWO":{"P50":8,"P90":20,"eff":(0.95,1.0)}
}

# ======================
# SELECT METHODS
# ======================
st.header("Step 4: Treatment Selection")

selected = st.multiselect("Water Treatment Methods", list(water_methods.keys()))

# ======================
# MASS BALANCE
# ======================
mass_in = {k:(v*water_volume)/1e9 for k,v in influent.items()}
remaining = mass_in.copy()

treatment_cost = 0

st.header("🔧 Treatment Calculations")

for m in selected:
    data = water_methods[m]
    unit_cost = data[cost_key]
    eff = data["eff"][eff_idx]
    cost = unit_cost * water_volume

    treatment_cost += cost

    for k in remaining:
        remaining[k] *= (1-eff)

    st.markdown(f"### {m}")

    with st.expander("📐 Calculation Details"):
        st.markdown(f"""
Cost = {unit_cost} × {water_volume:,} = £{cost:,.0f}

Efficiency = {eff*100:.1f}%

Remaining = Initial × (1 − Efficiency)

Based on EPA-style engineering costing approach  
""")

# ======================
# RESULTS
# ======================
total_in = sum(mass_in.values())
total_out = sum(remaining.values())
removed = total_in - total_out

final_conc = (total_out*1e9)/water_volume

st.header("Step 5: Results")

st.metric("PFAS Removed (kg)", f"{removed:.2f}")
st.metric("Final Concentration (µg/L)", f"{final_conc:.4f}")

# ======================
# ✅ COMPLIANCE
# ======================
st.header("Step 6: Compliance")

THRESHOLDS = {
    "Drinking water":{
        "PFOA":0.004,"PFOS":0.004,"PFHxS":0.02,"PFNA":0.02,
        "General PFAS":0.1
    },
    "Surface water":{
        "PFOA":0.1,"PFOS":0.05,"PFHxS":0.1,"PFNA":0.1,
        "General PFAS":0.5
    },
    "Wastewater":{
        "PFOA":1.0,"PFOS":0.5,"PFHxS":1.0,"PFNA":1.0,
        "General PFAS":2.0
    }
}

receptor = st.selectbox("Receptor", list(THRESHOLDS.keys()))

limits = THRESHOLDS[receptor]

rows = []
hazard = 0

for k in chains:
    conc = remaining[k]*1e9/water_volume
    limit = limits.get(k, list(limits.values())[0])

    ratio = conc / limit
    hazard += ratio

    status = "✅ Pass" if conc <= limit else "❌ Exceeds"

    rows.append([k, conc, limit, ratio, status])

df = pd.DataFrame(rows, columns=["PFAS","Result","Limit","Ratio","Status"])
st.table(df)

st.metric("Hazard Index", f"{hazard:.2f}")

if hazard <= 1:
    st.success("✅ Compliant")
else:
    st.error("❌ Not Compliant")

with st.expander("ℹ Explanation"):
    st.markdown("""
Ratio = Result ÷ Limit  

- <1 → safe  
- >1 → exceeds  

Hazard Index = sum of ratios  
""")

# ======================
# COST MODEL
# ======================
capex = flow_rate * 200
opex = treatment_cost * duration * 0.01
waste = water_volume * 0.05 * 250
monitoring = 50000

total_cost = capex + opex + waste + monitoring

# ======================
# COSTS
# ======================
st.header("Step 7: Costs")

col1,col2,col3 = st.columns(3)
col1.metric("CAPEX", f"£{capex:,.0f}")
col2.metric("OPEX", f"£{opex:,.0f}")
col3.metric("Total", f"£{total_cost:,.0f}")

if removed > 0:
    st.metric("£/kg removed", f"£{total_cost/removed:,.0f}")

# ======================
# PROOF
# ======================
with st.expander("📐 Full Calculation"):
    st.markdown(f"""
Mass = Conc × Volume / 1e9  

CAPEX = Flow × 200 = £{capex:,.0f}  

OPEX = Treatment × Duration × 1% = £{opex:,.0f}  

Waste = 5% × Volume × 250 = £{waste:,.0f}  

Total = £{total_cost:,.0f}
""")

# ======================
# GRAPH
# ======================
df_cost = pd.DataFrame({
    "Type":["CAPEX","OPEX","Waste"],
    "Cost":[capex,opex,waste]
})

st.plotly_chart(px.bar(df_cost, x="Type", y="Cost", text="Cost"))
