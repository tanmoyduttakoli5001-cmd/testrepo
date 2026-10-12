"""
Final Assignment: Part 2 - Create Dashboard with Plotly and Dash
XYZAutomotives: Automobile Sales Statistics Dashboard

Before running:
1. Place automobile_sales.csv in the same folder as this script.
2. Install dependencies:
       pip install pandas plotly dash
3. Run:
       python automobile_dashboard_part2.py
4. Open the local URL printed in the terminal (usually http://127.0.0.1:8050).

Expected CSV columns:
Date, Recession, Automobile_Sales, GDP, Unemployment_Rate,
Consumer_Confidence, Seasonality_Weight, Price,
Advertising_Expenditure, Vehicle_Type, Competition, Month, Year
"""

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output


# ---------------------------------------------------------------------
# 1. Load and prepare the data
# ---------------------------------------------------------------------
CSV_FILE = "automobile_sales.csv"

data = pd.read_csv(CSV_FILE)

required_columns = {
    "Date",
    "Recession",
    "Automobile_Sales",
    "Unemployment_Rate",
    "Advertising_Expenditure",
    "Vehicle_Type",
}
missing_columns = required_columns.difference(data.columns)
if missing_columns:
    raise ValueError(
        "The CSV file is missing required columns: "
        + ", ".join(sorted(missing_columns))
    )

data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
data = data.dropna(subset=["Date"]).copy()

# Derive Month and Year from Date if they are not supplied.
if "Year" not in data.columns:
    data["Year"] = data["Date"].dt.year
else:
    data["Year"] = pd.to_numeric(data["Year"], errors="coerce")
    data["Year"] = data["Year"].fillna(data["Date"].dt.year).astype(int)

if "Month" not in data.columns:
    data["Month"] = data["Date"].dt.month
else:
    data["Month"] = pd.to_numeric(data["Month"], errors="coerce")
    data["Month"] = data["Month"].fillna(data["Date"].dt.month).astype(int)

data["Recession"] = pd.to_numeric(data["Recession"], errors="coerce").fillna(0).astype(int)

numeric_columns = [
    "Automobile_Sales",
    "Unemployment_Rate",
    "Advertising_Expenditure",
    "GDP",
    "Price",
]
for column in numeric_columns:
    if column in data.columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

year_list = sorted(data["Year"].dropna().astype(int).unique().tolist())
if not year_list:
    raise ValueError("No valid years were found in the dataset.")


# ---------------------------------------------------------------------
# 2. Create the Dash app
# ---------------------------------------------------------------------
app = Dash(__name__)
app.title = "XYZAutomotives Automobile Sales Dashboard"

REPORT_OPTIONS = [
    {"label": "Yearly Statistics", "value": "Yearly Statistics"},
    {
        "label": "Recession Period Statistics",
        "value": "Recession Period Statistics",
    },
]


# ---------------------------------------------------------------------
# 3. Define the dashboard layout
# ---------------------------------------------------------------------
app.layout = html.Div(
    children=[
        html.H1(
            "XYZAutomotives Automobile Sales Statistics Dashboard",
            style={
                "textAlign": "center",
                "color": "#503D36",
                "fontSize": "26px",
                "marginBottom": "24px",
            },
        ),

        html.Div(
            children=[
                html.Label("Select Statistics:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="dropdown-statistics",
                    options=REPORT_OPTIONS,
                    value="Recession Period Statistics",
                    placeholder="Select a report type",
                    clearable=False,
                ),
            ],
            style={"width": "48%", "display": "inline-block", "padding": "8px"},
        ),

        html.Div(
            children=[
                html.Label("Select Year:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="select-year",
                    options=[{"label": str(year), "value": year} for year in year_list],
                    value=year_list[-1],
                    placeholder="Select a year",
                    clearable=False,
                    disabled=True,
                ),
            ],
            style={"width": "48%", "display": "inline-block", "padding": "8px"},
        ),

        html.Hr(),

        html.Div(
            id="output-container",
            className="chart-grid",
            children=[],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(420px, 1fr))",
                "gap": "18px",
            },
        ),

        html.Footer(
            "Source: assignment-provided synthetic automobile sales dataset.",
            style={"textAlign": "center", "color": "#666", "marginTop": "25px"},
        ),
    ],
    style={"fontFamily": "Arial, sans-serif", "padding": "20px"},
)


# ---------------------------------------------------------------------
# 4. Callback: enable year selection only for Yearly Statistics
# ---------------------------------------------------------------------
@app.callback(
    Output("select-year", "disabled"),
    Input("dropdown-statistics", "value"),
)
def update_input_container(selected_statistics):
    """Enable the year dropdown for yearly reports; disable it for recession reports."""
    return selected_statistics != "Yearly Statistics"


# ---------------------------------------------------------------------
# Helper: return a readable message if a report has no data
# ---------------------------------------------------------------------
def no_data_message(message):
    return html.Div(
        message,
        style={
            "padding": "18px",
            "border": "1px solid #ddd",
            "borderRadius": "6px",
            "color": "#444",
        },
    )


