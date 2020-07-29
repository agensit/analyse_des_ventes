import os
from itertools import combinations
from collections import Counter

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import dash_table

## CONFIG
# dash & plotly
import plotly.io as pio
pio.templates.default = "plotly_white"
config_dash = {'displayModeBar': False, 'showAxisDragHandles':False, 'responsive':True}  
margin = dict(l=0, r=0, t=0, b=0)
# get acess to mapbox
with open('mapbox_token.txt') as f:
    lines=[x.rstrip() for x in f]
mapbox_access_token = lines[0]
px.set_mapbox_access_token(mapbox_access_token)
# color palette
colors_palette = {'Computers':'#264653',
           'Phone':'#2a9d8f',
           'Gears':'#e9c46a',
           'TV & Monitor':'#f4a261',
           'Washing Machine':'#e76f51'}
str_to_int = {key: i for i, key in enumerate(colors_palette.keys())}
# Readable big number
def millify(n):
    if n>999:
        if n > 1e6-1:
            return f'{round(n/1e6,1)}M'
        return f'{round(n/1e3,1)}K'
    return n
# external CSS + dash bootstrap components
external_stylesheets=[dbc.themes.BOOTSTRAP, "assets/main.css"]
# config dash
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

## LOAD DATA
dirty_data = pd.read_csv('all_data.csv')
data = pd.read_csv('clean_data.csv')
cities = data['City'].unique()

## Categories and Product
df = data.groupby(['Categories', 'Product']).sum()
df = df.reset_index().sort_values('Categories')
# create dimensions
cat_dim = go.parcats.Dimension(values=df['Categories'].values, label='Categorie')
product_dim = go.parcats.Dimension(values=df['Product'].values, label='Produit')
# color 
colors = df['Categories'].apply(lambda x:str_to_int[x])
colorscale = [value for value in colors_palette.values()]
# plot
Parcats = go.Figure(go.Parcats(
    dimensions=[cat_dim, product_dim],
    line={'color':colors, 'colorscale':colorscale, 'shape':'hspline'},
    labelfont = dict(size = 15),
    hoverinfo='none'))

## Product by Order
prod_by_order = data.groupby(['Order ID', 'Order Date']).count()['Product'].value_counts()
prod_by_order = prod_by_order.reset_index()
prod_by_order['percent'] = np.round(prod_by_order['Product']/prod_by_order['Product'].sum() * 100,2)

# plot
bar_hour_sales = go.Figure(go.Bar(
    y = prod_by_order['Product'],
    x = prod_by_order['index'],
    customdata = prod_by_order['percent'],
    hovertemplate = '<b>%{x} Produits</b><br>%{y} commandes<br> ↳ soit %{customdata} % des ventes<extra></extra>',
))
# updates
bar_hour_sales.update_layout(hoverlabel=dict(bgcolor="white",font_size=14), hovermode='x')
bar_hour_sales.update_yaxes(title= 'Nombre de commandes', showgrid=False, showticklabels=False)
bar_hour_sales.update_xaxes(title= 'Nombre de produits achetés', showgrid=False)

## Top Product sale together
# drop the command of only one product
multi_purchase = data[data['Order ID'].duplicated(keep=False)]
# gather in one cell all article purchase by 'Order ID'
multi_purchase.loc[:,'Grouped'] = multi_purchase.groupby('Order ID')['Product'].transform(lambda x: ','.join(x))
# drop the duplicate ID
multi_purchase = multi_purchase.drop_duplicates(subset='Order ID')
# Count the number of combination 
count = Counter()
for row in multi_purchase['Grouped']:
    row_list = row.split(',')
    count.update(Counter(combinations(row_list, 2)))

group_product = {'Product':[], 'Sales':[]}
for key,value in count.most_common(10):
    group_product['Product'].append(key)
    group_product['Sales'].append(value)
    
top_group_sales = pd.DataFrame(group_product)
top_group_sales['Product'] = top_group_sales['Product'].apply(lambda x: f'{x[0]} et {x[1]}')
top_group_sales = top_group_sales.sort_values(by='Sales')
group_sale_plot = go.Figure(go.Bar(y = top_group_sales['Product'],
                                   x = top_group_sales['Sales'],
                                   orientation='h',
                                   hovertemplate ='<b>%{y}</b><br> %{x} commandes<extra></extra>'
                                    ))

