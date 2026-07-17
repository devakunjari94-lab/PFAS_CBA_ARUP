import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

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

    st.title("🔐 PFAS Login")

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):

        if password == PASSWORD:
            st.session_state.auth = True
            st.rerun()

        else:
            st.error("Incorrect password")

    st.stop()

# ==================================================
# TITLE
# ==================================================

st.title("PFAS Decision Support Tool")

st.caption(
    "Screening-Level Treatment, Compliance & Liability Assessment"
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
    - Liability assessment

    Not intended for detailed engineering design.
    """)

# ==================================================
# MEDIA
# ==================================================

st.header("Environmental Media")

media = st.radio(
    "Select Media",
    ["Water", "Soil"]
)

# ==================================================
# SITE INFO
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
# PFAS MAP
# ==================================================

st.header("🌍 Global PFAS Database")

st.markdown(
    "[Open Global PFAS Map](https://pdh.cnrs.fr/en/map/)"
)

components.iframe(
    "https://pdh.cnrs.fr/en/map/",
    height=500,
    scrolling=True
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

st.header("Potential Source")

source = st.selectbox(
    "Source",
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

source_notes = {
    "Unknown": "Source not yet characterised.",
    "AFFF": "Associated with firefighting foam releases.",
    "Airport": "Often linked to fire training areas.",
    "Landfill": "PFAS may arise from leachate.",
    "Chemical Manufacturing": "Potential industrial PFAS source.",
    "Textiles": "Historically associated with fluorinated coatings.",
    "Metal Plating": "PFAS used as mist suppressants.",
    "WWTW": "Wastewater treatment can accumulate PFAS."
}

st.info(source_notes[source])

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
        "Commercial": 0.10,
        "Industrial": 1.00
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

st.header("Treatment Technologies")

if media == "Water":

    technologies = ["GAC", "Ion Exchange", "RO", "AOP"]

    efficiencies = {
        "GAC": 0.80,
        "Ion Exchange": 0.90,
        "RO": 0.98,
        "AOP": 0.75
    }

    costs = {
        "GAC": 0.10,
        "Ion Exchange": 0.12,
        "RO": 0.25,
        "AOP": 0.80
    }

else:

    technologies = [
        "Excavation + Disposal",
        "Soil Washing",
        "Thermal Desorption",
        "Solidification/Stabilisation"
    ]

    efficiencies = {
        "Excavation + Disposal": 0.95,
        "Soil Washing": 0.70,
        "Thermal Desorption": 0.99,
        "Solidification/Stabilisation": 0.60
    }

    costs = {
        "Excavation + Disposal": 250,
        "Soil Washing": 120,
        "Thermal Desorption": 500,
        "Solidification/Stabilisation": 100
    }

selected_methods = st.multiselect(
    "Select Technologies",
    technologies,
    default=[technologies[0]]
)

# ==================================================
# CALCULATIONS
# ==================================================

final_conc = influent

for method in selected_methods:
    final_conc *= (1 - efficiencies[method])

cost_factor = sum(costs[m] for m in selected_methods)

if media == "Water":

    treatment_cost = cost_factor * water_volume
    capex = flow_rate * 200
    waste = water_volume * 0.05 * 250

    removed_mass = (
        (influent - final_conc)
        * water_volume
        / 1e9
    )

else:

    treatment_cost = cost_factor * soil_mass
    capex = soil_mass * 10
    waste = soil_mass * 50

    removed_mass = (
        (influent - final_conc)
        * soil_mass * 1000
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
    f"{removed_mass:.3f}"
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
# CHART
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

st.header("Summary")

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

st.table(summary_df)

# ==================================================
# EXPORT
# ==================================================

st.header("Export Report")

csv = summary_df.to_csv(index=False)

st.download_button(
    label="📥 Download CSV Report",
    data=csv,
    file_name="PFAS_Report.csv",
    mime="text/csv"
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
        f"{removed_mass:.3f}",
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
