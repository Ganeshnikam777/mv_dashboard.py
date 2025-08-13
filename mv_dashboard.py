import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="📊 M&V Master Dashboard", layout="wide")
st.title("📊 Hourly Measurement & Verification Dashboard")
st.markdown("Upload hourly energy data and input model parameters to analyze savings per meter.")

# Upload Excel file
uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Validate required columns
        meter_cols = ["M1", "M2", "M3", "M4", "M5"]
        required_cols = set(meter_cols + ["timestamp", "CDD"])
        if not required_cols.issubset(df.columns):
            st.error(f"Missing columns. Required: {required_cols}")
            st.stop()

        # Convert timestamp
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"] = df["timestamp"].dt.date

        # Sidebar inputs
        st.sidebar.header("📌 Model Parameters")
        m = st.sidebar.number_input("Enter model coefficient m", value=1.2)
        C = st.sidebar.number_input("Enter model constant C", value=50.0)

        st.sidebar.header("🎯 Monthly Target Savings (kWh)")
        target_savings = {}
        for meter in meter_cols:
            target_savings[meter] = st.sidebar.number_input(f"Target for {meter}", value=1000)

        # Melt meter columns
        long_df = df.melt(id_vars=["timestamp", "CDD", "date"], value_vars=meter_cols,
                          var_name="meter_id", value_name="reporting_kwh")

        # Apply model
        long_df["baseline_kwh"] = m * long_df["CDD"] + C
        long_df["actual_saving_kwh"] = long_df["baseline_kwh"] - long_df["reporting_kwh"]
        long_df["target_saving_kwh"] = long_df["meter_id"].map(target_savings)

        # Daily summary
        daily_summary = long_df.groupby(["date", "meter_id"]).agg({
            "reporting_kwh": "sum",
            "baseline_kwh": "sum",
            "actual_saving_kwh": "sum",
            "target_saving_kwh": "mean"
        }).reset_index()

        # Cumulative savings
        daily_summary["cumulative_actual"] = daily_summary.groupby("meter_id")["actual_saving_kwh"].cumsum()
        daily_summary["cumulative_target"] = daily_summary.groupby("meter_id")["target_saving_kwh"].cumsum()

        # Performance flag
        daily_summary["performance_met"] = daily_summary["actual_saving_kwh"] >= daily_summary["target_saving_kwh"]

        # Filters
        meters = daily_summary["meter_id"].unique()
        selected_meters = st.multiselect("Filter by meter", meters, default=list(meters))
        filtered = daily_summary[daily_summary["meter_id"].isin(selected_meters)]

        # Charts
        st.subheader("📊 Daily Actual vs Target Savings")
        chart = alt.Chart(filtered).mark_line(point=True).encode(
            x="date:T",
            y="actual_saving_kwh:Q",
            color="meter_id:N",
            tooltip=["date", "meter_id", "actual_saving_kwh", "target_saving_kwh"]
        ).properties(title="Actual Daily Savings")

        target_chart = alt.Chart(filtered).mark_line(point=True, strokeDash=[5, 5]).encode(
            x="date:T",
            y="target_saving_kwh:Q",
            color="meter_id:N"
        )

        st.altair_chart(chart + target_chart, use_container_width=True)

        # Cumulative chart
        st.subheader("📈 Cumulative Savings")
        cum_chart = alt.Chart(filtered).mark_line().encode(
            x="date:T",
            y="cumulative_actual:Q",
            color="meter_id:N",
            tooltip=["date", "meter_id", "cumulative_actual", "cumulative_target"]
        ).properties(title="Cumulative Actual Savings")

        target_cum_chart = alt.Chart(filtered).mark_line(strokeDash=[5, 5]).encode(
            x="date:T",
            y="cumulative_target:Q",
            color="meter_id:N"
        )

        st.altair_chart(cum_chart + target_cum_chart, use_container_width=True)

        # Table
        st.subheader("📋 Daily Summary Table")
        st.dataframe(filtered.style.format({
            "reporting_kwh": "{:.2f}",
            "baseline_kwh": "{:.2f}",
            "actual_saving_kwh": "{:.2f}",
            "target_saving_kwh": "{:.2f}"
        }))

        # Download option
        st.download_button("Download Summary CSV", filtered.to_csv(index=False), "daily_summary.csv", "text/csv")

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
else:
    st.info("📁 Upload an Excel file to begin.")
