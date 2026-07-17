import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
from io import BytesIO

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="PFAS Decision Support Tool",
    layout="wide"
)

# ==================================================
# LOGIN
# ==================================================

PASSWORD = "PFAS2026"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:

    st.title("🔐 PFAS Tool Login")

    pw = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):

        if pw == PASSWORD:
            st.session_state.auth = True
            st.rerun()

        else:
            st.error("Incorrect Password")

    st.stop()

# ==================================================
# TITLE
# ==================================================

st.title("PFAS Decision Support Tool")

st.caption(
    "Screening-Level PFAS Treatment, Compliance and Liability Assessment"
)

# ==================================================
# SCOPE
# ==================================================

with st.expander("⚠ Scope & Limitations"):

    st.markdown("""
    Screening-level estimates only.

    Suitable for:

    - Early-stage planning
    - Technology comparison
    - Option screening
    - Liability assessments

    Not intended for detailed design or regulatory submissions.
    """)

# ==================================================
# MEDIA
# ==================================================

media = st.radio(
    "Environmental Media",
    ["Water", "Soil"]
)

# ==================================================
# SCENARIO
# ==================================================

scenario = st.selectbox(
    "Cost Scenario",
    ["Optimistic", "Average", "Conservative"]
)

uncertainty = st.slider(
    "Uncertainty (%)",
    0,
    100,
    50
)

# ==================================================
# SITE DATA
# ==================================================

st.header("Site Information")

if media == "Water":

    c1, c2 = st.columns(2)

    water_volume = c1.number_input(
        "Water Volume (m³)",
        value=1000000.0
    )

    flow_rate = c2.number_input(
        "Flow Rate (m³/day)",
        value=5000.0
    )

else:

    c1, c2 = st.columns(2)

    soil_mass = c1.number_input(
        "Contaminated Soil Mass (tonnes)",
        value=10000.0
    )

    excavation_depth = c2.number_input(
        "Excavation Depth (m)",
        value=2.0
    )

# ==================================================
# MAP
# ==================================================

st.header("🌍 Global PFAS Map")

st.markdown(
    "[Open Global PFAS Database](https://pdh.cnrs.fr/en/map/)"
)

components.iframe(
    "https://pdh.cnrs.fr/en/map/",
    height=500
)

# ==================================================
# PFAS DATA
# ==================================================

st.header("PFAS Data")

influent = st.number_input(
    "Total PFAS Concentration",
    value=10.0
)

# ==================================================
# SOURCE
# ==================================================

source = st.selectbox(
    "Potential Source",
    [
        "Unknown",
        "AFFF",
        "Airport",
        "Landfill",
        "Chemical Manufacturing",
        "Textiles",
        "Metal Plating",
        "WWTW"
    ]
)

# ==================================================
# TARGETS
# ==================================================

if media == "Water":

    targets = {
        "UK DWI": 0.1,
        "EU DWD": 0.5,
        "EPA": 0.004
    }

    units = "µg/L"

else:

    targets = {
        "Residential": 0.01,
        "Commercial": 0.1,
        "Industrial": 1.0
    }

    units = "mg/kg"

target_name = st.selectbox(
    "Compliance Target",
    list(targets.keys())
)

target_limit = targets[target_name]

# ==================================================
# TREATMENT
# ==================================================

if media == "Water":

    techs = [
        "GAC",
        "Ion Exchange",
        "RO",
        "AOP"
    ]

    efficiency = {
        "GAC": 0.80,
        "Ion Exchange": 0.90,
        "RO": 0.98,
        "AOP": 0.75
    }

    costs = {
        "GAC": (0.02, 0.20),
        "Ion Exchange": (0.03, 0.12),
        "RO": (0.05, 0.25),
        "AOP": (0.50, 1.00)
    }

else:

    techs = [
        "Excavation + Disposal",
        "Soil Washing",
        "Thermal Desorption",
        "Solidification/Stabilisation"
    ]

    efficiency = {
        "Excavation + Disposal": 0.95,
        "Soil Washing": 0.70,
        "Thermal Desorption": 0.99,
        "Solidification/Stabilisation": 0.60
    }

    costs = {
        "Excavation + Disposal": (100, 350),
        "Soil Washing": (50, 180),
        "Thermal Desorption": (250, 700),
        "Solidification/Stabilisation": (60, 180)
    }