# ---------------------------------------------------------------------
# 5. Callback: create the selected report and its graphs
# ---------------------------------------------------------------------
@app.callback(
    Output("output-container", "children"),
    Input("dropdown-statistics", "value"),
    Input("select-year", "value"),
)
def update_output_container(selected_statistics, input_year):
    """Update all report charts when the report type or year changes."""

    if selected_statistics == "Recession Period Statistics":
        recession_data = data[data["Recession"] == 1].copy()

        if recession_data.empty:
            return no_data_message("No recession-period records were found.")

        # Chart 1: average automobile sales by year during recession periods.
        yearly_rec = (
            recession_data.groupby("Year", as_index=False)["Automobile_Sales"]
            .mean()
            .sort_values("Year")
        )
        chart1 = dcc.Graph(
            figure=px.line(
                yearly_rec,
                x="Year",
                y="Automobile_Sales",
                markers=True,
                title="Average Automobile Sales During Recession Periods",
                labels={
                    "Year": "Year",
                    "Automobile_Sales": "Average Automobile Sales",
                },
            )
        )

        # Chart 2: average sales by vehicle type during recessions.
        average_sales = (
            recession_data.groupby("Vehicle_Type", as_index=False)["Automobile_Sales"]
            .mean()
            .sort_values("Automobile_Sales", ascending=False)
        )
        chart2 = dcc.Graph(
            figure=px.bar(
                average_sales,
                x="Vehicle_Type",
                y="Automobile_Sales",
                title="Average Sales by Vehicle Type During Recessions",
                labels={
                    "Vehicle_Type": "Vehicle Type",
                    "Automobile_Sales": "Average Automobile Sales",
                },
            )
        )

        # Chart 3: advertising expenditure share by vehicle type during recessions.
        advertising = (
            recession_data.groupby("Vehicle_Type", as_index=False)[
                "Advertising_Expenditure"
            ]
            .sum()
        )
        chart3 = dcc.Graph(
            figure=px.pie(
                advertising,
                names="Vehicle_Type",
                values="Advertising_Expenditure",
                title="Advertising Expenditure by Vehicle Type During Recessions",
            )
        )

        # Chart 4: average unemployment rate by vehicle type during recessions.
        unemployment = (
            recession_data.groupby("Vehicle_Type", as_index=False)["Unemployment_Rate"]
            .mean()
        )
        chart4 = dcc.Graph(
            figure=px.bar(
                unemployment,
                x="Vehicle_Type",
                y="Unemployment_Rate",
                title="Average Unemployment Rate by Vehicle Type During Recessions",
                labels={
                    "Vehicle_Type": "Vehicle Type",
                    "Unemployment_Rate": "Average Unemployment Rate",
                },
            )
        )

        return [
            html.H2("Recession Period Statistics", style={"gridColumn": "1 / -1"}),
            chart1,
            chart2,
            chart3,
            chart4,
        ]

    if selected_statistics == "Yearly Statistics":
        if input_year is None:
            input_year = year_list[-1]

        yearly_data = data[data["Year"] == int(input_year)].copy()
        if yearly_data.empty:
            return no_data_message(f"No records were found for {input_year}.")

        yearly_data = yearly_data.sort_values("Date")

        # Chart 1: monthly automobile sales in the selected year.
        monthly_sales = (
            yearly_data.groupby("Month", as_index=False)["Automobile_Sales"]
            .mean()
            .sort_values("Month")
        )
        chart1 = dcc.Graph(
            figure=px.line(
                monthly_sales,
                x="Month",
                y="Automobile_Sales",
                markers=True,
                title=f"Monthly Automobile Sales in {input_year}",
                labels={
                    "Month": "Month (1 = January)",
                    "Automobile_Sales": "Average Automobile Sales",
                },
            )
        )

        # Chart 2: average sales by vehicle type in the selected year.
        vehicle_sales = (
            yearly_data.groupby("Vehicle_Type", as_index=False)["Automobile_Sales"]
            .mean()
            .sort_values("Automobile_Sales", ascending=False)
        )
        chart2 = dcc.Graph(
            figure=px.bar(
                vehicle_sales,
                x="Vehicle_Type",
                y="Automobile_Sales",
                title=f"Average Automobile Sales by Vehicle Type in {input_year}",
                labels={
                    "Vehicle_Type": "Vehicle Type",
                    "Automobile_Sales": "Average Automobile Sales",
                },
            )
        )

        # Chart 3: advertising expenditure share by vehicle type in the selected year.
        yearly_advertising = (
            yearly_data.groupby("Vehicle_Type", as_index=False)[
                "Advertising_Expenditure"
            ]
            .sum()
        )
        chart3 = dcc.Graph(
            figure=px.pie(
                yearly_advertising,
                names="Vehicle_Type",
                values="Advertising_Expenditure",
                title=f"Advertising Expenditure by Vehicle Type in {input_year}",
            )
        )

        # Chart 4: monthly unemployment rate in the selected year.
        monthly_unemployment = (
            yearly_data.groupby("Month", as_index=False)["Unemployment_Rate"]
            .mean()
            .sort_values("Month")
        )
        chart4 = dcc.Graph(
            figure=px.line(
                monthly_unemployment,
                x="Month",
                y="Unemployment_Rate",
                markers=True,
                title=f"Monthly Unemployment Rate in {input_year}",
            )
        )

        return [
            html.H2(
                f"Yearly Statistics: {input_year}",
                style={"gridColumn": "1 / -1"},
            ),
            chart1,
            chart2,
            chart3,
            chart4,
        ]

    return no_data_message("Please select a report type.")


# ---------------------------------------------------------------------
# 6. Run the app
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
