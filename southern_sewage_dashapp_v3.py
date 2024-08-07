# V3 TRIES TO ADD FANCY COLOURS OTHER FORMATTING ETC. V2 IS FUNCTIONALLY OKAY! #
# Imports
import pandas as pd
from dash import Dash, html, dcc, callback
from dash.dependencies import Input, Output
import plotly_express as px
import numpy as np
import dash_bootstrap_components as dbc
import gunicorn

# Read in dataset and process useful columns:
df = pd.read_csv("C:/Users/tomwr/Datascience/Datasets/Tabular/southern_water_spills/southern_water_spills_2017_2023.csv",
                 parse_dates=["CR_StartDate", "CR_StartTime", "CR_EndDate", "CR_EndTime"])

df[["CR_DischargeDuration", "CR_DischargePeriod"]] = df[["CR_DischargePeriod", "CR_DischargeDuration"]].apply(pd.to_timedelta)
df["Year"] = df["CR_StartDate"].dt.year
df["Month"] = df["CR_StartDate"].dt.month
df["Day"] = df["CR_StartDate"].dt.day
df["Hour"] = df["CR_StartTime"].dt.hour
df["Duration_Mins"] = df["CR_DischargeDuration"].dt.seconds / 60
df["Period_Mins"] = df["CR_DischargePeriod"].dt.seconds / 60

unique_counties = list(np.unique(df['County']))
unique_sites = list(np.unique(df["Site"]))

# Key dataframes
#Homepage, average duration through time linechart
full_time_average_df = df[["CR_StartDate", "Duration_Mins", "Period_Mins", "Spills"]].groupby(by="CR_StartDate", as_index=False).mean().sort_values(by="CR_StartDate", ascending=True).reset_index(drop=True)

#Homepage, total duration through time linechart. Use this for total spills on the above chart . Switch between this and above.
full_time_discharge_sum_df = df[["CR_StartDate", "Duration_Mins"]].groupby(by="CR_StartDate", as_index=False).sum().sort_values(by="CR_StartDate", ascending=True).reset_index(drop=True)

#Homepage, spills through time linechart.
full_time_spill_sum_df = df[["CR_StartDate", "Spills"]].groupby(by="CR_StartDate", as_index=False).sum().sort_values(by="CR_StartDate", ascending=True).reset_index(drop=True)

#Homepage, spill duration by different time periods and types.
full_timeperiod_discharge_df = df[["Year", "Month", "Day", "Hour", "Duration_Mins", "Type"]].groupby(by=["Type", "Year", "Month", "Day", "Hour"], as_index=False).sum().reset_index(drop=True)

#Homepage, total discharge by year barchart
year_total_discharge_df = df[["Year", "Type", "Duration_Mins"]].groupby(by=["Year", "Type"], as_index=False).sum().sort_values(by="Year", ascending=True).reset_index(drop=True)

#Homepage, total discharge by type piechart
type_total_discharge_df = df[["Year", "Type", "Duration_Mins"]].groupby(by=["Year","Type"], as_index=False).sum().reset_index(drop=True)

# Counties, total discharge over time, filterable by county(s) and type; linechart
counties_time_discharge_df = df[["CR_StartDate", "Type", "County", "Duration_Mins", "Spills"]].groupby(by=["CR_StartDate", "County", "Type"], as_index=False).sum().reset_index(drop=True)

# Counties, AVERAGE discharge over time, filterable by county(s) and type; linechart
counties_time_avg_discharge_df = df[["CR_StartDate", "Type", "County", "Duration_Mins", "Spills"]].groupby(by=["CR_StartDate", "County", "Type"], as_index=False).mean().reset_index(drop=True)

# Counties, total spills over time, can flip between this and the above chart on the same space
counties_time_spills_df = df[["CR_StartDate", "Type", "County", "Spills"]].groupby(by=["CR_StartDate", "County", "Type"], as_index=False).sum().reset_index(drop=True)

# Counties, discharge by type and year, filterable by county(s) and time; piechart
counties_type_total_discharge_df = df[["County", "Type", "Year", "Duration_Mins"]].groupby(by=["County", "Year", "Type"], as_index=False).sum().reset_index(drop=True)

