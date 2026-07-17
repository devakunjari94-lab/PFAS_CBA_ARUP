import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import streamlit.components.v1 as components

st.set_page_config(page_title="PFAS Decision Support Tool", layout="wide")

PASSWORD="PFAS2026"
if "auth" not in st.session_state:
    st.session_state.auth=False
if not st.session_state.auth:
    st.title("PFAS Tool Login")
    pw=st.text_input("Password",type="password")
    if st.button("Login"):
        if pw==PASSWORD:
            st.session_state.auth=True
            st.rerun()
        else:
            st.error("Incorrect Password")
    st.stop()

st.title("PFAS Decision Support Tool")
media=st.radio("Media",["Water","Soil"])
scenario=st.selectbox("Scenario",["Optimistic","Average","Conservative"])
uncertainty=st.slider("Uncertainty %",0,100,50)

if media=="Water":
    water_volume=st.number_input("Water Volume (m3)",1000000.0)
    flow_rate=st.number_input("Flow Rate (m3/day)",5000.0)
else:
    soil_mass=st.number_input("Soil Mass (tonnes)",10000.0)

conc=st.number_input("PFAS Concentration",10.0)
source=st.selectbox("Source",["Unknown","AFFF","Airport","Landfill","WWTW"])

if media=="Water":
    targets={"UK DWI":0.1,"EU DWD":0.5,"EPA":0.004}
    units="ug/L"
    techs=["GAC","Ion Exchange","RO","AOP"]
    costs={"GAC":(0.02,0.2),"Ion Exchange":(0.03,0.12),"RO":(0.05,0.25),"AOP":(0.5,1)}
    effs={"GAC":0.8,"Ion Exchange":0.9,"RO":0.98,"AOP":0.75}
else:
    targets={"Residential":0.01,"Commercial":0.1,"Industrial":1.0}
    units="mg/kg"
    techs=["Excavation + Disposal","Soil Washing","Thermal Desorption","Solidification/Stabilisation"]
    costs={"Excavation + Disposal":(100,350),"Soil Washing":(50,180),"Thermal Desorption":(250,700),"Solidification/Stabilisation":(60,180)}
    effs={"Excavation + Disposal":0.95,"Soil Washing":0.7,"Thermal Desorption":0.99,"Solidification/Stabilisation":0.6}

selected=st.multiselect("Technologies",techs,default=[techs[0]])
target=st.selectbox("Target",list(targets.keys()))

final_conc=conc
for t in selected:
    final_conc*=1-effs[t]

cost_factor=0
for t in selected:
    best,worst=costs[t]
    val=best if scenario=="Optimistic" else worst if scenario=="Conservative" else best+(worst-best)*uncertainty/100
    cost_factor+=val

if media=="Water":
    treatment_cost=cost_factor*water_volume
    capex=flow_rate*200
    waste=water_volume*0.05*250
else:
    treatment_cost=cost_factor*soil_mass
    capex=soil_mass*10
    waste=soil_mass*50

opx=treatment_cost*0.01
total_cost=capex+opx+waste

st.success("Compliant") if final_conc<=targets[target] else st.error("Non-compliant")

summary=pd.DataFrame({"Metric":["Media","Source","Final PFAS","Total Cost"],"Value":[media,source,f"{final_conc:.4f} {units}",f"£{total_cost:,.0f}"]})

st.dataframe(summary,use_container_width=True)
fig=px.bar(pd.DataFrame({'Category':['CAPEX','OPEX','Waste'],'Cost':[capex,opx,waste]}),x='Category',y='Cost',color='Category')
st.plotly_chart(fig,use_container_width=True)

csv=summary.to_csv(index=False)
st.download_button('Download CSV',csv,'PFAS_Report.csv','text/csv')

xlsx=BytesIO()
with pd.ExcelWriter(xlsx,engine='openpyxl') as writer:
    summary.to_excel(writer,index=False,sheet_name='Summary')
st.download_button('Download Excel',xlsx.getvalue(),'PFAS_Report.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

html=f"<h1>PFAS Report</h1><p>Media: {media}</p><p>Source: {source}</p><p>Final PFAS: {final_conc:.4f} {units}</p><p>Total Cost: £{total_cost:,.0f}</p>"
components.html(html,height=250)
st.download_button('Download HTML',html,'PFAS_Report.html','text/html')
