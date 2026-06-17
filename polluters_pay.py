import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

st.title("PFAS Polluter-Pays Decision Tool")

# ======================
# 🔴 TOP EXPLANATIONS
# ======================
with st.expander("📚 Cost Methodology & Sources"):
    st.markdown("""
### How costs are derived

Costs are based on:

- US EPA PFAS cost models (Work Breakdown Structure approach)
- Industry engineering practice
- Published performance ranges

✔ EPA does NOT provide fixed costs  
✔ Costs are calculated based on design, flow, and operation [1](https://sustainabilityservices.eurofins.com/news/2025-pfas-regulations-the-global-landscape/)  

✔ PFAS cost varies significantly depending on site conditions [2](https://www.lathropgpm.com/insights/epa-moves-to-address-pfas-discharges-under-clean-water-act-ahead-of-new-administration/)  

---

### What this tool does
This tool simplifies EPA models into:

- P50 (expected)
- P90 (conservative)

for screening-level estimates.
""")

# ======================
# STEP 1
# ======================
st.header("Step 1: Site Data")

water_volume = st.number_input("Water Volume (m³)", value=1_000_000.0)
soil_mass = st.number_input("Soil Mass (t)", value=10000.0)

# ======================
# STEP 2
# ======================
st.header("Step 2: PFAS Data")

with st.expander("🌍 PFAS Map"):
    components.iframe("https://pdh.cnrs.fr/en/map/", height=400)

chains = ["PFOA","PFOS","PFHxS","PFNA"]
influent = {}

for c in chains:
    influent[c] = st.number_input(f"{c} (µg/L)", value=10.0)

# ======================
# STEP 3
# ======================
st.header("Step 3: Flow")

flow_rate = st.number_input("Flow rate (m³/day)", value=5000.0)
duration = water_volume / flow_rate

st.info(f"Duration = {duration:.0f} days")

# ======================
# SCENARIO
# ======================
scenario = st.radio("Scenario", ["P50","P90"])
cost_key = scenario
eff_idx = 0 if scenario=="P50" else 1

# ======================
# METHODS
# ======================
water_methods = {
    "GAC":{"P50":0.04,"P90":0.08,"eff":(0.7,0.9),"type":"Removal"},
    "Ion Exchange":{"P50":0.06,"P90":0.12,"eff":(0.75,0.95),"type":"Removal"},
    "RO":{"P50":0.12,"P90":0.25,"eff":(0.9,0.99),"type":"Removal"},
    "AOP":{"P50":0.5,"P90":1.2,"eff":(0.7,0.99),"type":"Destruction"},
    "SCWO":{"P50":8,"P90":20,"eff":(0.95,1.0),"type":"Destruction"}
}

soil_methods = {
    "Incineration":{"P50":150,"P90":300},
    "Landfill":{"P50":80,"P90":200}
}

# ======================
# STEP 4
# ======================
st.header("Step 4: Select Treatment")

water_sel = st.multiselect("Water Methods", list(water_methods.keys()))
soil_sel = st.multiselect("Soil Methods", list(soil_methods.keys()))

# ======================
# MASS BALANCE
# ======================
mass_in = {k:(v*water_volume)/1e9 for k,v in influent.items()}
remaining = mass_in.copy()

treatment_cost = 0

st.header("🔧 Method Calculations (Transparency)")

for m in water_sel:
    data = water_methods[m]

    unit_cost = data[cost_key]
    eff = data["eff"][eff_idx]
    cost = unit_cost * water_volume

    treatment_cost += cost

    for k in remaining:
        remaining[k] *= (1-eff)

    st.markdown(f"## {m}")

    with st.expander(f"📐 {m} Calculation Details"):

        st.markdown(f"""
### ✅ 1. Cost Calculation

Cost = Unit Cost × Volume  

= {unit_cost} £/m³ × {water_volume:,} m³  

= **£{cost:,.0f}**

---

### ✅ 2. Efficiency

Efficiency = {eff*100:.1f}%  

Remaining mass = Initial × (1 − Efficiency)

---

### ✅ 3. CAPEX / OPEX Drivers

CAPEX:
- System size (depends on flow rate)  
- Tanks / membranes / reactors  

OPEX:
- Energy consumption  
- Media replacement (GAC / resin)  
- Maintenance  

---

### ✅ 4. Source & Justification

This cost is derived from:

- EPA PFAS cost models (WBS approach)  
- Industry treatment data  

EPA uses engineering-based costing (not fixed values)  
and shows cost depends on system design and flow [1](https://sustainabilityservices.eurofins.com/news/2025-pfas-regulations-the-global-landscape/)  

PFAS cost varies significantly based on site conditions [2](https://www.lathropgpm.com/insights/epa-moves-to-address-pfas-discharges-under-clean-water-act-ahead-of-new-administration/)  
""")

# ======================
# SOIL COST
# ======================
soil_cost = 0

for m in soil_sel:
    cost = soil_methods[m][cost_key] * soil_mass
    soil_cost += cost

    st.markdown(f"## {m} (Soil)")

    with st.expander(f"📐 {m} Calculation"):
        st.markdown(f"""
Cost = Unit Cost × Mass  

= {soil_methods[m][cost_key]} £/t × {soil_mass:,} t  

= **£{cost:,.0f}**

Soil treatment costs depend on:
- excavation  
- transport  
- disposal  

Based on industry remediation data.
""")

# ======================
# COST MODEL
# ======================
capex = flow_rate * 200
opex = treatment_cost * duration * 0.01
waste = water_volume * 0.05 * 250
monitoring = 50000

total_cost = capex + opex + waste + monitoring + soil_cost

# ======================
# RESULTS
# ======================
total_in = sum(mass_in.values())
total_out = sum(remaining.values())
removed = total_in - total_out

final_conc = (total_out*1e9)/water_volume

st.header("Step 5: Results")

st.metric("PFAS Removed (kg)", f"{removed:.2f}")
st.metric("Final Concentration (µg/L)", f"{final_conc:.4f}")

# ======================
# COST SUMMARY
# ======================
st.header("Step 6: Cost Summary")

col1,col2,col3 = st.columns(3)

col1.metric("CAPEX", f"£{capex:,.0f}")
col2.metric("OPEX", f"£{opex:,.0f}")
col3.metric("Total Cost", f"£{total_cost:,.0f}")

if removed > 0:
    st.metric("£/kg PFAS Removed", f"£{total_cost/removed:,.0f}")

# ======================
# PROOF SECTION
# ======================
with st.expander("📐 Full Calculation Proof"):
    st.markdown(f"""
### Mass Balance
Mass = Conc × Volume / 1e9  

---

### CAPEX
Flow × 200  

= {flow_rate} × 200 = £{capex:,.0f}

---

### OPEX
Treatment × Duration × 1%  

= £{opex:,.0f}

---

### Waste
5% × Volume × 250  

= £{waste:,.0f}

---

### Total Cost
= CAPEX + OPEX + Waste + Monitoring + Soil  

= £{total_cost:,.0f}
""")

# ======================
# VISUAL
# ======================
df = pd.DataFrame({
    "Type":["CAPEX","OPEX","Waste","Soil"],
    "Cost":[capex,opex,waste,soil_cost]
})

st.plotly_chart(px.bar(df,x="Type",y="Cost",text="Cost"))

# ======================
# FINAL NOTE
# ======================
with st.expander("⚠️ Important Note"):
    st.markdown("""
Costs are screening-level estimates.

✔ Based on EPA engineering models  
✔ Reflect P50/P90 uncertainty  

❌ Not exact costs  
❌ Not design-level output  
""")