group_sale_plot.update_layout(showlegend=False, 
                                hoverlabel=dict(bgcolor="white",font_size=14),
                                title = "Top 10 des produits les plus vendus ensembles")
group_sale_plot.update_yaxes(title= 'Produit', showticklabels=False, showgrid=False)
group_sale_plot.update_xaxes(title= 'Nombre de ventes')

## DASH LAYOUT
app.layout = html.Div(children=[
	dcc.Markdown(children='''
		# Analyse des ventes d'une entreprise en ligne d'électronique
		---
		Ce projet est un exemple dont le but est de vous aidez à envisager les problèmes liés à votre entreprise 
		sous l'angle de l'analyse de vos données. Notre objectif est de vous démontrer que l'extraction de connaissances 
		à partir de vos données facilite les prises de décisions et constitue un avantage stratégique.

		__Les données utilisées représente les ventes réalisé par une entreprise d'électronique lors de l’année 2019__. 
		Un exemple du jeux de données est visible a travers le tableau-ci dessous.
	'''),
	dash_table.DataTable(
		columns=[{'name':c, 'id':c}for c in dirty_data.columns],
		data=dirty_data[:5].to_dict('records'),
	    style_data_conditional=[
	        {'if': {'row_index':'odd'}, 'backgroundColor':'rgb(248, 248, 248)'},
	        # {'if':
	        # 	{'filter_query': '{Order ID} = 295668'},
	        # 	'backgroundColor': '#858585',
         #    	'color': 'white'}
	    ],
	    style_as_list_view=True,
	    style_header={'backgroundColor':'rgb(230, 230, 230)', 'fontWeight':'bold'}
	),
	# html.Br(),
	dcc.Markdown('''
		_legende_

		On y retrouve des informations pertinentes sur nos clients, tel que les `produits achetés`, 
		`l'heure d'achat` où encore `l’adresse de livraison`.

		➜ Le client répertorié par l'id __295665__ a acheté un __Macbook Pro__ à __1700$__ le __30 décembre 2019 à 00:01__, 
		son adress de livraison est __136 Church St, New York City, NY 10001__ 

		#### Descriptif des données collectées
		- __ID__, numéro unique par client 
		- __Produit__, nom du matériel informatique acheté 
		- __Quantité commandée__, nombre d’exemplaires vendu
		- __Prix__, prix unnitaire de chaque produit
		- __Date__, date et heure de l'achat
		- __Adresse__, adresse de livraison
		- __Catégorie__, nature du produit (Computers, Washing Machine, Gears, TV & Monitor, Phone)
	'''),
	dcc.Markdown('''
		## Sommaire
		---
		1. [Présentation des produits ](#cleanning)
		2. [Présentation des lieux de ventes](#augment)
		3. [Etude temporelle](#okay)

		## 1. Présentation des produits 
		---
		Notre entreprise d’électronique vend __19 produits__ différents regroupés en __5 catégories__. On constate par exemple que 
		seulement deux type d’ordinateur sont vendus, le macbook pro et le ThinkPad Laptop. Explorer par vous même la gamme des produits 
		vendu par cette entreprise d'électronique.
	'''),
	dcc.Graph(figure=Parcats, config=config_dash),
	dcc.Markdown('''
		Maintenant que nous connaissons un peu mieux les produits vendus focalisont nous sur nos ventes
		### Quels sont les produits qui se sont le mieux vendus en 2019?
	'''), 
	dcc.Dropdown(
		id='dropdown_type',
		options=[{'label':'Sales', 'value':'Sales'}, {'label':'Quantity Ordered', 'value':'Quantity Ordered'}],
		value='Quantity Ordered',
	),
	dcc.Graph(id='product_ranking', config=config_dash),
	dcc.Markdown('### Volume de ventes par categories et par produit'),
	dcc.Graph(id='pie_product', config=config_dash),
	dcc.Graph(id='parcast_product', config=config_dash),
	dcc.Markdown('''
		## 2. Présentation des lieux de ventes
		---
		Le service de livraison est disponible dans 9 villes Américaine 
	'''),
	dcc.Graph(id='map_plot', config={**config_dash, 'scrollZoom':False}),
	dcc.Markdown('### Quelle est la ville qui a réalisé le plus grand nombre de ventes ?'),
	dcc.Graph(id='bar_city_sales', config=config_dash),
	dcc.Graph(id='city_pie', config=config_dash),
	dcc.Markdown('''
		## 3. Etude détaillée
		---
		### Quel a été le meilleur mois de vente ? 
	'''),
	dcc.Graph(id='bar_month_sales', config=config_dash),
	dcc.Markdown('''
		↳ les ventes du mois de décembre sont le meilleurs avec desventes à 4.61 M de dollars il surpasse de 
		15% le 2eme mois le plus prolifique, Octobre. Quant au mois le moins rentable il s'agit du mois de 
		Janvier avec 1.8 M$ de ventes soit 2XX % moins que le mois de decembre

		### À quelle heure devrions-nous afficher la publicité ? 
		pour maximiser la probabilité que le client achète le produit 
	'''),
	dcc.Dropdown(
		id='dropdown_city', 
		options=[{'value':city,'label':city} for city in cities],
		value=None,
		multi=True
	),
	dcc.Graph(id='bar_hour_sales',config=config_dash),
	dcc.Markdown('''
		### Quel est le nombre de produit different acheté par commande?
	'''),
	dcc.Graph(figure=bar_hour_sales, config=config_dash),
	dcc.Markdown('''
		↳ Il y a peu d'achat groupé. 96% des clients n’achète qu'un seul produit. 
		Ce qui peut être amélioré en ajoutant un systeme de promotions sur le deuxième article. 

		## Quels sont les produits qui sont le plus souvent vendus ensemble ?
	'''),
	dcc.Graph(figure=group_sale_plot, config=config_dash)
])

