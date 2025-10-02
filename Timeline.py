# import
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import holidays
from st_aggrid import AgGrid, GridOptionsBuilder

# Set page config
st.set_page_config(
    page_title="XPL Timeline Planner",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Upload CSV", "Timeline"]
)


# Required headers
REQUIRED_HEADERS = [
    "Program Name",
    "Program Start Date",
    "Program End Date",
    "Dec Shutdown Start",
    "Dec Shutdown End",
    "Block/Module Name",
    "Block Start Date",
    "Block End Date"
]

# Initialize session storage
if "timeline_data" not in st.session_state:
    st.session_state.timeline_data = None

# South African holidays (auto for any year)
za_holidays = holidays.SouthAfrica()

def working_days(start, end):
    """Calculate working days between two dates excluding weekends & ZA public holidays."""
    if pd.isna(start) or pd.isna(end):
        return None

    start = pd.to_datetime(start)
    end = pd.to_datetime(end)

    if end < start:
        return None

    # Business days
    all_days = pd.date_range(start, end, freq="B")

    # Exclude holidays (holidays lib automatically shifts Sat/Sun holidays to Monday)
    working = [d for d in all_days if d not in za_holidays]

    return len(working)

if page == "Upload CSV":
    st.title("📂 Upload CSV")
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)

            # --- HEADER VALIDATION ---
            missing_headers = [h for h in REQUIRED_HEADERS if h not in df.columns]
            if missing_headers:
                st.error(f"❌ CSV is missing required columns: {', '.join(missing_headers)}")
                st.stop()
            else:
                st.success("✅ All required columns are present.")

            st.subheader("Validate Entries")

            # Track errors
            errors = {}

            # --- Shutdown dates ---
            shutdown_start = pd.to_datetime(df["Dec Shutdown Start"].iloc[0], errors="coerce")
            shutdown_end = pd.to_datetime(df["Dec Shutdown End"].iloc[0], errors="coerce")

            if pd.isna(shutdown_start):
                errors["Dec Shutdown Start"] = shutdown_start
            if pd.isna(shutdown_end):
                errors["Dec Shutdown End"] = shutdown_end
            if not pd.isna(shutdown_start) and not pd.isna(shutdown_end) and shutdown_start >= shutdown_end:
                errors["Dec Shutdown Period"] = (shutdown_start, shutdown_end)

            # --- Row-level date validation ---
            date_columns = ["Program Start Date", "Program End Date", "Block Start Date", "Block End Date"]
            for col in date_columns:
                if col in df.columns:
                    for i in df.index:
                        val = pd.to_datetime(df.loc[i, col], errors="coerce")
                        if pd.isna(val):
                            errors[(col, i)] = val

            # --- Block/Module within Program validation ---
            for i in df.index:
                block_start = pd.to_datetime(df.loc[i, "Block Start Date"], errors="coerce")
                block_end = pd.to_datetime(df.loc[i, "Block End Date"], errors="coerce")
                prog_start = pd.to_datetime(df.loc[i, "Program Start Date"], errors="coerce")
                prog_end = pd.to_datetime(df.loc[i, "Program End Date"], errors="coerce")

                if pd.notna(block_start) and pd.notna(prog_start) and block_start < prog_start:
                    errors[(f"Block Start Date < Program Start Date", i)] = block_start
                if pd.notna(block_end) and pd.notna(prog_end) and block_end > prog_end:
                    errors[(f"Block End Date > Program End Date", i)] = block_end

            # --- Name validation (cannot be null/empty) ---
            for i in df.index:
                if pd.isna(df.loc[i, "Program Name"]) or str(df.loc[i, "Program Name"]).strip() == "":
                    errors[(f"Program Name Missing", i)] = None
                if pd.isna(df.loc[i, "Block/Module Name"]) or str(df.loc[i, "Block/Module Name"]).strip() == "":
                    errors[(f"Block/Module Name Missing", i)] = None

            # --- Display errors and inputs if any ---
            if errors:
                st.warning("⚠️ The following entries need your attention:")

                input_values = {}
                for key in errors:
                    if key == "Dec Shutdown Start":
                        input_values[key] = st.date_input("Fix Dec Shutdown Start", value=pd.Timestamp.today().date())
                    elif key == "Dec Shutdown End":
                        input_values[key] = st.date_input("Fix Dec Shutdown End", value=pd.Timestamp.today().date())
                    elif key == "Dec Shutdown Period":
                        s, e = errors[key]
                        input_values[key] = (
                            st.date_input("Fix Shutdown Start", value=s.date() if pd.notna(s) else pd.Timestamp.today().date()),
                            st.date_input("Fix Shutdown End", value=e.date() if pd.notna(e) else pd.Timestamp.today().date())
                        )
                    elif isinstance(key, tuple) and "Name Missing" in key[0]:
                        col_desc, idx = key
                        input_values[key] = st.text_input(
                            f"Enter {col_desc} for row {idx}", value=""
                        )
                    else:
                        col_desc, idx = key
                        input_values[key] = st.date_input(
                            f"Fix {col_desc} for row {idx}",
                            value=pd.Timestamp.today().date()
                        )

                # --- Submit button ---
                if st.button("Submit Changes"):
                    # Apply fixes
                    for key, val in input_values.items():
                        if key == "Dec Shutdown Start":
                            df["Dec Shutdown Start"] = pd.to_datetime(val)
                        elif key == "Dec Shutdown End":
                            df["Dec Shutdown End"] = pd.to_datetime(val)
                        elif key == "Dec Shutdown Period":
                            s, e = val
                            df["Dec Shutdown Start"] = pd.to_datetime(s)
                            df["Dec Shutdown End"] = pd.to_datetime(e)
                        elif isinstance(key, tuple) and "Name Missing" in key[0]:
                            col_desc, idx = key
                            if "Program Name" in col_desc:
                                df.loc[idx, "Program Name"] = val.strip()
                            elif "Block/Module Name" in col_desc:
                                df.loc[idx, "Block/Module Name"] = val.strip()
                        else:
                            col_desc, idx = key
                            df.loc[idx, col_desc] = pd.to_datetime(val)

                    st.success("✅ All changes submitted and entries are now valid!")
                    st.session_state.timeline_data = df

            else:
                # No errors: show success and remove edit options
                st.success("✅ All entries are valid!")
                st.session_state.timeline_data = df

            # Show updated DataFrame
            st.subheader("Current Data Preview")
            st.dataframe(df)

        except Exception as e:
            st.error(f"Error reading file: {e}")

