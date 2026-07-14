import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit.components.v1 as components

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="PFAS Decision Support Tool",
    layout="wide"
)

# =====================================
# PASSWORD
# =====================================

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

# =====================================
# LOGO
# =====================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "arup_logo.png")

col1, col2 = st.columns([1, 4])

with col1:

    if os.path.exists(logo_path):

        st.image(
            logo_path,
            width=150
        )

with col2:

    st.title(
        "PFAS Polluter-Pays Decision Support Tool"
    )

    st.caption(
        "Screening-Level PFAS Treatment, Compliance and Liability Assessment"
    )

st.divider()

# =====================================
# DISCLAIMER
# =====================================

with st.expander("⚠ Scope & Limitations"):

    st.markdown("""
    This tool provides screening-level estimates only.

    ✅ Suitable for:
    - Early-stage planning
    - Technology comparison
    - Option screening
    - Polluter-pays assessments

    ❌ Not suitable for:
    - Regulatory submissions
    - Detailed design
    - Contractor pricing
    """)

# =====================================
# SCENARIO
# =====================================

st.header("Scenario")

scenario = st.selectbox(
    "Cost Scenario",
    [
        "Optimistic",
        "Average",
        "Conservative"
    ]
)

uncertainty = st.slider(
    "Uncertainty (%)",
    0,
    100,
    50
)

# =====================================
# SITE INFORMATION
# =====================================

st.header("Site Information")

c1, c2 = st.columns(2)

water_volume = c1.number_input(
    "Water Volume (m³)",
    value=1_000_000.0
)

flow_rate = c2.number_input(
    "Flow Rate (m³/day)",
    value=5000.0
)

# =====================================
# CNRS MAP
# =====================================

st.header("🌍 Global PFAS Intelligence Map")

st.markdown(
    "[Open CNRS PFAS Map in New Window](https://pdh.cnrs.fr/en/map/)"
)

components.iframe(
    "https://pdh.cnrs.fr/en/map/",
    height=650,
    scrolling=True
)

# =====================================
# PFAS INPUT
# =====================================

st.header("PFAS Data")

use_general = st.checkbox(
    "I don't know individual PFAS compounds (Use Total PFAS)"
)

influent = {}

if use_general:

    influent["Total PFAS"] = st.number_input(
        "Total PFAS (µg/L)",
        value=10.0
    )

else:

    influent["PFOA"] = st.number_input(
        "PFOA (µg/L)",
        value=5.0
    )

    influent["PFOS"] = st.number_input(
        "PFOS (µg/L)",
        value=5.0
    )

    influent["PFHxS"] = st.number_input(
        "PFHxS (µg/L)",
        value=1.0
    )

    influent["PFNA"] = st.number_input(
        "PFNA (µg/L)",
        value=1.0
    )

    influent["GenX"] = st.number_input(
        "GenX (µg/L)",
        value=0.0
    )

# =====================================
# SOURCE
# =====================================

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

# =====================================
# REGULATORY TARGET
# =====================================

st.header("Regulatory Compliance")

targets = {
    "UK DWI": 0.1,
    "EU DWD": 0.5,
    "EPA": 0.004
}

target_name = st.selectbox(
    "Target",
    list(targets.keys())
)

target_limit = targets[target_name]

# =====================================
# TREATMENT TRAIN
# =====================================

st.header("Treatment Train")

selected_methods = st.multiselect(
    "Technologies",
    [
        "GAC",
        "Ion Exchange",
        "RO",
        "AOP"
    ],
    default=["GAC"]
)

# =====================================
# EFFICIENCIES
# =====================================

tech_eff = {

    "PFOA": {
        "GAC": 0.92,
        "Ion Exchange": 0.96,
        "RO": 0.99,
        "AOP": 0.70
    },

    "PFOS": {
        "GAC": 0.98,
        "Ion Exchange": 0.99,
        "RO": 0.99,
        "AOP": 0.75
    },

    "PFHxS": {
        "GAC": 0.85,
        "Ion Exchange": 0.95,
        "RO": 0.99,
        "AOP": 0.65
    },

    "PFNA": {
        "GAC": 0.90,
        "Ion Exchange": 0.96,
        "RO": 0.99,
        "AOP": 0.70
    },

    "GenX": {
        "GAC": 0.40,
        "Ion Exchange": 0.80,
        "RO": 0.95,
        "AOP": 0.60
    }

}

generic_eff = {
    "GAC": 0.80,
    "Ion Exchange": 0.90,
    "RO": 0.98,
    "AOP": 0.75
}

# =====================================
# COST DATA
# =====================================

tech_cost = {
    "GAC": (0.02, 0.20),
    "Ion Exchange": (0.03, 0.12),
    "RO": (0.05, 0.25),
    "AOP": (0.50, 1.00)
}

# =====================================
# CALCULATIONS
# =====================================

remaining = {}
removed_total = 0

