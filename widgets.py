from datetime import date
from bokeh.models.widgets import CheckboxGroup, Select, DateRangeSlider, MultiSelect, Div

def get_multselect_options(var):
    """Constrói listas com opções de seleção para o widget multselect com base em uma coluna específica do dataset

    Parâmetros
    ----------
    var : str
        Nome da coluna do dataset correspondente ao widget
    Retorna
    -------
    list
        Lista com as opções de seleção do widget
    """
    global data
    options = data[var].unique().tolist()
    options.insert(0,'Todos')
    try:
        options.remove('')
    except:
        pass
    return options

def create_div_title(title):
    """Constrói div com texto formatado para ser o título dos widgets

    Parâmetros
    ----------
    title : str
        Nome do título do widget
    Retorna
    -------
    Div
        Elemento do tipo Div do Bokeh
    """
    text = f'<b><font size=2 color="#00004C">{title}</font></b>'
    div = Div(text=text)
    return div

networks = data.SocialNetwork.unique().tolist()
editorials = get_multselect_options('Editoria')
categories = get_multselect_options('Categoria')
products = get_multselect_options('Produto')

month_select = DateRangeSlider(start=date(2019,1,1), end=date(2019,9,1),value=(date(2019,1,1),date(2019,9,1)), step=1, format="%b %Y")

metric_select = Select(title="Métrica:", value="velocity", options=[("velocity","Parâmetro de Crise"), 
                                                                    ("positivity","Grau de Positividade"),
                                                                    ("gradiente","Grau de Negatividade"),
                                                                    ("brand_health","Saúde da Maca"),
                                                                    ("post_health","Saúde do Post")])

product_select = MultiSelect(value=['Todos'],
                           options=products)
category_select = MultiSelect(value=['Todos'],
                           options=categories)
editorial_select = MultiSelect(value=['Todos'],
                           options=editorials)
social_network_select = CheckboxGroup(
        labels=networks, active=list(range(len(networks))))

metric_title = create_div_title('MÉTRICA')
network_title = create_div_title('REDE SOCIAL')
category_title = create_div_title('CATEGORIA')
editorial_title = create_div_title('EDITORIA')
product_title = create_div_title('PRODUTO')