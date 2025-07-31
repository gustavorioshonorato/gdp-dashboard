import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime, date
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="Offshore Pipeline Projects Dashboard",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_pipeline_data():
    """
    Load pipeline data from CSV file or session state
    """
    # First check if there's data in session state
    if 'pipeline_data' in st.session_state and not st.session_state.pipeline_data.empty:
        return st.session_state.pipeline_data
    
    # Try to load existing CSV file
    try:
        if os.path.exists("data/pipeline_data.csv"):
            df = pd.read_csv("data/pipeline_data.csv")
            st.session_state.pipeline_data = df
            return df
        elif os.path.exists("data/sample_pipeline_data.csv"):
            df = pd.read_csv("data/sample_pipeline_data.csv")
            # Clean column names removing line breaks
            df.columns = [col.replace('\n', ' ').strip() for col in df.columns]
            st.session_state.pipeline_data = df
            return df
        else:
            # Return empty DataFrame with default columns
            columns = [
                'Country', 'Project', 'Vessel', 'Pipe Type', 'Line Type',
                'Pipe OD', 'Pipe Wall Thickness', 'Coating Thickness',
                'Steel Density', 'Coating Density', 'Clad Thickness',
                'Vessel Name', 'Water Depth', 'Estimated Optimal JLT Angle', 'JLT Angle',
                'Installation Date'
            ]
            df = pd.DataFrame(columns=columns)
            st.session_state.pipeline_data = df
            return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

def save_pipeline_data(df):
    """
    Save pipeline data to CSV file and session state
    """
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save to CSV file
        df.to_csv("data/pipeline_data.csv", index=False)
        
        # Update session state
        st.session_state.pipeline_data = df
        
        return True
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        return False

def add_new_pipeline_row(new_data):
    """
    Add a new row to pipeline data
    """
    df = load_pipeline_data()
    
    # Convert new data to DataFrame
    new_row = pd.DataFrame([new_data])
    
    # Concatenate with existing data
    df = pd.concat([df, new_row], ignore_index=True)
    
    # Save data
    if save_pipeline_data(df):
        st.success("New record added successfully!")
        st.rerun()
    else:
        st.error("Failed to save new record.")

def create_filter_sidebar(df):
    """
    Create dynamic filters in sidebar based on dataframe columns
    """
    st.sidebar.header("Data Filters")
    
    # Filter style selection
    filter_style = st.sidebar.radio(
        "Filter Style:",
        ["Multiselect", "Checkboxes"],
        key="filter_style"
    )
    
    # Filter controls
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Select All", key="select_all"):
            st.session_state.update({f"filter_{col}": df[col].dropna().unique().tolist() 
                                   for col in df.columns if col in df.select_dtypes(include=['object']).columns})
            st.rerun()
    with col2:
        if st.button("Clear All", key="clear_all"):
            for col in df.columns:
                if f"filter_{col}" in st.session_state:
                    del st.session_state[f"filter_{col}"]
            st.rerun()
    
    filtered_df = df.copy()
    
    for column in df.columns:
        if df[column].dtype == 'object':  # Text/Categorical columns
            unique_values = df[column].dropna().unique()
            if len(unique_values) > 0:
                if filter_style == "Multiselect":
                    selected_values = st.sidebar.multiselect(
                        f"Filter by {column}:",
                        options=unique_values,
                        default=st.session_state.get(f"filter_{column}", []),
                        key=f"filter_{column}"
                    )
                else:  # Checkboxes
                    st.sidebar.write(f"**{column}:**")
                    selected_values = []
                    for value in unique_values:
                        if st.sidebar.checkbox(
                            str(value),
                            key=f"checkbox_{column}_{value}",
                            value=str(value) in st.session_state.get(f"filter_{column}", [])
                        ):
                            selected_values.append(value)
                    st.session_state[f"filter_{column}"] = selected_values
                
                if selected_values:
                    filtered_df = filtered_df[filtered_df[column].isin(selected_values)]
        
        elif pd.api.types.is_numeric_dtype(df[column]):  # Numeric columns
            if not df[column].isna().all():
                min_val = float(df[column].min())
                max_val = float(df[column].max())
                
                if min_val != max_val:
                    selected_range = st.sidebar.slider(
                        f"{column} Range:",
                        min_value=min_val,
                        max_value=max_val,
                        value=(min_val, max_val),
                        key=f"slider_{column}"
                    )
                    filtered_df = filtered_df[
                        (filtered_df[column] >= selected_range[0]) & 
                        (filtered_df[column] <= selected_range[1])
                    ]
        
        elif 'date' in column.lower():  # Date columns
            try:
                df[column] = pd.to_datetime(df[column], errors='coerce')
                valid_dates = df[column].dropna()
                
                if len(valid_dates) > 0:
                    min_date = valid_dates.min().date()
                    max_date = valid_dates.max().date()
                    
                    selected_date_range = st.sidebar.date_input(
                        f"{column} Range:",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date,
                        key=f"date_{column}"
                    )
                    
                    if len(selected_date_range) == 2:
                        start_date, end_date = selected_date_range
                        filtered_df = filtered_df[
                            (pd.to_datetime(filtered_df[column]).dt.date >= start_date) &
                            (pd.to_datetime(filtered_df[column]).dt.date <= end_date)
                        ]
            except:
                pass  # Skip if date conversion fails
    
    return filtered_df

