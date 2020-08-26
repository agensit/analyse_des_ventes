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


'''------------------------------------------------------------------------------------------- 
                                            LAYOUT
   ------------------------------------------------------------------------------------------- 
'''
app.layout = html.Div(
    [
        # header and filters
        dbc.Card(
            [
                dbc.Row(html.H1("Centre de Commande"), className='ml-2 mt-1'),
                html.Hr(className="mt-2 mb-0"),
                dbc.Row(
                    [
                        dbc.Col(metric_dropdown, className="ml-2", width=2),
                        dbc.Col(date_dropdown, width=2)
                    ],
                    justify="start",
                    className="mt-2 mb-2"
                )
            ],
            # style={"height": "15vh", "background-color": "blue"},
        ), 
        # vizu
        dbc.Row(
            [
            	# colonne de gauche
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.P("kpi 1"), 
                                    style={"background-color": "red"},
                                    className="mr-3"
                                ),
                                dbc.Col(
                                    html.P("kpi 2"), 
                                    style={"background-color": "green"},
                                    
                                )
                            ],
                            style={"height": "30%"},
                        ),
                        dbc.Row(
                            html.P("bilan mensuelle"),
                            style={"height": "58%", "background-color": "yellow"},
                            className="mt-3"
                        )
                    ],
                    width = 8,
                    className="mr-3"
                ),
                # colonne de droite
                dbc.Col(
                    html.P("bilan par ville"), 
                    style={"background-color": "grey"},
                )
            ],
            style={"height": "83vh"},
            className="mr-3 ml-3 mt-3"
        )
    ],
    style={"height": "100vh"},
)

'''------------------------------------------------------------------------------------------- 
                                            INTERACT
   ------------------------------------------------------------------------------------------- 
'''

# @app.callback(
#     [
#         Output('progress_pie', 'figure'),
#         Output('card_sum', 'figure'),
#         Output('city_sales', 'figure'),
#         Output('monthly_sales', 'figure')
#     ],
#     [
#         Input('metric_dropwdown', 'value'),
#         Input('date_dropwdown', 'value')
#     ]
# )

# def global_update(metric, month):
#     filtred_sales = sales.loc[sales['Date'].dt.month.isin([month])]
#     target = 'sales_target' if metric == 'sales_2020' else 'profit_target'

#     #  CREATION DES KPI
#     # --------------------------------------------------------

#     # Pie Progress
#     amount = filtred_sales[metric].sum()
#     progress = amount /  filtred_sales[target].sum()
#     rest = 1 - progress if 1 - progress > 0 else 0
#     progress_color = green if progress > 1 else red 
#     values = [progress, rest]
#     colors = [progress_color, 'white']
#     progress_pie = go.Figure(
#         go.Pie(
#             values = values, 
#             hole = .95, 
#             marker_colors = colors
#         )
#     )
#     progress_pie.update_layout(showlegend = False, hovermode = False )
#     progress_pie.update_traces(textinfo='none')
#     progress_pie.update_layout(
#         margin = margin,
#         annotations = [
#             dict(
#                 x=0.5,
#                 y=0.40,
#                 text="Objectif de Mars",
#                 showarrow=False,
#                 font=dict(
#                     size=30,
#                     color="#000000"
#                 )
#             ),
#             dict(
#                 x=0.5,
#                 y=0.55,
#                 text='{}%'.format(int(progress*100)),
#                 showarrow=False,
#                 font=dict(
#                     size=70,
#                     color=progress_color
#                 )
#             )
#         ]
#     )

#     # Summary card 
#     target_goal = filtred_sales.loc[filtred_sales['Date'].dt.date <= dashboard_date, target].sum()
#     score = amount / target_goal -1

#     if score > 0:
#         color = green
#         text_score = '+ {}% ⬆︎'.format(int(score*100))
#     else:
#         color = red
#         text_score = '{}% ⬇︎'.format(int(score*100))
#     # create a white pie
#     card_sum = go.Figure(go.Pie(values = [0,0]))
#     # add annotation
#     card_sum.update_layout(
#         margin = margin,
#         annotations = [
#             dict(
#                 x = 0.5,
#                 y = 0.45,
#                 text = "Chiffre d'Affaires ($)" if metric=="sales_2020" else "Bénéfices",
#                 showarrow = False,
#                 font = dict(
#                     size = 30,
#                     color = "#000000"
#                 )
#             ),
#             dict(
#                 x = 0.5,
#                 y = 0.60,
#                 text = '{}'.format(millify(amount)),
#                 showarrow = False,
#                 font = dict(
#                     size = 70,
#                     color = blue
#                 )
#             ),
#             dict(
#                 x = 0.5,
#                 y = 0.35,
#                 text = text_score,
#                 showarrow = False,
#                 # bgcolor=green,
#                 font = dict(
#                     size = 30,
#                     color = color
#                 )
#             )
#         ]
#     )

#     #  CITY SALES
#     # --------------------------------------------------------
#     city_sales = filtred_sales.groupby('City').sum()
#     percents = city_sales[metric] / city_sales[target]
#     # plot
#     city_plot = go.Figure([
#         go.Bar(
#             name = 'target', 
#             y = city_sales.index, 
#             x = city_sales[target], 
#             marker_color=grey,
#             marker_line_width=0.5,
#             marker_line_color='black',
#             opacity=target_opacity
#         ),
#         go.Bar(
#             name = metric, 
#             y = city_sales.index, 
#             x = city_sales[metric],
#             text = percents,
#             marker_color = red_or_green(percents),
#             marker_line_width=0,
#             width = 0.5,
#         )
#     ])
#     # update
#     city_plot.update_traces(texttemplate='%{text:.0%}', textposition='inside', selector=dict(name=metric))
#     city_plot.update_traces(orientation='h')
#     city_plot.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', barmode='overlay', margin = margin, showlegend=False)
#     city_plot.update_xaxes(nticks=5, linecolor='lightgrey', zeroline=True)
#     city_plot.update_yaxes(linewidth=0.5, linecolor='black', zeroline=True)

#     #  MONTH SALES
#     # --------------------------------------------------------
#     daily_sales = sales.groupby('Date').sum()
#     monthly_sales = daily_sales.resample('MS').sum()
#     percents = monthly_sales[metric] / monthly_sales[target]
#     # plot
#     monthly_plot = go.Figure([
#         go.Bar(
#             name = 'target', 
#             x = monthly_sales.index, 
#             y = monthly_sales[target], 
#             marker_color=grey,
#             marker_line_width=0.5,
#             marker_line_color='black',
#             opacity=target_opacity
#         ),
#         go.Bar(
#             name = metric, 
#             x = monthly_sales.index, 
#             y = monthly_sales[metric],
#             text = percents,
#             width = 0.6 *(1000*3600*24*22),
#             marker_color = red_or_green(percents),
#             marker_line_width=0,
#         )
#     ])
#     monthly_plot.update_traces(texttemplate='%{text:.0%}', textposition='auto', selector=dict(name=metric))
#     monthly_plot.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', barmode='overlay', margin =margin)
#     monthly_plot.update_xaxes(nticks=12, linecolor='black', zeroline=True)
#     monthly_plot.update_yaxes(nticks=6)

#     # OUTPUT
#     # --------------------------------------------------------
#     output_tuple = (
#         progress_pie,
#         card_sum,
#         city_plot,
#         monthly_plot
#     )
#     return output_tuple


if __name__ == '__main__':
    app.run_server(debug=True)







