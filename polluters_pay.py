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
# PAGE CONFIG
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

# ======================
# Step 0: UK PFAS Plan Context
# ======================
with st.expander("📘 UK PFAS Plan: Vision for the Future"):
    st.markdown("""
The UK PFAS Plan provides strategic guidance for monitoring and managing PFAS contamination.  

It includes:  
- Future regulatory standards  
- Improved monitoring and thresholds  
- Stakeholder engagement  

**Note:** Current numeric thresholds in this app are based on UK EA guidance.  
Future statutory limits under the PFAS Plan may update these values.

Read the official plan: [UK PFAS Plan](https://www.gov.uk/government/publications/pfas-plan/pfas-plan-building-a-safer-future-together)
""")

# ======================
# Step 1: Site Information
# ======================
st.header("Step 1: Site Information")
c1, c2, c3 = st.columns(3)
with c1:
    site_name = st.text_input("Site name", value="My PFAS Site")
with c2:
    water_volume = st.number_input("Water volume to treat (m³)", min_value=0.0, value=1_000_000.0)
with c3:
    soil_mass = st.number_input("Soil mass to treat (tonnes)", min_value=0.0, value=10_000.0)

receptor_type = st.radio(
    "Receptor type (affects thresholds):",
    ["Drinking water", "Environmental / Surface water"],
    horizontal=True
)

jurisdiction = st.selectbox(
    "Regulatory jurisdiction:",
    ["UK (Environment Agency)", "EU (Drinking Water Directive)", "Australia (Guideline Values)", "USA (EPA 2024 MCLs)"]
)

# ======================
# Step 2: PFAS Concentrations
# ======================
st.header("Step 2: PFAS Concentrations")
conc_unit = st.selectbox("Concentration unit:", ["ng/L", "µg/L", "mg/L"], index=1)
UNIT_CONVERSION = {"ng/L":0.001,"µg/L":1,"mg/L":1000}

default_chains = ["PFOA", "PFOS", "PFHxS", "PFNA"]
use_general = st.checkbox("I do not have chain-specific PFAS data (use general PFAS)")
pfas_chains = ["General PFAS"] if use_general else default_chains

influent_pf = {}
cols = st.columns(len(pfas_chains))
for col, chain in zip(cols, pfas_chains):
    with col:
        val = st.number_input(f"{chain} concentration ({conc_unit})", min_value=0.0, value=10.0)
        influent_pf[chain] = val * UNIT_CONVERSION[conc_unit]

# ======================
# Step 3: Treatment Methods
# ======================
st.header("Step 3: Treatment Methods")

SCENARIOS = {
    "Conservative": {"description": "Higher costs, maximum caution", "cost_index": 1},
    "Moderate": {"description": "Balanced risk and cost", "cost_index": 0}
}
scenario_selection = st.radio(
    "Cost scenario:",
    [f"{k} – {v['description']}" for k,v in SCENARIOS.items()],
    horizontal=True
)
scenario_key = scenario_selection.split(" – ")[0]
cost_index = SCENARIOS[scenario_key]["cost_index"]

# Water methods
water_methods = {
    "GAC (Removal)": {"cost": (0.02,0.08),"type":"Removal","efficiency":(0.6,0.9),"secondary_waste":True,"waste_form":"spent carbon"},
    "Ion Exchange (Removal)": {"cost": (0.03,0.12),"type":"Removal","efficiency":(0.7,0.95),"secondary_waste":True,"waste_form":"resin brine"},
    "RO/NF (Removal)": {"cost": (0.05,0.20),"type":"Removal","efficiency":(0.8,0.99),"secondary_waste":True,"waste_form":"concentrate/brine"},
    "AOP (Destruction)": {"cost": (0.15,1.0),"type":"Destruction","efficiency":(0.7,0.99),"secondary_waste":False},
    "SCWO (Destruction)": {"cost": (6.8,25.5),"type":"Destruction","efficiency":(0.9,1.0),"secondary_waste":False}
}

# Soil methods
soil_methods = {
    "Excavate & Incinerate (Destruction)": {"cost": (50,250),"type":"Destruction","efficiency":(0.9,1.0),"secondary_waste":True,"waste_form":"incineration ash"},
    "Excavate & Hazardous Landfill (Removal)": {"cost": (50,250),"type":"Removal","efficiency":(0.3,0.5),"secondary_waste":True,"waste_form":"landfill soil"},
    "Soil Washing + SCWO/AOP (Destruction)": {"cost": (8,20),"type":"Destruction","efficiency":(0.7,0.95),"secondary_waste":False}
}

