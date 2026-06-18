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
# INTRO
# ======================
with st.expander("📘 How to Use This Tool"):
    st.markdown("""
1. Enter site data  
2. Add PFAS concentrations  
3. Choose treatments  
4. Review results, compliance, and cost  

Outputs:
- PFAS removal  
- final concentration  
- compliance  
- cost estimate  
""")

# ======================
# DISCLAIMER
# ======================
with st.expander("⚠️ Model Scope & Limitations"):
    st.markdown("""
Screening-level tool only.

✅ early decision-making  
✅ comparing options  

❌ not for design or regulatory submission  

Based on EPA-style engineering models.
""")

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
    components.iframe("https://pdh.cnrs.fr/en/map/", height=800, scrolling=True)

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

with st.expander("ℹ️ What is Flow Rate?"):
    st.markdown("""
Flow rate = volume treated per day.

Affects:
- plant size (CAPEX)
- duration
- energy use
""")

# ======================
# METHODS
# ======================
water_methods = {
    "GAC":{"cost":0.04,"eff":0.7},
    "Ion Exchange":{"cost":0.06,"eff":0.8},
    "RO":{"cost":0.12,"eff":0.95},
    "AOP":{"cost":0.5,"eff":0.85}
}

soil_methods = {
    "Excavate & Incinerate":150,
    "Landfill":80,
    "Soil Washing":50
}

# ======================
# METHOD EXPLANATION
# ======================
with st.expander("🔧 Treatment Methods Explained"):
    st.markdown("""
GAC: adsorption → spent carbon  
Ion Exchange: resin → waste resin  
RO: filtration → brine  
AOP: oxidation → high energy  

Most methods transfer PFAS to waste.
""")

# ======================
# BYPRODUCTS
# ======================
with st.expander("⚗️ Treatment By-Products"):
    st.markdown("""
- GAC → carbon  
- RO → brine  
- IX → resin  
- soil → contaminated soil  

PFAS often moved, not destroyed.
""")

# ======================
# STEP 4
# ======================
st.header("Step 4: Scenario Comparison")

compare = st.multiselect("Compare methods", list(water_methods.keys()))

rows = []

for m in compare:
    d = water_methods[m]

    mass = sum([v*water_volume/1e9 for v in influent.values()])
    remaining = mass*(1-d["eff"])
    conc = remaining*1e9/water_volume
    cost = d["cost"]*water_volume

    rows.append([m, conc, cost])

if rows:
    st.table(pd.DataFrame(rows, columns=["Method","Final Conc","Cost"]))

# ======================
# STEP 5
# ======================
st.header("Step 5: Detailed Analysis")

method = st.selectbox("Select method", list(water_methods.keys()))
soil_sel = st.multiselect("Select soil treatments", list(soil_methods.keys()))

d = water_methods[method]

mass_in = sum([v*water_volume/1e9 for v in influent.values()])
remaining = mass_in*(1-d["eff"])

final_conc = remaining*1e9/water_volume
removed = mass_in-remaining

treatment_cost = d["cost"]*water_volume
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
# COST EXPLANATION
# ======================
with st.expander("📊 Cost Methodology"):
    st.markdown("""
Total = CAPEX + OPEX + Waste + Monitoring

CAPEX = flow × factor  
OPEX = treatment × duration  
Waste = 5% × volume  

Screening-level estimates based on engineering scaling.
""")

# ======================
# RESULTS
# ======================
st.header("Step 6: Results")

st.metric("PFAS Removed (kg)", f"{removed:.4f}")
st.metric("Final Concentration (µg/L)", f"{final_conc:.4f}")

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
limit = THRESH[receptor]

ratio = final_conc/limit

st.metric("Ratio (Result / Limit)", f"{ratio:.2f}")

if ratio <= 1:
    st.success("✅ Compliant")
else:
    st.error("❌ Not Compliant")

with st.expander("⚖️ Compliance Explanation"):
    st.markdown("""
Ratio = Result ÷ Limit  

<1 = pass  
>1 = exceed  

Used to assess compliance quickly.
""")

# ======================
# COST
# ======================
st.header("Step 8: Cost Summary")

col1,col2,col3 = st.columns(3)

col1.metric("CAPEX", f"£{capex:,.0f}")
col2.metric("OPEX", f"£{opex:,.0f}")
col3.metric("Total Cost", f"£{total_cost:,.0f}")

# ======================
# GRAPH
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
<p>Final Concentration: {final_conc:.4f}</p>
<p>Total Cost: £{total_cost:,.0f}</p>
<p>Ratio: {ratio:.2f}</p>
</body>
</html>
"""

st.download_button("Download Report", html_report, "PFAS_Report.html")

st.info("Open file → Ctrl+P → Save as PDF")