for compound, conc in influent.items():

    current = conc

    for method in selected_methods:

        eff = (
            generic_eff[method]
            if compound == "Total PFAS"
            else tech_eff[compound][method]
        )

        current *= (1-eff)

    remaining[compound] = current

    mass_in = conc * water_volume / 1e9
    mass_out = current * water_volume / 1e9

    removed_total += (mass_in - mass_out)

final_conc = sum(remaining.values())

cost_per_m3 = 0

for method in selected_methods:

    best, worst = tech_cost[method]

    if scenario == "Optimistic":
        val = best

    elif scenario == "Conservative":
        val = worst

    else:
        val = best + (
            (worst - best)
            * uncertainty / 100
        )

    cost_per_m3 += val

treatment_cost = (
    cost_per_m3 *
    water_volume
)

capex = flow_rate * 200
opex = treatment_cost * 0.01
waste = water_volume * 0.05 * 250

total_cost = capex + opex + waste

carbon_factors = {
    "GAC": 0.20,
    "Ion Exchange": 0.15,
    "RO": 0.80,
    "AOP": 1.20
}

carbon = sum(
    carbon_factors[m] * water_volume
    for m in selected_methods
)

carbon_cost = (
    carbon / 1000
) * 80

mass_remaining = (
    final_conc *
    water_volume / 1e9
)

removal_efficiency = (
    removed_total /
    max(
        removed_total + mass_remaining,
        0.000001
    )
) * 100

unit_cost = total_cost / water_volume

liability = total_cost

# =====================================
# COMPLIANCE
# =====================================

st.header("Compliance")

if final_conc <= target_limit:

    st.success(
        f"✅ Compliant with {target_name}"
    )

else:

    st.error(
        f"❌ Exceeds {target_name}"
    )

# =====================================
# EXECUTIVE DASHBOARD
# =====================================

st.header("Executive Dashboard")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "PFAS Removed (kg)",
    f"{removed_total:.3f}"
)

c2.metric(
    "Final PFAS (µg/L)",
    f"{final_conc:.4f}"
)

c3.metric(
    "Removal Efficiency (%)",
    f"{removal_efficiency:.1f}"
)

c4.metric(
    "Total Cost (£)",
    f"{total_cost:,.0f}"
)

c5, c6, c7, c8 = st.columns(4)

c5.metric(
    "Unit Cost (£/m³)",
    f"{unit_cost:.2f}"
)

c6.metric(
    "Carbon (kgCO₂e)",
    f"{carbon:,.0f}"
)

c7.metric(
    "Carbon Cost (£)",
    f"{carbon_cost:,.0f}"
)

c8.metric(
    "Liability (£)",
    f"{liability:,.0f}"
)

# =====================================
# COST BREAKDOWN
# =====================================

st.header("Cost Breakdown")

cost_df = pd.DataFrame({
    "Category": [
        "CAPEX",
        "OPEX",
        "Waste"
    ],
    "Cost": [
        capex,
        opex,
        waste
    ]
})

fig = px.bar(
    cost_df,
    x="Category",
    y="Cost",
    color="Category",
    text_auto=".0f"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================
# MONTE CARLO
# =====================================

st.header("Monte Carlo Cost Analysis")

mc = np.random.triangular(
    cost_per_m3 * 0.5,
    cost_per_m3,
    cost_per_m3 * 1.5,
    10000
)

st.plotly_chart(
    px.histogram(
        pd.DataFrame({"Cost": mc}),
        x="Cost"
    ),
    use_container_width=True
)

# =====================================
# RECOMMENDATION
# =====================================

st.header("Recommendation")

if final_conc <= target_limit:

    st.success(
        "✅ Recommended treatment train."
    )

else:

    st.error(
        "❌ Treatment train does not achieve compliance."
    )

# =====================================
# SUMMARY
# =====================================

st.header("Summary")

st.table(
    pd.DataFrame({
        "Metric": [
            "Source",
            "Treatment Train",
            "Final PFAS",
            "Total Cost"
        ],
        "Value": [
            source,
            " -> ".join(selected_methods),
            f"{final_conc:.4f}",
            f"£{total_cost:,.0f}"
        ]
    })
)

# =====================================
# REPORT EXPORT
# =====================================

st.header("📄 Export Report")

st.info(
    "Press Ctrl+P (Windows) or Cmd+P (Mac) and choose Save as PDF."
)

report_html = f"""
<div style="background:white;padding:40px;font-family:Arial;">

<h1>PFAS Decision Support Report</h1>

<h2>Source</h2>
<p>{source}</p>

<h2>Treatment Train</h2>
<p>{" → ".join(selected_methods)}</p>

<h2>Results</h2>

<ul>
<li>PFAS Removed: {removed_total:.3f} kg</li>
<li>Final PFAS: {final_conc:.4f} µg/L</li>
<li>Total Cost: £{total_cost:,.0f}</li>
<li>Liability: £{liability:,.0f}</li>
<li>Carbon Footprint: {carbon:,.0f} kgCO₂e</li>
</ul>

<p style="color:gray;">
Screening-level estimate only.
</p>

</div>
"""

components.html(
    report_html,
    height=700,
    scrolling=True
)
