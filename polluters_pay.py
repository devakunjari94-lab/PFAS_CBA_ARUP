import os
import base64
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
    st.markdown("# 🔐 PFAS Tool – Secure Access")
    st.info("Enter password to access the application")

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
# CONFIG + LOGO
# ======================
st.set_page_config(layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "arup_logo.png")

if os.path.exists(logo_path):
    st.image(logo_path, width=120)

st.title("PFAS Polluter-Pays Decision Support Tool")

# ======================
# DISCLAIMER
# ======================
with st.expander("⚠️ Model Scope & Limitations"):
    st.markdown("""
This tool provides **screening-level estimates only**

✅ Use for:
- comparing treatment options  
- early-stage planning  

❌ Do NOT use for:
- contractor pricing  
- regulatory submission  

Costs depend on:
- water quality  
- PFAS type  
- design  
- waste disposal  

👉 Results are **indicative, not exact**
""")

# ======================
# SCENARIO
# ======================
st.header("⚙️ Cost Scenario")

scenario = st.selectbox(
    "Select scenario",
    ["Optimistic (Best Case)", "Average", "Conservative (Worst Case)"]
)

uncertainty = st.slider("Uncertainty (%)", 0, 100, 50)

# ✅ CLEAR EXPLANATION
with st.expander("ℹ️ What does 'Uncertainty' mean?"):
    st.markdown("""
In real projects, PFAS treatment cost is uncertain because:

- water quality changes cost  
- PFAS type affects difficulty  
- design differs between contractors  
- disposal costs vary  

---

### What this slider does

- 0% → simple site → lower cost  
- 50% → typical site  
- 100% → complex site → higher cost  

👉 This tool shows a **range of possible costs**
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
st.header("Step 1: Site Data")

col1, col2 = st.columns(2)
water_volume = col1.number_input("Water Volume (m³)", value=1_000_000.0)
flow_rate = col2.number_input("Flow Rate (m³/day)", value=5000.0)

# ======================
# PFAS INPUT
# ======================
st.header("Step 2: PFAS Data")

with st.expander("🌍 PFAS Global Map"):
    components.iframe("https://pdh.cnrs.fr/en/map/", height=600)

use_general = st.checkbox("I don’t know PFAS → use Total PFAS")

influent = {}

if use_general:
    influent["Total PFAS"] = st.number_input("Total PFAS (µg/L)", value=10.0)
else:
    influent["PFOA"] = st.number_input("PFOA (µg/L)", value=5.0)
    influent["PFOS"] = st.number_input("PFOS (µg/L)", value=5.0)

    with st.expander("➕ Additional PFAS"):
        influent["PFHxS"] = st.number_input("PFHxS (µg/L)", value=0.0)
        influent["PFNA"] = st.number_input("PFNA (µg/L)", value=0.0)

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

mass_in = sum([v*water_volume/1e9 for v in influent.values()])
remaining = mass_in*(1-d["eff"])

final_conc = remaining*1e9/water_volume
removed = mass_in - remaining

treatment_cost = selected_cost*water_volume

capex = flow_rate*200
opex = treatment_cost*0.01
waste = water_volume*0.05*250

total_cost = capex + opex + waste

# ======================
# RESULTS
# ======================
st.header("Results")

col1, col2 = st.columns(2)
col1.metric("PFAS Removed (kg)", f"{removed:.4f}")
col2.metric("Final Concentration (µg/L)", f"{final_conc:.4f}")

# ======================
# COST RANGE
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
# REPORT
# ======================
st.header("📄 Export Report")

logo_base64 = ""

if os.path.exists(logo_path):
    with open(logo_path, "rb") as img:
        logo_base64 = base64.b64encode(img.read()).decode()

report_html = f"""
<div style="background:white;padding:40px;font-family:Arial">

<img src="data:image/png;base64,{logo_base64}" width="120">

<h1>PFAS Treatment Report</h1>

<hr>

<h2>Method</h2>
<p>{method}</p>

<h2>Results</h2>
<ul>
<li>PFAS Removed: {removed:.4f} kg</li>
<li>Final Concentration: {final_conc:.4f} µg/L</li>
</ul>

<h2>Cost Summary</h2>
<ul>
<li>Treatment Cost: £{treatment_cost:,.0f}</li>
<li>CAPEX: £{capex:,.0f}</li>
<li>OPEX: £{opex:,.0f}</li>
<li>Total Cost: £{total_cost:,.0f}</li>
</ul>

<h2>Scenario</h2>
<p>{scenario} (Uncertainty: {uncertainty}%)</p>

<hr>
<p style="font-size:12px;color:gray">
Screening-level estimate only. Not for design or procurement.
</p>

</div>
"""

components.html(report_html, height=600)

st.info("👉 Press Ctrl + P → Save as PDF")
