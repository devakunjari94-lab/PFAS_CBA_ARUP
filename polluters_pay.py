import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# =====================================
# PASSWORD
# =====================================

PASSWORD = "PFAS2026"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:

    st.title("🔐 PFAS Tool Login")

    pw = st.text_input("Password", type="password")

    if st.button("Login"):
        if pw == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Incorrect Password")

    st.stop()

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="PFAS Decision Support Tool",
    layout="wide"
)

st.title("PFAS Polluter Pays Decision Support Tool")

# =====================================
# DISCLAIMER
# =====================================

with st.expander("⚠ Model Scope & Limitations"):

    st.markdown("""
    This tool provides screening-level estimates only.

    ✅ Suitable for:

    - Early-stage option assessment
    - Technology comparison
    - Polluter-pays scenarios

    ❌ Not suitable for:

    - Detailed design
    - Procurement
    - Regulatory submission
    """)

# =====================================
# SCENARIO
# =====================================

st.header("Project Scenario")

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
# SITE DATA
# =====================================

st.header("Site Information")

col1, col2 = st.columns(2)

water_volume = col1.number_input(
    "Water Volume (m³)",
    value=1000000.0
)

flow_rate = col2.number_input(
    "Flow Rate (m³/day)",
    value=5000.0
)

# =====================================
# PFAS INPUTS
# =====================================

st.header("PFAS Concentrations")

pfoa = st.number_input("PFOA (µg/L)", value=5.0)
pfos = st.number_input("PFOS (µg/L)", value=5.0)
pfhxs = st.number_input("PFHxS (µg/L)", value=1.0)
pfna = st.number_input("PFNA (µg/L)", value=1.0)

influent = {
    "PFOA": pfoa,
    "PFOS": pfos,
    "PFHxS": pfhxs,
    "PFNA": pfna
}

# =====================================
# REGULATION
# =====================================

st.header("Regulatory Target")

targets = {
    "UK DWI": 0.1,
    "EU Drinking Water Directive": 0.5,
    "EPA": 0.004
}

target_name = st.selectbox(
    "Regulatory Standard",
    list(targets.keys())
)

target_limit = targets[target_name]

# =====================================
# TREATMENT TRAIN
# =====================================

st.header("Treatment Train")

selected_methods = st.multiselect(
    "Select Technologies",
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

efficiency = {

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
    }

}

# =====================================
# TECHNOLOGY COSTS
# =====================================

tech_cost = {

    "GAC": {
        "best": 0.02,
        "worst": 0.20
    },

    "Ion Exchange": {
        "best": 0.03,
        "worst": 0.12
    },

    "RO": {
        "best": 0.05,
        "worst": 0.25
    },

    "AOP": {
        "best": 0.50,
        "worst": 1.00
    }

}

# =====================================
# CALCULATIONS
# =====================================

remaining = {}
removed_total = 0
mass_total = 0

for compound, conc in influent.items():

    current = conc

    for method in selected_methods:

        removal = efficiency[compound][method]

        current = current * (1 - removal)

    remaining[compound] = current

    mass_in = conc * water_volume / 1e9
    mass_out = current * water_volume / 1e9

    mass_total += mass_in
    removed_total += (mass_in - mass_out)

final_concentration = sum(remaining.values())

# =====================================
# COMPLIANCE
# =====================================

st.header("Compliance Check")

if final_concentration <= target_limit:
    st.success(f"✅ Compliant with {target_name}")

else:
    st.error(f"❌ Exceeds {target_name}")

# =====================================
# COSTING
# =====================================

cost_per_m3 = 0

for method in selected_methods:

    best = tech_cost[method]["best"]
    worst = tech_cost[method]["worst"]

    if scenario == "Optimistic":
        value = best

    elif scenario == "Conservative":
        value = worst

    else:
        value = best + (
            (worst - best)
            * uncertainty
            / 100
        )

    cost_per_m3 += value

treatment_cost = cost_per_m3 * water_volume

capex = flow_rate * 200
opex = treatment_cost * 0.01
waste = water_volume * 0.05 * 250

total_cost = capex + opex + waste

# =====================================
# CARBON
# =====================================

carbon_factors = {

    "GAC": 0.2,
    "Ion Exchange": 0.15,
    "RO": 0.8,
    "AOP": 1.2

}

carbon = 0

for method in selected_methods:
    carbon += water_volume * carbon_factors[method]

# =====================================
# LIABILITY
# =====================================

cost_per_kg = total_cost / max(
    removed_total,
    0.000001
)

liability = removed_total * cost_per_kg

# =====================================
# MONTE CARLO
# =====================================

distribution = np.random.triangular(
    cost_per_m3 * 0.5,
    cost_per_m3,
    cost_per_m3 * 1.5,
    10000
)

p10 = np.percentile(distribution, 10)
p50 = np.percentile(distribution, 50)
p90 = np.percentile(distribution, 90)

# =====================================
# RESULTS
# =====================================

st.header("Results")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "PFAS Removed (kg)",
    f"{removed_total:.3f}"
)

c2.metric(
    "Final PFAS (µg/L)",
    f"{final_concentration:.4f}"
)

c3.metric(
    "Total Cost (£)",
    f"{total_cost:,.0f}"
)

c4.metric(
    "Carbon (kg CO₂e)",
    f"{carbon:,.0f}"
)

# =====================================
# LIABILITY
# =====================================

st.header("Polluter Pays")

c1, c2 = st.columns(2)

c1.metric(
    "Cost per kg Removed",
    f"£{cost_per_kg:,.0f}"
)

c2.metric(
    "Estimated Liability",
    f"£{liability:,.0f}"
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

fig = px.pie(
    cost_df,
    names="Category",
    values="Cost",
    title="Project Cost Breakdown"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================
# MONTE CARLO CHART
# =====================================

st.header("Monte Carlo Cost Analysis")

mc_df = pd.DataFrame({
    "Cost £/m³": distribution
})

fig2 = px.histogram(
    mc_df,
    x="Cost £/m³",
    nbins=40
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

col1, col2, col3 = st.columns(3)

col1.metric("P10", f"£{p10:.2f}")
col2.metric("P50", f"£{p50:.2f}")
col3.metric("P90", f"£{p90:.2f}")

# =====================================
# TECHNOLOGY SUMMARY
# =====================================

st.header("Technology Comparison")

comparison = pd.DataFrame({

    "Technology": [
        "GAC",
        "Ion Exchange",
        "RO",
        "AOP"
    ],

    "Removal %": [
        75,
        85,
        95,
        85
    ],

    "Relative Cost": [
        2,
        3,
        5,
        4
    ],

    "Carbon Score": [
        2,
        2,
        5,
        4
    ]

})

fig3 = px.scatter(
    comparison,
    x="Relative Cost",
    y="Removal %",
    color="Technology",
    size="Carbon Score"
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

# =====================================
# REPORT
# =====================================

st.header("Report Summary")

report = pd.DataFrame({

    "Parameter": [
        "Treatment Train",
        "Final Concentration",
        "Total Cost",
        "PFAS Removed",
        "Carbon Footprint",
        "Liability"
    ],

    "Value": [
        " → ".join(selected_methods),
        f"{final_concentration:.4f} µg/L",
        f"£{total_cost:,.0f}",
        f"{removed_total:.3f} kg",
        f"{carbon:,.0f} kg CO₂e",
        f"£{liability:,.0f}"
    ]

})

st.table(report)

st.success("PFAS Decision Support Analysis Complete")