# Counties, Sewage discharge by year, month, day, hour; quad linechart
counties_discharge_timeperiod = df[["County","Type", "Duration_Mins", "Year", "Month", "Day", "Hour"]].groupby(by=["County","Type", "Year", "Month", "Day", "Hour"], as_index=False).sum().reset_index(drop=True)

# Sites, Sewage total discharge over time, filterbale by site(s) and type; linechart
site_time_discharge_df = df[["CR_StartDate", "Type", "Site", "Duration_Mins"]].groupby(by=["CR_StartDate", "Site", "Type"], as_index=False).sum().reset_index(drop=True)

# Sites, average sewage discharge over time, filterable by site and type, linechart
site_time_avg_discharge_df = df[["CR_StartDate", "Type", "Site", "Duration_Mins"]].groupby(by=["CR_StartDate", "Site", "Type"], as_index=False).mean().reset_index(drop=True)

# Sites, Sewaage makeup by site and year; piechart
site_type_total_discharge_df = df[["Site", "Type", "Year", "Duration_Mins"]].groupby(by=["Year", "Type"], as_index=False).sum().reset_index(drop=True)

# Sites, sewage discharge by year, month, day, hour; quad linechart. Filtered to a single site selectable.
sites_discharge_timeperiod = df[["Site", "Year", "Month", "Day", "Hour", "Duration_Mins"]].groupby(by=["Site", "Year", "Month", "Day", "Hour"], as_index=False).sum().reset_index(drop=True)

###############################################################################################
#### DASHAPP SETUP ####

# List of colours that can be used in plots (using tetradic - https://imagecolorpicker.com/color-code/0065ab)
colours_sequence = ['#0065ab', '#9b00ab', '#ab4600', '#0fab00']

# Colour mapping to use in plots (to keep consistent for sewage types)
type_colour_map = {"Emergency Sewage": "#0065ab",
                   "Storm Sewage": "#9b00ab",
                   "Partially Treated Sewage": "#ab4600"}

#Colours dictionary - refer back to this using dict['key] in html elements for different colours
colours = {
    'background': '#e6f7fd',
    'contrasting_background': '#fdece6',
    'title_text': '#0065ab',
    'banners_buttons': '#80d6f9',
    'text': '#000000',
    'borders': '#003348'
}

# Other style dictionaries:

#Tabs
tab_style = {"background": colours["contrasting_background"],
             "color": colours["text"],
             "border": colours["title_text"],
             "align-items": "center",
             "font-weight": "bold",
             "font-family": "aperto",
             "font-size": "28px"}

# Whole page style
whole_page_style = {"background": colours["background"],
                    "border": colours["borders"],
                    "font-family": "aperto"}

dropdown_style = {"background": colours["contrasting_background"],
                  "border": colours["borders"],
                  "align-items": "center",
                  "font-weight": "bold",
                  "color": colours["text"],
                  "font-family": "aperto"}

app = Dash(__name__,
           suppress_callback_exceptions=True,
           external_stylesheets=[dbc.themes.BOOTSTRAP])

# Defining app layout #

