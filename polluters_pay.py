import streamlit as st
import pandas as pd
import plotly.express as px
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ======================
# PASSWORD
# ======================
PASSWORD = "PFAS2026"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pw = st.text_input("Enter password", type="password")
    if pw == PASSWORD:
        st.session_state.auth = True
        st.success("✅ Access granted")
    else:
        st.stop()

# ======================
# TITLE
# ======================
st.title("PFAS Decision Support Tool (Consultancy Version)")

# ======================
# INPUTS
# ======================
st.header("1. Site Data")

water_volume = st.number_input("Water Volume (m³)", value=1_000_000.0)
flow_rate = st.number_input("Flow Rate (m³/day)", value=5000.0)

duration = water_volume / flow_rate if flow_rate > 0 else 0

# PFAS input
use_general = st.checkbox("Use General PFAS")

chains = ["General PFAS"] if use_general else ["PFOA","PFOS","PFHxS","PFNA"]

influent = {}
for c in chains:
    influent[c] = st.number_input(f"{c} (µg/L)", 10.0)

# ======================
# METHODS
# ======================
methods = {
    "GAC": {"cost":0.04,"eff":0.7},
    "IX": {"cost":0.06,"eff":0.8},
    "RO": {"cost":0.12,"eff":0.95},
    "AOP": {"cost":0.5,"eff":0.85}
}

# ======================
# SCENARIO COMPARISON
# ======================
st.header("2. Scenario Comparison")

scenarios = st.multiselect("Select Scenarios", list(methods.keys()))

results_table = []

for m in scenarios:
    data = methods[m]

    # mass
    mass = sum([v * water_volume / 1e9 for v in influent.values()])
    remaining = mass * (1 - data["eff"])

    final_conc = remaining * 1e9 / water_volume
    cost = data["cost"] * water_volume

    compliant = final_conc < 0.1

    results_table.append([m, final_conc, cost, "✅" if compliant else "❌"])

df_scen = pd.DataFrame(results_table, columns=["Method","Final Conc","Cost","Compliance"])

st.table(df_scen)

# ======================
# MAIN SELECTED
# ======================
st.header("3. Detailed Analysis")

selected = st.selectbox("Select Method", list(methods.keys()))

data = methods[selected]

mass = sum([v * water_volume / 1e9 for v in influent.values()])
remaining = mass * (1 - data["eff"])
final_conc = remaining * 1e9 / water_volume

treatment_cost = data["cost"] * water_volume

# full cost model
capex = flow_rate * 200
opex = treatment_cost * duration * 0.01
waste = water_volume * 0.05 * 250

total_cost = capex + opex + waste

# ======================
# RESULTS
# ======================
st.metric("Final Concentration (µg/L)", f"{final_conc:.4f}")
st.metric("Total Cost", f"£{total_cost:,.0f}")

# ======================
# COMPLIANCE
# ======================
limit = 0.1  # simple
ratio = final_conc / limit

st.metric("Compliance Ratio", f"{ratio:.2f}")

if ratio <= 1:
    st.success("✅ Compliant")
else:
    st.error("❌ Not Compliant")

# ======================
# CHART
# ======================
chart = pd.DataFrame({"Type":["CAPEX","OPEX","Waste"],
                      "Cost":[capex,opex,waste]})

st.plotly_chart(px.bar(chart,x="Type",y="Cost"))

# ======================
# PDF REPORT
# ======================
st.header("4. Export Report")

def generate_pdf():
    doc = SimpleDocTemplate("pfas_report.pdf")
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph("PFAS Treatment Report", styles["Title"]))
    content.append(Spacer(1,10))

    content.append(Paragraph(f"Water Volume: {water_volume}", styles["Normal"]))
    content.append(Paragraph(f"Flow Rate: {flow_rate}", styles["Normal"]))
    content.append(Paragraph(f"Selected Method: {selected}", styles["Normal"]))

    content.append(Spacer(1,10))

    content.append(Paragraph(f"Final Concentration: {final_conc:.4f} µg/L", styles["Normal"]))
    content.append(Paragraph(f"Total Cost: £{total_cost:,.0f}", styles["Normal"]))

    doc.build(content)

generate = st.button("Generate PDF Report")

if generate:
    generate_pdf()
    with open("pfas_report.pdf", "rb") as f:
        st.download_button("Download Report", f, file_name="PFAS_Report.pdf")