left_col, right_col = st.columns(2)
with left_col:
    if water_volume > 0:
        selected_water_method = st.selectbox("Select Water Method", list(water_methods.keys()))
        wm_info = water_methods[selected_water_method]
        st.markdown(f"**Type:** {wm_info['type']} | **Efficiency:** {wm_info['efficiency'][cost_index]*100:.0f}%")
        if wm_info.get("secondary_waste"):
            st.info(f"Generates secondary waste: {wm_info['waste_form']}")
    else:
        wm_info = None

    if soil_mass > 0:
        selected_soil_method = st.selectbox("Select Soil Method", list(soil_methods.keys()))
        sm_info = soil_methods[selected_soil_method]
        st.markdown(f"**Type:** {sm_info['type']} | **Efficiency:** {sm_info['efficiency'][cost_index]*100:.0f}%")
        if sm_info.get("secondary_waste"):
            st.info(f"Generates secondary waste: {sm_info['waste_form']}")
    else:
        sm_info = None

# ======================
# Step 4: Compliance Check
# ======================
st.header("Step 4: Compliance Check")

THRESHOLDS = {
    "UK (Environment Agency)": {"Drinking water":{"PFOA":0.4,"PFOS":0.015,"PFHxS":0.2,"PFNA":0.3,"General PFAS":0.4},
                                "Environmental / Surface water":{"PFOA":2,"PFOS":0.2,"PFHxS":0.5,"PFNA":0.6,"General PFAS":2}},
    "EU (Drinking Water Directive)": {"Drinking water":{c:0.1 for c in pfas_chains},"Environmental / Surface water":{c:0.5 for c in pfas_chains}},
    "Australia (Guideline Values)": {"Drinking water":{"PFOA":0.56,"PFOS":0.56,"PFHxS":0.1,"PFNA":0.07,"General PFAS":0.5},"Environmental / Surface water":{"PFOA":2,"PFOS":0.2,"PFHxS":0.5,"PFNA":0.6,"General PFAS":2}},
    "USA (EPA 2024 MCLs)": {"Drinking water":{"PFOA":0.004,"PFOS":0.004,"PFHxS":0.02,"PFNA":0.02,"General PFAS":0.01},"Environmental / Surface water":{"PFOA":0.01,"PFOS":0.01,"PFHxS":0.05,"PFNA":0.05,"General PFAS":0.02}}
}

thresholds = THRESHOLDS[jurisdiction][receptor_type]

def calc_residual(data, method):
    if method:
        return {k:v*(1-method["efficiency"][cost_index]) for k,v in data.items()}
    return data

res_water = calc_residual(influent_pf, wm_info)
res_soil  = calc_residual(influent_pf, sm_info)
res_combined = {k:min(res_water[k], res_soil[k]) for k in pfas_chains}

table=[]
hazard=0
for c in pfas_chains:
    r=res_combined[c]
    t=thresholds[c]
    hazard+=r/t
    table.append([c, r, t, "✅ Pass" if r<=t else "❌ Exceeds"])

st.table(pd.DataFrame(table, columns=["PFAS","Residual (µg/L)","Threshold (µg/L)","Status"]))
if hazard <=1:
    st.success(f"Hazard Index {hazard:.2f} — Compliant")
else:
    st.error(f"Hazard Index {hazard:.2f} — Exceeds")

# ======================
# Step 5: Cost Summary
# ======================
st.header("Step 5: Cost Summary")
cost_water = wm_info["cost"][cost_index]*water_volume if wm_info else 0
cost_soil = sm_info["cost"][cost_index]*soil_mass if sm_info else 0
grand_total = cost_water + cost_soil

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

st.download_button("Download Cost CSV", summary_df.to_csv(index=False), file_name=f"{site_name}_PFAS_Polluter_Pays.csv")

# ======================
# Step 6: PFAS Maps & Resources
# ======================
st.header("Step 6: PFAS Maps & Resources")
st.markdown("Use the following reliable links to view PFAS contamination maps:")

if jurisdiction.startswith("UK") or jurisdiction.startswith("EU"):
    st.markdown("- **EU PFAS Map (PDH Map):** [https://pdh.cnrs.fr/en/map/](https://pdh.cnrs.fr/en/map/)")
if jurisdiction.startswith("USA"):
    st.markdown("- **USA EPA PFAS Dashboard:** [https://www.epa.gov/pfas/pfas-data-dashboard](https://www.epa.gov/pfas/pfas-data-dashboard)")
if jurisdiction.startswith("Australia"):
    st.markdown("- **Australia PFAS Portal:** [https://www.pfasportal.org.au/](https://www.pfasportal.org.au/)")

st.info("Interactive maps may require external browser. Click links to view.")

