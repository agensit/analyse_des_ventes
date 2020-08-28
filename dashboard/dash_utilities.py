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
                                       >> CARD <<
   ------------------------------------------------------------------------------------------- 
'''

class Card:
    """
    >> INPUTS <<
    ---------------------------------------------------------------------------------------------
        * title: card title (str)
        * tooltip: add a tolltip to describe the card in the top right corner (str, default = False)
        * graph: plotly figure (plotly.graph_objs._figure.Figure)
        * dash_config: dash configuration for the plotly figure (dict, default = {'displayModeBar': False, 'showAxisDragHandles':False})
        * width: card's width (1<=int<=12, default = 12)
        * height: card's height (str default = '100%')
        * row_number: row location in the dashboard (int)
        * order: card's order in the row (int)

    >> OUTPUT <<
    -------------------------------------------------------
    create a card object which could be use in the dashboard
"""
    def __init__(self, title, graph, tooltip=None, dash_config={'displayModeBar': False, 'showAxisDragHandles':False}):
        self.title = html.H2(title)
        self.graph = dcc.Graph(figure=graph, config=dash_config, style={"width":"100%"})
        self.width = 12
        self.height = "100%" # need to be remoove
        self.row_number = None
        self.order = None

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

    def set_format(self, width=12, height="100%"):
        self.width = width
        self.height = height # will be remoove

    def set_location(self, row_number, order):
        self.row_number = row_number
        self.order = order

    def create(self):
        top_row = [dbc.Col(self.title, width=4, className="ml-5")]
        if self.tooltip:
            top_row.append(dbc.Col(self.tooltip, width=1, className="mt-1"))

        return html.Div(
            [
                dbc.Row(top_row, justify="between"),
                dbc.Row(self.graph, className="ml-3 mr-3")
            ],
            className="my-4 mx-0 border",
            style={"background-color": "white"}
        )


'''------------------------------------------------------------------------------------------- 
                                         >> Container <<
   ------------------------------------------------------------------------------------------- 
'''         
class Container:
    """
        >> INPUTS <<
        ---------------------------------------------------------------------------------------------
            * margin: set the margin between the cards (0<=int<=5, default=4)
            * backgorund_color: color of the background ( str, default="white")

        >> OUTPUT <<
        -------------------------------------------------------
        Create the panel where we organise all our cards. This is the core of our dashboard
    """
    def __init__(self, cards, margin=4, background_color="white"):
        self.cards = cards
        self.margin = margin
        self.background_color = background_color

    def info(self):
        print("CONTAINER:")
        print("---------------")
        print(f"margin: {self.margin}")
        print(f"background color: {self.background_color}")
        for i,card in enumerate(self.cards):
            print("")
            print(f"CARD #{i}")
            print(f"\ttitle:{card.title.children}")
            print(f"\t width: {card.width}")
            print(f"\t height: {card.height}")
            print(f"\t row's number: {card.row_number}")
            print("\t order in row: {card.order}")

    def create_row(self, n, size):
        cards = [card for card in self.cards if card.row_number == n]
        row = dbc.Row(
            children =[],
            style={"height": size},
            className="mx-2"
            )
        for card in cards:
            row.children.append(dbc.Col(card.create(), width=card.width))
        return row



'''------------------------------------------------------------------------------------------- 
                                            Test
   ------------------------------------------------------------------------------------------- 
'''
if __name__ == '__main__':

    # create a simple graph
    df = px.data.iris() # iris is a pandas DataFrame
    fig = px.scatter(df, x="sepal_width", y="sepal_length")
    fig.update_layout(margin=dict(l=20, r=20, t=10, b=10))

    # create cards
    card1 = Card("Boos", fig, tooltip="test")
    card1.set_location(row_number=1, order=1)
    card1.set_format(width=10)
    card2 = Card("attention", fig, tooltip="test")
    card2.set_location(row_number=1, order=2)
    card2.set_format(width=2)
    cards = [card1, card2]

    # container
    container = Container(cards)
    # container.info()
    row1 = container.create_row(1, '100%')

    app.layout = html.Div(row1)
    app.run_server(debug=True)







