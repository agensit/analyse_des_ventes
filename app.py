import os
from itertools import combinations
from collections import Counter

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State
import dash_table


'''
   ------------------------------------------------------------------------------------------- 
                                            CONFIG
   ------------------------------------------------------------------------------------------- 

'''
## PLOTLY
import plotly.io as pio
pio.templates.default = "plotly_white"
config_dash = {'displayModeBar': False, 'showAxisDragHandles':False}
no_margin = dict(l=0, r=0, t=0, b=0)
# get acess to mapbox
with open('mapbox_token.txt') as f:
    lines=[x.rstrip() for x in f]
mapbox_access_token = lines[0]

## DASH
# external CSS + dash bootstrap components
external_stylesheets=[dbc.themes.BOOTSTRAP, "assets/main.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


## COLOR PALETTE
colors_palette = {'Computers':'#264653',
           'Phone':'#2a9d8f',
           'Gears':'#e9c46a',
           'TV & Monitor':'#f4a261',
           'Washing Machine':'#e76f51'}
str_to_int = {key: i for i, key in enumerate(colors_palette.keys())}
blue_info_color = '#16a2b8'

# READ BIG NUMBER
def millify(n):
    if n>999:
        if n > 1e6-1:
            return f'{round(n/1e6,1)}M'
        return f'{round(n/1e3,1)}K'
    return n

'''
   ------------------------------------------------------------------------------------------- 
                                            CREATE THE FIGURE
   ------------------------------------------------------------------------------------------- 

'''
## LOAD DATA
dirty_data = pd.read_csv('all_data.csv')
data = pd.read_csv('clean_data.csv')

## 1. ANALYSE DES PRODUITS
## -----------------------
product_report = data.groupby(['Categories', 'Product','Price Each']).sum()
product_list = product_report.index.get_level_values('Product')
categories_list =product_report.index.get_level_values('Categories')
# PARCAST  : découverte des produits
df = product_report.reset_index().sort_values('Categories')
cat_dim = go.parcats.Dimension(values=df['Categories'].values)
product_dim = go.parcats.Dimension(values=product_list)
colors = df['Categories'].apply(lambda x:str_to_int[x])
colorscale = [value for value in colors_palette.values()]
parcats = go.Figure(go.Parcats(
    dimensions=[cat_dim, product_dim],
    line={'color':colors, 'colorscale':colorscale, 'shape':'hspline'},
    tickfont = dict(size = 12),
    hoverinfo='none'))
parcats.update_layout(margin=dict(l=75, r=75, t=0, b=0))

# BAR CHART : Quel produit fait le meilleur chiffre de vente
product_rank = product_report['Sales'].sort_values().reset_index(['Categories','Price Each'])
product_bar= go.Figure()
top3 = product_rank['Sales'][-3:][::-1]
sales_revenue = product_report['Sales'].sum()
legend_list = []
for product in product_rank.index:
    cat = product_rank.loc[product,'Categories']
    if cat in legend_list:
        legend_status = False
    else:
        legend_status = True
        legend_list.append(cat)        	    
    product_bar.add_trace(go.Bar(
    	y = [product], 
    	x = [product_rank.loc[product,'Sales']],
    	marker_color = colors_palette[cat],
	    orientation='h',
	    hovertemplate="%{x:.3s} $<extra></extra>",
	    legendgroup=cat,
	    showlegend=legend_status,
	    name=cat))
product_bar.update_layout(
	margin=no_margin,
	title_font_size=20,
	hovermode = 'y unified',
	hoverlabel=dict(bgcolor="white",font_size=12),
	legend=dict(
		orientation="v",
		yanchor="bottom", y=0.5,
		xanchor="right", x=0.93))
product_bar.update_yaxes(showgrid=False, linecolor='black', linewidth=0.5)
product_bar.update_xaxes(nticks=5)

# SCATTER PLOT: volume des ventes des produits selon leurs prix
df = product_report[['Sales', 'Quantity Ordered']].reset_index()
size = df['Quantity Ordered']
scatter_plot_product = go.Figure(go.Scatter(x=df["Price Each"], 
                           y=df["Sales"],
                           mode="markers", 
                           marker=dict(
                               color=df["Categories"].map(lambda x: colors_palette[x]),
                               line=dict(width=0.5, color='black'),
                               size=size,
                               sizemode='area',
                               sizeref=3.*max(size)/(40.**2),
                            ),                           
                           text=df["Product"],
                           hovertemplate="<b>%{text}</b><br>"+"prix unitaire, <b>%{x} $</b><br>"+ 
                               "volume des ventes, <b>%{y:.2s} $</b> <extra></extra>"        
                          ))
scatter_plot_product.update_xaxes(title='<b>Prix des produits</b>, en $', nticks=5, zerolinewidth=1, zerolinecolor='black')
scatter_plot_product.update_yaxes(title='<b>Volume de ventes</b>, en $', zerolinewidth=1, zerolinecolor='black')
scatter_plot_product.update_layout(margin = no_margin)
scatter_plot_product.add_annotation(x=1700, y=8e6, text='Macbook Pro', font_color='#264653', arrowcolor='#264653')
scatter_plot_product.add_annotation(x=600, y=4e5, text='Machine à laver', font_color='#e76f51', arrowcolor='#e76f51')

# DONUT: Analyse du volume de ventes
labels = categories_list
colors  = product_report.reset_index(0)['Categories'].apply(lambda x: colors_palette[x])
donut = go.Figure(go.Pie(labels=labels, values=product_report['Quantity Ordered'], marker_colors= colors,
                     hovertemplate="<b>%{label}</b><br>"+
                     "%{percent} des ventes<br>"+
                     "↳ %{value:.2s} de ventes <extra></extra>",
                     title = dict(
                         text=f"<b>{millify(product_report['Quantity Ordered'].sum())}</b><br>Ventes",
                         font=dict(size=25)),
                    ))
donut.update_traces(hole=.4,textinfo='label+percent')
donut.update_layout(margin = no_margin, showlegend=False)

# BAR CHART: Quel est le nombre de produit different acheté par commande?
df = data.groupby(['Order ID', 'Order Date']).count()['Product'].value_counts()
df = df.reset_index()
df['percent'] = np.round(df['Product']/df['Product'].sum() * 100,2)
df.set_index('index', inplace=True)
prod_by_order = go.Figure(go.Bar(
    y = df['Product'],
    x = df.index,
  	marker=dict(color=blue_info_color),
    customdata = df['percent'],
    hovertemplate = '<b>%{y} commandes</b><br> ↳ soit %{customdata} % des ventes<extra></extra>',
))
prod_by_order.update_layout(hoverlabel=dict(bgcolor="white",font_size=14), hovermode='x', margin=no_margin)
prod_by_order.update_yaxes(showgrid=False,showticklabels=False)
prod_by_order.update_xaxes(title = 'Nombre de produits achetés par commandes', showgrid=False, linecolor='black', linewidth=0.5)

## 2. ANALYSE DES LIEUX DE VENTES
## -------------------------------
city_sales = data.groupby(['City','lat','long']).sum()['Sales'].reset_index()
city_sales['Sales_text'] = city_sales['Sales'].apply(lambda x: millify(x))
cities = city_sales['City']
city_sales['percents'] = city_sales['Sales']/city_sales['Sales'].sum()

# MAP: cartographie des lieux de ventes
map_plot = go.Figure(go.Scattermapbox(
  lat = city_sales['lat'], 
  lon = city_sales['long'],
  marker = dict(
    size=city_sales['Sales']/350000, 
    opacity=0.5,
    allowoverlap=True,
    color='#094D92'),
  hoverinfo='none'
))

# add border
map_plot.add_trace(go.Scattermapbox(
  lat = city_sales['lat'], 
  lon = city_sales['long'],
  marker = dict(
    size=city_sales['Sales']/200000, 
    opacity=0.3,
    allowoverlap=True,
    color='#094D92'),
  mode="markers+text",
  textposition="top center",
  textfont=dict(family="sans serif", size=16, color='black'),
  hovertemplate ='<b>%{text}</b><br>' + '%{customdata} $<extra></extra>',
  text = cities,
  customdata = city_sales['Sales_text']))
                     
map_plot.update_layout(
    hoverlabel=dict(
        bgcolor="white",
        font_size=12),
    margin=no_margin,
    mapbox = dict(
        accesstoken = mapbox_access_token,
        zoom = 2.9,
        center = go.layout.mapbox.Center(lat=40,lon=-97),
        style = "mapbox://styles/axelitorosalito/ckb2erv2q148d1jnp7959xpz0"), 
    showlegend=False
)

# BAR PLOT : San Francisco est la ville au plus gros volume de ventes
df = city_sales.sort_values(by='Sales', ascending=False)
best_city_plot= go.Figure(go.Bar(
    x = df['City'], 
    y = df['Sales'],
    customdata=df['percents'],
    hovertemplate ='%{y:.3s} $<br>'+'soit %{customdata:%} du CA<br><extra></extra>'))
best_city_plot.update_layout(
	margin = no_margin,
	hovermode = 'x unified', 
	hoverlabel=dict(
		bgcolor="white",
		font_size=12))
best_city_plot.update_yaxes(title='<b>Volume de ventes</b>, en $', nticks=5)
best_city_plot.update_xaxes(showgrid=False, linecolor='black', linewidth=0.5)
best_city_plot.update_traces(marker_color = blue_info_color)

# PIE: San Francisco, New York et Los Angeles représent 53% des ventes
pie_color = ['grey'] * len(city_sales)
pie_color[:3] = [blue_info_color] * 3
city_pie_plot =go.Figure(go.Pie(
    labels=df['City'],
    values=df['Sales'],
))
city_pie_plot.update_layout(margin=no_margin, showlegend=False)
city_pie_plot.update_traces(
    textposition='inside', 
    textinfo='percent+label',
    marker=dict(colors=pie_color, line=dict(color='black', width=0.2))
)

# PARTIE DETAILÉE
df = pd.read_csv("city_info.csv")

# SCATTER PLOT : Population en fonction des Ventes
sales_pop = px.scatter(df, x='pop_2019', y='Sales', text='City' )
sales_pop.update_traces(textposition='top center')
sales_pop.update_xaxes(title="<b>Nombre d'habitants</b>", nticks=5)
sales_pop.update_yaxes(title="<b>Volume de ventes</b>, en $", nticks=5)
sales_pop.update_layout(margin=no_margin)

# SCATTER PLOT : Salaire moyen en fonction des Ventes
sales_income = go.Figure(go.Scatter(
    x=df["income_2010"], 
    y=df["Sales"],
    mode="markers+text",
    text=df["City"],
    hovertemplate="<b>%{text}</b><br>"+"<b>%{y:.2s} $</b> de chiffres d'affaires<br>"+ 
       "<b>%{x:.2s} $</b> de salaire moyen<extra></extra>"))
sales_income.update_traces(
    textposition='top center',
    marker=dict(
        size=10,
        color = blue_info_color,
        line=dict(width=0.5, color='black')))
sales_income.update_xaxes(title="<b>Salaire moyen</b>, en $", nticks=5)
sales_income.update_yaxes(title="<b>Volume de ventes</b>, en $", nticks=5)
sales_income.update_layout(
  hoverlabel=dict(bgcolor="white", font_size=14),
  margin=no_margin)

# SCATTER PLOT : Saliare moyen en fonction des Ventes
sales_ads = px.scatter(df, x='ads_budget', y='Sales', text='City' )
sales_ads = go.Figure(go.Scatter(
    x=df["ads_budget"], 
    y=df["Sales"],
    mode="markers+text",
    text=df["City"],
    hovertemplate="<b>%{text}</b><br>"+"<b>%{y:.2s} $</b> de chiffres d'affaires<br>"+ 
       "<b>%{x:.2s} $</b>de budget publicitaire<extra></extra>"))
sales_ads.update_traces(
    textposition='top center',
    marker=dict(
        size=10,
        color = blue_info_color,
        line=dict(width=0.5, color='black')))
sales_ads.update_xaxes(title="<b>Budget publicitaire</b>, par ville", nticks=5)
sales_ads.update_yaxes(title="<b>Volume de ventes</b>, en $", nticks=5)
sales_ads.update_layout(
    hoverlabel=dict(bgcolor="white", font_size=14),
    margin=no_margin)

## 3. ANALYSE  TEMPORELLE
## -----------------------
sales_per_month = data.groupby(['Month_num', 'Month'])['Sales'].sum().reset_index()

# AREA: chiffre d'affaires mensuel
ca_per_month = go.Figure(go.Scatter(
    x=sales_per_month["Month"],
    y=sales_per_month["Sales"], 
    fill="tozeroy",
    hovertemplate="%{y:.2s} $ de CA<extra></extra>",
    marker=dict(
        size=10,
        color=blue_info_color,
        line=dict(width=0.5, color='black'))
))
ca_per_month.update_yaxes(title="<b>Chiffre d'Affaires mensuelle</b>, en $", nticks=5)
ca_per_month.update_layout(hoverlabel=dict(bgcolor="white",font_size=14), hovermode='x unified', margin=no_margin)
ca_per_month.update_layout(
  hoverlabel=dict(bgcolor="white",font_size=14), 
  hovermode='x unified',
  shapes=[
          dict(
              type="rect",
              xref="x", x0=5, x1=8,
              yref="paper", y0=0, y1=1,
              fillcolor="grey",
              opacity=0.2,
              layer="below",
              line_width=0,
          ),
            dict(
              type="rect",
              xref="x", x0=0, x1=2,
              yref="paper", y0=0, y1=1,
              fillcolor="grey",
              opacity=0.2,
              layer="below",
              line_width=0,
          )
        ])
ca_per_month.add_annotation(x=6.5, y=3.5e6, text='Vacances Scolaires', font=dict(size=14), showarrow=False)
ca_per_month.add_annotation(x=1, y=3.5e6, text='Après Fêtes', font=dict(size=14), showarrow=False)
ca_per_month.add_annotation(x=11, y=4.6e6, font=dict(size=14), text="Fêtes")

# PARTIE DETAILÉE
buying_hours = data.groupby('Hour').sum()['Quantity Ordered']

sales_per_hour = go.Figure(go.Scatter(
    x = buying_hours.index,
    y = buying_hours,
    fill="tozeroy",
    hovertemplate ='<b>%{x}h</b><br>'+
    '%{y:.0f} commandes<extra></extra>',
    mode='markers+lines',
    marker=dict(
        color=blue_info_color,
        )
))
sales_per_hour.update_yaxes(title= '<b>Nombre de commande</b>', nticks=5)
sales_per_hour.update_xaxes(title= "<b>Heure d'achats</b>", showticklabels=False, showgrid=False, zeroline=False)
sales_per_hour.update_layout(
	hoverlabel=dict(bgcolor="white",font_size=14), 
	hovermode='x',
	margin=no_margin,
	shapes=[
            dict(
                type="rect",
                xref="x", x0=0, x1=7,
                yref="paper", y0=0, y1=1,
                fillcolor="grey",
                opacity=0.2,
                layer="below",
                line_width=0,
            ),
              dict(
                type="rect",
                xref="x", x0=21, x1=23,
                yref="paper", y0=0, y1=1,
                fillcolor="grey",
                opacity=0.2,
                layer="below",
                line_width=0,
            )
        ])
sales_per_hour.add_annotation(x=3, y=7.5e3, text='<b>Nuit,</b><br> période creuse', font=dict(size=14), showarrow=False)
sales_per_hour.add_annotation(x=12, y=14202, text='<b>12h,</b> pause déjeuner ', font=dict(size=14))
sales_per_hour.add_annotation(x=19, y=14470, text='<b>19h</b>, temps libre', font=dict(size=14))

#
'''------------------------------------------------------------------------------------------- 
                                            DASH LAYOUT
   ------------------------------------------------------------------------------------------- 
'''
app.layout = dbc.Container([
	html.Div(children=[
		dcc.Markdown('''
			# Analyse des ventes d'une entreprise en ligne d'électronique 
			---
		'''),
		dbc.Alert(
			children='''Ce projet est un exemple dont le but est de vous aidez à envisager les problèmes liés à votre entreprise 
			sous l'angle de l'analyse de vos données. Notre objectif est de vous démontrer que l'extraction de connaissances 
			à partir de vos données facilite les prises de décisions et constitue un avantage stratégique.''',
			color="info"),
	##  Introduction et présentation des données
		dcc.Markdown('''
			## Introduction et présentation des données
			---
			Les données utilisées représente les ventes réalisées par une entreprise d'électronique lors de l’année 2019. 
			Attention l'entreprise n'existe pas, il s'agit de données fictives. Ci-dessous vous pouvez vous familiraser avec le jeu de données 
			que nous allons utiliser durant toute notre analyse.
		'''),
		dbc.Table.from_dataframe(dirty_data[:4], striped=True, bordered=True, hover=True, responsive=True, className="mb-0"),
		dbc.Row(dbc.Alert('''
      Échantilon des données que nous allons utiliser durant notre analyse. On y retrouve des informations pertinentes sur nos clients, 
      tel que les produits achetés, l'heure d'achat où encore l’adresse de livraison.''', color='light', className="mt-0"),
    justify="center"),
		dcc.Markdown('''
			Pour chaque commande un ensemble d'informations est collecté sur le client. Par example en lisant la premiere ligne du tableau ci-dessus on sait que
			le client répertorié par l'id __295665__ a acheté un __Macbook Pro__ à __1700$__ le __30 décembre 2019 à 00:01__, son adresse de livraison est 
			le __136 Church St, New York City, NY 10001__. Veuillez vous référer à la liste ci-dessous pour une meilleur compréhension des informations collectés 
			lors d'une commande.
		'''),
		dbc.Alert([
			html.H5("Descriptif des informations récoltées lors d'une commandes"),
			html.Hr(),
			dcc.Markdown('''
				- __ID__, numéro unique par client 
				- __Produit__, nom du matériel informatique acheté 
				- __Quantité commandée__, nombre d’exemplaires vendu
				- __Prix__, prix unnitaire de chaque produit
				- __Date__, date et heure de l'achat
				- __Adresse__, adresse de livraison
				- __Catégorie__, nature du produit (Computers, Washing Machine, Gears, TV & Monitor, Phone)
			''')
		], color='info'),
		dcc.Markdown('''
			__Maintenant que nous nous sommes familiariser avec nos données, nous pouvons les analyser pour en extraire des informations pertinentes__. 
			La suite de ce rapport est divisé en trois parties:

			1. __Analyse des produits__, après avoir découvert la gamme de produit vendu, nous déterminerons les produits phares de l'entreprises
			2. __Analyse des lieux de ventes__, aprés une rapide présentation des lieux de ventes, nous verrons qu'elles sont les villes les plus prolifiques
			3. __Analyse des ventes durant l'année__, nous analyserons les tendances d'achat des clients afin d'y determiner les périodes creuses et les périodes pleines  
		'''),
		dbc.Alert([
			html.P('''Nous avons ajouté à la fin de chacun des trois parties des analyses detailés pour les personnes désirant aller plus loin. Vous trouverez des boutons 
				similaires à celui ci-dessous à la fin de chacune des trois parties.'''),
	        dbc.Button(
	            "Cliquez ici pour continuer l'analyse",
	            className="mb-2 mt-3",
	            color="info",
	            id="collapse_button_0",
	            block=True),
	         dbc.Collapse(
	         	html.P("Simple exemple!"),
	         	id="collapse_0"), 
			],
			color='info'
		),

	## 1. ANALYSE DES PRODUITS
	## -----------------------
		html.H1('1. ANALYSE DES PRODUITS') ,
		html.Hr(),
		dcc.Markdown('''
			Notre entreprise d’électronique vend __19 produits__ différents regroupés en __5 catégories__. On compte dans les produits vendus 2 ordinateurs, 7 accessoires,
			3 téléphones, 4 écrans et 2 machines à laver. Pour plus d'information sur les produits vendus veuillez vous referez au diagramme ci-dessous.
		'''),
		# 5 catégories de 19 produits
		dbc.Card(
			dbc.CardBody([
				dbc.Row(html.H1("5 catégories de 19 produits"), justify="center", className='mb-0'),
				dcc.Graph(figure=parcats, config=config_dash),
				dbc.Row(dbc.Alert('''Figure 1: On a à gauche les differentes catégories de produits vendus, à droite la liste des 19 produits''', 
          color="light"),
        justify='center'),
			]),
		className='border-0'),
		# Quels sont les produits phares?				
		dcc.Markdown('''
			Après avoir pris connaissances des differents produits, nous pouvons analyser les ventes pour __déterminer ceux qui se sont les mieux vendus en 2019__. 
			En regardant le diagramme en barres ci-dessous on constate que le macbook pro represente le plus gros chiffre de ventes.
		''', className='mt-2'), 
		dbc.Row(html.H1("Quels sont les produits phares?"), justify="center", className='mb-2'),
		dbc.Row([
			dbc.Col(
				dbc.Card(
					dbc.CardBody([
						html.H6("Chiffre d'Affaires (CA)", className="card-subtitle text-secondary"),
						html.H4(f"{millify(sales_revenue)} $", className="card-title")
					]),
				),
				width=3
			),
			*[dbc.Col(
				dbc.Card(
					dbc.CardBody([
						html.H6(f'{rank+1}.  {p}', className="card-subtitle text-secondary"),
						html.H4(f"{int(p_revenue/sales_revenue * 100)} % du CA", className="card-title"),
					]),
				),
				width=3,
			) for rank,(p, p_revenue) in enumerate(zip(top3.index, top3.values))]
		],className="mb-2"),
		html.H4("Classement des produits selon leurs ventes ($)"),
		dbc.Card(
			dbc.CardBody(
			[
				dcc.Graph(figure=product_bar, config=config_dash),
				dbc.Row(dbc.Alert("Figure 2: ce diagramme liste les produits selon leur ventes. On attribue à chaque catégorie une couleur", 
          color="light",
					className="card-text"), 
        justify='center'),
			]),
		),
		# PARTIE 1 DETAILÉ : stratégie produit
		dbc.Alert(
			[
				dcc.Markdown('''Dans cette première partie d'approfondisement, __nous mettrons en place une stratègie produits__ construite 
					à l'aide de l'analyse de données'''),
				dbc.Button("Cliquez ici pour continuer l'analyse",
					id="collapse_button_1",
					className="mb-2 mt-3",
					color="info",
					block=True),
				dbc.Collapse(
        	dbc.Card(
      			[
      				dcc.Markdown("""
      					À l'aide du graphique en nuage de points ci-dessous on observe une forte corrélation entre le prix de vente d'un produit 
      					et le volume total de ses ventes durant l'année 2019. Autrement dit, __les produits avec un prix élevé ont tendances à avoir un volume 
      					de ventes important__."""),
      				dbc.Row(html.H3("Volume de ventes des produits selon leur prix"), justify="center"),
  	        	dcc.Graph(figure=scatter_plot_product, config=config_dash),
              dbc.Row(dbc.Alert('''Figure 3: volume de ventes des produits selon leur prix.''', color="light", className="mb-0"), justify="center"),
							dcc.Markdown('''
                Chaque couleur est rataché à une catégorie. Quant à la grandeur des bulles, elle dépends du nombre de ventes en 2019. 
                Par exemple les bulles jaunes font parties de la catégorie des accessoires, leur surface, plutôt étendus, decrivent un nombre de 
                ventes élevées. Les machines à lavés, au contraire, sont representés par des bulles rouges de petites superficies ce qui signifie 
                que le nombre de ventes de ces produits est minces''', className="mt-0"),
              dcc.Markdown('''
								Le graphique ci-dessus permet de mettre en évidence __trois points fondamentaux pour booster les ventes des années 
								à venir__:

								1. __Proposer davantage de produits haut de gamme__. On constate que le macbook pro est le seul ordinateur haut de gamme 
								proposé. Le Chiffre d'Affaires pourait augmenter en offrant d'autres offres d'ordinateurs haut de gammes. 
								La même logique est appliquable pour les télephones.

								2. __Stopper la vente de machines à laver__. Cette catégorie rapporte peut à notre entreprise. Il s'agit de produits 
								encombrant et lourd, leur frais de livraison est élevés. Il est preferable de focaliser nos efforts dans d'autres catégories.

								3. __Continuer la vente d'accesoires__. Cette catégorie représentent 75% des produits vendus, voir figure X. D'après la figure X+1,
								96% des commandes ne contiennent qu'un seul produit. On peut en conclure que les accesoires attirent un grand nombre de clients 
								sur notre site. __Une stratégie interresante serait de valoriser les produits haut de gamme afin d'insiter les clients à réaliser 
								des achats multiples.__'''),
							dbc.Row(html.H3("75% des ventes concernent les accessoires"), justify="center"),
							dcc.Graph(figure=donut, config=config_dash),
							dbc.Row(dbc.Alert("Figure 4: nombre de ventes des differentes catégories", color="light", className="mt-0"), justify="center"),
							dbc.Row(html.H3("96% des commandes sont constitués d'un seul produit", className="mb-0"), justify="center"),
        		  dcc.Graph(figure=prod_by_order, config=config_dash),		
							dbc.Row(dbc.Alert("Figure 5: quantité de commandes suivant le nombre de produits différents achetés", color="light"), justify="center"),		    	        								
		    	  ],
		        body=True, className='border-0'),
		    id="collapse_1",),
			],
			color="info",
			className="mt-2"
		),
	## 2. ANALYSE DES LIEUX DE VENTES
	## ------------------------------
		html.H1("2. ANALYSE DES LIEUX DE VENTES") ,
		html.Hr(),
		dcc.Markdown("""__Le service de livraison est disponible dans 9 villes Américaine__, on compte des villes tels que New York, Los Angeles ou
		encore San Francisco..."""),
		dcc.Graph(figure=map_plot, config={**config_dash, **{'scrollZoom':False}}),
		dbc.Row(dbc.Alert("""Figure 6: volume de ventes de chaque ville durant l'année 2019""", color="light"), justify="center"),
		# BAR & PIE CHART: Volume de ventes par ville
		dcc.Markdown("""A l'aide des figures ci-dessous, on observe que __San Francisco est la ville qui a réalisé le plus gros volume de ventes en 2019__. 
			De plus, on estime le volume de ventes des 3 villes les plus prolifiques à plus de 50% du Chiffre d'Affaires de 2019"""),
		dbc.Row(html.H3("San Francisco est la ville au plus gros volume de ventes", className='mt-5'), justify="center"),
		dcc.Graph(figure=best_city_plot, config=config_dash),
    dbc.Row(dbc.Alert("""Figure 7: classement des villes selon leur volume de ventes en 2019""", color="light"), justify="center"),
		# dbc.Row(html.H3("San Francisco, Los Angeles et New York représentent 53% du Chiffres d'Affaires", className="mt-5"), justify="center"),
		# dcc.Graph(figure=city_pie_plot, config=config_dash, className="mt-2"),	
		dcc.Markdown("""Maintenant que nous savons que San Francisco est la ville la plus prolifique, il serait interresant d'en comprendre les raisons.
		En effet __comprendre les facteurs de réussite d'une ville est un élément extrémement important pour booster le chiffre d'affaire des années à venir__. 
		Il peut être utile pour cibler de nouveau marcher mais aussi pour corriger notre strategie de ventes dans des villes à faible chiffre d'affaires.
			""", className="mt-0"),
		# PARTIE 2 DETAILÉE : Quel sont les facteurs qui sont font fluctué le volume des ventes
		dbc.Alert(
			[
				dcc.Markdown("""__Souvent difficile à déterminer__, ces facteurs peuvent dépendre d'un grand nombre de paramètres. Dans la partie d'approfondisement 
					ci-dessous nous analyserons la correlation entre:"""),
				dcc.Markdown("""
					- le volume des ventes  et __le salaire moyen__
					- le volume des ventes et __le budget publicitaire__"""),
				dbc.Button("Cliquez ici pour continuer l'analyse",
					id="collapse_button_2",
					className="mb-2 mt-3",
					color="info",
					block=True),
				dbc.Collapse(
		        	dbc.Card(
	        			[
	      #   				html.H3("Peu de corrélation avec le nombre d'habitants"),
	      #   				dcc.Markdown("""A premiere vu on pourait pensé que le nombre d'habitant est lié au volume de ventes, pourtant ce n'est pas le cas. 
	      #   					En regardant la figure ci-dessous on se rends compte que __le volume des ventes est peu correllé aux nombres d'habitants__. 
	      #   					La ville de New York par example posséde dix fois plus d'habitants que San Francisco pourtant son chiffre d'affaires est deux 
	      #   					fois moins importants."""),
							# dbc.Row(html.H4("Volume de ventes des villes selon leur population", className='mt-2'), justify="center"),
	      #   				dcc.Graph(figure=sales_pop, config=config_dash),
	        				html.H3("Peu de corrélation avec le salaire moyen"),
	        				dcc.Markdown("""
	        					A premiere vu on pourait pensé que le niveau de vie est lié aux volumes de ventes. Les appareils électronique ne sont pas de premiere 
	        					nécéssité. Il s'agit de produits réservé à une classe sociale avec un minimun de moyen. __Pourtant en regardant le graph ci-dessous,
	        					on remarque que ce n'est pas le cas, le niveau de vie à peut d'influence sur le volume des ventes__. Par exemple, la ville de Seattle 
	        					posséde le salaire moyen le plus elevée, 39.3k $, pourtant elle compte parmis les villes avec le volumes de ventes le plus bas, 2.7 M $"""),
	        				dcc.Graph(figure=sales_income, config=config_dash),	
	        				dbc.Row(dbc.Alert("Figure 8: volume de ventes des villes selon le salaire moyen", color="light", className="mt-0"), justify="center"),
	        				html.H3("Forte corrélation avec le budget publicitaire", className='mt-2'),
	        				dcc.Markdown("""En s'appuyant sur la figure ci-dessous on constate que le budget aloué à la publicité à beaucoup d'influence sur le volume 
	        					des ventes."""),
	        				dcc.Graph(figure=sales_ads, config=config_dash),
	        				dbc.Row(dbc.Alert("Figure 9: volume de ventes des villes selon le budget alloué à la publicté", color="light", className="mt-0"), 
	        					justify="center"),
        					dcc.Markdown("""EXPLIQUER QUE CA DEPENDS DE PLEIN D AUTRES FACTEURS"""),	       				
				    	],
					    body=True, className='border-0'),
		            id="collapse_2",
        		),
			],
			color="info",
			className="mt-4"
		),	
	## 3. ANALYSE  TEMPORELLE
	## -----------------------
		html.H1('3. ANALYSE TEMPORELLE') ,
		html.Hr(),
		dcc.Markdown("""La figure ci-dessous souligne la présence d'__un pic des ventes en décembre, pendant la periode des fêtes__. On remarque aussi __deux périodes 
			creuse__ durant l'année. La première est situé aprés les fêtes de fin d'année. Les gens ont depensés beaucoup durant les fêtes ils économisent pendant les 
			premiers mois de l'année. La deuxieme est situé pendant la période de vacances scolaire. Durant cet intervalle, la plus part des dépenses sont utilisés 
			pour les vacances et les frais dans les autres secteurs sont réduits. 
			"""),
		dbc.Row(html.H3("Pic de ventes pour les fêtes de fin d'année"), justify='center'),
	    dcc.Graph(figure=ca_per_month, config=config_dash),
	    # 
	    dbc.Row(dbc.Alert("Figure 10: évolution mensuelle du chiffre d'affaires de 2019", color="light", className="mt-0"), 
	        justify="center"),
	    		dbc.Alert(
					[
						dcc.Markdown("""Dans cette partie d'approfondissement nous verrons __quels sont les meilleurs moments pour afficher la publicité__"""),
						dbc.Button("Cliquez ici pour continuer l'analyse",
							id="collapse_button_3",
							className="mb-2 mt-3",
							color="info",
							block=True),
						dbc.Collapse(
				        	dbc.Card(
			        			[
			      	        		dcc.Markdown("""__Le meilleur moment pour afficher la publicté est à 12h et à 19h__, car nos ventes sont maximales pendant cette 
			      	        			période"""),
			      	        		dcc.Graph(figure=sales_per_hour, config=config_dash), 
			        				dbc.Row(dbc.Alert("Figure 11: somme du nombres de commandes regroupés par heure d'achat", color="light", className="mt-0"), 
			        					justify="center"),			      	        		     				
						    	],
							    body=True, className='border-0'),
				            id="collapse_3",
		        		),
					],
				color="info",
				className="mt-4"
		),	

	
	])
], 
# fluid=True
)

'''------------------------------------------------------------------------------------------- 
                                            INTERACTIVITÉ
   ------------------------------------------------------------------------------------------- 
'''
# Présentation du bouton étude detailée
@app.callback(
    Output("collapse_0", "is_open"),
    [Input("collapse_button_0", "n_clicks")],
    [State("collapse_0", "is_open")],
)
def toggle_collapse_0(n, is_open):
    if n:
        return not is_open
    return is_open

# 1. Analyse des produits,bouton analyse detailée
@app.callback(
    Output("collapse_1", "is_open"),
    [Input("collapse_button_1", "n_clicks")],
    [State("collapse_1", "is_open")],
)
def toggle_collapse_1(n, is_open):
    if n:
        return not is_open
    return is_open

# 2. Analyse des lieux de ventes,bouton analyse detailée
@app.callback(
    Output("collapse_2", "is_open"),
    [Input("collapse_button_2", "n_clicks")],
    [State("collapse_2", "is_open")],
)
def toggle_collapse_2(n, is_open):
    if n:
        return not is_open
    return is_open

 # 3. Analyse temporelle, bouton analyse detailée 
@app.callback(
    Output("collapse_3", "is_open"),
    [Input("collapse_button_3", "n_clicks")],
    [State("collapse_3", "is_open")],
)
def toggle_collapse_2(n, is_open):
    if n:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(debug=True)
