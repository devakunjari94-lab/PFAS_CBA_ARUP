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

Guidance & thresholds aligned with **UK Environment Agency PFAS thresholds**:  
[EA PFAS Thresholds Summary](https://www.gov.uk/government/publications/developing-thresholds-for-managing-pfas-in-the-water-environment/developing-thresholds-for-managing-pfas-in-the-water-environment-summary)
""")

# ======================
# STEP 1: SITE INPUTS & PFAS CONCENTRATIONS
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

# PFAS Map
with st.expander("🌍 PFAS Contamination Data Reference (PDH Map)"):
    st.markdown("""
Interactive PDH Map showing PFAS contamination in water and soil.  
If easier, open directly: [PDH Map](https://pdh.cnrs.fr/en/map/)
""")
    components.iframe("https://pdh.cnrs.fr/en/map/", height=850)

# PFAS concentrations
st.subheader("Influent PFAS concentrations")
default_chains = ["PFOA", "PFOS", "PFHxS", "PFNA"]
use_general = st.checkbox("I do not have chain-specific PFAS data (use general PFAS)")
pfas_chains = ["General PFAS"] if use_general else default_chains

influent_pf = {}
cols = st.columns(len(pfas_chains))
for col, chain in zip(cols, pfas_chains):
    with col:
        influent_pf[chain] = st.number_input(f"{chain} concentration", min_value=0.0, value=10.0)

# ======================
# STEP 2: SELECT SCENARIO & METHODS
# ======================
st.header("Step 2: Select Scenario & Treatment Methods")

SCENARIOS = {
    "Conservative (UK precautionary)": {"description": "Higher costs, maximum caution", "cost_index": 1},
    "Moderate (Risk-based UK)": {"description": "Expected costs, balanced risk", "cost_index": 0}
}

scenario_selection = st.radio(
    "Select a cost scenario:",
    [f"{k} – {v['description']}" for k, v in SCENARIOS.items()],
    horizontal=True
)

scenario_key = scenario_selection.split(" – ")[0]
scenario_config = SCENARIOS[scenario_key]
cost_index = scenario_config["cost_index"]

EA_THRESHOLDS = {
    "Drinking water": {"PFOA":0.4,"PFOS":0.015,"PFHxS":0.2,"PFNA":0.3,"General PFAS":0.4},
    "Environmental / Surface water": {"PFOA":2,"PFOS":0.2,"PFHxS":0.5,"PFNA":0.6,"General PFAS":2}
}

# Water methods
water_methods = {
    "Granular Activated Carbon (GAC) (Removal – offsite liability)": {
        "cost": (0.02,0.08), "type":"Removal","efficiency":(0.6,0.9),
        "secondary_waste": True, "waste_form":"spent carbon","pfas_scope":pfas_chains
    },
    "Ion Exchange (IE) (Removal – offsite liability)": {
        "cost": (0.03,0.12), "type":"Removal","efficiency":(0.7,0.95),
        "secondary_waste": True, "waste_form":"resin brine","pfas_scope":pfas_chains
    },
    "RO / Nanofiltration (RO/NF) (Removal – offsite liability)": {
        "cost": (0.05,0.20), "type":"Removal","efficiency":(0.8,0.99),
        "secondary_waste": True, "waste_form":"concentrate / brine","pfas_scope":pfas_chains
    },
    "Foam Fractionation (Removal – offsite liability)": {
        "cost": (0.01,0.05), "type":"Removal","efficiency":(0.3,0.6),
        "secondary_waste": True, "waste_form":"foam / concentrate","pfas_scope":pfas_chains
    },
    "Advanced Oxidation Process (AOP) (Destruction – mineralisation)": {
        "cost": (0.15,1.0), "type":"Destruction","efficiency":(0.7,0.99),
        "secondary_waste": False,"pfas_scope":pfas_chains
    },
    "Supercritical Water Oxidation (SCWO) (Destruction – mineralisation)": {
        "cost": (6.8,25.5), "type":"Destruction","efficiency":(0.9,1.0),
        "secondary_waste": False,"pfas_scope":pfas_chains
    },
    "Pump-and-Treat + Incineration (Removal – offsite liability)": {
        "cost": (0.10,0.30), "type":"Removal","efficiency":(0.5,0.8),
        "secondary_waste": True,"waste_form":"incineration ash","pfas_scope":pfas_chains
    },
    "Pump-and-Treat + Incineration (Destruction – mineralisation)": {
        "cost": (0.10,0.30), "type":"Destruction","efficiency":(0.7,0.95),
        "secondary_waste": False,"pfas_scope":pfas_chains
    },
    "Electrochemical (Destruction – mineralisation, pilot / early deployment)": {
        "cost": (0.05,0.20), "type":"Destruction","efficiency":(0.5,0.95),
        "secondary_waste": False,"pfas_scope":pfas_chains,
        "technology_readiness":"pilot",
        "info":"⚠️ Technology at pilot / early deployment stage"
    }
}

# Soil methods
soil_methods = {
    "Excavate & Incinerate (Destruction – mineralisation)": {
        "cost": (50,250),"type":"Destruction","efficiency":(0.9,1.0),
        "secondary_waste": True,"waste_form":"incineration ash","pfas_scope":pfas_chains
    },
    "Excavate & Hazardous Landfill (Removal – offsite liability)": {
        "cost": (50,250),"type":"Removal","efficiency":(0.3,0.5),
        "secondary_waste": True,"waste_form":"landfill soil","pfas_scope":pfas_chains
    },
    "Soil Washing + SCWO/AOP (Removal – offsite liability)": {
        "cost": (8,20),"type":"Removal","efficiency":(0.5,0.8),
        "secondary_waste": True,"waste_form":"eluate","pfas_scope":pfas_chains
    },
    "Soil Washing + SCWO/AOP (Destruction – mineralisation)": {
        "cost": (8,20),"type":"Destruction","efficiency":(0.7,0.95),
        "secondary_waste": False,"pfas_scope":pfas_chains
    },
    "Thermal Desorption (Destruction – mineralisation)": {
        "cost": (100,600),"type":"Destruction","efficiency":(0.8,1.0),
        "secondary_waste": True,"waste_form":"desorption residues","pfas_scope":pfas_chains
    },
    "In-Situ Stabilisation (Removal – offsite liability)": {
        "cost": (20,80),"type":"Removal","efficiency":(0.2,0.5),
        "secondary_waste": False,"pfas_scope":pfas_chains
    },
    "AOP (ex-situ eluate) (Destruction – mineralisation)": {
        "cost": (10,40),"type":"Destruction","efficiency":(0.7,0.95),
        "secondary_waste": False,"pfas_scope":pfas_chains
    }
}

# ======================
# STEP 2: SIDE-BY-SIDE METHODS & COMPLIANCE
# ======================
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Treatment Methods")
    if water_volume > 0:
        selected_water_method = st.selectbox("Select Water Treatment Method", list(water_methods.keys()))
        wm_info = water_methods[selected_water_method]
        st.markdown(f"**Type:** {wm_info['type']}  |  **Efficiency:** {wm_info['efficiency'][cost_index]*100:.0f}%")
        if wm_info.get("secondary_waste"):
            st.info(f"Generates secondary waste: {wm_info['waste_form']}")
        if wm_info.get("technology_readiness") == "pilot":
            st.warning(wm_info.get("info"))
    else:
        selected_water_method = None
        wm_info = None

    if soil_mass > 0:
        selected_soil_method = st.selectbox("Select Soil Treatment Method", list(soil_methods.keys()))
        sm_info = soil_methods[selected_soil_method]
        st.markdown(f"**Type:** {sm_info['type']}  |  **Efficiency:** {sm_info['efficiency'][cost_index]*100:.0f}%")
        if sm_info.get("secondary_waste"):
            st.info(f"Generates secondary waste: {sm_info['waste_form']}")
    else:
        selected_soil_method = None
        sm_info = None

with right_col:
    st.subheader("Compliance Check")
    def calc_residual(data, method):
        return {k:v*(1-method["efficiency"][cost_index]) for k,v in data.items()}

    res_water = calc_residual(influent_pf, wm_info) if wm_info else influent_pf
    res_soil  = calc_residual(influent_pf, sm_info) if sm_info else influent_pf

    res_combined = {k:min(res_water[k],res_soil[k]) for k in pfas_chains}
    thresholds = EA_THRESHOLDS[receptor_type]

    table=[]
    hazard=0
    for c in pfas_chains:
        r=res_combined[c]; t=thresholds[c]
        hazard += r/t
        table.append([c,r,t,"✅ Pass" if r<=t else "❌ Exceeds"])

    st.table(pd.DataFrame(table, columns=["PFAS","Residual","Threshold","Status"]))
    if hazard <=1:
        st.success(f"Hazard Index {hazard:.2f} — Compliant")
    else:
        st.error(f"Hazard Index {hazard:.2f} — Exceeds")

# ======================
# STEP 3: COST SUMMARY
# ======================
cost_water = wm_info["cost"][cost_index]*water_volume if wm_info else 0
cost_soil  = sm_info["cost"][cost_index]*soil_mass if sm_info else 0

rem_w = cost_water if wm_info and wm_info["type"]=="Removal" else 0
des_w = cost_water if wm_info and wm_info["type"]=="Destruction" else 0
rem_s = cost_soil if sm_info and sm_info["type"]=="Removal" else 0
des_s = cost_soil if sm_info and sm_info["type"]=="Destruction" else 0
grand_total = rem_w+des_w+rem_s+des_s

st.header("Step 3: Cost Summary")
summary_df = pd.DataFrame([
    ["Water Removal",rem_w],
    ["Water Destruction",des_w],
    ["Soil Removal",rem_s],
    ["Soil Destruction",des_s],
    ["Grand Total",grand_total]
], columns=["Category","Cost (£)"])

st.table(summary_df)
st.metric("Total Polluter-Pays Cost", f"£{grand_total:,.0f}")

with st.expander("📈 Cost Visualization"):
    fig = px.bar(summary_df, x="Category", y="Cost (£)", text="Cost (£)")
    fig.update_traces(texttemplate='£%{y:,.0f}', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# Download CSV
st.download_button(
    "Download Cost Breakdown CSV",
    summary_df.to_csv(index=False),
    file_name=f"{site_name}_PFAS_Polluter_Pays.csv"
)