# Whole page div
app.layout = html.Div(
    style=whole_page_style,
    children=[
        dcc.Tabs([
            dcc.Tab(label="Homepage",
                    style=tab_style,
                    children=[
                        html.H1("Southern Water Sewage 2017-2023",
                                style={"textAlign": "center",
                                       "font-weight": "bold",
                                       "color": colours["title_text"]}),
                        html.Hr(),
                        # Div for all graphs excluding Header for homepage
                        html.Div(children=[
                            # Top row, left column
                            dbc.Row([
                                dbc.Col([
                                    html.Div(children=[
                                        dcc.Slider(min=2017,
                                                   max=2023,
                                                   step=1,
                                                   id="hp-pie-year-slider",
                                                   value=2023,
                                                   marks={2017: "2017",
                                                          2018: "2018",
                                                          2019: "2019",
                                                          2020: "2020",
                                                          2021: "2021",
                                                          2022: "2022",
                                                          2023: "2023"}),
                                        dcc.Graph(id="hp-type-pie")
                                        ]),
                                    ]),
                                # Top row, right column
                                dbc.Col([
                                    html.Div(children=[
                                        dcc.RadioItems(["Average", "Total Sum"],
                                                       value="Average",
                                                       id="hp-line-calc-radio"),
                                        dcc.Graph(id="hp-discharge-time-line")
                                        ])
                                    ])
                                ]),
                            # Bottom row, left column
                            dbc.Row([
                                dbc.Col([
                                    html.Div(children=[
                                        dcc.RadioItems(options=["Year", "Month", "Day", "Hour"],
                                                       value="Year",
                                                       id="hp-timeperiod-type-radio"),
                                        dcc.Graph(id="hp-timeperiod-type-discharge-line")
                                        ]),
                                    ]),
                                # Bottom row, right column
                                dbc.Col([
                                    html.Div(children=[
                                        dcc.Graph(id="hp-box")
                                        ])
                                    ])
                            ])
                        ])
                    ]),
            # 2nd Tab - Counties
            dcc.Tab(label="Counties",
                    style=tab_style,
                    children=[
                        html.H1("Sewage by County - 2017-2023",
                                style={"textAlign": "center",
                                       "font-weight": "bold",
                                       "color": colours["title_text"]}),
                        html.Hr(),
                        html.Div(children=[
                            # Top row, left column
                            dbc.Row([
                                dbc.Col([
                                    html.Div(children=[
                                        dcc.RadioItems(options=["Sum", "Average", "Spills"],
                                                       value="Sum",
                                                       id="cp-sum-avg-spills-calc-radio"),
                                        dcc.Dropdown(options=unique_counties,
                                                     value="EAST SUSSEX",
                                                     id="cp-sum-avg-spills-county-dropdown",
                                                     style=dropdown_style),
                                        dcc.Graph(id="cp-sum-avg-spills-line-fig")
                                        ])
                                    ]),
                                dbc.Col([
                                    html.Div(children=[
                                        dcc.Dropdown(
                                            options=[2017, 2018, 2019, 2020, 2021, 2022, 2023],
                                            value=2023,
                                            id="cp-type-duration-pie-year-dropdown",
                                            style=dropdown_style),
                                        dcc.Graph(id="cp-type-duration-pie-fig")
                                        ])
                                    ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(children=[
                                        dcc.Dropdown(options=["Year", "Month", "Day", "Hour"],
                                                     value="Year",
                                                     id="cp-timeperiod-type-dropdown",
                                                     style=dropdown_style),
                                        dcc.Graph(id="cp-timeperiod-line-fig")
                                        ])
                                    ]),
                                dbc.Col([
                                    html.Div(children=[
                                        dcc.Graph(id="cp-average-boxplot")
                                        ])
                                    ])
                                ])
                        ])
                    ])

            ]),
            # Sites Tab
            dcc.Tab(label="Sites",
                    style=tab_style,
                    children=[
                        html.H1("Sewage by Site - 2017-2023",
                                style={"textAlign": "center",
                                       "font-weight": "bold",
                                       "color": colours["title_text"]}),
                        html.Hr(),
                        html.Div(children=[
                            # Top left cell
                            dbc.Row([
                                dbc.Col([
                                    html.Div(children=[
                                        dcc.RadioItems(options=["Sum", "Spills"],
                                                       value="Sum",
                                                       id="sp-calc-type-radio"),
                                        dcc.Dropdown(options=unique_sites,
                                                     value=unique_sites[0],
                                                     id="sp-site-dropdown",
                                                     style=dropdown_style,
                                                     placeholder="Please select a site"),
                                        dcc.Graph(id="sp-discharge-time-line-fig")
                                        ])
                                    ]),
                                # Top right cell
                                dbc.Col([
                                    html.Div(children=[
                                        dcc.Dropdown(options=[2017,2018,2019,2020,2021,2022,2023],
                                                     value=2023,
                                                     id="sp-year-pie-dropdown",
                                                     style=dropdown_style),
                                        dcc.Graph(id="sp-pie-fig")
                                        ])
                                    ]),
                                ]),
                            # Bottom left cell
                            dbc.Row([
                                dbc.Col([
                                    html.Div(children=[
                                        dcc.RadioItems(options=["Year", "Month", "Day", "Hour"],
                                                       value="Year",
                                                       id="sp-timeperiod-timeperiod-radio"),
                                        dcc.Graph(id="sp-timeperiod-line-fig")
                                        ])

                                    ]),
                                dbc.Col([
                                    html.Div(children=[
                                        dcc.Graph(id="sp-box")
                                        ])
                                    ])
                                ])
                            ])
                        ])
            ])
        ])



