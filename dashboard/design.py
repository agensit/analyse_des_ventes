import os

import pandas as pd
import numpy as np
from dateutil.parser import parse
import plotly.graph_objects as go

import datetime
import calendar

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input


'''
   ------------------------------------------------------------------------------------------- 
                                            CONFIG
   ------------------------------------------------------------------------------------------- 
'''
# ## TODO: GET RESOLUTION OF THE WEB BROWSER

## PLOTLY
import plotly.io as pio
pio.templates.default = "plotly_white"

## DASH
config_dash = {'displayModeBar': False, 'showAxisDragHandles':False, "responsive":True}  
margin = dict(l=20, r=20, t=10, b=10)
# External CSS + Dash Bootstrap components
external_stylesheets=[dbc.themes.BOOTSTRAP, "assets/main.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

## USE THE FRENCH DATE - not working with heroku
import locale
locale.setlocale(locale.LC_TIME, "fr_FR")

## COLOR & OPACITY
blue = '#3980b7'
green = '#55a630'
red ='#e71d36'  
grey = '#6c757d'
target_opacity = 0.7

## USEFUL FUNCTION
def millify(n):
    if n > 999:
        if n > 1e6-1:
            return f'{round(n/1e6,1)}M'
        return f'{round(n/1e3,1)}K'
    return n

def format_date(str_date, date_format):
    date = parse(str_date)
    return date.strftime(date_format) 

def red_or_green(df):
    return df.apply(lambda x: green if x >=1 else red)



'''
   ------------------------------------------------------------------------------------------- 
                                            LOAD THE DATA
   ------------------------------------------------------------------------------------------- 

'''
sales = pd.read_csv('sales_summary.csv', parse_dates=[0])
dashboard_date = datetime.date(2019, 5, 23)


'''------------------------------------------------------------------------------------------- 
                                        DASH COMPONENTS
   ------------------------------------------------------------------------------------------- 
'''

# Filters
# --------------------------
metric_dropdown = dcc.Dropdown(
    id='metric_dropwdown',
    options=[
        {'label': "Chiffre d'affaire", 'value': 'sales_2020'},
        {'label': "Bénéfices", 'value': 'profit_2020'},
    ],
    value='sales_2020',
    searchable=False,
    clearable=False
)

months = sales['Date'].dt.month.unique()
month_option = [{'label':calendar.month_abbr[m], 'value':m}for m in range(1,dashboard_date.month+1)]
# month_option.append({'label':None, 'value':"Année"})
date_dropdown = dcc.Dropdown(
    id='date_dropwdown',
    options=month_option,
    value=dashboard_date.month,
    searchable=False,
    clearable=False
)


### TEST
# create a simple graph
import plotly.express as px
df = px.data.iris() # iris is a pandas DataFrame
fig = px.scatter(df, x="sepal_width", y="sepal_length")

# Create the tooltips
text = """  testing 
"""
tooltip_info = html.Div(
	[
		dbc.Button("?", outline=True, className="rounded-circle", id="tooltip-target"),
		dbc.Tooltip(text, target="tooltip-target", placement="left")
	]
)
# Create a card
card = html.Div(
	[
		dbc.Row(
			[
			dbc.Col(html.H1("Title"), width=4, className="ml-2", style={"background-color": "green"}),
			dbc.Col(tooltip_info, width=1, style={"background-color": "yellow"})
			],
			justify="between",
			style={"background-color": "red"}
			
		),
		dbc.Row(dcc.Graph(figure=fig, config=config_dash, style={"width":"100%"}, 
			className="ml-3 mr-3"),
			style={"background-color": "blue"})
	],
	className="m-5 border",
	# style={"background-color": "red"}
)


'''------------------------------------------------------------------------------------------- 
                                            LAYOUT
   ------------------------------------------------------------------------------------------- 
'''
app.layout = html.Div(
    [
    	card
        # # header and filters
        # dbc.Card(
        #     [
        #         dbc.Row(html.H1("Centre de Commande"), className='ml-2 mt-1'),
        #         html.Hr(className="mt-2 mb-0"),
        #         dbc.Row(
        #             [
        #                 dbc.Col(metric_dropdown, className="ml-2", width=2),
        #                 dbc.Col(date_dropdown, width=2)
        #             ],
        #             justify="start",
        #             className="mt-2 mb-2"
        #         )
        #     ],
        #     # style={"height": "15vh", "background-color": "blue"},
        # ), 
        # # vizu
        # dbc.Row(
        #     [
        #     	# colonne de gauche
        #         dbc.Col(
        #             [
        #                 dbc.Row(
        #                     [
        #                         dbc.Col(
        #                             html.P("kpi 1"), 
        #                             style={"background-color": "red"},
        #                             className="mr-3"
        #                         ),
        #                         dbc.Col(
        #                             html.P("kpi 2"), 
        #                             style={"background-color": "green"},
                                    
        #                         )
        #                     ],
        #                     style={"height": "40%"},
                            
        #                 ),
        #                 dbc.Row(
        #                     html.P("bilan mensuelle"),
        #                     style={"height": "58%", "background-color": "yellow"},
        #                     className="mt-3"
        #                 )
        #             ],
        #             width = 8,
        #             className="mr-3"
        #         ),
        #         # colonne de droite
        #         dbc.Col(
        #             html.P("bilan par ville"), 
        #             style={"background-color": "grey"},
        #         )
        #     ],
        #     style={"height": "83vh"},
        #     className="mr-3 ml-3 mt-3"
        # )
    ],
    style={"height": "100vh"},
)


if __name__ == '__main__':
    app.run_server(debug=True)







