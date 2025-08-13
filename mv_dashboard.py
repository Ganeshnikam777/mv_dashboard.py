import streamlit as st
import pandas as pd
import altair as alt
import os

st.set_page_config(page_title="📊 M&V Energy Dashboard", layout="wide")
st.title("📊 Measurement & Verification Dashboard")
st.markdown("Compare monthly energy savings across projects using your uploaded data.")

# Upload File
uploaded_file = st.file_uploader("Upload your energy data file", type=["csv", "xlsx", "json", "txt"])

if uploaded_file:
    file_type = os.path.splitext(uploaded_file.name)[-1].lower()

    try:
        if file_type == ".csv":
            df = pd.read_csv(uploaded_file, parse_dates=["month"])
        elif file_type == ".xlsx":
            df = pd.read_excel(uploaded_file, parse_dates=["month"])
        elif file_type == ".json":
            df = pd.read_json(uploaded_file)
            df["month"] = pd.to_datetime(df["month"])
        elif file_type == ".txt":
            df = pd.read_csv(uploaded_file, delimiter="\t", parse_dates=["month"])
        else:
            st.error("⚠️ Unsupported file format.")
            st.stop()
    except Exception as e:
        st.error(f"❌ Failed to load file: {e}")
        st.stop()

    # Preview uploaded data
    st.subheader("🔍 Uploaded Data Preview")
    st.dataframe(df.head())

    # Check required columns
    required_columns = {"month", "project", "meter_id", "baseline_kwh", "reporting_kwh", "target_saving_kwh"}
    if not required_columns.issubset(df.columns):
        st.error(f"Missing required columns. Required: {required_columns}")
        st.stop()

    # Calculate actual savings
    df["actual_saving_kwh"] = df["baseline_kwh"] - df["reporting_kwh"]

    # Group by month and project
    summary = df.groupby(["month", "project"]).agg({
        "actual_saving_kwh": "sum",
        "target_saving_kwh": "sum"
    }).reset_index()

    # Plot actual vs target savings
    st.subheader("📈 Energy Savings Comparison")
    actual_chart = alt.Chart(summary).mark_line(point=True).encode(
        x="month:T",
        y="actual_saving_kwh:Q",
        color="project:N",
        tooltip=["month", "project", "actual_saving_kwh"]
    ).properties(title="Actual Energy Savings (kWh)")

    target_chart = alt.Chart(summary).mark_line(point=True, strokeDash=[5, 5]).encode(
        x="month:T",
        y="target_saving_kwh:Q",
        color="project:N",
        tooltip=["month", "project", "target_saving_kwh"]
    )

    st.altair_chart(actual_chart + target_chart, use_container_width=True)

    # Show summary table
    st.subheader("📋 Monthly Summary Table")
    st.dataframe(summary.style.format({"actual_saving_kwh": "{:.0f}", "target_saving_kwh": "{:.0f}"}))
else:
    st.info("📁 Upload a file to get started.")