######################################################################################################
# Callback Functions
# Homepage - Change Year in Piechart, including title
@callback(
    Output("hp-type-pie", "figure"),
    Input("hp-pie-year-slider", "value"))
def update_hp_pie_year(year):
    filtered_df = type_total_discharge_df[type_total_discharge_df["Year"] == year]

    new_hp_pie = px.pie(filtered_df,
                        names="Type",
                        values="Duration_Mins",
                        title=f"Sewage Overflow Duration by Type - {str(year)}",
                        color_discrete_sequence=colours_sequence)
    new_hp_pie.update_layout(transition_duration=500,
                             plot_bgcolor=colours["background"],
                             paper_bgcolor=colours["background"],
                             font_family="Aperto",
                             title_font_family="Aperto")

    return new_hp_pie


# Homepage - Switch between average and total duration over full period
@callback(
    Output("hp-discharge-time-line", "figure"),
    Input("hp-line-calc-radio", "value")
)
def update_hp_sum_avg_line(chart_type):
    if chart_type == "Average":
        df = full_time_average_df
        new_line_fig = px.line(data_frame=df,
                               x="CR_StartDate",
                               y="Duration_Mins",
                               title=f"Sewage Overflow Duration 2017-2023 - {str(chart_type)}",
                               color_discrete_sequence=colours_sequence)
        new_line_fig.update_layout(transition_duration=500,
                                   plot_bgcolor=colours["background"],
                                   paper_bgcolor=colours["background"],
                                   font_family="Aperto",
                                   title_font_family="Aperto")
    elif chart_type == "Total Sum":
        df = full_time_discharge_sum_df
        new_line_fig = px.line(data_frame=df,
                               x="CR_StartDate",
                               y="Duration_Mins",
                               title=f"Sewage Overflow Duration 2017-2023 - {str(chart_type)}",
                               color_discrete_sequence=colours_sequence)
        new_line_fig.update_layout(transition_duration=500,
                                   plot_bgcolor=colours["background"],
                                   paper_bgcolor=colours["background"],
                                   font_family="Aperto",
                                   title_font_family="Aperto")
    new_line_fig.update_xaxes(title_text="Start Date")
    new_line_fig.update_yaxes(title_text="Duration (mins)")
    return new_line_fig

# Homepage - switch plot by timeperiod type (Year, Month, Day, Hour), coloured by Type., using radioitems
@callback(
    Output("hp-timeperiod-type-discharge-line", "figure"),
    Input("hp-timeperiod-type-radio", "value")
)
def update_hp_timeperiod_line(chosen_timeperiod):
    regrouped_df = full_timeperiod_discharge_df.groupby(by=[chosen_timeperiod,"Type"], as_index=False).sum().reset_index(drop=True)
    regrouped_line_fig = px.line(data_frame=regrouped_df,
                                 x=chosen_timeperiod,
                                 y="Duration_Mins",
                                 color="Type",
                                 title=f"Total Sewage Overflows by {chosen_timeperiod}",
                                 color_discrete_sequence=colours_sequence,
                                 color_discrete_map=type_colour_map)

    regrouped_line_fig.update_yaxes(title_text="Duration (mins)")
    regrouped_line_fig.update_layout(transition_duration=500,
                                     plot_bgcolor=colours["background"],
                                     paper_bgcolor=colours["background"],
                                     font_family="Aperto",
                                     title_font_family="Aperto")
    return regrouped_line_fig


# Home page box plot - filtered by year, coloured by Type
@callback(
    Output("hp-box", "figure"),
    Input("hp-pie-year-slider","value")
)
def update_hp_box(year):
    filtered_df = df[df["Year"] == year]
    box = px.box(data_frame=filtered_df,
                 x="Type",
                 y="Duration_Mins",
                 color="Type",
                 title=f"Sewage Overflow Duration by Type - {str(year)}",
                 color_discrete_sequence=colours_sequence,
                 color_discrete_map=type_colour_map)
    box.update_yaxes(title_text = "Duration (mins)")
    box.update_layout(transition_duration=500,
                      plot_bgcolor=colours["background"],
                      paper_bgcolor=colours["background"],
                      font_family="Aperto",
                      title_font_family="Aperto")

    return box


