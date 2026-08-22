# ============================================================
# PROTEX Explorer
#
# Interactive visualization tool for:
# logKow - logKaw - logKwater property space
#
# Input:
# Excel file
#
# Requirements:
#   First three columns:
#       logKow
#       logKaw
#       logKwater
#
# Following columns:
#       model outputs
#
# ============================================================


import os
from pathlib import Path

import pandas as pd
import numpy as np

import streamlit as st

import plotly.express as px
import plotly.graph_objects as go



# ============================================================
# CONFIG
# ============================================================


DATA_FOLDER = "./"


K_COLUMNS = [
    "logKow",
    "logKaw",
    "logKwater"
]


DEFAULT_COLOR = "Viridis"



# ============================================================
# PAGE CONFIG
# ============================================================


st.set_page_config(
    page_title="PROTEX Explorer",
    layout="wide"
)



# ============================================================
# FUNCTIONS
# ============================================================



def scan_excel_files(folder):
    """
    Find excel files in folder
    """

    files = []

    folder = Path(folder)

    for f in folder.iterdir():

        if f.suffix.lower() in [
            ".xlsx",
            ".xls"
        ]:

            files.append(f.name)


    return sorted(files)



def clean_excel(df):
    """
    Remove empty columns.

    Empty means:
    all values are NaN.

    """

    df = df.copy()


    # remove completely empty columns

    df = df.dropna(
        axis=1,
        how="all"
    )


    # remove completely empty rows

    df = df.dropna(
        axis=0,
        how="all"
    )


    return df



def load_excel(file):

    """
    Load all sheets
    """

    xls = pd.ExcelFile(file)

    return xls.sheet_names



def read_sheet(file, sheet):

    """
    Read selected sheet

    """

    df = pd.read_excel(
        file,
        sheet_name=sheet
    )


    df = clean_excel(df)


    return df



def detect_columns(df):

    """
    Identify K columns and output columns

    """

    columns = list(df.columns)


    # first 3 columns
    # are treated as K

    k_cols = columns[:3]


    value_cols = columns[3:]


    return k_cols, value_cols



def make_slice(
        df,
        x_col,
        y_col,
        fixed_col,
        fixed_value,
        value_col):

    """
    Extract 2D slice
    """


    sub = df[
        np.isclose(
            df[fixed_col],
            fixed_value
        )
    ]


    if len(sub) == 0:

        return None



    pivot = sub.pivot(
        index=y_col,
        columns=x_col,
        values=value_col
    )


    pivot = pivot.sort_index(
        ascending=True
    )


    return pivot




# ============================================================
# SIDEBAR
# ============================================================


st.sidebar.title(
    "PROTEX Explorer"
)



# -------------------------
# Excel selection
# -------------------------


files = scan_excel_files(
    DATA_FOLDER
)


if len(files) == 0:

    st.error(
        "No Excel files found."
    )

    st.stop()



selected_file = st.sidebar.selectbox(
    "Project Name",
    files
)



file_path = os.path.join(
    DATA_FOLDER,
    selected_file
)



# -------------------------
# Sheet selection
# -------------------------


sheets = load_excel(
    file_path
)


selected_sheet = st.sidebar.selectbox(
    "Sensitivity of Interest",
    sheets
)



# -------------------------
# Read data
# -------------------------


df = read_sheet(
    file_path,
    selected_sheet
)



st.sidebar.write(
    "Data size:",
    df.shape
)



# -------------------------
# Detect variables
# -------------------------


k_cols, value_cols = detect_columns(
    df
)



if len(value_cols)==0:

    st.error(
        "No output variables detected."
    )

    st.stop()



value_col = st.sidebar.selectbox(
    "Phase of Interest",
    value_cols
)


# ============================================================
# K SPACE CONTROL
# ============================================================


st.sidebar.subheader(
    "Property Space"
)


available_k = k_cols



# X axis

x_col = st.sidebar.selectbox(
    "X Axis",
    available_k,
    index=0
)



# Y axis

y_candidates = [
    c for c in available_k
    if c != x_col
]


y_col = st.sidebar.selectbox(
    "Y Axis",
    y_candidates,
    index=0
)



# Fixed axis

fixed_candidates = [
    c for c in available_k
    if c not in [
        x_col,
        y_col
    ]
]


fixed_col = fixed_candidates[0]



st.sidebar.write(
    "Fixed Axis:",
    fixed_col
)



# fixed value

fixed_values = sorted(
    df[fixed_col]
    .dropna()
    .unique()
)


fixed_value = st.sidebar.selectbox(
    "Fixed Value",
    fixed_values
)



# ============================================================
# DISPLAY OPTIONS
# ============================================================


st.sidebar.subheader(
    "Display"
)



plot_type = st.sidebar.radio(
    "Plot Type",
    [
        "Heatmap",
        "Contour",
        "3D Surface"
    ]
)



color_scale = st.sidebar.selectbox(
    "Color Scale",
    [
        "Viridis",
        "Turbo",
        "Inferno",
        "Magma",
        "Plasma",
        "Cividis"
    ]
)



log_scale = st.sidebar.checkbox(
    "Log10 Color Scale",
    value=False
)



# ============================================================
# CREATE SLICE
# ============================================================


matrix = make_slice(
    df,
    x_col,
    y_col,
    fixed_col,
    fixed_value,
    value_col
)



if matrix is None:

    st.error(
        "No data found for this slice."
    )

    st.stop()



plot_matrix = matrix.copy()



if log_scale:

    plot_matrix = np.log10(
        plot_matrix
    )



# ============================================================
# MAIN TITLE
# ============================================================


st.title(
    "PROTEX Chemical Property Explorer"
)



st.markdown(
f"""
### Current Selection

**File:** {selected_file}

**Sheet:** {selected_sheet}

**Variable:** {value_col}

**Slice:**

{fixed_col} = {fixed_value}

"""
)



# ============================================================
# PLOT
# ============================================================



if plot_type == "Heatmap":


    fig = px.imshow(
        plot_matrix,
        labels=dict(
            x=x_col,
            y=y_col,
            color=value_col
        ),
        aspect="auto",
        color_continuous_scale=color_scale
    )


    fig.update_layout(
        height=700
    )



elif plot_type == "Contour":


    fig = go.Figure(
        data=
        go.Contour(
            z=plot_matrix.values,
            x=plot_matrix.columns,
            y=plot_matrix.index,
            colorscale=color_scale,
            colorbar=dict(
                title=value_col
            )
        )
    )


    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title=y_col,
        height=700
    )



elif plot_type == "3D Surface":


    fig = go.Figure(
        data=
        go.Surface(
            z=plot_matrix.values,
            x=plot_matrix.columns,
            y=plot_matrix.index,
            colorscale=color_scale
        )
    )


    fig.update_layout(

        scene=dict(

            xaxis_title=x_col,

            yaxis_title=y_col,

            zaxis_title=value_col

        ),

        height=800

    )




st.plotly_chart(
    fig,
    use_container_width=True
)



# ============================================================
# DATA TABLE
# ============================================================


with st.expander(
    "Show Slice Data"
):

    st.dataframe(
        matrix
    )



# ============================================================
# EXPORT
# ============================================================


st.sidebar.subheader(
    "Export"
)



csv = matrix.to_csv()


st.sidebar.download_button(

    label="Download Slice CSV",

    data=csv,

    file_name=
    f"{selected_sheet}_{value_col}_slice.csv",

    mime="text/csv"

)