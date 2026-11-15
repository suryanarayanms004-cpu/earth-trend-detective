import streamlit as st
import pandas as pd
import requests
from scipy import stats
import plotly.express as px

st.set_page_config(page_title="Earth System Trend Detective", layout="wide")
st.title("🌍 Earth System Trend Detective")
st.markdown("Analyze 10+ years of **NASA POWER** satellite data to uncover significant environmental trends and regional contrasts.")

LOCATIONS = {
    "Thiruvananthapuram, India (Tropical Coast)": (8.5241, 76.9366),
    "Jaisalmer, India (Arid Desert)": (26.9157, 70.9083),
    "Manaus, Brazil (Amazon Rainforest)": (-3.1190, -60.0217),
    "Fresno, California (Agricultural Valley)": (36.7378, -119.7871),
    "Custom Coordinates": (0.0, 0.0)
}

VARIABLES = {
    "Surface Temperature (°C)": "T2M",
    "Precipitation / Rainfall (mm/day)": "PRECTOTCORR",
    "Root Zone Soil Wetness (0-1 scale)": "GWETROOT"
}

@st.cache_data
def fetch_nasa_data(lat, lon, start_year, end_year, param):
    url = f"https://nasa.gov{param}&community=AG&longitude={lon}&latitude={lat}&start={start_year}&end={end_year}&format=JSON"
    res = requests.get(url).json()
    data = res["properties"]["parameter"][param]
    df = pd.DataFrame(list(data.items()), columns=["Year", "Value"])
    df["Year"] = df["Year"].astype(int)
    df = df[df["Value"] > -900]
    return df

def analyze_trend(df):
    slope, intercept, r_val, p_val, std_err = stats.linregress(df["Year"], df["Value"])
    total_change = slope * (df["Year"].max() - df["Year"].min())
    is_sig = p_val < 0.05
    return slope, total_change, p_val, is_sig

st.sidebar.header("🔍 Detective Controls")
selected_var_name = st.sidebar.selectbox("1. Select Earth Variable", list(VARIABLES.keys()))
param_code = VARIABLES[selected_var_name]
year_range = st.sidebar.slider("2. Select Decade Range", 2005, 2025, (2014, 2024))
compare_mode = st.sidebar.checkbox("Enable Side-by-Side Region Comparison", value=True)

def render_region_panel(col, label, default_idx):
    with col:
        st.subheader(label)
        loc_choice = st.selectbox(f"Choose Location ({label})", list(LOCATIONS.keys()), index=default_idx, key=label)
        if loc_choice == "Custom Coordinates":
            lat = st.number_input("Latitude", value=8.52, key=f"lat_{label}")
            lon = st.number_input("Longitude", value=76.93, key=f"lon_{label}")
        else:
            lat, lon = LOCATIONS[loc_choice]

        with st.spinner("Fetching NASA Satellite Data..."):
            df = fetch_nasa_data(lat, lon, year_range[0], year_range[1], param_code)
            slope, total_change, p_val, is_sig = analyze_trend(df)

            direction = "increased" if total_change > 0 else "decreased"
            var_clean = selected_var_name.split(" (")[0].lower()
            if is_sig:
                st.success(f"**DETECTIVE VERDICT: Significant Trend Detected (p = {p_val:.3f})**\n\nOver this period, {var_clean} **{direction} by {abs(total_change):.2f}** units. This is a statistically real shift, not random weather noise.")
            else:
                st.info(f"**DETECTIVE VERDICT: Normal Fluctuation (p = {p_val:.3f})**\n\nAlthough values shifted by **{total_change:+.2f}**, year-to-year swings mean this trend is not yet statistically significant.")

            fig = px.scatter(df, x="Year", y="Value", trendline="ols", title=f"{selected_var_name} ({year_range[0]}–{year_range[1]})")
            fig.update_traces(mode="lines+markers")
            st.plotly_chart(fig, use_container_width=True)

if compare_mode:
    col1, col2 = st.columns(2)
    render_region_panel(col1, "Region A", 0)
    render_region_panel(col2, "Region B", 1)
else:
    render_region_panel(st.container(), "Target Region", 0)
