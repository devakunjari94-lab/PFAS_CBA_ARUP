import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ======================
# 🔐 PASSWORD (IMPROVED)
# ======================
PASSWORD = "PFAS2026"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("# 🔐 PFAS Tool – Secure Access")
    st.info("Enter the password to access the application")

    pw = st.text_input("Password", type="password")

    if st.button("Unlock"):
        if pw == PASSWORD:
            st.session_state.auth = True
            st.success("✅ Access granted")
            st.rerun()
        else:
            st.error("❌ Incorrect password")

    st.stop()

# ======================
# CONFIG
# ======================
st.set_page_config(layout="wide")

st.title("PFAS Polluter-Pays Decision Support Tool")

# ======================
# DISCLAIMER
# ======================
with st.expander("⚠️ Model Scope & Limitations"):
    st.markdown("""
### Important

This tool provides **screening-level estimates only**.

✅ Suitable:
- option comparison  
- early-stage feasibility  

❌ Not suitable:
- contractor pricing  
- regulatory submission  

Costs vary depending on:
- water chemistry  
- PFAS composition  
- system design  
- waste disposal  

👉 Use for decision support, not final pricing.
""")

# ======================
# SCENARIO
# ======================
st.header("⚙️ Cost Scenario")

scenario = st.selectbox(
    "Select scenario",
    [
        "Optimistic (Best Case)",
        "Average",
        "Conservative (Worst Case)"
    ]
)

uncertainty = st.slider("Uncertainty (%)", 0, 100, 50)

with st.expander("ℹ️ What does uncertainty mean?"):
    st.markdown("""
Costs vary in reality.

This slider moves between:
- Best case (0%)
- Typical case (50%)
- Worst case (100%)

👉 This reflects uncertainty in real projects.
""")

def get_cost(best, worst):
    if scenario.startswith("Optimistic"):
        return best
    elif scenario.startswith("Conservative"):
        return worst
    else:
        return best + (worst - best)*(uncertainty/100)

# ======================
# INPUTS
# ======================
st.header("Step 1: Inputs")

water_volume = st.number_input("Water Volume (m³)", value=1_000_000.0)
flow_rate = st.number_input("Flow Rate (m³/day)", value=5000.0)

# ======================
# METHODS
# ======================
methods = {
    "GAC": {"best":0.02,"worst":0.20,"eff":0.75},
    "Ion Exchange": {"best":0.03,"worst":0.12,"eff":0.85},
    "RO": {"best":0.05,"worst":0.25,"eff":0.95},
    "AOP": {"best":0.50,"worst":1.00,"eff":0.85}
}

method = st.selectbox("Select Treatment Method", list(methods.keys()))
d = methods[method]

# ======================
# CALCULATIONS
# ======================
selected_cost = get_cost(d["best"], d["worst"])

mass_in = 0.01  # simplified example
remaining = mass_in * (1 - d["eff"])

final_conc = remaining * 1e9 / water_volume
removed = mass_in - remaining

treatment_cost = selected_cost * water_volume

capex = flow_rate * 200
opex = treatment_cost * 0.01
waste = water_volume * 0.05 * 250

total_cost = capex + opex + waste

# ======================
# RESULTS
# ======================
st.header("Results")

col1, col2 = st.columns(2)
col1.metric("PFAS Removed (kg)", f"{removed:.4f}")
col2.metric("Final Concentration (µg/L)", f"{final_conc:.4f}")

# ======================
# COST RANGE TABLE
# ======================
st.header("Cost Range")

df = pd.DataFrame({
    "Scenario":["Best","Selected","Worst"],
    "£/m³":[d["best"],selected_cost,d["worst"]],
    "Total (£)":[
        d["best"]*water_volume,
        treatment_cost,
        d["worst"]*water_volume
    ]
})

st.table(df)

# ======================
# TOTAL COST
# ======================
st.header("Total Cost")

st.metric("Estimated Cost (£)", f"{total_cost:,.0f}")

# ======================
# CHART
# ======================
df_chart = pd.DataFrame({
    "Type":["CAPEX","OPEX","Waste"],
    "Cost":[capex,opex,waste]
})

st.plotly_chart(px.bar(df_chart, x="Type", y="Cost"))

# ======================
# 📄 PRINTABLE REPORT (NEW)
# ======================
st.header("📄 Export Report")

st.markdown("### Printable Summary (Press Ctrl+P → Save as PDF)")

report_html = f"""
<div style="background:white;padding:30px">

<h1>PFAS Treatment Report</h1>

<h2>Method</h2>
<p>{method}</p>

<h2>Results</h2>
<ul>
<li>PFAS Removed: {removed:.4f} kg</li>
<li>Final Concentration: {final_conc:.4f} µg/L</li>
</ul>

<h2>Costs</h2>
<ul>
<li>Selected Cost: £{treatment_cost:,.0f}</li>
<li>CAPEX: £{capex:,.0f}</li>
<li>OPEX: £{opex:,.0f}</li>
<li>Total Cost: £{total_cost:,.0f}</li>
</ul>

<h2>Scenario</h2>
<p>{scenario} (Uncertainty: {uncertainty}%)</p>

<p style="margin-top:40px">
This report is a screening-level estimate and not a final design or cost quotation.
</p>

</div>
"""

st.components.v1.html(report_html, height=600)

st.info("👉 Press Ctrl+P → Save as PDF")
