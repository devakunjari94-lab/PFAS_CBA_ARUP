import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(page_title="PFAS Decision Support Tool", layout="wide")

PASSWORD = "PFAS2026"
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title('🔐 PFAS Tool Login')
    pw = st.text_input('Password', type='password')
    if st.button('Login'):
        if pw == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error('Incorrect password')
    st.stop()

st.title('PFAS Polluter-Pays Decision Support Tool')

with st.expander('⚠ Scope & Limitations'):
    st.write('Screening-level estimates only.')

st.header('Scenario')
scenario = st.selectbox('Scenario',['Optimistic','Average','Conservative'])
uncertainty = st.slider('Uncertainty (%)',0,100,50)

st.header('Site Information')
col1,col2 = st.columns(2)
water_volume = col1.number_input('Water Volume (m3)',value=1000000.0)
flow_rate = col2.number_input('Flow Rate (m3/day)',value=5000.0)

st.header('PFAS Global Map')
components.iframe('https://pdh.cnrs.fr/en/map/',height=700,scrolling=True)

st.header('PFAS Data')
use_general = st.checkbox("I don't know individual PFAS compounds - Use Total PFAS")

influent = {}
if use_general:
    influent['Total PFAS'] = st.number_input('Total PFAS (ug/L)',value=10.0)
else:
    influent['PFOA'] = st.number_input('PFOA (ug/L)',value=5.0)
    influent['PFOS'] = st.number_input('PFOS (ug/L)',value=5.0)
    influent['PFHxS'] = st.number_input('PFHxS (ug/L)',value=1.0)
    influent['PFNA'] = st.number_input('PFNA (ug/L)',value=1.0)
    influent['GenX'] = st.number_input('GenX (ug/L)',value=0.0)

st.header('Potential Source')
source = st.selectbox('Source',['Unknown','AFFF','Airport','Landfill','Chemical Manufacturing','Textiles','Metal Plating','WWTW'])

st.header('Location')
lat = st.number_input('Latitude',value=51.5074)
lon = st.number_input('Longitude',value=-0.1278)
st.map(pd.DataFrame({'lat':[lat],'lon':[lon]}))

st.header('Regulatory Compliance')
targets = {'UK DWI':0.1,'EU DWD':0.5,'EPA':0.004}
target_name = st.selectbox('Target',list(targets.keys()))
target_limit = targets[target_name]

st.header('Treatment Train')
selected_methods = st.multiselect('Technologies',['GAC','Ion Exchange','RO','AOP'],default=['GAC'])

tech_eff = {
'PFOA':{'GAC':0.92,'Ion Exchange':0.96,'RO':0.99,'AOP':0.7},
'PFOS':{'GAC':0.98,'Ion Exchange':0.99,'RO':0.99,'AOP':0.75},
'PFHxS':{'GAC':0.85,'Ion Exchange':0.95,'RO':0.99,'AOP':0.65},
'PFNA':{'GAC':0.9,'Ion Exchange':0.96,'RO':0.99,'AOP':0.7},
'GenX':{'GAC':0.4,'Ion Exchange':0.8,'RO':0.95,'AOP':0.6}}

generic_eff = {'GAC':0.8,'Ion Exchange':0.9,'RO':0.98,'AOP':0.75}

tech_cost = {
'GAC':(0.02,0.20),
'Ion Exchange':(0.03,0.12),
'RO':(0.05,0.25),
'AOP':(0.50,1.00)}

remaining = {}
removed_total = 0
for c,v in influent.items():
    current=v
    for m in selected_methods:
        eff = generic_eff[m] if c=='Total PFAS' else tech_eff[c][m]
        current *= (1-eff)
    remaining[c]=current
    mass_in=v*water_volume/1e9
    mass_out=current*water_volume/1e9
    removed_total += (mass_in-mass_out)

final_conc=sum(remaining.values())

cost_per_m3=0
for m in selected_methods:
    best,worst=tech_cost[m]
    if scenario=='Optimistic': val=best
    elif scenario=='Conservative': val=worst
    else: val=best+(worst-best)*(uncertainty/100)
    cost_per_m3+=val

treatment_cost=cost_per_m3*water_volume
capex=flow_rate*200
opex=treatment_cost*0.01
waste=water_volume*0.05*250

total_cost=capex+opex+waste

carbon_factors={'GAC':0.2,'Ion Exchange':0.15,'RO':0.8,'AOP':1.2}
carbon=sum(carbon_factors[m]*water_volume for m in selected_methods)

cost_per_kg= total_cost/max(removed_total,1e-6)
liability=cost_per_kg*removed_total

st.header('Results')
if final_conc<=target_limit:
    st.success(f'Compliant with {target_name}')
else:
    st.error(f'Exceeds {target_name}')

c1,c2,c3,c4=st.columns(4)
c1.metric('PFAS Removed (kg)',f'{removed_total:.3f}')
c2.metric('Final PFAS (ug/L)',f'{final_conc:.4f}')
c3.metric('Total Cost (£)',f'{total_cost:,.0f}')
c4.metric('Carbon (kgCO2e)',f'{carbon:,.0f}')

st.header('Polluter Pays')
st.metric('Estimated Liability (£)',f'{liability:,.0f}')

cost_df=pd.DataFrame({'Category':['CAPEX','OPEX','Waste'],'Cost':[capex,opex,waste]})
st.plotly_chart(px.pie(cost_df,names='Category',values='Cost'),use_container_width=True)

mc=np.random.triangular(cost_per_m3*0.5,cost_per_m3,cost_per_m3*1.5,10000)
st.plotly_chart(px.histogram(pd.DataFrame({'Cost':mc}),x='Cost'),use_container_width=True)

st.header('Summary')
st.table(pd.DataFrame({'Metric':['Source','Treatment Train','Final PFAS','Total Cost'], 'Value':[source,' -> '.join(selected_methods),f'{final_conc:.4f}',f'£{total_cost:,.0f}']}))
