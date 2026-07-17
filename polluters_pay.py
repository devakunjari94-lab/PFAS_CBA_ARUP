import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
from io import BytesIO

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="PFAS Decision Support Tool",
    layout="wide"
)

# ==========================================================
# LOGIN
# ==========================================================

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

# ==========================================================
# TITLE
# ==========================================================

st.title("PFAS Decision Support Tool")

st.caption(
    "Screening-Level PFAS Treatment, Compliance and Liability Assessment"
)

# ==========================================================
# SCOPE
# ==========================================================

with st.expander("⚠ Scope & Limitations"):

    st.markdown("""
    Screening-level estimates only.

    Suitable for:

    - Early-stage planning
    - Technology comparison
    - Option screening
    - Liability assessments

    Not intended for regulatory submissions or detailed design.
    """)

# ==========================================================
# MEDIA
# ==========================================================

st.header("Environmental Media")

media = st.radio(
    "Select Media",
    ["Water", "Soil"]
)

# ==========================================================
# SCENARIO
# ==========================================================

st.header("Scenario")

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

# ==========================================================
# SITE DATA
# ==========================================================

st.header("Site Information")

if media == "Water":

    col1, col2 = st.columns(2)

    water_volume = col1.number_input(
        "Water Volume (m³)",
        value=1000000.0
    )

    flow_rate = col2.number_input(
        "Flow Rate (m³/day)",
        value=5000.0
    )

else:

    col1, col2 = st.columns(2)

    soil_mass = col1.number_input(
        "Contaminated Soil Mass (tonnes)",
        value=10000.0
    )

    excavation_depth = col2.number_input(
        "Excavation Depth (m)",
        value=2.0
    )

# ==========================================================
# MAP
# ==========================================================

st.header("Global PFAS Map")

st.markdown(
    "[Open Global PFAS Database](https://pdh.cnrs.fr/en/map/)"
)

components.iframe(
    "https://pdh.cnrs.fr/en/map/",
    height=600,
    scrolling=True
)

# ==========================================================
# PFAS DATA
# ==========================================================

st.header("PFAS Data")

use_general = st.checkbox(
    "Use Total PFAS",
    value=True
)

influent = {}

if use_general:

    influent["Total PFAS"] = st.number_input(
        "PFAS Concentration",
        value=10.0
    )

else:

    influent["PFOA"] = st.number_input(
        "PFOA",
        value=5.0
    )

    influent["PFOS"] = st.number_input(
        "PFOS",
        value=5.0
    )

    influent["PFHxS"] = st.number_input(
        "PFHxS",
        value=1.0
    )

    influent["PFNA"] = st.number_input(
        "PFNA",
        value=1.0
    )

    influent["GenX"] = st.number_input(
        "GenX",
        value=0.0
    )

# ==========================================================
# SOURCE
# ==========================================================

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

# ==========================================================
# COMPLIANCE TARGETS
# ==========================================================

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

# ==========================================================
# TREATMENT
# ==========================================================

st.header("Treatment Train")

if media == "Water":

    techs = [
        "GAC",
        "Ion Exchange",
        "RO",
        "AOP"
    ]

else:

    techs = [
        "Excavation + Disposal",
        "Soil Washing",
        "Thermal Desorption",
        "Solidification/Stabilisation"
    ]

selected_methods = st.multiselect(
    "Technologies",
    techs,
    default=[techs[0]]
)

# ==========================================================
# PERFORMANCE ASSUMPTIONS
# ==========================================================

tech_eff = {
    "PFOA": {"GAC": 0.92, "Ion Exchange": 0.96, "RO": 0.99, "AOP": 0.70},
    "PFOS": {"GAC": 0.98, "Ion Exchange": 0.99, "RO": 0.99, "AOP": 0.75},
    "PFHxS": {"GAC": 0.85, "Ion Exchange": 0.95, "RO": 0.99, "AOP": 0.65},
    "PFNA": {"GAC": 0.90, "Ion Exchange": 0.96, "RO": 0.99, "AOP": 0.70},
    "GenX": {"GAC": 0.40, "Ion Exchange": 0.80, "RO": 0.95, "AOP": 0.60}
}

generic_eff = {
    "GAC": 0.80,
    "Ion Exchange": 0.90,
    "RO": 0.98,
    "AOP": 0.75
}

soil_eff = {
    "Excavation + Disposal": 0.95,
    "Soil Washing": 0.70,
    "Thermal Desorption": 0.99,
    "Solidification/Stabilisation": 0.60
}

