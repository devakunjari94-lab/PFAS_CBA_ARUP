import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ======================
# 🔐 PASSWORD PROTECTION
# ======================
APP_PASSWORD = "ARUPPFASSWS2026"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password_input = st.text_input(
        "Enter password to access the PFAS Polluter-Pays Calculator",
        type="password"
    )

    if password_input == APP_PASSWORD:
        st.session_state.authenticated = True
        st.success("✅ Password correct! You can now use the app.")
        # Removed st.stop() here so the app continues
    elif password_input:
        st.warning("❌ Incorrect password. Try again.")
    else:
        st.stop()  # Stops only if no password entered yet

# ======================
# BASE DIRECTORY & LOGO
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "arup_logo.png")
page_icon = logo_path if os.path.exists(logo_path) else "🌍"

st.set_page_config(
    page_title="PFAS Polluter-Pays Calculator",
    page_icon=page_icon,
    layout="wide"
)

if os.path.exists(logo_path):
    st.image(logo_path, width=150)

# ======================
# HEADER
# ======================
st.title("PFAS Polluter-Pays Cost–Benefit Calculator")
st.markdown("""
Estimate PFAS remediation costs under the **polluter-pays principle**.  
Costs are separated into **water vs soil** and **PFAS removal vs PFAS destruction**.
""")

# ======================
# SITE INPUTS
# ======================
st.header("Site Inputs")
site_name = st.text_input("Site name", value="My PFAS Site")

water_volume = st.number_input(
    "Water volume to treat (m³)",
    min_value=0.0,
    value=1_000_000.0
)

soil_mass = st.number_input(
    "Soil mass to treat (tonnes)",
    min_value=0.0,
    value=10_000.0
)

# ======================
# COST SCENARIO (single-choice)
# ======================
scenario = st.radio(
    "Select a cost scenario (pick only one):",
    ["Conservative (high-end estimate)", "Balanced (most likely estimate)"]
)

cost_index = 1 if scenario.startswith("Conservative") else 0

# ======================
# WATER METHODS
# ======================
st.header("💧 Water Treatment Methods")
st.info("Select one or more methods.")

water_methods = {
    "Granular Activated Carbon (GAC)": {"cost": (0.02, 0.06), "type": "Removal"},
    "Ion Exchange": {"cost": (0.03, 0.08), "type": "Removal"},
    "RO / Nanofiltration": {"cost": (0.05, 0.15), "type": "Removal"},
    "Foam Fractionation": {"cost": (0.01, 0.05), "type": "Removal"},
    "Advanced Oxidation (AOP)": {"cost": (0.10, 0.50), "type": "Destruction"},
    "Supercritical Water Oxidation (SCWO)": {"cost": (0.20, 1.00), "type": "Destruction"},
    "Pump-and-Treat + Incineration": {"cost": (0.10, 0.20), "type": "Removal + Destruction"},
    "Electrochemical": {"cost": (0.001, 0.001), "type": "Destruction"}
}

pfas_removal_water = 0
pfas_destruction_water = 0

for method, info in water_methods.items():
    selected = st.checkbox(f"{method} ({info['type']})", key=f"water_{method}")
    if selected:
        cost_per_m3 = info["cost"][cost_index]
        total_cost = cost_per_m3 * water_volume
        if "Removal" in info["type"]:
            pfas_removal_water += total_cost
        if "Destruction" in info["type"]:
            pfas_destruction_water += total_cost

# ======================
# SOIL METHODS
# ======================
st.header("🌱 Soil Treatment Methods")
st.info("Select one or more methods.")

soil_methods = {
    "Excavate & Incinerate / Landfill": {"cost": (50, 200), "type": "Removal + Destruction"},
    "Soil Washing + SCWO/AOP": {"cost": (8, 20), "type": "Removal + Destruction"},
    "Thermal Desorption": {"cost": (100, 500), "type": "Destruction"},
    "In-Situ Stabilisation": {"cost": (20, 40), "type": "Removal"},
    "AOP (ex-situ eluate)": {"cost": (0.10, 0.50), "type": "Destruction"}
}

pfas_removal_soil = 0
pfas_destruction_soil = 0

for method, info in soil_methods.items():
    selected = st.checkbox(f"{method} ({info['type']})", key=f"soil_{method}")
    if selected:
        cost_per_tonne = info["cost"][cost_index]
        total_cost = cost_per_tonne * soil_mass
        if "Removal" in info["type"]:
            pfas_removal_soil += total_cost
        if "Destruction" in info["type"]:
            pfas_destruction_soil += total_cost

# ======================
# GRAND TOTAL & VISUALS
# ======================
grand_total = (
    pfas_removal_water +
    pfas_destruction_water +
    pfas_removal_soil +
    pfas_destruction_soil
)

if grand_total == 0:
    st.warning("⚠️ Select at least one treatment method to calculate costs.")
else:
    st.header("💰 Cost Summary")

    summary_df = pd.DataFrame([
        {"Category": "PFAS Removal from Water", "Cost (£)": pfas_removal_water},
        {"Category": "PFAS Destruction from Water", "Cost (£)": pfas_destruction_water},
        {"Category": "PFAS Removal from Soil", "Cost (£)": pfas_removal_soil},
        {"Category": "PFAS Destruction from Soil", "Cost (£)": pfas_destruction_soil},
        {"Category": "Grand Total", "Cost (£)": grand_total}
    ])

    color = "red" if scenario.startswith("Conservative") else "green"
    st.markdown(
        f"<h2 style='color:{color}'>Total Polluter-Pays Cost ({scenario}): £{grand_total:,.0f}</h2>",
        unsafe_allow_html=True
    )

    st.table(summary_df.style.format({"Cost (£)": "£{:,.0f}"}))

    fig = px.bar(
        summary_df.iloc[:-1],
        x="Category",
        y="Cost (£)",
        color="Category",
        text="Cost (£)"
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Download Cost Breakdown CSV")
    csv = summary_df.to_csv(index=False)
    st.download_button(
        "Download CSV",
        csv,
        file_name=f"{site_name}_PFAS_Polluter_Pays.csv",
        mime="text/csv"
    )
