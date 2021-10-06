from __future__ import print_function
from google.oauth2 import service_account
import utility
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from dash.dependencies import Input, Output


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = 'keys.json'

credentials=None
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# The ID and range of a sample spreadsheet.
CHARGE_SPREADSHEET_ID = '1Lq519W-aIu9kERUwDgY1Z6W0xIjChPk7WSf58wM5ZWw'
TRIP_SPREADSHEET_ID = '16BraPT4BMTZZu_8q7DxqlZYI1ITXjnb3MUR5GEB5Qo4'
PARK_SPREADSHEET_ID = '1rvgmptBj0Yec7m6-E8t1V-Mdnv3HI2Fm0Y0qnuwjsnY'

#fetch trip , charge and park details and create df
charge_df = utility.getChargeDF(credentials, CHARGE_SPREADSHEET_ID)
trip_df = utility.getTripDF(credentials, TRIP_SPREADSHEET_ID, charge_df)
park_df = utility.getParkDF(credentials, PARK_SPREADSHEET_ID)

#filtering data that is not important
park_df = park_df[park_df["duration"] / (60 * 60) > 1]
trip_df = trip_df[trip_df["distance_traveled"] >= 1]

#creating cols for analysis
trip_df["avg_temp"] = trip_df["avg_temp"].apply(np.ceil)
trip_df["trip_start_mm"] = pd.to_datetime(trip_df["trip_start_date"]).dt.strftime('%Y-%m')

charge_df["charge_start_mm"] = pd.to_datetime(charge_df["session_start_date"]).dt.strftime('%Y-%m')
charge_df["charge_duration"] = charge_df["charge_duration"] / (60 * 60)

park_df["avg_temp"] = park_df['avg_temp'].apply(np.ceil)
park_df["park_start_mm"] = pd.to_datetime(park_df["park_start_date"]).dt.strftime('%Y-%m')
park_df["duration"] = park_df["duration"] / (60 * 60)
park_df = park_df[park_df["duration"] < 24]

########TRIP###############

trip_dis_date = trip_df.groupby("trip_start_date").agg({'distance_traveled': 'sum', 'efficiency': 'mean','avg_temp':'mean'})
trip_dis_date_mm = trip_df.groupby("trip_start_mm").agg({'distance_traveled': 'sum', 'efficiency': 'mean','avg_temp':'mean'})\
    .rename(columns = {"trip_start_mm" : "trip_start_date"})

trip_temp_wh_date = trip_df.groupby("trip_start_date").mean()[["wh/km", "avg_temp", "max_kwh", "real_dis"]]
trip_temp_wh_mm = trip_df.groupby("trip_start_mm").mean()[["wh/km", "avg_temp", "max_kwh", "real_dis"]]\
    .rename(columns = {"trip_start_mm" : "trip_start_date"})

trip_eff_temp = trip_df.groupby("avg_temp").mean()["efficiency"]

trip_freq_date = trip_df.groupby("trip_start_date").count()["charge_session_id"].rename("count")
trip_freq_mm = trip_df.groupby("trip_start_mm").count()["charge_session_id"].rename("count")

trip_avg_dis_date = trip_df.groupby("trip_start_date").mean()["distance_traveled"]
trip_avg_dis_mm = trip_df.groupby("trip_start_mm").mean()["distance_traveled"]

#########PARK LOSS############
park_loss_date_df = park_df.groupby("park_start_date").sum()[["battery_%_lost", "duration"]]
park_loss_mm_df = park_df.groupby("park_start_mm").sum()[["battery_%_lost", "duration"]]\
    .rename(columns = {"park_start_mm" : "park_start_date"})

#park_loss_df.reset_index(inplace=True)

park_loss_sentry_df = park_df[park_df["wh_loss_rate_per_hr"] > 0].groupby(["avg_temp", "park_sentry_mode"]).mean()[
        "wh_loss_rate_per_hr"]
