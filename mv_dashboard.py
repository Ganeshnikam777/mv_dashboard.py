import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="M&V Energy Dashboard", layout="wide")

st.title("📊 Measurement & Verification Dashboard")
st.markdown("Compare monthly energy savings across projects.")

# Upload CSV
uploaded_file = st.file_uploader("Upload monthly energy data CSV", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=["month"])

    # Calculate actual savings
    df["actual_saving_kwh"] = df["baseline_kwh"] - df["reporting_kwh"]

    # Aggregate by month and project
    summary = df.groupby(["month", "project"]).agg({
        "actual_saving_kwh": "sum",
        "target_saving_kwh": "sum"
    }).reset_index()

    # Plot savings comparison
    st.subheader("📈 Energy Savings Comparison")
    chart = alt.Chart(summary).mark_line(point=True).encode(
        x="month:T",
        y="actual_saving_kwh:Q",
        color="project:N",
        tooltip=["month", "project", "actual_saving_kwh", "target_saving_kwh"]
    ).properties(title="Actual Energy Savings (kWh)")

    target_chart = alt.Chart(summary).mark_line(point=True, strokeDash=[5,5]).encode(
        x="month:T",
        y="target_saving_kwh:Q",
        color="project:N",
        tooltip=["month", "project", "actual_saving_kwh", "target_saving_kwh"]
    )

    st.altair_chart(chart + target_chart, use_container_width=True)

    # Show data table
    st.subheader("📋 Monthly Summary Table")
    st.dataframe(summary.style.format({"actual_saving_kwh": "{:.0f}", "target_saving_kwh": "{:.0f}"}))
else:
    st.info("Please upload a CSV file to begin.")
