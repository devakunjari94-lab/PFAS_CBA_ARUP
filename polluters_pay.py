# =====================================
# PFAS DATA
# =====================================

st.header("Step 2: PFAS Data")

with st.expander("🌍 Global PFAS Contamination Map"):

    st.markdown(
        """
        Interactive PFAS contamination map maintained by CNRS.

        If the embedded map does not load,
        click the link below.
        """
    )

    st.markdown(
        "[Open CNRS PFAS Map](https://pdh.cnrs.fr/en/map/)"
    )

    components.iframe(
        "https://pdh.cnrs.fr/en/map/",
        height=900,
        scrolling=True
    )

# ---------------------
# PFAS INPUT MODE
# ---------------------

use_general = st.checkbox(
    "I don't know individual PFAS compounds - Use Total PFAS"
)

influent = {}

if use_general:

    st.warning(
        """
        PFAS composition is unknown.

        Generic removal efficiencies are used.

        Results should be considered
        screening-level estimates only.
        """
    )

    influent["Total PFAS"] = st.number_input(
        "Total PFAS (µg/L)",
        value=10.0,
        min_value=0.0
    )

else:

    influent["PFOA"] = st.number_input(
        "PFOA (µg/L)",
        value=5.0,
        min_value=0.0
    )

    influent["PFOS"] = st.number_input(
        "PFOS (µg/L)",
        value=5.0,
        min_value=0.0
    )

    with st.expander("Additional PFAS"):

        influent["PFHxS"] = st.number_input(
            "PFHxS (µg/L)",
            value=0.0,
            min_value=0.0
        )

        influent["PFNA"] = st.number_input(
            "PFNA (µg/L)",
            value=0.0,
            min_value=0.0
        )

        influent["GenX"] = st.number_input(
            "GenX (µg/L)",
            value=0.0,
            min_value=0.0
        )