@app.callback(
	[
		Output('product_ranking', 'figure'),
		Output('pie_product', 'figure'),
		Output('parcast_product', 'figure'),
		Output('map_plot', 'figure'),
		Output('bar_city_sales', 'figure'),
		Output('city_pie', 'figure'),
		Output('bar_month_sales', 'figure'),
		Output('bar_hour_sales', 'figure'),
	],
	[
		Input('dropdown_type','value'),
		Input('dropdown_city','value')
	]
)

def global_update(dropdown_type, dropdown_city):
## 1. Etudes des produits
# Product Bar Chart
	product_ranking = data.groupby(['Categories','Product']).sum()[dropdown_type]
	product_ranking = product_ranking.sort_values().reset_index()
	product_ranking = product_ranking.set_index('Product')
	product_bar= go.Figure()
	legend_list = []
	for product in product_ranking.index:
	    cat = product_ranking.loc[product,'Categories']
	    if cat in legend_list:
	        legend_status = False
	    else:
	        legend_status = True
	        legend_list.append(cat)        	    
	    product_bar.add_trace(go.Bar(
	    y = [product], 
	    x = [product_ranking.loc[product,dropdown_type]],
	    marker_color = colors_palette[cat],
	    orientation='h',
	    legendgroup=cat,
	    showlegend=legend_status,
	    name=cat))
	product_bar.update_layout(hovermode = 'y unified', 
	                  height=700,
	                  hoverlabel=dict(bgcolor="white",font_size=12),
	                 legend=dict(
	                     orientation="h",
	                     yanchor="bottom", y=1,
	                     xanchor="right", x=0.95))
	product_bar.update_yaxes(showgrid=False)
	if dropdown_type == 'Sales':
	    product_bar.update_xaxes(title='Montant des ventes ($)')
	    product_bar.update_traces(hovertemplate='%{x} $ de ventes<extra></extra>')
	else:
	    product_bar.update_xaxes(title='Quantité de ventes')
	    product_bar.update_traces(hovertemplate='%{x} commandes<extra></extra>')

