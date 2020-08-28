import numpy as np 

# PLOTLY
import plotly.express as px
import plotly.io as pio
pio.templates.default = "plotly_white"

# DASH
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server



'''------------------------------------------------------------------------------------------- 
                                        Cards Class
   ------------------------------------------------------------------------------------------- 
'''

class Card:
    """Créer un panel pour notre dashboard"""
    def __init__(self, title, graph, tooltip=None, dash_config={'displayModeBar': False, 'showAxisDragHandles':False}):
        self.title = html.H2(title)
        self.graph = dcc.Graph(figure=graph, config=dash_config, style={"width":"100%"})

        if tooltip :
            self.tooltip = self.create_tooltip(tooltip) 
        else :
            self.tooltip = None

    def create_tooltip(self, tooltip):
        return html.Div(
            [
                dbc.Button("?", outline=True, className="rounded-circle", id=f"tooltip-target_{self.title.children}"),
                dbc.Tooltip(tooltip, target=f"tooltip-target_{self.title.children}", placement="left")
            ]
        )

    def create(self):
        top_row = [dbc.Col(self.title, width=4, className="ml-5")]
        if self.tooltip:
            top_row.append(dbc.Col(self.tooltip, width=1, className="mt-1"))

        return html.Div(
            [
                dbc.Row(top_row, justify="between"),
                dbc.Row(self.graph, className="ml-3 mr-3", style={"background-color": "blue"})
            ],
            className="m-4 border",
            style={"background-color": "white"}
        )


'''------------------------------------------------------------------------------------------- 
                                         Class Container
   ------------------------------------------------------------------------------------------- 
'''         
class Container:
    """Créer la partie central de notre dashboard"""
    def __init__(self, cards_info, margin=4, backgorund_color="white"):
        self.cards_info = cards_info
        self.margin = margin
        self.backgorund_color = backgorund_color

    def get_card_info(self):
        for (card, n_row, order, width) in self.cards_info:
            print(card.title.children.upper())
            print("---------------")
            print(f"row number {n_row}")
            print(f"width: {width}")
            print(f"margin: {self.margin}")
            print("")

    # def create(self):






'''------------------------------------------------------------------------------------------- 
                                            Test
   ------------------------------------------------------------------------------------------- 
'''
if __name__ == '__main__':

    # create a simple graph
    df = px.data.iris() # iris is a pandas DataFrame
    fig = px.scatter(df, x="sepal_width", y="sepal_length")
    fig.update_layout(margin=dict(l=20, r=20, t=10, b=10))
    card1 = Card("Boos", fig, tooltip="test")
    card2 = Card("attention", fig, tooltip="test")

    cards = [[card1,1,1,5],[card2,1,3,10]]
    container = Container(cards)
    container.get_card_info()

    app.layout = html.Div([card1.create(), card2.create()])
    app.run_server(debug=True)







