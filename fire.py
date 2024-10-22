import pandas as pd  # (versio0.24.2)
import dash
from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
df = pd.read_csv("df_MP_Final1.csv",encoding='unicode_escape')
df['acq_date'] = pd.to_datetime(df['acq_date'],dayfirst=True).dt.date
#nat_parks = gpd.read_file("nat_parks.geojson")
#nat_parks_MP = nat_parks[(nat_parks.State.isin(['Madhya Pradesh']))].reset_index().drop(columns=['index'])

# radio = dbc.RadioItems(
#     options=[{"label": "Yes", "value": 0}, {"label": "No", "value": 1}],
#     value=1,
#     id="map-radio",
# )
# animation = dbc.RadioItems(
#         options=[{"label": "Yes", "value": 0}, {"label": "No", "value": 1}],
#         value=1,
#         id="map-animation-radio",
#     )
styleDrop = dcc.Dropdown(
    options=[
        "carto-darkmatter",
        "carto-positron",
        "white-bg",
        "open-street-map",
    ],
    value="open-street-map",
    id="map-dropdown",
    clearable=False,
)
fire_group = (
    df.groupby(by=["name", "acq_year", "Month_Year"])["rain (mm)"]
    .count()
    .reset_index()
)
fire_group.columns = ["Park", "Year", "Month_Year", "WildFires_Count"]

fig = px.scatter_mapbox(df,
                        lat='lat_adj',
                        lon='lon_adj',
                        # z='brightness',
                        # radius=10,
                        #center=dict(lat=df.lat_adj.median(), lon=df.lon_adj.median()),
                        zoom=9,
                        mapbox_style="open-street-map",
                        custom_data=[
                            "name",
                            "acq_date",
                            "elevation",
                            "rain (mm)",
                            "wind_speed_max (km/h)",
                            "wind_gusts_max (km/h)",
                            "wind_direction_dominant (°N)",
                            "precipitation (mm)",
                            "temp_mean (°C)",
                            "temp_max (°C)",
                        ]
                        )
fig3 = px.bar(
    df,
    x="Month_Year",
    y="name",
    color="name",
    barmode="group",
    height=500,
)

fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, showlegend=False)
fig.update_traces(hovertemplate="Park: %{custom_data[0]} <br>Date: %{custom_data[1]}")

yearFilter = dcc.Dropdown(
    options=["all"] + [year for year in df.acq_year.unique()],
    value="all",
    id="years-dropdown",
    clearable=False,
)

parkFilter = dcc.Dropdown(
    options=["all"] + [park for park in df.name.unique()],
    value="all",
    id="parks-dropdown",
    clearable=False,
)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                )
server = app.server

app.layout = dbc.Container(
    html.Div([
        html.Br(),
        dbc.Row(
            [
                dbc.Col(html.H6("Wild-Fires in Protected Areas of MP, India", className="ml-4",
                                style={"font-family": "Open Sans", "font-weight": "bold", "font-size": 26,
                                       'color': '#ffffff',
                                       'marginTop': 10, 'marginLeft': 200}),width=7),
                dbc.Col(
                html.Div(
                    [
                        dbc.Button(
                            "INFO",
                            id="popover-target",
                            className="me-1",
                        ),
                        dbc.Popover(
                            dbc.PopoverBody(
                                html.H6(" This application explores the fires of recent years in protected areas of MP, India using data from NASA."
                                        " The data set was downlaoded from Nasa's Firms website(https://firms.modaps.eosdis.nasa.gov/)"
                                        " Data subset over 2019-2023 timeframe."
                                        " Wildfires detected over with high confidence - MODIS data confindence >= 80%."
                                        " Dataset enriched with weather condition from open-meteo api."
                                            )
                            ),
                            target="popover-target",
                            trigger="click",
                            is_open=False,
                        ),
                    ], style={'marginTop': 5, 'marginLeft': 450}
                ),width=2
                )
            ], style={'background-color': '#2184fa'}, align="center",
                className="border rounded-3 p-1",
        ),
        html.Br(),
        dbc.Container([
            dbc.Row(
                [
                    html.H4("Data Filters", className="card-text"),
                    dbc.Col([dbc.Label("Years"), yearFilter], width=3),
                    dbc.Col([dbc.Label("Parks"), parkFilter], width=4),
                    #dbc.Col([dbc.Label("Animation"), animation]),
                    #dbc.Col([dbc.Label("Parks Borders"), radio]),
                    dbc.Col([dbc.Label("Style"), styleDrop],width=3),
                ],
                align="center",
                className="border rounded-3 p-3",
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col([dcc.Graph(figure=fig, clickData=None, id="map")], width=9),
                    dbc.Col(
                        [
                            html.H4("WildFires Details", className="card-text"),
                            html.H6("click points on the map", className="card-text"),
                            html.Hr(),
                            html.Div(children="", id="clicked-data"),
                        ],
                        width=3,
                        className="border rounded-3 p-3",
                    ),
                ]
            ),
            dbc.Row(dbc.Spinner(html.Div(id="loading-output"))),
            html.Br(),
            dbc.Row(
                [
                    html.H4("Wildfires Trend", className="card-text", style={'marginLeft': 400}),
                    dbc.Col([dcc.Graph(figure=fig3, id="trend")]),
                ]
            ,className="border rounded-3 p-3"),
        ])
    ])
)