# Pie Chart
	cat = data.groupby('Categories').sum()[dropdown_type].reset_index()
	cat['parents'] = '' 
	cat['colors'] = cat['Categories'].apply(lambda x: colors_palette[x]) 
	cat = cat.rename(columns={'Categories':'labels'})
	cat['percents'] = np.round(cat[dropdown_type] / cat[dropdown_type].sum() * 100,1)
	product = data.groupby(['Categories','Product']).sum()[dropdown_type].reset_index()
	product = product.rename(columns={'Categories':'parents', 'Product':'labels'})
	product['percents'] = np.round(product[dropdown_type] / product[dropdown_type].sum() * 100,1)
	df = pd.concat([cat,product])
	df['hover_data'] = df[dropdown_type].map(lambda x: millify(x))
	pie_product =go.Figure(go.Sunburst(
	    labels= df['labels'],
	    parents=df['parents'],
	    values=df[dropdown_type],
	    branchvalues='total',
	    marker=dict(colors=df['colors']),
	    customdata=df['percents'],
	    maxdepth=2))
	pie_product.update_layout(margin = dict(t=0, l=0, r=0, b=0))
	if dropdown_type == 'Sales':
	    pie_product.update_traces( hovertemplate='<b>%{label}</b><br>'+
	    '%{value:.2s} $ de ventes<br>'+'↳ %{customdata}% du total des ventes<extra></extra>')
	else:
	    pie_product.update_traces( hovertemplate='<b>%{label}</b><br>'+
	    '%{value:.2s} commandes<br>'+'↳ %{customdata}% du nombre total de commandes<extra></extra>')

# Parcast
	df = data.groupby(['Categories', 'Product']).sum()[dropdown_type]
	df = df.sort_values(ascending=False).reset_index()
	cat_dim = go.parcats.Dimension(values=df['Categories'].values,label='Categorie')
	product_dim = go.parcats.Dimension(values=df['Product'].values, label='Produit')
	colors = df['Categories'].map(lambda x: colors_palette[x])
	parcast_product = go.Figure(go.Parcats(
	    dimensions=[cat_dim, product_dim],
	    line={'color': colors, 'colorscale': colorscale, 'shape': 'hspline'},
	    counts=df[dropdown_type],
	    labelfont={'size': 16}))
	if dropdown_type == 'Sales':
	    parcast_product.update_traces(hovertemplate='<b>%{category}</b><br>'+'%{count:.3s} $ de ventes<br>'
	                      +'↳ %{probability:.1%} des ventes en 2019<br>')
	else:
	        parcast_product.update_traces( hovertemplate='<b>%{category}</b><br>'+'%{count:.3s} commandes<br>'
	                      +'↳ %{probability:.1%} des commandes en 2019<br>')
	parcast_product.update_layout(hovermode='y unified')

## 2. Etude des lieux de ventes
	city_sales = data.groupby(['City','lat','long']).sum()['Sales'].reset_index()
	city_sales['Sales_text'] = city_sales['Sales'].apply(lambda x: millify(x))

	map_plot = go.Figure(go.Scattermapbox(
	        lat = city_sales['lat'], 
	        lon = city_sales['long'],
	        marker = dict(size=city_sales['Sales'], sizeref = 150000),
	        hovertemplate ='<b>%{text}</b><br>' +
	                '%{customdata} $<extra></extra>',
	        text = city_sales['City'],
	        customdata = city_sales['Sales_text']))
	                     
	map_plot.update_layout(hoverlabel=dict(bgcolor="white",font_size=12),
	                       title='Total des ventes durant l’année par ville',
	                       width=800, 
	                       height=600,
	                       mapbox = dict(accesstoken = mapbox_access_token,
	                                     zoom = 2.9,
	                                     center = go.layout.mapbox.Center(lat=42,lon=-97),
	                                    ), 
                       showlegend=False)

