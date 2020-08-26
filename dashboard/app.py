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
config_dash = {'displayModeBar': False, 'showAxisDragHandles':False}  
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

## 1. CREATION DU HEADER
# --------------------------------------------------------

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
# month_option.append({'label':None, 'value':"Année"}) # TODO: ajouter une option "Année"
date_dropdown = dcc.Dropdown(
    id='date_dropwdown',
    options=month_option,
    value=dashboard_date.month,
    searchable=False,
    clearable=False
)

header = dbc.Card([
    dbc.Row(html.H1("Centre de Commande"), className='ml-2 mt-1'),
    html.Hr(className="mt-1 mb-0"),
    dbc.Row(
        [
            dbc.Col(metric_dropdown, className="ml-2", lg=2, xs=4),
            dbc.Col(date_dropdown, lg=2, xs=4)
        ],
        justify="start",
        className="mt-2 mb-2"
    )
])

# 2. Colonne de Gauche
# --------------------------------------------------------

progress_bar = dcc.Graph(id='progress_pie', config=config_dash, style={'height':'100%'})
summary = dcc.Graph(id='card_sum', config=config_dash, style={'height':'100%'})
monthly_sales = dcc.Graph(id='monthly_sales', config=config_dash, style={'width':'100%','height':'100%'}, className="border")

left_block = dbc.Col(
    children = [
        dbc.Row(
            children = [
                dbc.Col(progress_bar, className="border mr-3 mt-3", style={"background-color": "white"}), 
                dbc.Col(summary, className="border mt-3", style={"background-color": "white"})
            ], 
            style = {"height": "40%"}),
        dbc.Row(monthly_sales, style={"height": "58%"}, className="mt-3")
    ],
    lg = 8,
    xs=12,
    className="mr-3",
    )

#  3. Colonne de droite
# --------------------------------------------------------
city_sales = dcc.Graph(
    id='city_sales', 
    config=config_dash, 
    style={'height':'100%', 'width':'100%'}
)

right_block = dbc.Col(
    city_sales, 
    style={"background-color": "white"}, 
    className=" mt-3 border"
)
    
                


'''------------------------------------------------------------------------------------------- 
                                            LAYOUT
   ------------------------------------------------------------------------------------------- 
'''
app.layout = html.Div(
    [
        header,
        dbc.Row(
            [
                left_block,
                right_block
            ],
            style={"height": "80vh"},
            className="mr-3 ml-3"
        )
    ],
    style={"height": "100vh"},
)
'''------------------------------------------------------------------------------------------- 
                                            INTERACT
   ------------------------------------------------------------------------------------------- 
'''

@app.callback(
    [
        Output('progress_pie', 'figure'),
        Output('card_sum', 'figure'),
        Output('city_sales', 'figure'),
        Output('monthly_sales', 'figure')
    ],
    [
        Input('metric_dropwdown', 'value'),
        Input('date_dropwdown', 'value')
    ]
)