selected_methods = st.multiselect(
    "Treatment Technologies",
    techs,
    default=[techs[0]]
)

# ==================================================
# CALCULATIONS
# ==================================================

final_conc = influent

for method in selected_methods:
    final_conc *= (1 - efficiency[method])

cost_factor = 0

for method in selected_methods:

    low, high = costs[method]

    if scenario == "Optimistic":
        value = low

    elif scenario == "Conservative":
        value = high

    else:
        value = low + ((high - low) * uncertainty / 100)

    cost_factor += value

if media == "Water":

    treatment_cost = cost_factor * water_volume
    capex = flow_rate * 200
    waste = water_volume * 0.05 * 250

    removed_total = (
        (influent - final_conc)
        * water_volume
        / 1e9
    )

else:

    treatment_cost = cost_factor * soil_mass
    capex = soil_mass * 10
    waste = soil_mass * 50

    removed_total = (
        (influent - final_conc)
        * soil_mass
        * 1000
        / 1e9
    )

opex = treatment_cost * 0.01

total_cost = capex + opex + waste

# ==================================================
# COMPLIANCE
# ==================================================

if final_conc <= target_limit:
    st.success(f"✅ Compliant with {target_name}")
else:
    st.error(f"❌ Exceeds {target_name}")

# ==================================================
# DASHBOARD
# ==================================================

st.header("Executive Dashboard")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "PFAS Removed",
    f"{removed_total:.3f}"
)

c2.metric(
    f"Final PFAS ({units})",
    f"{final_conc:.4f}"
)

c3.metric(
    "Technologies",
    len(selected_methods)
)

c4.metric(
    "Total Cost (£)",
    f"{total_cost:,.0f}"
)

# ==================================================
# COST CHART
# ==================================================

cost_df = pd.DataFrame({
    "Category": ["CAPEX", "OPEX", "Waste"],
    "Cost": [capex, opex, waste]
})

fig = px.bar(
    cost_df,
    x="Category",
    y="Cost",
    color="Category",
    title="Cost Breakdown"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==================================================
# SUMMARY
# ==================================================

summary_df = pd.DataFrame({
    "Metric": [
        "Media",
        "Source",
        "Treatment Train",
        "Final PFAS",
        "Total Cost"
    ],
    "Value": [
        media,
        source,
        " -> ".join(selected_methods),
        f"{final_conc:.4f} {units}",
        f"£{total_cost:,.0f}"
    ]
})

st.header("Summary")

st.table(summary_df)

# ==================================================
# EXPORTS
# ==================================================

st.header("Export Report")

csv = summary_df.to_csv(index=False)

st.download_button(
    "📥 Download CSV",
    csv,
    "PFAS_Report.csv",
    "text/csv"
)

excel_buffer = BytesIO()

with pd.ExcelWriter(
    excel_buffer,
    engine="openpyxl"
) as writer:

    summary_df.to_excel(
        writer,
        sheet_name="Summary",
        index=False
    )

    cost_df.to_excel(
        writer,
        sheet_name="Cost Breakdown",
        index=False
    )

st.download_button(
    "📊 Download Excel",
    excel_buffer.getvalue(),
    "PFAS_Report.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ==================================================
# REPORT PREVIEW
# ==================================================

st.header("📋 Report Preview")

report_df = pd.DataFrame({
    "Metric": [
        "Media",
        "Source",
        "Compliance Target",
        "Treatment Train",
        "Final PFAS",
        "PFAS Removed",
        "CAPEX (£)",
        "OPEX (£)",
        "Waste (£)",
        "Total Cost (£)"
    ],
    "Value": [
        media,
        source,
        target_name,
        " -> ".join(selected_methods),
        f"{final_conc:.4f} {units}",
        f"{removed_total:.3f}",
        f"{capex:,.0f}",
        f"{opex:,.0f}",
        f"{waste:,.0f}",
        f"{total_cost:,.0f}"
    ]
})

st.dataframe(
    report_df,
    use_container_width=True,
    hide_index=True
)
