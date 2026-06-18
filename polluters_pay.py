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
# ✅ DISCLAIMER (FIXED)
# ======================
with st.expander("⚠️ Model Scope & Limitations"):
    st.markdown("""
### Important – How to Use These Results

This tool provides **screening-level estimates only**.

✅ Suitable for:
- early-stage feasibility  
- comparing treatment options  

❌ Not suitable for:
- detailed design  
- contractor pricing  
- regulatory submission  

---

### Why results vary

Costs depend on:
- water chemistry  
- PFAS type  
- system design  
- waste disposal  

👉 **Use results for comparison, not exact pricing**
""")

# ======================
# ✅ SCENARIO (NEW)
# ======================
st.header("⚙️ Cost Scenario Settings")

scenario = st.selectbox(
    "Cost Scenario (risk level)",
    [
        "Optimistic (Best Case – lower cost)",
        "Average (Typical case)",
        "Conservative (Worst Case – higher cost)"
    ]
)

uncertainty = st.slider("Uncertainty (%)", 0, 100, 50)

# ✅ EXPLANATION (FIXED POSITION)
with st.expander("ℹ️ What does 'Uncertainty' mean?"):
    st.markdown("""
Costs are not fixed.

They depend on:
- water quality  
- design  
- waste  

---

### Slider meaning:
- **0% → Best case**
- **50% → Typical**
- **100% → Worst case**

👉 This shows a **range**, not a single cost.
""")

# ======================
# FUNCTION
# ======================
def get_cost(best, worst):
    if scenario.startswith("Optimistic"):
        return best
    elif scenario.startswith("Conservative"):
        return worst
    else:
        return best + (worst - best)*(uncertainty/100)

# ======================
# STEP 1
# ======================
st.header("Step 1: Site")

col1, col2 = st.columns(2)
water_volume = col1.number_input("Water Volume (m³)", value=1_000_000.0)
soil_mass = col2.number_input("Soil Mass (t)", value=10000.0)

# ======================
# STEP 2
# ======================
st.header("Step 2: PFAS")

with st.expander("🌍 PFAS Map"):
    components.iframe("https://pdh.cnrs.fr/en/map/", height=800)

chains = ["PFOA","PFOS"]
influent = {}

for c in chains:
    influent[c] = st.number_input(f"{c} (µg/L)", value=10.0)

# ======================
# STEP 3
# ======================
st.header("Step 3: Flow")

flow_rate = st.number_input("Flow (m³/day)", value=5000.0)
duration = water_volume / flow_rate if flow_rate > 0 else 0

st.info(f"Duration: {duration:.0f} days")

# ======================
# METHODS (UPDATED)
# ======================
water_methods = {
    "GAC": {"best":0.02,"worst":0.20,"eff":0.75},
    "Ion Exchange": {"best":0.03,"worst":0.12,"eff":0.85},
    "RO": {"best":0.05,"worst":0.25,"eff":0.95},
    "AOP": {"best":0.50,"worst":1.00,"eff":0.85}
}

soil_methods = {
    "Excavate & Incinerate":150,
    "Soil Washing":20
}

# ======================
# STEP 4
# ======================
st.header("Step 4: Compare")

compare = st.multiselect("Select methods", list(water_methods.keys()))

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
# STEP 5
# ======================
st.header("Step 5: Detail")

method = st.selectbox("Method", list(water_methods.keys()))
d = water_methods[method]

selected_cost = get_cost(d["best"], d["worst"])

mass_in = sum([v*water_volume/1e9 for v in influent.values()])
remaining = mass_in*(1-d["eff"])

final_conc = remaining*1e9/water_volume
removed = mass_in-remaining

treatment_cost = selected_cost*water_volume
soil_cost = sum([soil_methods[s]*soil_mass for s in st.multiselect("Soil", soil_methods.keys())])

# ======================
# COST MODEL
# ======================
capex = flow_rate*200
opex = treatment_cost*duration*0.01
waste = water_volume*0.05*250

total_cost = capex + opex + waste + soil_cost

# ======================
# RESULTS
# ======================
st.header("Results")

st.metric("Removed (kg)", f"{removed:.3f}")
st.metric("Final Conc (µg/L)", f"{final_conc:.3f}")

# ======================
# TRANSPARENCY
# ======================
st.header("Cost Range")

df = pd.DataFrame({
    "Scenario":["Best","Selected","Worst"],
    "£/m³":[d["best"],selected_cost,d["worst"]],
    "Total":[
        d["best"]*water_volume,
        treatment_cost,
        d["worst"]*water_volume
    ]
})

st.table(df)

# ======================
# COMPLIANCE
# ======================
st.header("Compliance")

limit = st.selectbox("Limit",[0.1,0.5,2.0])
ratio = final_conc/limit

st.metric("Ratio", f"{ratio:.2f}")

if ratio <= 1:
    st.success("✅ Compliant")
else:
    st.error("❌ Exceeds")

# ======================
# COST SUMMARY
# ======================
st.header("Costs")

st.metric("Total (£)", f"{total_cost:,.0f}")

# ======================
# CHART
# ======================
chart = pd.DataFrame({
    "Type":["CAPEX","OPEX","Waste","Soil"],
    "Cost":[capex,opex,waste,soil_cost]
})

st.plotly_chart(px.bar(chart, x="Type", y="Cost"))

# ======================
# REPORT
# ======================
st.download_button(
    "Download Report",
    f"Total Cost: £{total_cost:,.0f}",
    "report.txt"
)
