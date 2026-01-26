import os
import streamlit as st
import pandas as pd

# ======================
# PASSWORD PROTECTION
# ======================
APP_PASSWORD = "ARUPPFASSWS2026"

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Show password input if not authenticated
if not st.session_state.authenticated:
    password_input = st.text_input(
        "🔐 Enter password to access the PFAS Polluter-Pays Calculator",
        type="password"
    )

    if password_input == APP_PASSWORD:
        st.session_state.authenticated = True
        st.experimental_rerun()  # reload app immediately
    elif password_input:
        st.warning("❌ Incorrect password. Please try again.")
    st.stop()  # stop rest of app until correct password

# ======================
# BASE DIRECTORY & LOGO
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "arup_logo.png")
page_icon = logo_path if os.path.exists(logo_path) else "🌍"

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(
    page_title="PFAS Polluter-Pays Calculator",
    page_icon=page_icon,
    layout="wide"
)

# Show logo if exists
if os.path.exists(logo_path):
    st.image(logo_path, width=150)

# ======================
# HEADER
# ======================
st.title("PFAS Polluter-Pays Cost–Benefit Calculator")
st.markdown("""
Estimate indicative PFAS remediation costs under the **polluter-pays principle**.  
Costs are separated into **water vs soil** and **removal vs destruction**.
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

scenario = st.radio(
    "Cost scenario",
    ["Worst-case (highest cost)", "Best-case (lowest cost)"]
)

# ======================
# WATER TREATMENT METHODS
# ======================
st.header("Water Treatment Methods")
st.info("💧 Select one or more methods. Costs are in £/m³ × water volume.")

water_methods = {
    "Granular Activated Carbon (GAC)": (0.02, 0.06, "Removal"),
    "Ion Exchange": (0.03, 0.08, "Removal"),
    "RO / Nanofiltration": (0.05, 0.15, "Removal"),
    "Foam Fractionation": (0.01, 0.05, "Removal"),
    "Advanced Oxidation (AOP)": (0.10, 0.50, "Destruction"),
    "Supercritical Water Oxidation (SCWO)": (0.20, 1.00, "Destruction"),
    "Pump-and-Treat + Incineration": (0.10, 0.20, "Removal + Destruction"),
    "Electrochemical": (0.001, 0.001, "Destruction")
}

water_removal = 0.0
water_destruction = 0.0

for method, (low, high, mtype) in water_methods.items():
    if st.checkbox(f"{method} ({mtype})", key=f"water_{method}"):
        unit_cost = high if scenario.startswith("Worst") else low
        cost = unit_cost * water_volume
        st.write(f"→ £{cost:,.0f}  ({unit_cost} £/m³ × {water_volume:,.0f} m³)")
        if "Removal" in mtype:
            water_removal += cost
        if "Destruction" in mtype:
            water_destruction += cost

# ======================
# SOIL TREATMENT METHODS
# ======================
st.header("Soil Treatment Methods")
st.info("🌱 Select one or more methods. Costs are in £/tonne × soil mass.")

soil_methods = {
    "Excavate & Incinerate / Landfill": (50, 200, "Removal + Destruction"),
    "Soil Washing + SCWO/AOP": (8, 20, "Removal + Destruction"),
    "Thermal Desorption": (100, 500, "Destruction"),
    "In-Situ Stabilisation": (20, 40, "Removal"),
    "AOP (ex-situ eluate)": (0.10, 0.50, "Destruction")
}

soil_removal = 0.0
soil_destruction = 0.0

for method, (low, high, mtype) in soil_methods.items():
    if st.checkbox(f"{method} ({mtype})", key=f"soil_{method}"):
        unit_cost = high if scenario.startswith("Worst") else low
        cost = unit_cost * soil_mass
        st.write(f"→ £{cost:,.0f}  ({unit_cost} £/t × {soil_mass:,.0f} t)")
        if "Removal" in mtype:
            soil_removal += cost
        if "Destruction" in mtype:
            soil_destruction += cost

# ======================
# TOTALS & SUMMARY
# ======================
grand_total = water_removal + water_destruction + soil_removal + soil_destruction

if grand_total == 0:
    st.warning("⚠️ Select at least one treatment method to calculate costs.")
else:
    st.header("Cost Summary")

    st.subheader("Water")
    st.write(f"Removal: £{water_removal:,.0f}")
    st.write(f"Destruction: £{water_destruction:,.0f}")

    st.subheader("Soil")
    st.write(f"Removal: £{soil_removal:,.0f}")
    st.write(f"Destruction: £{soil_destruction:,.0f}")

    color = "red" if scenario.startswith("Worst") else "green"
    st.markdown(
        f"<h2 style='color:{color}'>Total Cost: £{grand_total:,.0f}</h2>",
        unsafe_allow_html=True
    )

    # ======================
    # CSV EXPORT
    # ======================
    df = pd.DataFrame({
        "Category": [
            "Water Removal",
            "Water Destruction",
            "Soil Removal",
            "Soil Destruction",
            "Grand Total"
        ],
        "Cost (£)": [
            water_removal,
            water_destruction,
            soil_removal,
            soil_destruction,
            grand_total
        ],
        "Scenario": [scenario] * 5
    })

    st.subheader("Download Cost Breakdown")
    st.table(df)

    st.download_button(
        "Download CSV",
        df.to_csv(index=False),
        file_name=f"{site_name}_PFAS_Polluter_Pays.csv",
        mime="text/csv"
    )
