import os
from io import BytesIO
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit.components.v1 as components
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

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
            st.error("Incorrect password")
    st.stop()

logo_path = "arup_logo.png"
col1,col2 = st.columns([1,4])
with col1:
    if os.path.exists(logo_path):
        st.image(logo_path,width=140)
with col2:
    st.title("PFAS Polluter-Pays Decision Support Tool")
    st.caption("Screening-Level PFAS Treatment, Compliance and Liability Assessment")

with st.expander("⚠ Scope & Limitations"):
    st.write("Screening-level estimates only.")

scenario = st.selectbox("Scenario", ["Optimistic","Average","Conservative"])
uncertainty = st.slider("Uncertainty (%)",0,100,50)

c1,c2 = st.columns(2)
water_volume = c1.number_input("Water Volume (m³)", value=1000000.0)
flow_rate = c2.number_input("Flow Rate (m³/day)", value=5000.0)

st.header("🌍 Global PFAS Intelligence Map")
components.iframe("https://pdh.cnrs.fr/en/map/", height=600, scrolling=True)

use_general = st.checkbox("I don't know individual PFAS compounds (Use Total PFAS)")
influent = {}

if use_general:
    influent["Total PFAS"] = st.number_input("Total PFAS (µg/L)", value=10.0)
else:
    influent["PFOA"] = st.number_input("PFOA (µg/L)", value=5.0)
    influent["PFOS"] = st.number_input("PFOS (µg/L)", value=5.0)
    influent["PFHxS"] = st.number_input("PFHxS (µg/L)", value=1.0)
    influent["PFNA"] = st.number_input("PFNA (µg/L)", value=1.0)
    influent["GenX"] = st.number_input("GenX (µg/L)", value=0.0)

source = st.selectbox("Source", ["Unknown","AFFF","Airport","Landfill","Chemical Manufacturing","Textiles","Metal Plating","WWTW"])

targets = {"UK DWI":0.1,"EU DWD":0.5,"EPA":0.004}
target_name = st.selectbox("Regulatory Target", list(targets.keys()))
target_limit = targets[target_name]

selected_methods = st.multiselect("Treatment Technologies", ["GAC","Ion Exchange","RO","AOP"], default=["GAC"])

tech_eff = {
'PFOA':{'GAC':0.92,'Ion Exchange':0.96,'RO':0.99,'AOP':0.7},
'PFOS':{'GAC':0.98,'Ion Exchange':0.99,'RO':0.99,'AOP':0.75},
'PFHxS':{'GAC':0.85,'Ion Exchange':0.95,'RO':0.99,'AOP':0.65},
'PFNA':{'GAC':0.90,'Ion Exchange':0.96,'RO':0.99,'AOP':0.70},
'GenX':{'GAC':0.40,'Ion Exchange':0.80,'RO':0.95,'AOP':0.60}}

generic_eff={'GAC':0.8,'Ion Exchange':0.9,'RO':0.98,'AOP':0.75}
tech_cost={'GAC':(0.02,0.20),'Ion Exchange':(0.03,0.12),'RO':(0.05,0.25),'AOP':(0.50,1.00)}

remaining={}
removed_total=0
for c,v in influent.items():
    current=v
    for m in selected_methods:
        eff = generic_eff[m] if c=='Total PFAS' else tech_eff[c][m]
        current *= (1-eff)
    remaining[c]=current
    removed_total += ((v-current)*water_volume/1e9)

final_conc=sum(remaining.values())

cost_per_m3=0
for m in selected_methods:
    best,worst=tech_cost[m]
    if scenario=='Optimistic':
        val=best
    elif scenario=='Conservative':
        val=worst
    else:
        val=best+((worst-best)*(uncertainty/100))
    cost_per_m3+=val

treatment_cost=cost_per_m3*water_volume
capex=flow_rate*200
opex=treatment_cost*0.01
waste=water_volume*0.05*250
total_cost=capex+opex+waste

carbon_factors={'GAC':0.2,'Ion Exchange':0.15,'RO':0.8,'AOP':1.2}
carbon=sum(carbon_factors[m]*water_volume for m in selected_methods)
carbon_cost=(carbon/1000)*80

mass_remaining=final_conc*water_volume/1e9
removal_efficiency=(removed_total/max(removed_total+mass_remaining,1e-6))*100
unit_cost=total_cost/water_volume
liability=total_cost

st.header('Compliance')
if final_conc <= target_limit:
    st.success(f'✅ Compliant with {target_name}')
else:
    st.error(f'❌ Exceeds {target_name}')

st.header('Executive Dashboard')
cols=st.columns(4)
cols[0].metric('PFAS Removed (kg)',f'{removed_total:.3f}')
cols[1].metric('Final PFAS (µg/L)',f'{final_conc:.4f}')
cols[2].metric('Removal Efficiency (%)',f'{removal_efficiency:.1f}')
cols[3].metric('Total Cost (£)',f'{total_cost:,.0f}')
cols=st.columns(4)
cols[0].metric('Unit Cost (£/m³)',f'{unit_cost:.2f}')
cols[1].metric('Carbon (kgCO2e)',f'{carbon:,.0f}')
cols[2].metric('Carbon Cost (£)',f'{carbon_cost:,.0f}')
cols[3].metric('Liability (£)',f'{liability:,.0f}')

cost_df=pd.DataFrame({'Category':['CAPEX','OPEX','Waste'],'Cost':[capex,opex,waste]})
st.plotly_chart(px.bar(cost_df,x='Category',y='Cost',color='Category'), use_container_width=True)

mc=np.random.triangular(cost_per_m3*0.5,cost_per_m3,cost_per_m3*1.5,10000)
st.plotly_chart(px.histogram(pd.DataFrame({'Cost':mc}),x='Cost'), use_container_width=True)

st.header('Recommendation')
if final_conc <= target_limit:
    st.success('Recommended treatment train.')
else:
    st.error('Treatment train does not achieve compliance.')

def create_pdf():
    buffer=BytesIO()
    doc=SimpleDocTemplate(buffer)
    styles=getSampleStyleSheet()
    story=[Paragraph('PFAS Decision Support Report',styles['Title']),Spacer(1,12),
           Paragraph(f'Source: {source}',styles['Normal']),
           Paragraph(f'Final PFAS: {final_conc:.4f} µg/L',styles['Normal']),
           Paragraph(f'Total Cost: £{total_cost:,.0f}',styles['Normal']),
           Paragraph(f'Carbon: {carbon:,.0f} kgCO2e',styles['Normal'])]
    doc.build(story)
    pdf=buffer.getvalue()
    buffer.close()
    return pdf

st.download_button('📄 Download PDF Report', create_pdf(), 'PFAS_Report.pdf', 'application/pdf')