############Money Saved#########
# total cost comparison between ice and aura per day , month , year
trip_cost_km_ev_date = trip_df[["trip_start_date", "cost_ev", "distance_traveled"]]
trip_cost_km_ev_date["type"] = "aura"
trip_cost_km_ev_date.rename(columns={"cost_ev": "cost"}, inplace=True)

trip_cost_km_ice_date = trip_df[["trip_start_date", "cost_ice", "distance_traveled"]]
trip_cost_km_ice_date["type"] = "ice"
trip_cost_km_ice_date.rename(columns={"cost_ice": "cost"}, inplace=True)

trip_cost_km = pd.concat([trip_cost_km_ev_date, trip_cost_km_ice_date])
trip_cost_km_date = trip_cost_km.groupby(["trip_start_date", "type"]).sum()

trip_cost_km["trip_start_date"] = pd.to_datetime(trip_cost_km["trip_start_date"]).dt.strftime('%Y-%m')
trip_cost_km_mm = trip_cost_km.groupby(["trip_start_date", "type"]).sum()

# relation between distance traved and money savings
dis_sav = trip_df.groupby("distance_traveled").mean()[["money_saved", "avg_temp"]]
# relation between temprature and money savings
temp_sav = trip_df.groupby("avg_temp").mean()["money_saved"]

###############Charge Details#####################
charge_df = charge_df[["session_start_date", "charge_start_mm", "charge_duration", "kwh_added", "charge_level", "cost"]]

charge_details_dd = charge_df.groupby(["session_start_date", "charge_level"]).mean()[["charge_duration", "cost"]]
charge_details_mm = charge_df.groupby(["charge_start_mm", "charge_level"]).agg(
        {'charge_duration': 'mean', 'cost': 'mean'})
charge_details_mm_tot = charge_df.groupby(["charge_start_mm", "charge_level"]).agg(
        {'charge_duration': 'mean', 'cost': 'sum'})
charge_freq = charge_df.groupby(["charge_start_mm", "charge_level"]).count()
###################################################

EXTERNAL_STYLESHEETS = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
TESLA_LOGO = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTotNbQQhpxWDf5-DhC5vwXo0PMzYynpeFRAQ&usqp=CAU"

###############################Navigation Bar#######################
NAVBAR = dbc.Navbar(
        children=[
                html.A(
                        # Use row and col to control vertical alignment of logo / brand
                        dbc.Row(
                                [
                                        dbc.Col(html.Img(src=TESLA_LOGO, height="30px")),
                                        dbc.Col(
                                                dbc.NavbarBrand("Aura's Report Card", className="ml-2")
                                        ),
                                ],
                                align="center",
                                no_gutters=True,
                        ),
                        href="https://ts.la/sarthak94017",
                )
        ],
        color="dark",
        dark=True,
        sticky="top",
)


########## Summary Blocks ##################
TOT_KM = dbc.Jumbotron(
    [
        html.H6(children="Distance Travelled"),
        html.Hr(className="my-2"),
        html.Label(str(float("{:.2f}".format(trip_df["distance_traveled"].sum()))) + " Km"),
    ]
)

TOT_CAD_SPENT = dbc.Jumbotron(
    [
        html.H6(children="Money Spent"),
        html.Hr(className="my-2"),
        html.Label(str(float("{:.2f}".format(charge_df["cost"].sum()))) + " CAD"),
    ]
)

TOT_CAD_SAVED = dbc.Jumbotron(
    [
        html.H6(children="Money Saved*"),
        html.Hr(className="my-2"),
        html.Label(str(float("{:.2f}".format(trip_df["money_saved"].sum()))) + " CAD"),
    ]
)

AVG_EFF = dbc.Jumbotron(
    [
        html.H6(children="Average Efficiency"),
        html.Hr(className="my-2"),
        html.Label(str(float("{:.2f}".format(trip_df["efficiency"].mean()))) + " %"),
    ]
)

