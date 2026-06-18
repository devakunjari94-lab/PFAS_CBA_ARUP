import os
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
# CONFIG + LOGO
# ======================
st.set_page_config(layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "arup_logo.png")

if os.path.exists(logo_path):
    st.image(logo_path, width=150)

st.title("PFAS Polluter-Pays Decision Support Tool")

# ======================
# SCENARIO SETTINGS (NEW)
# ======================
st.header("⚙️ Cost Scenario Settings")

scenario = st.selectbox(
    "Select Cost Scenario",
    ["Optimistic (Best Case)", "Average", "Conservative (Worst Case)"]
)

uncertainty = st.slider("Uncertainty (%)", 0, 100, 50)

def get_cost(best, worst):
    if scenario == "Optimistic (Best Case)":
        return best
    elif scenario == "Conservative (Worst Case)":
        return worst
    else:
        return best + (worst - best)*(uncertainty/100)

# ======================
# STEP 1
# ======================
st.header("Step 1: Site Information")

col1, col2 = st.columns(2)
water_volume = col1.number_input("Water Volume (m³)", value=1_000_000.0)
soil_mass = col2.number_input("Soil Mass (tonnes)", value=10000.0)

# ======================
# STEP 2
# ======================
st.header("Step 2: PFAS Data")

with st.expander("🌍 PFAS Map"):
    components.iframe("https://pdh.cnrs.fr/en/map/", height=800)

use_general = st.checkbox("Use General PFAS only")

chains = ["General PFAS"] if use_general else ["PFOA","PFOS","PFHxS","PFNA"]

influent = {}
for c in chains:
    influent[c] = st.number_input(f"{c} (µg/L)", value=10.0)

# ======================
# STEP 3
# ======================
st.header("Step 3: Flow")

flow_rate = st.number_input("Flow rate (m³/day)", value=5000.0)
duration = water_volume / flow_rate if flow_rate > 0 else 0

st.info(f"Treatment duration: {duration:.0f} days")

# ======================
# UPDATED METHODS (RANGE BASED)
# ======================
water_methods = {
    "GAC": {"best":0.02,"worst":0.20,"eff":0.75},
    "Ion Exchange": {"best":0.03,"worst":0.12,"eff":0.85},
    "RO": {"best":0.05,"worst":0.25,"eff":0.95},
    "Foam Fractionation": {"best":0.01,"worst":0.08,"eff":0.80},
    "AOP": {"best":0.50,"worst":1.00,"eff":0.85},
    "Electrochemical": {"best":0.20,"worst":1.50,"eff":0.90}
}

soil_methods = {
    "Excavate & Incinerate":100,
    "Landfill":80,
    "Soil Washing":20
}

# ======================
# STEP 4: COMPARISON
# ======================
st.header("Step 4: Scenario Comparison")

compare = st.multiselect("Compare methods", list(water_methods.keys()))

rows = []

for m in compare:
    d = water_methods[m]
    cost = get_cost(d["best"], d["worst"])

    mass = sum([v*water_volume/1e9 for v in influent.values()])
    remaining = mass*(1-d["eff"])
    conc = remaining*1e9/water_volume

    rows.append([m, conc, cost*water_volume])

if rows:
    st.table(pd.DataFrame(rows, columns=["Method","Final Conc","Cost (£)"]))

# ======================
# STEP 5: DETAILED
# ======================
st.header("Step 5: Detailed Analysis")

method = st.selectbox("Select method", list(water_methods.keys()))
soil_sel = st.multiselect("Select soil treatments", list(soil_methods.keys()))

d = water_methods[method]
selected_cost = get_cost(d["best"], d["worst"])

mass_in = sum([v*water_volume/1e9 for v in influent.values()])
remaining = mass_in*(1-d["eff"])

final_conc = remaining*1e9/water_volume
removed = mass_in-remaining

treatment_cost = selected_cost*water_volume
soil_cost = sum([soil_methods[s]*soil_mass for s in soil_sel])

# ======================
# COST MODEL
# ======================
capex = flow_rate*200
opex = treatment_cost*duration*0.01
waste = water_volume*0.05*250
monitoring = 50000

total_cost = capex+opex+waste+monitoring+soil_cost

# ======================
# RESULTS
# ======================
st.header("Step 6: Results")

st.metric("PFAS Removed (kg)", f"{removed:.4f}")
st.metric("Final Concentration (µg/L)", f"{final_conc:.4f}")

# ======================
# TRANSPARENCY TABLE (NEW)
# ======================
st.header("Cost Transparency")

df_transparency = pd.DataFrame({
    "Scenario":["Best","Selected","Worst"],
    "£/m³":[d["best"], selected_cost, d["worst"]],
    "Total (£)":[
        d["best"]*water_volume,
        treatment_cost,
        d["worst"]*water_volume
    ]
})
st.table(df_transparency)

# ======================
# COMPLIANCE
# ======================
st.header("Step 7: Compliance")

THRESH = {
    "Drinking water":0.1,
    "Surface water":0.5,
    "Wastewater":2.0
}

receptor = st.selectbox("Receptor", list(THRESH.keys()))
ratio = final_conc/THRESH[receptor]

st.metric("Ratio", f"{ratio:.2f}")

if ratio <= 1:
    st.success("✅ Compliant")
else:
    st.error("❌ Not Compliant")

# ======================
# COST SUMMARY
# ======================
st.header("Step 8: Costs")

col1,col2,col3 = st.columns(3)

col1.metric("CAPEX", f"£{capex:,.0f}")
col2.metric("OPEX", f"£{opex:,.0f}")
col3.metric("Total Cost", f"£{total_cost:,.0f}")

# ======================
# CHART
# ======================
df = pd.DataFrame({
    "Type":["CAPEX","OPEX","Waste","Soil"],
    "Cost":[capex,opex,waste,soil_cost]
})

st.plotly_chart(px.bar(df, x="Type", y="Cost", text="Cost"),
                use_container_width=True)

# ======================
# REPORT
# ======================
st.header("Step 9: Export Report")

html_report = f"""
<html>
<body>
<h1>PFAS Treatment Report</h1>
<p>Method: {method}</p>
<p>Final Concentration: {final_conc:.4f}</p>
<p>Total Cost: £{total_cost:,.0f}</p>
<p>Scenario: {scenario}</p>
<p>Ratio: {ratio:.2f}</p>
</body>
</html>
"""

st.download_button("Download Report", html_report, "PFAS_Report.html")
