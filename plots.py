# Pacotes
import numpy as np, pandas as pd, time
from numpy import cumprod, linspace, random
from collections import Counter
from math import pi

from bokeh.layouts import gridplot, row, column, widgetbox
from bokeh.plotting import figure, show, output_file # ColumnDataSource
from bokeh.models import HoverTool, CustomJS, Slider, ColumnDataSource, BoxAnnotation, DatetimeTickFormatter, NumeralTickFormatter
from bokeh.io import output_notebook, show, output_file
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
from bokeh.palettes import Category20c
from bokeh.transform import cumsum, factor_cmap

def make_plot_donut(dados, title_graph):
    
    """Função para plotar a tabela de ranking de engajamento dos posts e os posts na íntegra
    ----------
    
    Ideia: Recebe um dataframe, feito a partir da biblioteca pandas
    Com 2 colunas: a primeira com os as labels
    a segunda coluna com os valores de cada label em percentual multiplicado por 100
     
    Nomes das colunas
     
    Parâmetros : 
    ----------
        
        data = dataframe
        title_graph = título do gráfico
        
    Retorna :
    -------
    plot donut
    """    
    
    p = figure(title=title_graph, toolbar_location=None, plot_width=488, plot_height=360,
               tools='hover', tooltips=[("Métrica", "@label"),("Valor", "@value{0.00 a}")])

    p.annular_wedge(x=0, y=1, inner_radius=0.2, outer_radius=0.4,
                    start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                    line_color="white", fill_color='color', legend='label', source=dados)

    p.axis.axis_label=None
    p.axis.visible=False

    return(p)

def make_table(data):
    
    """Função para plotar a tabela de ranking de engajamento dos posts e os posts na íntegra
    ----------
    
    Ideia: Recebe um dataframe, feito a partir da biblioteca pandas
    Com 2 colunas: a primeira com os posts que mais performaram
    a segunda coluna com os valores os escores calculados
     
    Nomes das colunas
     
    Parâmetros : 
    ----------
        data = dataframe
    
    Retorna :
    -------
    table
    """
    columns = [
            TableColumn(field="post", title="Posts que mais performaram"),
            TableColumn(field="score", title="Escore"),
        ]
    data_table = DataTable(source=data, columns=columns, width=1000, height=900)

    # output_file("table_chart.html", title="Table Chart")
    #show(widgetbox(data_table))
    
    return(data_table)


def make_plot_ts(data, title_graph, sentiment):
    
    """Função para plotar o gráfico de séries temporais
    ----------
    
    Ideia: Recebe um dataframe, feito a partir da biblioteca pandas
    Com 3 colunas: a primeira de data no formato 2019-09-10 14:23:23.736512
    criado a partir de: pd.date_range(pd.datetime.today(), periods=len(x)).strftime("%d-%m-%Y")
    a segunda coluna com os valores da métrica e a terceira da norma desta métrica
    
    Agora, há o argumento de 'sentiment' imposto para cada métrica para a confecção da região do gráfico.
    
    Nomes das colunas
     
    Parâmetros : 
    ----------
        data = dataframe
        
        title_graph = título do gráfico
    
    Retorna :
    -------
    
    plot de time series
    
    """
    #sentiment = 'Negativo'

    # montando o grádico
    TOOLS = "box_select, hover" # ,lasso_select,help
    p = figure(x_axis_type="datetime", title=title_graph, tools= TOOLS, plot_width=1000, plot_height=300)
    p.line(source = data, x = 'time', y = 'norm', color='#A6CEE3', legend='Norma', line_width = 2, 
            line_color="tomato", line_dash="dotted")
    p.circle(source=data, x = 'time', y = 'norm', fill_color=None, line_color="tomato")

    p.circle(source = data, x = 'time', y = 'metric', fill_color=None, line_color="blue")
    p.line(source = data, x = 'time', y = 'metric', legend='Métrica', line_width = 2.5)

    # legenda
    p.legend.location = "top_right"
    
    #box = make_box(data, sentiment)

    #p.add_layout(box)

    # tooltips
    hover = p.select(dict(type=HoverTool))
    hover.tooltips = [
        ("Métrica", "@metric{0.00 a}"),
        ("Norma", "@norm{0.00 a}")
    ]

    p.yaxis.formatter=NumeralTickFormatter(format="00")

    return(p)