def global_update(metric, month):
    filtred_sales = sales.loc[sales['Date'].dt.month.isin([month])]
    target = 'sales_target' if metric == 'sales_2020' else 'profit_target'

    #  CREATION DES KPI
    # --------------------------------------------------------

    # Pie Progress
    amount = filtred_sales[metric].sum()
    progress = amount /  filtred_sales[target].sum()
    rest = 1 - progress if 1 - progress > 0 else 0
    progress_color = green if progress > 1 else red 
    values = [progress, rest]
    colors = [progress_color, 'white']
    progress_pie = go.Figure(
        go.Pie(
            values = values, 
            hole = .95, 
            marker_colors = colors
        )
    )
    progress_pie.update_layout(showlegend = False, hovermode = False )
    progress_pie.update_traces(textinfo='none')
    progress_pie.update_layout(
        margin = margin,
        annotations = [
            dict(
                x=0.5,
                y=0.40,
                text="Objectif pour Mars",
                showarrow=False,
                font=dict(
                    size=20,
                    color="#000000"
                )
            ),
            dict(
                x=0.5,
                y=0.60,
                text='{}%'.format(int(progress*100)),
                showarrow=False,
                font=dict(
                    size=70,
                    color=progress_color
                )
            )
        ]
    )

    # Summary card 
    target_goal = filtred_sales.loc[filtred_sales['Date'].dt.date <= dashboard_date, target].sum()
    score = amount / target_goal -1

    if score > 0:
        color = green
        text_score = '+ {}% ⬆︎'.format(int(score*100))
    else:
        color = red
        text_score = '{}% ⬇︎'.format(int(score*100))
    # create a white pie
    card_sum = go.Figure(go.Pie(values = [0,0]))
    # add annotation
    card_sum.update_layout(
        margin = margin,
        annotations = [
            dict(
                x = 0.5,
                y = 0.40,
                text = "Chiffre d'Affaires ($)" if metric=="sales_2020" else "Bénéfices",
                showarrow = False,
                font = dict(
                    size = 25,
                    color = "#000000"
                )
            ),
            dict(
                x = 0.5,
                y = 0.60,
                text = '{}'.format(millify(amount)),
                showarrow = False,
                font = dict(
                    size = 70,
                    color = blue
                )
            ),
            dict(
                x = 0.5,
                y = 0.20,
                text = text_score,
                showarrow = False,
                # bgcolor=green,
                font = dict(
                    size = 23,
                    color = color
                )
            )
        ]
    )

    #  CITY SALES
    # --------------------------------------------------------
    city_sales = filtred_sales.groupby('City').sum()
    percents = city_sales[metric] / city_sales[target]
    # plot
    city_plot = go.Figure([
        go.Bar(
            name = 'Objectif', 
            y = city_sales.index, 
            x = city_sales[target], 
            marker_color=grey,
            marker_line_width=0.5,
            marker_line_color='black',
            opacity=target_opacity
        ),
        go.Bar(
            name = "Chiffre d'affaires" if metric=="sales_2020" else "Bénéfices", 
            y = city_sales.index, 
            x = city_sales[metric],
            text = percents,
            marker_color = red_or_green(percents),
            marker_line_width=0,
            width = 0.5,
        )
    ])
    # update
    city_plot.update_traces(texttemplate='%{text:.0%}', textposition='inside', selector=dict(marker_line_width=0))
    city_plot.update_traces(orientation='h', hovertemplate="%{x:.2s} $",)
    city_plot.update_layout(
        hovermode="y unified",
        uniformtext_minsize=8, 
        uniformtext_mode='hide', 
        barmode='overlay', 
        margin = margin, 
        showlegend=False)
    city_plot.update_xaxes(nticks=5)
    city_plot.update_yaxes(linewidth=0.5, linecolor='black', zeroline=True)

    #  MONTH SALES
    # --------------------------------------------------------
    daily_sales = sales.groupby('Date').sum()
    monthly_sales = daily_sales.resample('MS').sum()
    percents = monthly_sales[metric] / monthly_sales[target]
    # plot
    monthly_plot = go.Figure([
        go.Bar(
            name = 'Objectif', 
            x = monthly_sales.index, 
            y = monthly_sales[target], 
            marker_color=grey,
            marker_line_width=0.5,
            marker_line_color='black',
            opacity=target_opacity
        ),
        go.Bar(
            name = "Chiffre d'affaires" if metric=="sales_2020" else "Bénéfices", 
            x = monthly_sales.index, 
            y = monthly_sales[metric],
            text = percents,
            width = 0.6 *(1000*3600*24*22),
            marker_color = red_or_green(percents),
            marker_line_width=0,
        )
    ])
    monthly_plot.update_traces(texttemplate='%{text:.0%}', textposition='auto', selector=dict(marker_line_width=0))
    monthly_plot.update_traces(hovertemplate="%{y:.2s} $")
    monthly_plot.update_layout(
        hovermode="x unified",
        uniformtext_minsize=8, 
        uniformtext_mode='hide', 
        barmode='overlay', 
        showlegend=False,
        margin =margin)
    monthly_plot.update_xaxes(
        nticks=12, 
        linecolor='black', 
        zeroline=True,
        ticktext=[datetime.datetime.strftime(date, "%b") for date in monthly_sales.index],
        tickvals=monthly_sales.index)
    monthly_plot.update_yaxes(nticks=6)    

    # OUTPUT
    # --------------------------------------------------------
    output_tuple = (
        progress_pie,
        card_sum,
        city_plot,
        monthly_plot
    )
    return output_tuple


if __name__ == '__main__':
    app.run_server(debug=True)