def display_logo():
    """
    Display company logo if uploaded
    """
    if 'company_logo' in st.session_state:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(st.session_state.company_logo, width=200)

def main():
    """
    Main application function
    """
    # Display logo
    display_logo()
    
    # Main title
    st.title("Offshore Pipeline Projects Dashboard")
    st.markdown("---")
    
    # Load data
    df = load_pipeline_data()
    
    # Sidebar for data management and filters
    with st.sidebar:
        st.header("Data Management")
        
        # Upload new spreadsheet
        uploaded_file = st.file_uploader(
            "Upload New Spreadsheet",
            type=['csv', 'xlsx'],
            help="Upload CSV or Excel file with pipeline data"
        )
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    new_df = pd.read_csv(uploaded_file)
                else:
                    new_df = pd.read_excel(uploaded_file)
                
                # Clean column names
                new_df.columns = [col.replace('\n', ' ').strip() for col in new_df.columns]
                
                if save_pipeline_data(new_df):
                    st.success("Data uploaded successfully!")
                    st.rerun()
                else:
                    st.error("Failed to save uploaded data.")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
        
        # Add new row functionality
        with st.expander("Add New Row"):
            with st.form("add_row_form"):
                st.write("**Required Fields:**")
                country = st.text_input("Country*", key="new_country")
                project = st.text_input("Project*", key="new_project")
                vessel = st.text_input("Vessel", key="new_vessel")
                pipe_type = st.text_input("Pipe Type", key="new_pipe_type")
                
                st.write("**Optional Fields:**")
                line_type = st.text_input("Line Type", key="new_line_type")
                pipe_od = st.number_input("Pipe OD (mm)", min_value=0.0, key="new_pipe_od")
                pipe_wall = st.number_input("Pipe Wall Thickness (mm)", min_value=0.0, key="new_pipe_wall")
                coating_thickness = st.number_input("Coating Thickness (mm)", min_value=0.0, key="new_coating_thickness")
                steel_density = st.number_input("Steel Density (kg/m³)", min_value=0.0, key="new_steel_density")
                coating_density = st.number_input("Coating Density (kg/m³)", min_value=0.0, key="new_coating_density")
                clad_thickness = st.number_input("Clad Thickness (mm)", min_value=0.0, key="new_clad_thickness")
                vessel_name = st.text_input("Vessel Name", key="new_vessel_name")
                water_depth = st.number_input("Water Depth (m)", min_value=0.0, key="new_water_depth")
                estimated_angle = st.number_input("Estimated Optimal JLT Angle (°)", key="new_estimated_angle")
                jlt_angle = st.number_input("JLT Angle (°)", key="new_jlt_angle")
                installation_date = st.date_input("Installation Date", key="new_installation_date")
                
                if st.form_submit_button("Add Row"):
                    if country and project:
                        new_data = {
                            'Country': country,
                            'Project': project,
                            'Vessel': vessel,
                            'Pipe Type': pipe_type,
                            'Line Type': line_type,
                            'Pipe OD': pipe_od if pipe_od > 0 else '',
                            'Pipe Wall Thickness': pipe_wall if pipe_wall > 0 else '',
                            'Coating Thickness': coating_thickness if coating_thickness > 0 else '',
                            'Steel Density': steel_density if steel_density > 0 else '',
                            'Coating Density': coating_density if coating_density > 0 else '',
                            'Clad Thickness': clad_thickness if clad_thickness > 0 else '',
                            'Vessel Name': vessel_name,
                            'Water Depth': water_depth if water_depth > 0 else '',
                            'Estimated Optimal JLT Angle': estimated_angle if estimated_angle != 0 else '',
                            'JLT Angle': jlt_angle if jlt_angle != 0 else '',
                            'Installation Date': installation_date
                        }
                        add_new_pipeline_row(new_data)
                    else:
                        st.error("Country and Project are required fields.")
        
        # Settings section
        with st.expander("Settings"):
            # Logo upload
            st.write("**Company Logo:**")
            logo_file = st.file_uploader(
                "Upload Logo",
                type=['png', 'jpg', 'jpeg'],
                key="logo_uploader"
            )
            
            if logo_file is not None:
                try:
                    image = Image.open(logo_file)
                    st.session_state.company_logo = image
                    st.success("Logo uploaded successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing logo: {str(e)}")
            
            if st.button("Remove Logo"):
                if 'company_logo' in st.session_state:
                    del st.session_state.company_logo
                    st.success("Logo removed successfully!")
                    st.rerun()
    
    # Main content area
    if not df.empty:
        # Apply filters
        filtered_df = create_filter_sidebar(df)
        
        # Key Performance Indicators
        st.header("Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Pipeline Lines",
                value=len(filtered_df)
            )
        
        with col2:
            unique_projects = filtered_df['Project'].nunique() if 'Project' in filtered_df.columns else 0
            st.metric(
                label="Unique Projects", 
                value=unique_projects
            )
        
        with col3:
            unique_vessels = filtered_df['Vessel'].nunique() if 'Vessel' in filtered_df.columns else 0
            st.metric(
                label="Unique Vessels",
                value=unique_vessels
            )
        
        with col4:
            unique_countries = filtered_df['Country'].nunique() if 'Country' in filtered_df.columns else 0
            st.metric(
                label="Countries",
                value=unique_countries
            )
        
        st.markdown("---")
        
        # Charts and visualizations
        st.header("Data Visualization")
        
        if 'Pipe Type' in filtered_df.columns and not filtered_df['Pipe Type'].isna().all():
            pipe_type_counts = filtered_df['Pipe Type'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Pipe Type Distribution")
                st.bar_chart(pipe_type_counts)
            
            with col2:
                st.subheader("Distribution Details")
                for pipe_type, count in pipe_type_counts.items():
                    percentage = (count / len(filtered_df)) * 100
                    st.write(f"**{pipe_type}**: {count} lines ({percentage:.1f}%)")
        
        # Data table
        st.header("Pipeline Data Table")
        st.write(f"Showing {len(filtered_df)} of {len(df)} total records")
        
        # Download button for filtered data
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv_data,
            file_name=f"pipeline_data_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Display filtered data table
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400
        )
        
        # Summary statistics for numeric columns
        numeric_columns = filtered_df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_columns) > 0:
            with st.expander("Numerical Summary Statistics"):
                st.dataframe(filtered_df[numeric_columns].describe())
    
    else:
        st.info("""
        **Welcome to the Offshore Pipeline Projects Dashboard!**
        
        To get started:
        1. Upload a CSV or Excel file using the sidebar
        2. Or add data manually using the "Add New Row" form
        
        The dashboard will automatically create appropriate filters for your data columns.
        """)

if __name__ == "__main__":
    main()
