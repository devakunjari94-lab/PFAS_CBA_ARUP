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
    elif password_input:
        st.warning("❌ Incorrect password. Try again")
    else:
        st.stop()

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
Costs are separated into **water vs soil**, **removal vs destruction**, and **PFAS chain-specific**.  

Guidance & thresholds aligned with **UK Environment Agency PFAS thresholds**:  
[EA PFAS Thresholds Summary](https://www.gov.uk/government/publications/developing-thresholds-for-managing-pfas-in-the-water-environment/developing-thresholds-for-managing-pfas-in-the-water-environment-summary)
""")

# ======================
# SITE INPUTS
# ======================
st.header("Site Inputs")
site_name = st.text_input("Site name", value="My PFAS Site")
water_volume = st.number_input("Water volume to treat (m³)", min_value=0.0, value=1_000_000.0)
soil_mass = st.number_input("Soil mass to treat (tonnes)", min_value=0.0, value=10_000.0)

receptor_type = st.radio(
    "Select receptor type (affects threshold):",
    ["Drinking water", "Environmental / Surface water"]
)

# PFAS chains inputs
st.subheader("Influent PFAS concentrations")
pfas_chains = ["PFOA", "PFOS", "PFHxS", "PFNA"]
influent_pf = {}
for chain in pfas_chains:
    influent_pf[chain] = st.number_input(f"{chain} (ng/L for water / µg/kg for soil)", min_value=0.0, value=10.0)

# ======================
# SCENARIOS
# ======================
SCENARIOS = {
    "Conservative (UK precautionary)": {
        "cost_index": 1,
        "allow_removal_only": False,
        "confidence_factor": 1.3
    },
    "Moderate (Risk-based UK)": {
        "cost_index": 0,
        "allow_removal_only": True,
        "confidence_factor": 1.0
    }
}

scenario = st.radio("Select a cost scenario:", list(SCENARIOS.keys()))
scenario_config = SCENARIOS[scenario]
cost_index = scenario_config["cost_index"]

# ======================
# UK PFAS thresholds
# ======================
EA_THRESHOLDS = {
    "Drinking water": {
        "PFOA": 0.4,
        "PFOS": 0.015,
        "PFHxS": 0.2,
        "PFNA": 0.3
    },
    "Environmental / Surface water": {
        "PFOA": 2.0,
        "PFOS": 0.2,
        "PFHxS": 0.5,
        "PFNA": 0.6
    }
}

# ======================
# WATER METHODS
# ======================
st.header("💧 Water Treatment Methods")
water_methods = {
    "Granular Activated Carbon (GAC) (Removal – offsite liability)": {
        "cost": (0.02, 0.08),
        "type": "Removal",
        "efficiency": (0.6, 0.9),
        "pfas_scope": ["PFOA","PFNA","PFOS"],
        "secondary_waste": True,
        "waste_form": "spent carbon"
    },
    "Ion Exchange (IE) (Removal – offsite liability)": {
        "cost": (0.03, 0.12),
        "type": "Removal",
        "efficiency": (0.7, 0.95),
        "pfas_scope": ["PFOA","PFNA","PFOS"],
        "secondary_waste": True,
        "waste_form": "resin brine"
    },
    "RO / Nanofiltration (RO/NF) (Removal – offsite liability)": {
        "cost": (0.05, 0.20),
        "type": "Removal",
        "efficiency": (0.8, 0.99),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": True,
        "waste_form": "concentrate / brine"
    },
    "Foam Fractionation (Removal – offsite liability)": {
        "cost": (0.01, 0.05),
        "type": "Removal",
        "efficiency": (0.3, 0.6),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": True,
        "waste_form": "foam / concentrate"
    },
    "Advanced Oxidation Process (AOP) (Destruction – mineralisation)": {
        "cost": (0.15, 1.00),
        "type": "Destruction",
        "efficiency": (0.7, 0.99),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": False
    },
    "Supercritical Water Oxidation (SCWO) (Destruction – mineralisation)": {
        "cost": (6.80, 25.50),
        "type": "Destruction",
        "efficiency": (0.9,1.0),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": False
    },
    "Pump-and-Treat + Incineration (Removal – offsite liability)": {
        "cost": (0.10, 0.30),
        "type": "Removal",
        "efficiency": (0.5,0.8),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": True,
        "waste_form": "incineration ash"
    },
    "Pump-and-Treat + Incineration (Destruction – mineralisation)": {
        "cost": (0.10, 0.30),
        "type": "Destruction",
        "efficiency": (0.7,0.95),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": False
    },
    "Electrochemical (Destruction – mineralisation, pilot / early deployment)": {
        "cost": (0.05, 0.20),
        "type": "Destruction",
        "efficiency": (0.5,0.95),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": False,
        "technology_readiness": "pilot",
        "info": "⚠️ Technology at pilot / early deployment stage (e.g., Oxyle client pilots)"
    }
}

selected_water_method = st.radio("Choose one water treatment method:", list(water_methods.keys()))

# ======================
# SOIL METHODS
# ======================
st.header("🌱 Soil Treatment Methods")
soil_methods = {
    "Excavate & Incinerate (Destruction – mineralisation)": {
        "cost": (50, 250),
        "type": "Destruction",
        "efficiency": (0.9, 1.0),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": True,
        "waste_form": "incineration ash"
    },
    "Excavate & Hazardous Landfill (Removal – offsite liability)": {
        "cost": (50, 250),
        "type": "Removal",
        "efficiency": (0.3,0.5),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": True,
        "waste_form": "landfill soil"
    },
    "Soil Washing + SCWO/AOP (Removal – offsite liability)": {
        "cost": (8, 20),
        "type": "Removal",
        "efficiency": (0.5,0.8),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": True,
        "waste_form": "eluate"
    },
    "Soil Washing + SCWO/AOP (Destruction – mineralisation)": {
        "cost": (8, 20),
        "type": "Destruction",
        "efficiency": (0.7,0.95),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": False
    },
    "Thermal Desorption (Destruction – mineralisation)": {
        "cost": (100, 600),
        "type": "Destruction",
        "efficiency": (0.8,1.0),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": True,
        "waste_form": "desorption residues"
    },
    "In-Situ Stabilisation (Removal – offsite liability)": {
        "cost": (20, 80),
        "type": "Removal",
        "efficiency": (0.2,0.5),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": False
    },
    "AOP (ex-situ eluate) (Destruction – mineralisation)": {
        "cost": (10, 40),
        "type": "Destruction",
        "efficiency": (0.7,0.95),
        "pfas_scope": ["PFOA","PFOS","PFHxS","PFNA"],
        "secondary_waste": False
    }
}

selected_soil_method = st.radio("Choose one soil treatment method:", list(soil_methods.keys()))

# ======================
# CALCULATION FUNCTIONS
# ======================
def calculate_residual(influent_dict, method):
    residual = {}
    info = method
    for chain, conc in influent_dict.items():
        if chain in info["pfas_scope"]:
            eff = info["efficiency"][cost_index]
            residual[chain] = conc * (1 - eff)
        else:
            residual[chain] = conc
    return residual

# Water calculation
pfas_removal_water = 0
pfas_destruction_water = 0
residual_water = influent_pf.copy()
if selected_water_method:
    info = water_methods[selected_water_method]
    residual_water = calculate_residual(influent_pf, info)
    total_cost = info["cost"][cost_index] * water_volume
    if info["type"] == "Removal":
        pfas_removal_water += total_cost
    else:
        pfas_destruction_water += total_cost
    if info.get("secondary_waste"):
        st.warning(f"⚠️ Water method generates secondary waste: {info['waste_form']}")
    if info.get("technology_readiness") == "pilot":
        st.info(info.get("info"))

# Soil calculation
pfas_removal_soil = 0
pfas_destruction_soil = 0
residual_soil = influent_pf.copy()
if selected_soil_method:
    info = soil_methods[selected_soil_method]
    residual_soil = calculate_residual(influent_pf, info)
    total_cost = info["cost"][cost_index] * soil_mass
    if info["type"] == "Removal":
        pfas_removal_soil += total_cost
    else:
        pfas_destruction_soil += total_cost
    if info.get("secondary_waste"):
        st.warning(f"⚠️ Soil method generates secondary waste: {info['waste_form']}")

# ======================
# COMPLIANCE CHECK
# ======================
residual_combined = {chain: min(residual_water[chain], residual_soil[chain]) for chain in pfas_chains}
thresholds = EA_THRESHOLDS[receptor_type]
hazard_index = sum(residual_combined[chain] / thresholds[chain] for chain in pfas_chains)

st.header("📊 PFAS Compliance Check")
st.write(f"Residual PFAS concentrations vs UK {receptor_type} thresholds:")

compliance_table = []
for chain in pfas_chains:
    compliant = "✅ Pass" if residual_combined[chain] <= thresholds[chain] else "❌ Exceeds"
    compliance_table.append({
        "PFAS Chain": chain,
        "Residual": residual_combined[chain],
        "Threshold": thresholds[chain],
        "Status": compliant
    })

st.table(pd.DataFrame(compliance_table))

if hazard_index <= 1:
    st.success(f"✅ Overall hazard index {hazard_index:.2f} ≤ 1 – Meets UK {receptor_type} thresholds")
else:
    st.error(f"❌ Overall hazard index {hazard_index:.2f} > 1 – Exceeds UK {receptor_type} thresholds")

# ======================
# GRAND TOTAL & VISUALS
# ======================
grand_total = pfas_removal_water + pfas_destruction_water + pfas_removal_soil + pfas_destruction_soil

st.header("💰 Cost Summary")
summary_df = pd.DataFrame([
    {"Category": "PFAS Removal from Water", "Cost (£)": pfas_removal_water},
    {"Category": "PFAS Destruction from Water", "Cost (£)": pfas_destruction_water},
    {"Category": "PFAS Removal from Soil", "Cost (£)": pfas_removal_soil},
    {"Category": "PFAS Destruction from Soil", "Cost (£)": pfas_destruction_soil},
    {"Category": "Grand Total", "Cost (£)": grand_total}
])
color = "red" if scenario.startswith("Conservative") else "green"
st.markdown(f"<h2 style='color:{color}'>Total Polluter-Pays Cost ({scenario}): £{grand_total:,.0f}</h2>", unsafe_allow_html=True)
st.table(summary_df.style.format({"Cost (£)": "£{:,.0f}"}))

# ======================
# BAR CHART
# ======================
st.header("📈 Cost Visualization")
chart_df = pd.DataFrame({
    "Category": ["Water", "Soil"],
    "Removal": [pfas_removal_water, pfas_removal_soil],
    "Destruction": [pfas_destruction_water, pfas_destruction_soil]
})
chart_df_melt = chart_df.melt(id_vars="Category", value_vars=["Removal","Destruction"], var_name="Type", value_name="Cost (£)")
fig = px.bar(chart_df_melt, x="Category", y="Cost (£)", color="Type", text="Cost (£)", barmode="group", title="PFAS Removal vs Destruction Costs")
fig.update_traces(texttemplate='£%{y:,.0f}', textposition='outside')
st.plotly_chart(fig, use_container_width=True)

# ======================
# CSV download
# ======================
st.subheader("Download Cost Breakdown CSV")
csv = summary_df.to_csv(index=False)
st.download_button("Download CSV", csv, file_name=f"{site_name}_PFAS_Polluter_Pays.csv", mime="text/csv")