AVG_WH = dbc.Jumbotron(
    [
        html.H6(children="Average Wh/Km"),
        html.Hr(className="my-2"),
        html.Label(float("{:.2f}".format(trip_df["wh/km"].mean()))),
    ]
)

#################################

#############Energy Capacity###########################################################################
def display_tot_cap():

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])


    # Add traces
    fig.add_trace(
        go.Scatter(x=trip_temp_wh_mm.index, y=trip_temp_wh_mm["max_kwh"], name="Energy capacity"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=trip_temp_wh_mm.index, y=trip_temp_wh_mm["real_dis"], name="Distance on full charge (KM)"),
        secondary_y="Secondary" == 'Secondary',
    )

    # Add figure title
    fig.update_layout(
        title_text="Energy Capacity"
    )

    # Set x-axis title
    fig.update_xaxes(title_text="Time")

    # Set y-axes titles
    fig.update_yaxes(
        title_text="Energy capacity (KWh)",
        secondary_y=False)
    fig.update_yaxes(
        title_text="Distance on full charge (KM)",
        secondary_y=True)

    return fig


TOT_KWH_PLOT = [
    dbc.CardHeader(html.H5("Energy Capacity")),
    dbc.CardBody(
        [
          dcc.Graph(id="line-chart-max-kwh",figure = display_tot_cap()),
        ],
        style={"marginTop": 0, "marginBottom": 0},
    ),
]

###### PLOTS for TRIP############
def display_trip_wh(df):
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Bar(x=df.index, y=df["wh/km"], name="wh/km"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=df.index, y=df["avg_temp"], name="Temprature"),
        secondary_y="Secondary" == 'Secondary',
    )

    # Add figure title
    fig.update_layout(
        title_text="wh/km across time"
    )

    # Set x-axis title
    fig.update_xaxes(title_text="Time")

    # Set y-axes titles
    fig.update_yaxes(
        title_text="wh/km",
        secondary_y=False)
    fig.update_yaxes(
        title_text="Temprature",
        secondary_y=True)

    return fig

def display_trip_dis_eff(df):
  # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Bar(x=df.index, y=df["distance_traveled"], name="Total Distance traveled"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=df.index, y=df["efficiency"], name="Avg Efficiency"),
        secondary_y="Secondary" == 'Secondary',
    )


    fig.add_trace(
        go.Scatter(x=df.index, y=df["avg_temp"], name="Avg Temp"),
        secondary_y="Secondary" == 'Secondary',
    )

    # Add figure title
    fig.update_layout(
        title_text="Distance Travelled Across Time"
    )

    # Set x-axis title
    fig.update_xaxes(title_text="Time")

    # Set y-axes titles
    fig.update_yaxes(
        title_text="Total Distance traveled",
        secondary_y=False)
    fig.update_yaxes(
        title_text="Avg Efficiency",
        secondary_y=True)

    return fig

def getBarGraph(df):
    return px.bar(df, x=df.index, y="count",title="Number of trips",labels={
                     "x": "Date",
                     "count": "count"
                 })

#Trip Freq per month
TRIP_FRQ = dbc.Card([
    dbc.Button('<-', id='trip_freq_back-button', outline=True, size="sm",className='mt-2 ml-2 col-1', style={'display': 'none'}),
    dcc.Graph(id="trip_freq",figure = getBarGraph(trip_freq_mm))])

#Trip Avg Distance
TRIP_AVG_DIST = dbc.Card(dcc.Graph(id="trip_avg_dis",figure = px.bar(trip_avg_dis_mm, x=trip_avg_dis_mm.index, y="distance_traveled",title="Average Trip Distance",labels={
                     "x": "Date",
                     "distance_traveled": "Average Distance"
                 })))


#TOTAL distance traveled per day/MOnth
DIS_TIME = dbc.Card([
    dbc.Button('<-', id='km_per_time_back-button', outline=True, size="sm",className='mt-2 ml-2 col-1', style={'display': 'none'}),
    dcc.Graph(id="km_per_time",figure = display_trip_dis_eff(trip_dis_date_mm))])

