import os
import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(page_title="PFAS Decision Support Tool", layout="wide")

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

st.title("PFAS Decision Support Tool")
st.caption("Screening-Level PFAS Treatment, Compliance and Liability Assessment")

with st.expander("⚠ Scope & Limitations"):
    st.markdown("""
    Screening-level estimates only.

    Suitable for:
    - Early-stage planning
    - Technology comparison
    - Option screening
    - Liability assessments
    """)

st.header("Environmental Media")
media = st.radio("Select Media", ["Water", "Soil"])

st.header("Scenario")
scenario = st.selectbox("Cost Scenario", ["Optimistic", "Average", "Conservative"])
uncertainty = st.slider("Uncertainty (%)", 0, 100, 50)

st.header("Site Information")
if media == "Water":
    c1, c2 = st.columns(2)
    water_volume = c1.number_input("Water Volume (m³)", value=1000000.0)
    flow_rate = c2.number_input("Flow Rate (m³/day)", value=5000.0)
else:
    c1, c2 = st.columns(2)
    soil_mass = c1.number_input("Contaminated Soil Mass (tonnes)", value=10000.0)
    excavation_depth = c2.number_input("Excavation Depth (m)", value=2.0)

st.header("🌍 Global PFAS Intelligence Map")
st.markdown("https://pdh.cnrs.fr/en/map/")
components.iframe("https://pdh.cnrs.fr/en/map/", height=600)

st.header("PFAS Data")
use_general = st.checkbox("Use Total PFAS", value=True)

influent = {}
if use_general:
    influent["Total PFAS"] = st.number_input("PFAS Concentration", value=10.0)
else:
    influent["PFOA"] = st.number_input("PFOA", value=5.0)
    influent["PFOS"] = st.number_input("PFOS", value=5.0)
    influent["PFHxS"] = st.number_input("PFHxS", value=1.0)
    influent["PFNA"] = st.number_input("PFNA", value=1.0)
    influent["GenX"] = st.number_input("GenX", value=0.0)

st.header("Potential Source")
source = st.selectbox("Source", ["Unknown", "AFFF", "Airport", "Landfill", "Chemical Manufacturing", "Textiles", "Metal Plating", "WWTW"])

if media == "Water":
    targets = {"UK DWI":0.1,"EU DWD":0.5,"EPA":0.004}
    units = "µg/L"
else:
    targets = {"Residential":0.01,"Commercial":0.1,"Industrial":1.0}
    units = "mg/kg"

target_name = st.selectbox("Compliance Target", list(targets.keys()))
target_limit = targets[target_name]

st.header("Treatment Train")
if media == "Water":
    techs = ["GAC","Ion Exchange","RO","AOP"]
else:
    techs = ["Excavation + Disposal","Soil Washing","Thermal Desorption","Solidification/Stabilisation"]

selected_methods = st.multiselect("Technologies", techs, default=[techs[0]])

tech_eff = {
    "PFOA":{"GAC":0.92,"Ion Exchange":0.96,"RO":0.99,"AOP":0.70},
    "PFOS":{"GAC":0.98,"Ion Exchange":0.99,"RO":0.99,"AOP":0.75},
    "PFHxS":{"GAC":0.85,"Ion Exchange":0.95,"RO":0.99,"AOP":0.65},
    "PFNA":{"GAC":0.90,"Ion Exchange":0.96,"RO":0.99,"AOP":0.70},
    "GenX":{"GAC":0.40,"Ion Exchange":0.80,"RO":0.95,"AOP":0.60}
}

generic_eff = {"GAC":0.80,"Ion Exchange":0.90,"RO":0.98,"AOP":0.75}
soil_eff = {"Excavation + Disposal":0.95,"Soil Washing":0.70,"Thermal Desorption":0.99,"Solidification/Stabilisation":0.60}

tech_cost = {"GAC":(0.02,0.20),"Ion Exchange":(0.03,0.12),"RO":(0.05,0.25),"AOP":(0.50,1.00)}
soil_cost = {"Excavation + Disposal":(100,350),"Soil Washing":(50,180),"Thermal Desorption":(250,700),"Solidification/Stabilisation":(60,180)}

remaining = {}
removed_total = 0
for compound, conc in influent.items():
    current = conc
    for method in selected_methods:
        if media == "Water":
            eff = generic_eff[method] if compound == "Total PFAS" else tech_eff[compound][method]
        else:
            eff = soil_eff[method]
        current *= (1-eff)
    remaining[compound] = current

    if media == "Water":
        mass_in = conc * water_volume / 1e9
        mass_out = current * water_volume / 1e9
    else:
        mass_in = conc * soil_mass * 1000 / 1e9
        mass_out = current * soil_mass * 1000 / 1e9

    removed_total += (mass_in - mass_out)

final_conc = sum(remaining.values())

cost_factor = 0
for method in selected_methods:
    best, worst = (tech_cost[method] if media == 'Water' else soil_cost[method])
    if scenario == 'Optimistic':
        val = best
    elif scenario == 'Conservative':
        val = worst
    else:
        val = best + ((worst-best)*uncertainty/100)
    cost_factor += val

if media == 'Water':
    treatment_cost = cost_factor * water_volume
    capex = flow_rate * 200
    waste = water_volume * 0.05 * 250
else:
    treatment_cost = cost_factor * soil_mass
    capex = soil_mass * 10
    waste = soil_mass * 50

opex = treatment_cost * 0.01
total_cost = capex + opex + waste

if final_conc <= target_limit:
    st.success(f'✅ Compliant with {target_name}')
else:
    st.error(f'❌ Exceeds {target_name}')

st.header('Executive Dashboard')
col1,col2,col3,col4 = st.columns(4)
col1.metric('PFAS Removed', f'{removed_total:.3f}')
col2.metric(f'Final PFAS ({units})', f'{final_conc:.4f}')
col3.metric('Technologies', len(selected_methods))
col4.metric('Total Cost (£)', f'{total_cost:,.0f}')

cost_df = pd.DataFrame({'Category':['CAPEX','OPEX','Waste'],'Cost':[capex,opex,waste]})
fig = px.bar(cost_df,x='Category',y='Cost',color='Category')
st.plotly_chart(fig, use_container_width=True)

st.header('Summary')
st.table(pd.DataFrame({
'Metric':['Media','Source','Treatment Train','Final PFAS','Total Cost'],
'Value':[media,source,' -> '.join(selected_methods),f'{final_conc:.4f} {units}',f'£{total_cost:,.0f}']
}))

st.header('Export Report')
report_html = f'<h1>PFAS Report</h1><p>Media: {media}</p><p>Source: {source}</p><p>Total Cost: £{total_cost:,.0f}</p>'
components.html(report_html, height=300)

