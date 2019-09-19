from datetime import date
import pandas as pd
from math import pi

from bokeh.layouts import column, row, WidgetBox
from bokeh.models import Panel, ColumnDataSource, HoverTool
from bokeh.models.widgets import CheckboxGroup, Select, DateRangeSlider, MultiSelect, Div
from bokeh.palettes import Category20c
from bokeh.plotting import figure

from scripts.auxiliary_functions import get_metric_attr, get_multselect_options, create_div_title, filter_data, filter_sentiment
from scripts.plots import make_plot_ts, make_dotplot, make_plot_donut, make_box
from scripts.metric_functions import percent, percent_avg, brand_health_monthly, brand_health_txengages, velocity, positivity, post_health, vetor_gradiente


def create_tab(data, name):
    
    def make_dataset(metric_fun, metric_sentiment, month_start, month_end, editorial, category, social_network, product):
        """Constrói os datasets para cada tipo de gráfico utilizado no dashboard

        Parâmetros
        ----------
        data : DataFrame
            Pandas DataFrame expandido com dados do Sprinklr
        metric_fun : FUN
            Função para calcular métrica específica selecionada no widget
        metric_sentiment : str
            Sentimento relacionado à métrica escolhida (Positividade: positivo, Gradiente: negativo, Crise: negativo, Saúde do post: positivo)
        [restante] : str
            Valaores selecionados nas opções de filtros nos widgets 
        Retorna
        -------
        dict
            Dicionário com três chaves, correspondentes aos três gráficos apresentados. Cada chave é relacionada ao nome o gráfico 
            e os valores são datasets no formato column data source
        """
        month_start = pd.Timestamp(month_start)
        month_end = pd.Timestamp(month_end)
        
        # Filtragem dos dados com base nas seleções dos widgets
        filters = {'Editoria':editorial,
        'Categoria':category,
        'SocialNetwork':social_network,
        'Produto':product}
        filtered_data = filter_data(data, filters)

        # Gera datasets para cada gráfico
        ts_data = metric_fun(filtered_data)
        ts_data = ts_data[(ts_data.time >= month_start) & (ts_data.time <= month_end)]

        donut_data = filtered_data[(filtered_data.Month >= month_start) & (filtered_data.Month <= month_end)]
        donut_data = percent(donut_data)
        donut_data['angle'] = donut_data['value']/sum(donut_data['value']) * 2*pi
        donut_data['color'] = Category20c[donut_data.shape[0]]
        
        avg_donut_data = percent_avg(filtered_data)
        avg_donut_data = avg_donut_data[avg_donut_data.Month == month_end][['Sentimento','MAVG']]
        avg_donut_data.columns = ['label','value']
        avg_donut_data['angle'] = avg_donut_data['value']/sum(avg_donut_data['value']) * 2*pi
        avg_donut_data['color'] = Category20c[avg_donut_data.shape[0]]
        
        top_data = filter_sentiment(filtered_data, metric_sentiment)
        top_data = top_data[(top_data.Month >= month_start) & (top_data.Month <= month_end)]
        top_data = brand_health_txengages(top_data)
        avg_top_data = round(top_data.score.mean(),2)
        top_data = top_data.sort_values('score', ascending=False).iloc[:10]
        top_data = top_data.sort_values('score')
        top_data['recorte'] = ['1','2','3','4','5','6','7','8','9','10']

        # Converte dataframes em column data source
        datasets = {'ts': ColumnDataSource(ts_data),
                'donut': ColumnDataSource(donut_data),
                'avg_donut': ColumnDataSource(avg_donut_data),
                'top': ColumnDataSource(top_data),
                'avg_top':avg_top_data}

        return datasets

    def update(attr, old, new):
        """Constrói os datasets para cada tipo de gráfico utilizado no dashboard

        Parâmetros
        ----------
        old : ColumnDataSource
            Dataframe antigo relacionado aos filtros antigos
        new : ColumnDataSource
            Dataframe novo, com linhas filtradas de acordo com seleções mais recentes
        """
        month_start = month_select.value_as_date[0]
        month_end = month_select.value_as_date[1]
        editorial = editorial_select.value
        category = category_select.value
        product = product_select.value
        social_network = [social_network_select.labels[i] for i in social_network_select.active]
        metric = metric_select.value
        metric_attr = get_metric_attr(metric)
        metric_fun = metric_attr['fun']
        metric_sentiment = metric_attr['sentiment']

        new_src = make_dataset(metric_fun = metric_fun, 
                               metric_sentiment = metric_sentiment, 
                               month_start = month_start, 
                               month_end = month_end, 
                               editorial = editorial, 
                               category = category, 
                               social_network = social_network, 
                               product = product)
        src['ts'].data.update(new_src['ts'].data)
        src['top'].data.update(new_src['top'].data)
        src['avg_top'] = new_src['avg_top']
        src['donut'].data.update(new_src['donut'].data)
        src['avg_donut'].data.update(new_src['avg_donut'].data)

    networks = data.SocialNetwork.unique().tolist()
    editorials = get_multselect_options(data, 'Editoria')
    categories = get_multselect_options(data, 'Categoria')
    products = get_multselect_options(data, 'Produto')

    month_select = DateRangeSlider(start=date(2019,1,1), end=date(2019,8,1),value=(date(2019,1,1),date(2019,8,1)), step=1, format="%b %Y")
    metric_select = Select(value="gradiente", options=[("velocity","Parâmetro de Crise"), 
                                                                        ("positivity","Grau de Positividade"),
                                                                        ("gradiente","Grau de Negatividade"),
                                                                        ("brand_health","Saúde da Marca"),
                                                                        ("post_health","Saúde do Post")])
    product_select = MultiSelect(value=['Todos'], options=products)
    category_select = MultiSelect(value=['Todos'], options=categories)
    editorial_select = MultiSelect(value=['Todos'], options=editorials)
    social_network_select = CheckboxGroup(labels=networks, active=list(range(len(networks))))

    metric_select.on_change('value', update)
    month_select.on_change('value', update)
    editorial_select.on_change('value', update)
    category_select.on_change('value', update)
    product_select.on_change('value', update)
    social_network_select.on_change('active', update)

    initial_metric_attr = get_metric_attr(metric_select.value)
    metric_sentiment = initial_metric_attr['sentiment']
    initial_networks = [social_network_select.labels[i] for i in social_network_select.active]
    
    src = make_dataset(metric_fun = initial_metric_attr['fun'],
                               metric_sentiment = metric_sentiment, 
                               month_start = month_select.value_as_date[0], 
                               month_end = month_select.value_as_date[1], 
                               editorial = editorial_select.value, 
                               category = category_select.value, 
                               social_network = initial_networks, 
                               product = product_select.value)

    p_ts = make_plot_ts(src['ts'], 'Evolução', metric_sentiment)
    p_top = make_dotplot(src['top'])
    avg_top = src['avg_top']
    avg_top = create_div_title(f'Escore Médio: {avg_top}')
    p_donut = make_plot_donut(src['donut'], 'Percentual')
    p_avg_donut = make_plot_donut(src['avg_donut'], 'Norma Percentual')
    
    metric_title = create_div_title('MÉTRICA')
    month_title = create_div_title('PERÍODO')
    network_title = create_div_title('REDE SOCIAL')
    category_title = create_div_title('CATEGORIA')
    editorial_title = create_div_title('EDITORIA')
    product_title = create_div_title('PRODUTO')

    controls = WidgetBox(column(metric_title, metric_select,
                        Div(height = 5),
                        month_title, month_select,
                        Div(height = 5),
                        editorial_title, editorial_select,
                        Div(height = 5),
                        category_title, category_select,
                        Div(height = 5),
                        product_title, product_select,
                        Div(height = 5),
                        network_title, social_network_select, 
                        width = 250))

    plots = column(p_ts, Div(height = 20), row(p_donut, p_avg_donut))
    layout = row(controls, Div(width=50), plots)
    layout = column(Div(text="", height = 5), layout, Div(width = 20), avg_top, p_top)
    tab = Panel(child=layout, title = name)

    return tab