#trip efficiency per day/Month + temprature
EFF_TIME_TEMP = dbc.Card(dcc.Graph(id="eff_per_time",figure = px.area(trip_eff_temp, x=trip_eff_temp.index, y="efficiency",title="Relation of Temprature and Efficiency",labels={
                     "x": "Temprature",
                     "efficiency": "Efficiency %"
                 })))

#wh/km across time + temprature
WH_TIME_TEMP = dbc.Card(dcc.Graph(id="wh_per_time",figure = display_trip_wh(trip_temp_wh_mm)))




################################
##############PLOTS for LOSS########
def display_loss_wh(df):

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])


    # Add traces
    fig.add_trace(
        go.Bar(x=df.index, y=df["battery_%_lost"], name="Phantom Loss %"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=df.index, y=df["duration"], name="Parking Duration (hr)"),
        secondary_y="Secondary" == 'Secondary',
    )

    # Add figure title
    fig.update_layout(
        title_text="Phantom Loss Across Time"
    )

    # Set x-axis title
    fig.update_xaxes(title_text="Time")

    # Set y-axes titles
    fig.update_yaxes(
        title_text="Phantom Loss %",
        secondary_y=False)
    fig.update_yaxes(
        title_text="Parking Duration (hr)",
        secondary_y=True)

    return fig

#total phantom loss per day/Month
LOSS_TIME = dbc.Card(dcc.Graph(id="loss_per_time",figure = display_loss_wh(park_loss_mm_df)))
#pantom loss rate per day/Month + temprature
LOSS_TIME_TEMP = dbc.Card(dcc.Graph(id="loss_per_temp",figure = px.bar(park_loss_sentry_df, x=park_loss_sentry_df.index.get_level_values('avg_temp'),
                                                                       y="wh_loss_rate_per_hr",barmode="group",color=park_loss_sentry_df.index.get_level_values("park_sentry_mode"),title="Phantom Loss and sentry mode"
                                                                       ,labels={
                     "x": "Temprature",
                     "wh_loss_rate_per_hr": "Loss Rate per Hour (Wh)",
                     "color":"Sentry Mode"
                 })))
