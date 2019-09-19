# Pandas for data management
import pandas as pd
from os.path import dirname, join

# Bokeh basics 
from bokeh.io import curdoc
from bokeh.models.widgets import Tabs

# Each tab is drawn by one script
from scripts.auxiliary_functions import import_treat_data
from scripts.main_tab import create_tab

# Read data into dataframes
data = import_treat_data(join(dirname(__file__), 'input_data', 'dados.csv'))

# Create each of the tabs
tab1 = create_tab(data, 'TIM')
tab2 = create_tab(data, 'Usuários')

# Put all the tabs into one application
tabs = Tabs(tabs = [tab1, tab2])

# Put the tabs in the current document for display
curdoc().add_root(tabs)