# Quelle est la ville qui a réalisé le plus grand nombre de ventes ?
	categories = data.groupby('Categories').sum()[dropdown_type].sort_values(ascending=False).index
	city_sales = data.groupby(['City','Categories']).sum()[dropdown_type]
	city_sales = city_sales.reset_index(level=0)
	# create the % of sales per city
	city_sales[dropdown_type]/city_sales.groupby('City').sum()[dropdown_type]
	sales_per_city = city_sales.groupby('City').sum()[dropdown_type]
	sales_per_city.rename('total_per_city', inplace=True)
	city_sales = pd.merge(city_sales,sales_per_city,left_on='City',right_index=True)
	city_sales['percents'] = np.round(city_sales[dropdown_type]/city_sales['total_per_city'] * 100)
	# plot
	bar_city_sales = go.Figure([go.Bar(
	    x = city_sales.loc[cat, 'City'], 
	    y = city_sales.loc[cat, dropdown_type],
	    marker_color = colors_palette[cat],
	    name = cat,
	    text=[cat] * len(cities),
	    customdata=city_sales.loc[cat,'percents'],
	    hovertemplate ='%{text}, '+
	                      '%{y:.3s} $<br>'+
	                      '%{customdata}% des ventes<br><extra></extra>')
	    for cat in categories])
	# updates
	bar_city_sales.update_layout(hovermode = 'x unified', barmode='stack',
	                  title = 'Volume des ventes par ville et par catégories',
	                  xaxis={'categoryorder':'category ascending'},
	                  hoverlabel=dict(bgcolor="white",font_size=12),
	                  legend=dict(
	                      orientation="h",
	                      yanchor="bottom", y=1,
	                      xanchor="right", x=0.63))
	bar_city_sales.update_xaxes(showgrid=False)
	if dropdown_type == 'Sales':
	    bar_city_sales.update_layout(title='Volume des ventes par ville et par catégories') 
	    bar_city_sales.update_yaxes(title='Ventes en $')
	else:
	    bar_city_sales.update_layout(title='Volume des commandes par ville et par catégories')
	    bar_city_sales.update_yaxes(title='Nombre de ventes')
# Volume des ventes par viles
	city_pie = px.pie(data, values='Sales', names='City', color_discrete_sequence=px.colors.sequential.ice)
	city_pie.update_traces(textposition='inside', textinfo='percent+label')

## 3. Etude detaillée
# Quel a été le meilleur mois de vente ? 
	sales_per_month = data.groupby(['Month_num', 'Month'])['Sales'].sum()
	sales_per_month = data.groupby(['Month_num', 'Month','Categories']).sum()[dropdown_type]
	sales_per_month = sales_per_month.reset_index().set_index('Categories')
	bar_month_sales = go.Figure([go.Bar(
	    x = sales_per_month.loc[cat,'Month'], 
	    y = sales_per_month.loc[cat,dropdown_type],
	    marker_color = colors_palette[cat],
	    name = cat)
	    for cat in categories])
	bar_month_sales.update_layout(hovermode="x unified",barmode='stack',
	                        title = "Total des ventes regroupé par mois, séparé par catégories",
	                        legend=dict(
	                            orientation="h",
	                            yanchor="bottom", y=1,
	                            xanchor="right", x=0.63))
	bar_month_sales.update_yaxes(title= 'Ventes en  USD($)')
	bar_month_sales.update_xaxes(showgrid=False)
# À quelle heure devrions-nous afficher la publicité ?
	if dropdown_city:
	    df = data[data['City'].isin(dropdown_city)]
	else:
	    df = data 
	buying_hours = df.groupby('Hour').sum()['Quantity Ordered']
	bar_hour_sales = go.Figure(go.Bar(
	    x = buying_hours.index,
	    y = buying_hours,
	    hovertemplate ='<b>%{x}h</b><br>'+
	    '%{y:.0f} commandes<extra></extra>'))

	bar_hour_sales.update_layout(showlegend=False,
	                                hoverlabel=dict(bgcolor="white",font_size=14),
	                                title="Nombre de commande par heure durant l’année 2019")
	bar_hour_sales.update_yaxes(title= 'Nombre de commande')
	bar_hour_sales.update_xaxes(title= "Heure d'achats", showticklabels=False, showgrid=False, zeroline=False)

# Quel est le nombre de produit different acheté par commande?


	## Output
	output_tuple =(
		product_bar,
		pie_product, 
		parcast_product,
		map_plot,
		bar_city_sales, 
		city_pie,
		bar_month_sales,
		bar_hour_sales
	)
	return output_tuple

if __name__ == '__main__':
    app.run_server(debug=True)