# Counties - Discharge by sum and average and spills (swappable) and filterable by county (dropdown) -linechart
@callback(
    Output("cp-sum-avg-spills-line-fig", "figure"),
    Input("cp-sum-avg-spills-calc-radio","value"),
    Input("cp-sum-avg-spills-county-dropdown","value")
)
def update_cp_sum_avg_line(calc, county):
    # Ensure the selection is a list even if only 1 item, so not to break the .isin()
    if isinstance(county, str):
        county = [county]
        county_title = county[0].strip("[\'").strip("\']")
    if calc == 'Sum':
        calc_df = df[["CR_StartDate", "Type", "County", "Duration_Mins"]].groupby(by=["CR_StartDate", "County", "Type"], as_index=False).sum().reset_index(drop=True)
    elif calc == 'Average':
        calc_df = df[["CR_StartDate", "Type", "County", "Duration_Mins"]].groupby(by=["CR_StartDate", "County", "Type"], as_index=False).mean().reset_index(drop=True)
    else:
        calc_df = df[["CR_StartDate", "Type", "County", "Spills"]].groupby(by=["CR_StartDate", "County", "Type"], as_index=False).sum().reset_index(drop=True)

    filtered_calc_df = calc_df[calc_df["County"].isin(county)]  # Can take multiple counties together

    if calc != "Spills":
        filtered_calc_line = px.line(data_frame=filtered_calc_df,
                                     x="CR_StartDate",
                                     y="Duration_Mins",
                                     title=f"{str(county_title)} - {calc} Sewage Overflow Duration 2017-2023",
                                     color_discrete_sequence=colours_sequence)
    elif calc == "Spills":
        filtered_calc_line = px.line(data_frame=filtered_calc_df,
                                     x="CR_StartDate",
                                     y="Spills",
                                     title=f"{str(county_title)} - Total Sewage {calc} 2017-2023",
                                     color_discrete_sequence=colours_sequence)
    filtered_calc_line.update_yaxes(title_text = "Duration (mins)")
    filtered_calc_line.update_layout(transition_duration=500,
                                     plot_bgcolor=colours["background"],
                                     paper_bgcolor=colours["background"],
                                     font_family="Aperto",
                                     title_font_family="Aperto")
    return filtered_calc_line


# Counties - Piechart - can change year and county.
@callback(
    Output("cp-type-duration-pie-fig","figure"),
    Input("cp-type-duration-pie-year-dropdown","value"),
    Input("cp-sum-avg-spills-county-dropdown","value")
)
def update_cp_pie(year, county):
    if isinstance(year, str):
        year = int(year)
    filtered_df = df[
        (df["County"] == county) &
        (df["Year"] == year)]
    grouped_df = filtered_df[["County", "Type", "Duration_Mins"]].groupby(by="Type", as_index=False).sum().reset_index(drop=True)

    # Update Figure
    filtered_pie = px.pie(data_frame=grouped_df,
                          names="Type",
                          values="Duration_Mins",
                          title=f"{str(county)} - Sewage Overflow Duration by Type - {str(year)}",
                          color_discrete_sequence=colours_sequence,
                          color_discrete_map=type_colour_map)
    filtered_pie.update_layout(transition_duration=100,
                               plot_bgcolor=colours["background"],
                               paper_bgcolor=colours["background"],
                               font_family="Aperto",
                               title_font_family="Aperto")
    return filtered_pie

## Counties, Sewage discharge by year, month, day, hour; quad linechart
@callback(
    Output("cp-timeperiod-line-fig", "figure"),
    Input("cp-sum-avg-spills-county-dropdown","value"),
    Input("cp-timeperiod-type-dropdown","value")
)
def update_cp_timeperiod_line(county, timeperiod):
    if isinstance(county, str):
        county = [county]
        county_title = county[0].strip("[\'").strip("\']")
    new_title = f"{str(county_title)} - Sewage Overflow by {str(timeperiod)}"
    filtered_df = counties_discharge_timeperiod[counties_discharge_timeperiod["County"].isin(county)]

    regrouped_filtered_df = filtered_df.groupby(by=[str(timeperiod),"Type"],as_index=False).sum().reset_index(drop=True)
    filtered_line = px.bar(data_frame=regrouped_filtered_df,
                           x=str(timeperiod),
                           y="Duration_Mins",
                           color="Type",
                           title=new_title,
                           color_discrete_sequence=colours_sequence,
                           color_discrete_map=type_colour_map)
    filtered_line.update_yaxes(title_text = "Duration (mins)")
    filtered_line.update_layout(transition_duration=100,
                                plot_bgcolor=colours["background"],
                                paper_bgcolor=colours["background"],
                                font_family="Aperto",
                                title_font_family="Aperto")
    return filtered_line