elif page == "Timeline":
    st.title("📅 Program & Module Timeline")

    if st.session_state.get("timeline_data") is None:
        st.warning("⚠️ Please upload and validate your CSV first in the 'Upload CSV' section.")
    else:
        df = st.session_state.timeline_data.copy()

        # ✅ Ensure date columns are proper datetime.date (no times)
        date_columns = ["Program Start Date", "Program End Date", "Block Start Date", "Block End Date"]
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

        # --- Helper function to calculate readable duration ---
        def readable_duration(start, end):
            """Return duration value and best unit (days, weeks, months)."""
            if pd.isna(start) or pd.isna(end):
                return None, None
            delta_days = (end - start).days + 1
            if delta_days < 7:
                return delta_days, "days"
            elif delta_days < 30:
                return round(delta_days / 7, 1), "weeks"
            else:
                return round(delta_days / 30, 1), "months"

        # --- Program Duration ---
        df["Program Duration"], df["Program Duration Unit"] = zip(
            *df.apply(lambda row: readable_duration(row["Program Start Date"], row["Program End Date"]), axis=1)
        )

        # --- Block/Module Duration ---
        df["Block Duration"], df["Block Duration Unit"] = zip(
            *df.apply(lambda row: readable_duration(row["Block Start Date"], row["Block End Date"]), axis=1)
        )

        # --- Display Table ---
        # Build grid options
        # Keep datetime64 for proper AgGrid display
        date_columns = ["Program Start Date", "Program End Date", "Block Start Date", "Block End Date"]
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        # Build grid options
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection(selection_mode="single", use_checkbox=True)

        # Format date columns for display
        for col in date_columns:
            gb.configure_column(col, type=["dateColumnFilter","customDateTimeFormat"], custom_format_string='yyyy-MM-dd')

        grid_options = gb.build()

        # Show AgGrid
        grid_response = AgGrid(df, gridOptions=grid_options, height=400, fit_columns_on_grid_load=True)

        # Get selected rows safely
        selected = grid_response.get('selected_rows', [])
        
        # Ensure it's a list for safe length checking
        if selected is None:
            selected = []
        
        if isinstance(selected, pd.DataFrame):
            selected = selected.to_dict('records')
        
        # Only proceed if there is at least one row selected
        if len(selected) > 0:
            selected_row = pd.DataFrame(selected).iloc[0]
        
            st.subheader(f"📄 Detailed View: {selected_row['Block/Module Name']}")
        
            # Module info with date-only formatting
            module_info = selected_row.to_dict()
            for col in ["Program Start Date", "Program End Date", "Block Start Date", "Block End Date"]:
                value = module_info.get(col)
                if value is not None:
                    dt_value = pd.to_datetime(value, errors='coerce')
                    if pd.notna(dt_value):
                        module_info[col] = dt_value.date()
            st.write("### Module Info")
            st.json(module_info)
        
            # Show all dates in module duration
            start = pd.to_datetime(selected_row['Block Start Date'])
            end = pd.to_datetime(selected_row['Block End Date'])
            all_dates = pd.date_range(start, end)
            dates_df = pd.DataFrame({
                "Date": [d.date() for d in all_dates],
                "Day of Week": [d.strftime("%A") for d in all_dates]
            })
            st.write("### All Dates in Module Duration")
            st.dataframe(dates_df, use_container_width=True)

        st.success("✅ Timeline durations calculated and displayed in user-friendly units.")


    
