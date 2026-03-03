import os
import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

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
    if password_input:
        if password_input == APP_PASSWORD:
            st.session_state.authenticated = True
            st.success("✅ Password correct! You can now use the app.")
        else:
            st.error("❌ Incorrect password. Access denied.")
            st.stop()
    else:
        st.info("🔐 Enter the password to continue.")
        st.stop()

# ======================
# PAGE CONFIG & LOGO
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

st.title("PFAS Polluter-Pays Cost–Benefit Calculator")
st.markdown("""
Estimate PFAS remediation costs under the **polluter-pays principle**.  
Costs are separated into **water vs soil**, **removal vs destruction**, and **PFAS chain-specific**.

Guidance & thresholds aligned with multiple international jurisdictions.
""")

# ======================
# STEP 1: SITE INPUTS
# ======================
st.header("Step 1: Enter Site Information & PFAS Concentrations")

c1, c2, c3 = st.columns(3)
with c1:
    site_name = st.text_input("Site name", value="My PFAS Site")
with c2:
    water_volume = st.number_input("Water volume to treat (m³)", min_value=0.0, value=1_000_000.0)
with c3:
    soil_mass = st.number_input("Soil mass to treat (tonnes)", min_value=0.0, value=10_000.0)

receptor_type = st.radio(
    "Select receptor type (affects threshold):",
    ["Drinking water", "Environmental / Surface water"],
    horizontal=True
)

# ======================
# CONCENTRATION UNITS
# ======================
st.subheader("Concentration Units")
conc_unit = st.selectbox(
    "Select concentration unit:",
    ["ng/L", "µg/L", "mg/L"],
    index=1
)
UNIT_CONVERSION = {"ng/L":0.001,"µg/L":1,"mg/L":1000}
st.caption("All concentrations are internally converted to µg/L for calculation.")

# ======================
# JURISDICTION SELECTION
# ======================
st.subheader("Select Regulatory Jurisdiction")
jurisdiction = st.selectbox(
    "Jurisdiction:",
    ["UK (Environment Agency)", "EU (Drinking Water Directive)", "Australia (Guideline Values)", "USA (EPA 2024 MCLs)"]
)

# ======================
# PFAS Map
# ======================
with st.expander("🌍 PFAS Contamination Data Reference (PDH Map)"):
    st.markdown("Interactive PDH Map showing PFAS contamination in water and soil: [PDH Map](https://pdh.cnrs.fr/en/map/)")
    components.iframe("https://pdh.cnrs.fr/en/map/", height=850)

# ======================
# PFAS concentrations
# ======================
st.subheader("Influent PFAS concentrations")
default_chains = ["PFOA", "PFOS", "PFHxS", "PFNA"]
use_general = st.checkbox("I do not have chain-specific PFAS data (use general PFAS)")
pfas_chains = ["General PFAS"] if use_general else default_chains

influent_pf = {}
cols = st.columns(len(pfas_chains))
for col, chain in zip(cols, pfas_chains):
    with col:
        value_input = st.number_input(
            f"{chain} concentration ({conc_unit})",
            min_value=0.0,
            value=10.0
        )
        influent_pf[chain] = value_input * UNIT_CONVERSION[conc_unit]

# ======================
# SCENARIOS
# ======================
st.header("Step 2: Select Scenario & Treatment Methods")
SCENARIOS = {
    "Conservative (UK precautionary)": {"description": "Higher costs, maximum caution", "cost_index": 1},
    "Moderate (Risk-based UK)": {"description": "Expected costs, balanced risk", "cost_index": 0}
}
scenario_selection = st.radio(
    "Select a cost scenario:",
    [f"{k} – {v['description']}" for k,v in SCENARIOS.items()],
    horizontal=True
)
scenario_key = scenario_selection.split(" – ")[0]
cost_index = SCENARIOS[scenario_key]["cost_index"]

# ======================
# THRESHOLDS PER JURISDICTION
# ======================
THRESHOLDS = {
    "UK (Environment Agency)": {
        "Drinking water": {"PFOA":0.4,"PFOS":0.015,"PFHxS":0.2,"PFNA":0.3,"General PFAS":0.4},
        "Environmental / Surface water": {"PFOA":2,"PFOS":0.2,"PFHxS":0.5,"PFNA":0.6,"General PFAS":2}
    },
    "EU (Drinking Water Directive)": {
        "Drinking water": {c:0.1 for c in pfas_chains},  # 0.1 µg/L individual PFAS
        "Environmental / Surface water": {c:0.5 for c in pfas_chains}  # approximate
    },
    "Australia (Guideline Values)": {
        "Drinking water": {"PFOA":0.56,"PFOS":0.56,"PFHxS":0.1,"PFNA":0.07,"General PFAS":0.5},
        "Environmental / Surface water": {"PFOA":2,"PFOS":0.2,"PFHxS":0.5,"PFNA":0.6,"General PFAS":2}
    },
    "USA (EPA 2024 MCLs)": {
        "Drinking water": {"PFOA":0.004,"PFOS":0.004,"PFHxS":0.02,"PFNA":0.02,"General PFAS":0.01},
        "Environmental / Surface water": {"PFOA":0.01,"PFOS":0.01,"PFHxS":0.05,"PFNA":0.05,"General PFAS":0.02}
    }
}
thresholds = THRESHOLDS[jurisdiction][receptor_type]

