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

    >> OUTPUT <<
    -------------------------------------------------------
    create a card object which could be use in the dashboard
"""
    def __init__(self, title, graph, tooltip=None, dash_config={'displayModeBar': False, 'showAxisDragHandles':False, 'responsive':True}):
        self.title = html.H2(title)
        self.graph = dcc.Graph(figure=graph, config=dash_config, style={"width":"100%"})
        self.width = True # default
        self.row_number = None

        if tooltip :
            self.tooltip = self.create_tooltip(tooltip) 
        else :
            self.tooltip = None

    def create_tooltip(self, tooltip):
        return html.Div(
            [
                dbc.Button("?", 
                	# outline=True, 
                	className="border rounded-circle mr-2 mt-1", 
                	id=f"tooltip-target_{self.title.children}", 
                	color="light",
                	style={"float":"right", "background-color": "white"},
                	),
                dbc.Tooltip(tooltip, target=f"tooltip-target_{self.title.children}", placement="left")
            ],
        )

    def format(self, row_number, width=12):
        self.row_number = row_number
        self.width = width

    def create(self):
        top_row = [dbc.Col(self.title, className="ml-2")] 
        # add tooltip in the right corner
        if self.tooltip:
            top_row.append(dbc.Col(self.tooltip)) 

        return html.Div(
            [
                dbc.Row(top_row, justify="between", style={"height":"10%"}),
                dbc.Row(self.graph, className="mx-2", style={"height":"85%"})
            ],
            className="m-2 border",
            style={"height":"98%","background-color": "white"}
        )

'''------------------------------------------------------------------------------------------- 
                                         >> Container <<
   ------------------------------------------------------------------------------------------- 
'''         
class Container:
    """
        >> INPUTS <<
        ---------------------------------------------------------------------------------------------
        	* cards: a list of card component difine with there row's location (num_row) and there width (width)
        	* row_dim: list of string which describe the height of each row
            * margin: set the margin between the cards (0<=int<=5, default=4)
            * backgorund_color: color of the background ( str, default="white")

        >> OUTPUT <<
        -------------------------------------------------------
        Create the panel where we organise all our cards. This is the core of our dashboard
    """
    def __init__(self, cards, row_dim, background_color="#fafafa"):
        self.cards = cards
        self.row_dim = row_dim
        self.background_color = background_color 

    def info(self):
        print("CONTAINER:")
        print("---------------")
        print(f"background color: {self.background_color}")
        for i,card in enumerate(self.cards):
            print("")
            print(f"CARD #{i}")
            print(f"\ttitle:{card.title.children}")
            print(f"\t width: {card.width}")
            print(f"\t height: {card.height}")
            print(f"\t row's number: {card.row_number}")

    def create_row(self, n, size):
        cards = [card for card in self.cards if card.row_number == n]
        row = dbc.Row(
            children =[],
            style={"height": size, "background-color": self.background_color},
            no_gutters=True,
            className="m-2"
            )
        for card in cards:
            row.children.append(dbc.Col(card.create(), width=card.width))
        return row

    def create_dashboard(self, cards, height="auto"):
    	n_row = max([card.row_number for card in cards])
    	container = html.Div([], style={"height":height, "background-color": self.background_color})
    	for row in range(n_row):
    		container.children.append(self.create_row(row+1, self.row_dim[row]))
    	return container



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
    card1 = Card("Boos", fig)
    card1.format(row_number=1,width=6)

    card2 = Card("attention", fig, tooltip="test")
    card2.format(row_number=1,width=6)

    card3 = Card("Allo", fig, tooltip="aloooo")
    card3.format(row_number=2, width=6)

    card4 = Card("test", fig, tooltip="test")
    card4.format(row_number=2,width=6)
   
    cards = [card1, card2,card3,card4]

    # container
    container = Container(cards, row_dim=["48%", "48%"])
    app.layout = container.create_dashboard(cards, "100vh")
    # TODO add footer | ADD Header



    app.run_server(debug=True)