@callback(
    Output("map", "figure"),
    Output("loading-output", "children"),
    Output("trend", "figure"),
    #Input("map-radio", "value"),
    Input("map-dropdown", "value"),
    #Input("map-animation-radio", "value"),
    Input("years-dropdown", "value"),
    Input("parks-dropdown", "value"),
    prevent_initial_call=True,
)
def update_map( vizStyle, year, park):
    custom_data = [
        "name",
        "acq_date",
        "elevation",
        "rain (mm)",
        "wind_speed_max (km/h)",
        "wind_gusts_max (km/h)",
        "wind_direction_dominant (°N)",
        "precipitation (mm)",
        "temp_mean (°C)",
        "temp_max (°C)",
    ]

    fire_ff = pd.DataFrame()
    #parks_ff = pd.DataFrame()
    #fire_group_ff = pd.DataFrame()
    fire_ff = df
    #parks_ff = nat_parks_MP
    fire_group_ff = fire_group
    if year != "all":
        fire_ff = fire_ff[fire_ff.acq_year == year]
        fire_group_ff = fire_group_ff[fire_group_ff.Year == year]

    if park != "all":
        fire_ff = fire_ff[fire_ff.name == park]
        #parks_ff = parks_ff[parks_ff.name == park]
        fire_group_ff = fire_group_ff[fire_group_ff.Park == park]

    #if (vizOption == 1):
        fig = px.scatter_mapbox(
            fire_ff,
            lat="lat_adj",
            lon="lon_adj",
            # center=dict(lat=fire.lat_adj.median(), lon=fire.lon_adj.median()),
            zoom=9,
            mapbox_style=vizStyle,  # "carto-positron",
            #animation_frame="year_month",
            custom_data=custom_data,
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig.update_traces(
            hovertemplate="Park: %{customdata[0]} <br>Date: %{customdata[1]}"
        )
    # elif (vizOption == 1):
    #     fig = px.scatter_mapbox(
    #         fire_ff,
    #         lat="lat_adj",
    #         lon="lon_adj",
    #         # center=dict(lat=fire.lat_adj.median(), lon=fire.lon_adj.median()),
    #         zoom=9,
    #         mapbox_style=vizStyle,  # "carto-positron",
    #         custom_data=custom_data,
    #     )
    #     fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    #     fig.update_traces(
    #         hovertemplate="Park: %{customdata[0]} <br>Date: %{customdata[1]}"
    #     )
    # elif (vizOption == 0):
    #     fig = px.scatter_mapbox(
    #         fire_ff,
    #         lat="lat_adj",
    #         lon="lon_adj",
    #         # center=dict(lat=fire.lat_adj.median(), lon=fire.lon_adj.median()),
    #         zoom=9,
    #         mapbox_style=vizStyle,  # "carto-positron",
    #         #animation_frame="year_month",
    #         custom_data=custom_data,
    #     )
    #     fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    #     fig.update_traces(
    #         hovertemplate="Park: %{customdata[0]} <br>Date: %{customdata[1]}"
    #     )
    #     fig2 = px.choropleth_mapbox(
    #         parks_ff,
    #         geojson=parks_ff.geometry,
    #         locations=parks_ff.index,
    #         color=parks_ff.name,
    #         color_continuous_scale="Viridis",
    #         range_color=(50, 100),
    #         mapbox_style=vizStyle,  # ""carto-positron",
    #         zoom=9,
    #         center={"lat": fire_ff.lat_adj.median(), "lon": fire_ff.lon_adj.median()},
    #         opacity=0.5,
    #     )
    #     trace0 = fig2
    #     for i in range(len(trace0.data)):
    #         fig.add_trace(trace0.data[i])
    #         trace0.layout.update(showlegend=False)
    #     print("update done ")
    #     fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    #     fig.update_traces(
    #         hovertemplate="Park: %{customdata[0]} <br>Date: %{customdata[1]}"
    #     )
    # else:
    #     fig = px.scatter_mapbox(
    #         fire_ff,
    #         lat="lat_adj",
    #         lon="lon_adj",
    #         center=dict(lat=fire_ff.lat_adj.median(), lon=fire_ff.lon_adj.median()),
    #         zoom=9,
    #         mapbox_style=vizStyle,
    #         custom_data=custom_data,  # ""carto-positron",
    #     )
    #     fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    #     fig.update_traces(
    #         hovertemplate="Park: %{customdata[0]} <br>Date: %{customdata[1]}"
    #     )
    #     fig2 = px.choropleth_mapbox(
    #         parks_ff,
    #         geojson=parks_ff.geometry,
    #         locations=parks_ff.index,
    #         color=parks_ff.name,
    #         color_continuous_scale="Viridis",
    #         range_color=(50, 100),
    #         mapbox_style=vizStyle,  # ""carto-positron",
    #         zoom=9,
    #         center={"lat": fire_ff.lat_adj.median(), "lon": fire_ff.lon_adj.median()},
    #         opacity=0.5,
    #     )
    #     trace0 = fig2
    #     for i in range(len(trace0.data)):
    #         fig.add_trace(trace0.data[i])
    #         trace0.layout.update(showlegend=False)
    #     print("update done ")
    #     fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    #     fig.update_traces(
    #         hovertemplate="Park: %{customdata[0]} <br>Date: %{customdata[1]}"
    #     )
    fig3 = px.bar(
        fire_group_ff,
        x="Month_Year",
        y="WildFires_Count",
        color="Park",
        barmode="group",
        height=500,
    )

    return fig, "", fig3


@callback(
    Output("clicked-data", "children"),
    Input("map", "clickData"),
    prevent_initial_call=True,
)
def clickedData(clickData):
    if "customdata" in clickData["points"][0].keys():
        print(f"{clickData['points'][0]['customdata']}")
        parkInfo = f"Park: {clickData['points'][0]['customdata'][0]}"
        dateInfo = f"Date: {clickData['points'][0]['customdata'][1]}"
        ElevationInfo = f"elevation: {clickData['points'][0]['customdata'][2]}"
        RainInfo = f"rain (mm): {clickData['points'][0]['customdata'][3]}"
        WindspeedInfo = (
            f"wind_speed_max (km/h): {clickData['points'][0]['customdata'][4]}"
        )
        WindgustInfo = f"wind_gusts_max (km/h): {clickData['points'][0]['customdata'][5]}"
        winddirectionInfo = f"wind_direction_dominant (°N): {clickData['points'][0]['customdata'][6]}"
        precipitaionInfo = f"precipitation (mm): {clickData['points'][0]['customdata'][7]} "
        tempmeanInfo = f"temp_mean (°C): {clickData['points'][0]['customdata'][8]} "
        tempmaxInfo = f"temp_max (°C): {clickData['points'][0]['customdata'][9]} "
        # info = [parkInfo, dateInfo, temperatureInfo]
        # click = f"Park: {clickData['points'][0]['customdata'][0]}\n Date: {clickData['points'][0]['customdata'][1]}\n "
        click = [
            html.P(parkInfo),
            html.P(dateInfo),
            html.P(ElevationInfo),
            html.P(RainInfo),
            html.P(WindspeedInfo),
            html.P(WindgustInfo),
            html.P(winddirectionInfo),
            html.P(precipitaionInfo),
            html.P(tempmeanInfo),
            html.P(tempmaxInfo),
        ]
    else:
        click = (
            "Invalid selecton. Details on demand enabled w/o Parks Borders only!"
        )
    # if clickData["points"][0]["customdata"] == None:
    #     click = "No valid point selected"
    # else:
    #     click = f"{clickData}"
    # click = f"{clickData['points'][0]['customdata']}"
    return click


if __name__ == '__main__':
    app.run_server(debug=True, port=8000)