# ======================
# WATER METHODS
# ======================
water_methods = {
    "Granular Activated Carbon (GAC) (Removal – offsite liability)": {
        "cost": (0.02,0.08), "type":"Removal","efficiency":(0.6,0.9),
        "secondary_waste": True, "waste_form":"spent carbon","pfas_scope":pfas_chains
    },
    "Advanced Oxidation Process (AOP) (Destruction – mineralisation)": {
        "cost": (0.15,1.0), "type":"Destruction","efficiency":(0.7,0.99),
        "secondary_waste": False,"pfas_scope":pfas_chains
    }
}

# ======================
# SOIL METHODS
# ======================
soil_methods = {
    "Excavate & Incinerate (Destruction – mineralisation)": {
        "cost": (50,250),"type":"Destruction","efficiency":(0.9,1.0),
        "secondary_waste": True,"waste_form":"incineration ash","pfas_scope":pfas_chains
    },
    "Excavate & Hazardous Landfill (Removal – offsite liability)": {
        "cost": (50,250),"type":"Removal","efficiency":(0.3,0.5),
        "secondary_waste": True,"waste_form":"landfill soil","pfas_scope":pfas_chains
    }
}

# ======================
# METHOD SELECTION
# ======================
left_col, right_col = st.columns(2)
with left_col:
    if water_volume > 0:
        selected_water_method = st.selectbox("Select Water Treatment Method", list(water_methods.keys()))
        wm_info = water_methods[selected_water_method]
    else:
        wm_info = None

    if soil_mass > 0:
        selected_soil_method = st.selectbox("Select Soil Treatment Method", list(soil_methods.keys()))
        sm_info = soil_methods[selected_soil_method]
    else:
        sm_info = None

with right_col:
    st.subheader("Compliance Check")

    def calc_residual(data, method):
        return {k:v*(1-method["efficiency"][cost_index]) for k,v in data.items()}

    res_water = calc_residual(influent_pf, wm_info) if wm_info else influent_pf
    res_soil  = calc_residual(influent_pf, sm_info) if sm_info else influent_pf
    res_combined = {k:min(res_water[k],res_soil[k]) for k in pfas_chains}

    # Hazard Index logic
    table=[]
    hazard=0
    for c in pfas_chains:
        r = res_combined[c]
        t = thresholds[c]
        hazard += r/t
        table.append([c, r, t, "✅ Pass" if r<=t else "❌ Exceeds"])

    # EU sum-of-PFAS logic (example)
    if jurisdiction.startswith("EU"):
        sum_residual = sum(res_combined.values())
        if sum_residual > 0.5:  # EU sum threshold in µg/L
            st.warning(f"⚠ Sum-of-PFAS exceeds EU threshold: {sum_residual:.2f} µg/L")

    st.table(pd.DataFrame(table, columns=["PFAS","Residual (µg/L)","Threshold (µg/L)","Status"]))

    if hazard <=1:
        st.success(f"Hazard Index {hazard:.2f} — Compliant")
    else:
        st.error(f"Hazard Index {hazard:.2f} — Exceeds")

# ======================
# COST SUMMARY
# ======================
cost_water = wm_info["cost"][cost_index]*water_volume if wm_info else 0
cost_soil  = sm_info["cost"][cost_index]*soil_mass if sm_info else 0
grand_total = cost_water + cost_soil

st.header("Step 3: Cost Summary")
summary_df = pd.DataFrame([
    ["Water Treatment", cost_water],
    ["Soil Treatment", cost_soil],
    ["Grand Total", grand_total]
], columns=["Category","Cost (£)"])

st.table(summary_df)
st.metric("Total Polluter-Pays Cost", f"£{grand_total:,.0f}")

with st.expander("📈 Cost Visualization"):
    fig = px.bar(summary_df, x="Category", y="Cost (£)", text="Cost (£)")
    fig.update_traces(texttemplate='£%{y:,.0f}', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

st.download_button(
    "Download Cost Breakdown CSV",
    summary_df.to_csv(index=False),
    file_name=f"{site_name}_PFAS_Polluter_Pays.csv"
)
