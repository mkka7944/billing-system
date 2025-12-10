import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import pandas as pd

def display_aggrid(df: pd.DataFrame, selection_mode="single", height=400):
    """
    Renders a robust AgGrid table with pagination, filtering, and customization.
    Returns the selected rows.
    """
    if df.empty:
        st.info("No data available to display.")
        return []

    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Defaults
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    gb.configure_side_bar() # Enable filters tool panel
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=False)
    
    # Selection
    gb.configure_selection(selection_mode, use_checkbox=True)
    
    # Style config
    gb.configure_grid_options(domLayout='normal')
    
    gridOptions = gb.build()
    
    table = AgGrid(
        df, 
        gridOptions=gridOptions, 
        height=height, 
        width='100%',
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED, 
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=False,
        theme='alpine', # 'streamlit', 'alpine', 'balham'
        allow_unsafe_jscode=True
    )
    
    return table["selected_rows"]