tech_cost = {
    "GAC": (0.02, 0.20),
    "Ion Exchange": (0.03, 0.12),
    "RO": (0.05, 0.25),
    "AOP": (0.50, 1.00)
}

soil_cost = {
    "Excavation + Disposal": (100, 350),
    "Soil Washing": (50, 180),
    "Thermal Desorption": (250, 700),
    "Solidification/Stabilisation": (60, 180)
}

# ==========================================================
# CALCULATIONS
# ==========================================================

remaining = {}
removed_total = 0

for compound, conc in influent.items():

    current = conc

    for method in selected_methods:

        if media == "Water":

            if compound == "Total PFAS":
                eff = generic_eff[method]
            else:
                eff = tech_eff[compound][method]

        else:
            eff = soil_eff[method]

        current *= (1 - eff)

    remaining[compound] = current

    if media == "Water":

        mass_in = conc * water_volume / 1e9
        mass_out = current * water_volume / 1e9

    else:

        mass_in = conc * soil_mass * 1000 / 1e9
        mass_out = current * soil_mass * 1000 / 1e9

    removed_total += (mass_in - mass_out)

final_conc = sum(remaining.values())

# ==========================================================
# COSTING
# ==========================================================

cost_factor = 0

for method in selected_methods:

    if media == "Water":
        best, worst = tech_cost[method]
    else:
        best, worst = soil_cost[method]

    if scenario == "Optimistic":
        val = best

    elif scenario == "Conservative":
        val = worst

    else:
        val = best + ((worst - best) * uncertainty / 100)

    cost_factor += val

if media == "Water":

    treatment_cost = cost_factor * water_volume
    capex = flow_rate * 200
    waste = water_volume * 0.05 * 250

else:

    treatment_cost = cost_factor * soil_mass
    capex = soil_mass * 10
    waste = soil_mass * 50

opex = treatment_cost * 0.01

total_cost = capex + opex + waste

# ==========================================================
# COMPLIANCE
# ==========================================================

if final_conc <= target_limit:

    st.success(
        f"✅ Compliant with {target_name}"
    )

else:

    st.error(
        f"❌ Exceeds {target_name}"
    )

# ==========================================================
# DASHBOARD
# ==========================================================

st.header("Executive Dashboard")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "PFAS Removed",
    f"{removed_total:.3f}"
)

col2.metric(
    f"Final PFAS ({units})",
    f"{final_conc:.4f}"
)

col3.metric(
    "Technologies",
    len(selected_methods)
)

col4.metric(
    "Total Cost (£)",
    f"{total_cost:,.0f}"
)

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

# ==========================================================
# SUMMARY TABLE
# ==========================================================

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

# ==========================================================
# EXPORTS
# ==========================================================

st.header("Export Report")

csv = summary_df.to_csv(index=False)

st.download_button(
    "📥 Download CSV",
    csv,
    file_name="PFAS_Report.csv",
    mime="text/csv"
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
    file_name="PFAS_Report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

html_report = f"""
<html>
<body>
<h1>PFAS Decision Support Report</h1>

<h2>Site Summary</h2>

<p><b>Media:</b> {media}</p>
<p><b>Source:</b> {source}</p>
<p><b>Target:</b> {target_name}</p>
<p><b>Treatment:</b> {" -> ".join(selected_methods)}</p>
<p><b>Final PFAS:</b> {final_conc:.4f} {units}</p>
<p><b>PFAS Removed:</b> {removed_total:.3f}</p>
<p><b>Total Cost:</b> £{total_cost:,.0f}</p>

"""
</body>
</html>
"""

st.download_button(
    "📄 Download HTML",
    html_report,
    file_name="PFAS_Report.html",
    mime="text/html"
)

st.subheader("📋 Report Preview")

st.markdown(f"""
### Site Summary

**Media:** {media}

**Source:** {source}

**Compliance Target:** {target_name}

**Treatment Train:** {" → ".join(selected_methods)}

**Final PFAS:** {final_conc:.4f} {units}

**PFAS Removed:** {removed_total:.3f}

**Total Cost:** £{total_cost:,.0f}
""")

if final_conc <= target_limit:
    st.success(f"✅ Compliant with {target_name}")
else:
    st.error(f"❌ Exceeds {target_name}")

st.dataframe(
    cost_df,
    use_container_width=True,
    hide_index=True
)

st.plotly_chart(
    fig,
    use_container_width=True
)