####################################
##############PLOTS for savings########
# total cost comparison between ice and aura per day , month , year
def display_cost_wh(df):
        aura = df[df.index.isin(['aura'], level=1)]
        ice = df[df.index.isin(['ice'], level=1)]

        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add traces
        fig.add_trace(
                go.Bar(x=aura.index.get_level_values("trip_start_date"), y=aura["cost"], name="Aura's expense (CAD)"),
                secondary_y=False,
        )

        fig.add_trace(
                go.Bar(x=ice.index.get_level_values("trip_start_date"), y=ice["cost"], name="ICE's expense (CAD)"),
                secondary_y=False,
        )

        fig.update_layout(barmode='group')

        fig.add_trace(
                go.Scatter(x=aura.index.get_level_values("trip_start_date"), y=aura["distance_traveled"],
                           name="Distance Traveled (km)"),
                secondary_y="Secondary" == 'Secondary',
        )

        # Add figure title
        fig.update_layout(
                title_text="Cost Comparison between Aura and ICE"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Set y-axes titles
        fig.update_yaxes(
                title_text="Cost (CAD)",
                secondary_y=False)
        fig.update_yaxes(
                title_text="Distance Traveled (km)",
                secondary_y=True)

        return fig


COST_TIME = dbc.Card(dcc.Graph(id="cost_time", figure=display_cost_wh(trip_cost_km_mm)))
# relation between distance traved and money savings
DIST_SAV = dbc.Card(dcc.Graph(id="dist_sav",
                              figure=px.scatter(dis_sav, x=dis_sav.index, y="money_saved", color="avg_temp",
                                                title="Relation Between Distance Traveled and Money Spent on Fuel",
                                                labels={
                                                        "x": "Distance Travelled",
                                                        "money_saved": "Savings (CAD)"
                                                })))
# relation between temprature and money savings
TEMP_SAV = dbc.Card(dcc.Graph(id="temp_sav", figure=px.line(temp_sav, x=temp_sav.index, y="money_saved",
                                                            title="Relation Between Temprature and Money Saved",
                                                            labels={
                                                                    "x": "Temprature",
                                                                    "money_saved": "Savings (CAD)"
                                                            })))
##########################################################
####################PLOTS for Charge##########################
#1. charge sessions by Month -- type , cost , duration
#Trip Freq per month
CHARGE_COST = dbc.Card(dcc.Graph(id="CHARGE_COST",figure = px.bar(charge_details_mm, x=charge_details_mm.index.get_level_values('charge_start_mm'), y='cost',title="Avg Charge Cost per Session",barmode="group",
                                                                  color=charge_details_mm.index.get_level_values('charge_level'),labels={
                     "x": "Date",
                     "cost": "cost (CAD)"
                 })))

TOT_CHARGE_COST = dbc.Card(dcc.Graph(id="TOT_CHARGE_COST",figure = px.bar(charge_details_mm_tot, x=charge_details_mm_tot.index.get_level_values('charge_start_mm'), y='cost',title="Total Charge Cost",barmode="group",
                                                                  color=charge_details_mm.index.get_level_values('charge_level'),labels={
                     "x": "Date",
                     "cost": "cost (CAD)"
                 })))


CHARGE_TIME = dbc.Card(dcc.Graph(id="CHARGE_TIME",figure = px.bar(charge_details_mm, x=charge_details_mm.index.get_level_values('charge_start_mm'), y="charge_duration"
                ,barmode="group",color=charge_details_mm.index.get_level_values('charge_level'),title="Avg Charge Time per Session",labels={
                     "x": "Date",
                     "count": "count"
                 })))

CHARGE_FREQ = dbc.Card(dcc.Graph(id="CHARGE_FREQ",figure = px.bar(charge_freq, x=charge_freq.index.get_level_values('charge_start_mm'), y="cost",barmode="group",
                                                                  color=charge_freq.index.get_level_values('charge_level'),title="Number of sessions",labels={
                     "x": "Date",
                     "cost": "count"
                 })))
##############################################################
############################Design###########################
DETAIL_PLOTS = [
        dbc.CardHeader(html.H5("Trip, Parking and Savings Details")),
        dbc.CardBody(
                [
                        dbc.Row(
                                [
                                dbc.Col(
                                        [
                                        dcc.Tabs(
                                                id="tabs",
                                                children=[
                                                        dcc.Tab(
                                                                label="Trip Details",
                                                                children=[
                                                                        dcc.Loading(
                                                                                id="loading-treemap",
                                                                                children=[
                                                                                        dbc.Row([dbc.Col(DIS_TIME), ],style={"marginTop": 30}),
                                                                                        dbc.Row([dbc.Col(EFF_TIME_TEMP), ],style={"marginTop": 30}),
                                                                                        dbc.Row([dbc.Col(TRIP_FRQ),dbc.Col(TRIP_AVG_DIST), ],style={"marginTop": 30}),
                                                                                        dbc.Row([dbc.Col(WH_TIME_TEMP), ],style={"marginTop": 30}),
                                                                                ],
                                                                                type="default",
                                                                        )
                                                                ],
                                                        ),
                                                        dcc.Tab(
                                                                label="Phantom Loss",
                                                                children=[
                                                                        dcc.Loading(
                                                                                id="loading-wordcloud",
                                                                                children=[
                                                                                        dbc.Row([dbc.Col(LOSS_TIME),], style={"marginTop": 30}),
                                                                                        dbc.Row([dbc.Col(LOSS_TIME_TEMP),], style={"marginTop": 30}),
                                                                                ],
                                                                                type="default",
                                                                        )
                                                                ],
                                                        ),
                                                        dcc.Tab(
                                                                label="Savings",
                                                                children=[
                                                                    dcc.Loading(
                                                                        id="sav_tab",
                                                                        children=[
                                                                            dbc.Row([dbc.Col(DIST_SAV),], style={"marginTop": 30}),
                                                                            dbc.Row([dbc.Col(COST_TIME),], style={"marginTop": 30}),
                                                                        ],
                                                                        type="default",
                                                                    )
                                                                ],
                                                            ),
                                                        dcc.Tab(
                                                                label="Charge",
                                                                children=[
                                                                    dcc.Loading(
                                                                        id="char_tab",
                                                                        children=[
                                                                            dbc.Row([dbc.Col(CHARGE_COST),dbc.Col(CHARGE_TIME),], style={"marginTop": 30}),
                                                                            dbc.Row([dbc.Col(TOT_CHARGE_COST),], style={"marginTop": 30}),
                                                                            dbc.Row([dbc.Col(CHARGE_FREQ),], style={"marginTop": 30}),
                                                                        ],
                                                                        type="default",
                                                                    )
                                                                ],
                                                            ),


                                                ],
                                        )
                                        ],
                                        md=12,
                                ),
                                ]
                        )
                ]
        ),
]

####################################################

BODY = dbc.Container(
    [
        dbc.Row([dbc.Col(TOT_KM),dbc.Col(AVG_EFF),dbc.Col(AVG_WH),dbc.Col(TOT_CAD_SPENT),dbc.Col(TOT_CAD_SAVED),], style={"marginTop": 30}),
        dbc.Row([dbc.Col(dbc.Card(TOT_KWH_PLOT)),], style={"marginTop": 30}),
        dbc.Row([dbc.Col(dbc.Card(DETAIL_PLOTS)),], style={"marginTop": 30}),
    ],
)




def serve_layout():
    return html.Div(children=[NAVBAR,BODY, html.Label("*Assumptions -->fule price = 1.20/L and Fule used per 100km = 7 L"),html.Label(" Data last updated @ " + str(datetime.datetime.now()))])

app.layout = serve_layout()



#Callback

@app.callback(
    [Output('trip_freq', component_property='figure'),
    Output('trip_freq_back-button', component_property='style')], #to hide/unhide the back button
    [Input('trip_freq', 'clickData'),Input('trip_freq_back-button', 'n_clicks')]
)
def noOfTripsdrilldown(click_data,n_clicks):
    # using callback context to check which input was fired
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == 'trip_freq':
        month = click_data['points'][0]['label'][:-3]
        fig = getBarGraph(trip_freq_date.filter(like=month))
        return fig, {'display': 'block'}
    else:
        return getBarGraph(trip_freq_mm), {'display': 'none'}


@app.callback(
    [Output('km_per_time', component_property='figure'),
    Output('km_per_time_back-button', component_property='style')], #to hide/unhide the back button
    [Input('km_per_time', 'clickData'),Input('km_per_time_back-button', 'n_clicks')]
)
def km_per_timedrilldown(click_data,n_clicks):
    # using callback context to check which input was fired
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == 'km_per_time':
        month = click_data['points'][0]['label'][:-3]
        fig = display_trip_dis_eff(trip_dis_date.filter(like=month,axis=0))
        return fig, {'display': 'block'}
    else:
        return display_trip_dis_eff(trip_dis_date_mm), {'display': 'none'}





if __name__ == '__main__':
        app.run_server(host="0.0.0.0", port=8050,debug=True)

#docker build -t dash .
#docker run -p 8050:8050 -v "$(pwd)"/app:/app --rm dash
#docker login
#docker tag dash sarthaknautiyal/dash-azure:1.0.0
#docker push sarthaknautiyal/dash-azure:1.0.0