# County page - boxplot of sewage overflow duration, split by overflow type 3 colours. Filtered to county and year (using year dropdown on pie)
@callback(
    Output("cp-average-boxplot","figure"),
    Input("cp-sum-avg-spills-county-dropdown","value"),
    Input("cp-type-duration-pie-year-dropdown","value")
)
def update_cp_boxplot(county, year):
    if isinstance(county, str):
        county=[county]
        county_title = county[0].strip("[\'").strip("\']")
    if isinstance(year, int):
        year = [year]
    filtered_df = df[(df["County"].isin(county)) & (df["Year"].isin(year))]

    filtered_box = px.box(data_frame=filtered_df,
                          x="Type",
                          y="Duration_Mins",
                          color="Type",
                          title=f"{county_title} - Sewage Overflow Duration by Type - {str(year).strip("[\'").strip("\']")}",
                          color_discrete_sequence=colours_sequence,
                          color_discrete_map=type_colour_map)
    filtered_box.update_yaxes(title_text = "Duration (mins)")
    filtered_box.update_layout(transition_duration=500,
                               plot_bgcolor=colours["background"],
                               paper_bgcolor=colours["background"],
                               font_family="Aperto",
                               title_font_family="Aperto")
    return filtered_box




# Sites, Sewage total discharge over time and average, filterable by site(s) and type; linechart
@callback(
    Output("sp-discharge-time-line-fig","figure"),
    Input("sp-calc-type-radio","value"),
    Input("sp-site-dropdown","value")
)
def update_sp_sum_avg_line(calc_type, site):
    if isinstance(site, str):
        site = [site]

    site_name=str(site).strip("[\'").strip("\']")

    if calc_type == "Sum":
        calc_df = df[["CR_StartDate", "Type", "Site", "Duration_Mins"]].groupby(by=["CR_StartDate", "Site", "Type"], as_index=False).sum().reset_index(drop=True)
    else:
        calc_df = df[["CR_StartDate", "Site", "Spills"]].groupby(by=["CR_StartDate", "Site"], as_index=False).sum().reset_index(drop=True)


    # Filter to specific site(s)
    filtered_calc_df = calc_df[calc_df["Site"].isin(site)]

    # Create lineplot
    if calc_type == "Spills":
        filtered_calc_line = px.line(data_frame=filtered_calc_df,
                                     x="CR_StartDate",
                                     y="Spills",
                                     title=f"{site_name} - {calc_type} Occurrence - 2017-2023",
                                     color_discrete_sequence=colours_sequence,
                                     color_discrete_map=type_colour_map)
        filtered_calc_line.update_xaxes(title_text="Start date")
    elif calc_type != "Spills":
        filtered_calc_line = px.line(data_frame=filtered_calc_df,
                                     x="CR_StartDate",
                                     y="Duration_Mins",
                                     title=f"{site_name} - {calc_type} Sewage Overflow Duration - 2017-2023",
                                     color_discrete_sequence=colours_sequence)
        filtered_calc_line.update_yaxes(title_text = "Duration (mins)")
        filtered_calc_line.update_xaxes(title_text="Start date")

    filtered_calc_line.update_layout(transition_duration=500,
                                     plot_bgcolor=colours["background"],
                                     paper_bgcolor=colours["background"],
                                     font_family="Aperto",
                                     title_font_family="Aperto")
    return filtered_calc_line

# Sites, Sewage makeup by site and year; piechart
@callback(
    Output("sp-pie-fig","figure"),
    Input("sp-site-dropdown","value"),
    Input("sp-year-pie-dropdown","value")
)
def update_sp_sewage_type_pie(site, year):
    filtered_df = df[(df["Site"] == site) & (df["Year"] == year)]
    filtered_grouped_df = filtered_df[["Site", "Type", "Year", "Duration_Mins"]].groupby(by="Type",as_index=False).sum().reset_index(drop=True)

    if filtered_grouped_df.empty:
        failed_pie = px.pie(title=f"No data for {site} in {str(year)}",
                            color_discrete_sequence=colours_sequence,
                            color_discrete_map=type_colour_map)
        failed_pie.update_layout(transition_duration=500,
                                 plot_bgcolor=colours["background"],
                                 paper_bgcolor=colours["background"],
                                 yaxis={'visible': False, 'showticklabels': False},
                                 xaxis={"visible": False, "showticklabels": False},
                                 showlegend=False,
                                 font_family="Aperto",
                                 title_font_family="Aperto")
        return failed_pie

    pie = px.pie(data_frame=filtered_grouped_df,
                 names="Type",
                 values="Duration_Mins",
                 title=f"{str(site)} - Sewage Overflow Duration by Type - {str(year)}",
                 color_discrete_sequence=colours_sequence,
                 color_discrete_map=type_colour_map)
    pie.update_layout(transition_duration=500,
                      plot_bgcolor=colours["background"],
                      paper_bgcolor=colours["background"],
                      font_family="Aperto",
                      title_font_family="Aperto")
    return pie


# Sites, sewage discharge by year, month, day, hour; quad linechart. Filtered to a single site selectable.
@callback(
    Output("sp-timeperiod-line-fig","figure"),
    Input("sp-site-dropdown","value"),
    Input("sp-timeperiod-timeperiod-radio","value")
)
def update_sp_sewage_timeperiod_line(site, timeperiod):
    site = str(site)
    filtered_df = df[df["Site"] == site]
    filtered_grouped_df = filtered_df[["Site",timeperiod, "Type", "Duration_Mins"]].groupby(by=[timeperiod, "Type"], as_index=False).sum().reset_index(drop=True)

    if not filtered_grouped_df.empty:
        line_fig = px.bar(data_frame=filtered_grouped_df,
                          x=timeperiod,
                          y="Duration_Mins",
                          color="Type",
                          title=f"{site} - Sewage Overflow Duration by {timeperiod}",
                          color_discrete_sequence=colours_sequence,
                          color_discrete_map=type_colour_map)
        line_fig.update_yaxes(title_text = "Duration (mins)")
        line_fig.update_layout(transition_duration=500,
                               plot_bgcolor=colours["background"],
                               paper_bgcolor=colours["background"],
                               font_family="Aperto",
                               title_font_family="Aperto")
        return line_fig
    else:
        failed_line = px.line(title=f"No data for {site} at {timeperiod}")
        failed_line.update_layout(transition_duration=500,
                                  plot_bgcolor=colours["background"],
                                  paper_bgcolor=colours["background"],
                                  yaxis={'visible': False, 'showticklabels': False},
                                  xaxis={"visible": False, "showticklabels": False},
                                  showlegend=False,
                                  font_family="Aperto",
                                  title_font_family="Aperto")
        return failed_line

# Sites, boxplot by year and type
@callback(
    Output("sp-box","figure"),
    Input("sp-year-pie-dropdown","value"),
    Input("sp-site-dropdown","value")
)
def update_sp_boxplot(year, site):
    filtered_df = df[(df["Year"] == year) & (df["Site"] == site)]

    if filtered_df.empty:
        failed_box = px.box(title=f"No data for {site} in {year}")
        failed_box.update_layout(transition_duration=500,
                                 plot_bgcolor=colours["background"],
                                 paper_bgcolor=colours["background"],
                                 yaxis={'visible': False, 'showticklabels': False},
                                 xaxis={"visible": False, "showticklabels": False},
                                 showlegend=False,
                                 font_family="Aperto",
                                 title_font_family="Aperto")
        return failed_box
    else:

        sp_box = px.box(data_frame=filtered_df,
                        x="Type",
                        y="Duration_Mins",
                        color="Type",
                        title=f"{site.strip("[\'").strip("\']")} Sewage Overflow Duration by Type - {str(year)}",
                        color_discrete_sequence=colours_sequence,
                        color_discrete_map=type_colour_map)
        sp_box.update_yaxes(title_text = "Duration (mins)")
        sp_box.update_layout(transition_duration=500,
                             plot_bgcolor=colours["background"],
                             paper_bgcolor=colours["background"],
                             font_family="Aperto",
                             title_font_family="Aperto")
        return sp_box

#######################################################################################################################
# Run the application locally.
if __name__ == '__main__':
    app.run(debug=True)