def make_box(data, sentiment):
    
    #sentiment = 'Negativo'

    if sentiment == 'Negativo':
        pos = list(data.data['metric']).index(np.nanmax(data.data['metric']))
    else:
        pos = list(data.data['metric']).index(np.nanmin(data.data['metric']))
        
    box_left = data.data['time'][pos-1]
    box_right = data.data['time'][pos+1]
    
    box = BoxAnnotation(left=box_left, right=box_right,
                     line_width=1, line_color='black', line_dash='dashed',
                     fill_alpha=0.2, fill_color='royalblue')

    return(box)


def make_bar_table(data):
    
    """Função para plotar o gráfico de barra do escore das menções e a tabela ao lado das menções
    ----------
    
    Ideia: Recebe um dataframe, feito a partir da biblioteca pandas
    Com 3 colunas: a primeira post
    a segunda coluna com os valores dos escore e a terceira de recorte dos dados de 
    menções (10 caracteres mais reticências)
     
    Nomes das colunas
     
    Parâmetros : 
    ----------
        data = dataframe
        
        post = menções
        score = ranking do escore
        recorte = 10 caracteres da coluna de menções + reticências
    
    Retorna :
    -------
    
    plot de barrras e tabela
    
    """
    
    recorte = data.data['recorte']
    p = figure(x_range=recorte, plot_height=300, plot_width=700, toolbar_location=None, title=" ")
    p.vbar(x='recorte', top='score', width=0.9, source=data, legend=False,
          line_color='white', fill_color=factor_cmap('recorte', palette=np.repeat('royalblue',len(recorte)), factors=recorte))

    columns = [
        TableColumn(field="post", title="Post que Mais Performaram"),
        TableColumn(field="score", title="Escore")
    ]
    data_table = DataTable(source=data, columns=columns, width=650, height=500, index_position=None)

    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.y_range.end = max(data.data['score']) + 0.5
    # p.legend.orientation = None
    # p.legend.location = "top_center"

    plot = row(p, data_table)
    return(plot)

def make_dotplot(data):
    
    """Função para plotar o gráfico dot plot do escore das menções
    ----------
    
    Ideia: Recebe um dataframe, feito a partir da biblioteca pandas
    Com 3 colunas: a primeira post
    a segunda coluna com os valores dos escore e a terceira de recorte dos dados de 
    menções (10 caracteres mais reticências)
     
    Nomes das colunas
     
    Parâmetros : 
    ----------
        data = dataframe
        
        post = menções
        score = ranking do escore
        recorte = 10 caracteres da coluna de menções + reticências
    
    Exemplo de dados:
    ----------------
    
        source = ColumnDataSource(
            data=dict(
                post = data.data['post'],
                score = data.data['score'],
                recorte = data.data['recorte'],
                net = data.data['net']
            )
        )
        
    Retorna :
    -------
    
    plot do dot plot
    
    """
        
    recorte = data.data['recorte']

    hover = HoverTool(
            tooltips=[
                ("Escore", "@score"),
                ("Rede Social", "@net"),
                ("Post", "@post"),
            ]
        )

    dot = figure(title="Performance do Post",
                y_range=recorte, x_range=[0,data.data['score'].max()+0.1],tools=[hover], 
                plot_width=1310, plot_height=400) # tools= 'hover',  
    dot.segment(0, 'recorte', 'score', 'recorte', line_width=4, line_color="royalblue", source=data)
    dot.circle('score', 'recorte', size=20, fill_color="royalblue", line_color="royalblue", line_width=10, source=data)

    return(dot)