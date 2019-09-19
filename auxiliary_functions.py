import pandas as pd
import numpy as np, os, re, sys
from math import pi
from emoji import unicode_codes
from datetime import datetime, date

from bokeh.models import ColumnDataSource
from bokeh.palettes import Category20c
from bokeh.models.widgets import Div

from scripts.metric_functions import percent, percent_avg, brand_health_monthly, brand_health_txengages, velocity, positivity, post_health, vetor_gradiente

def import_data(file):
    """Função para importar e tratar os dados do Sprinklr
    ----------
    file : str ou list
        Caminho dos arquivos que se deseja importa
    
    Retorna
    -------
    DataFrame
        DataFrame com as colunas necessárias para as análises
    """
    data = pd.DataFrame()

    for i in file:
        df = pd.read_excel(f'../input_data/{i}')
        data = data.append(df)
    
    data['Year'] = data.CreatedTime.apply(lambda x: str(x)[:4])
    data['Month'] = pd.to_datetime(data.CreatedTime.apply(lambda x: str(x)[:7]+'-01'))
    data['Day'] = pd.to_datetime(data.CreatedTime.apply(lambda x: str(x)[:10]))
    data['SocialNetwork'] = data.SocialNetwork.apply(lambda x: x.lower().capitalize())
    data['share'] = data['Shares Count (SUM)']+data['Twitter Retweets (SUM)']
    data['comments'] = [data.iloc[x]['Replies Count (SUM)']+data.iloc[x]['Comments Count (SUM)'] if data.iloc[x]['Comments Count (SUM)'] == 0 else data.iloc[x]['Comments Count (SUM)'] for x in range(0,data.shape[0])]
    data['likes'] = data['Likes Count (SUM)']

    data = data.fillna('')
    data = data.drop_duplicates(subset=['UniversalMessageId'])    
    data = reescreve_sentimento(data, 31, new_column = "Sentimento", words = ["NEUTRAL","POSITIVE","NEGATIVE"], vector_replace = ["Neutro","Positivo","Negativo"])
    data = explode_split(data, 'UniversalMessageId', 'Assunto', ',', 'Categoria')
    data = explode_split(data, 'Id', 'Detalhamento', ',', 'Produto')
    data = data[['UniversalMessageId','Message','Year','Month','Day','Editoria','Categoria','Produto','SocialNetwork','Sentimento','shares','comments','likes','alcance']]

    return data

def import_treat_data(file):
    """Função para importar os dados já tratados do Sprinklr
    ----------
    file : str ou list
        Caminho do arquivo que se deseja importar
    
    Retorna
    -------
    DataFrame
        DataFrame com as colunas necessárias para as análises
    """
    data = pd.read_csv(file)
    data = data.fillna('')
    data['Month'] = pd.to_datetime(data.Month)
    data['Day'] = pd.to_datetime(data.Day)
    return data

def export(data, path, chunk_size):
    """Função exportar dados em chunks
    ----------
    data : DataFrame
        Pandas DataFrame com dados para exportar
    path : str
        Caminho do arquivo a ser exportado
    chunk_size : int
        Número de linhas em cada chunk
    """
    try:
        pd.read_csv(path)
    except:
        file = pd.DataFrame(columns=data.columns)
        file.to_csv(path, index = False, encoding='utf-8')
        
    index = range(1 * chunk_size, (len(data) // chunk_size + 1) * chunk_size, chunk_size)
    chunks = np.split(data, index)
    for c in chunks:
        c.to_csv(path, index = False, encoding='utf-8', mode='a', header=False)

def reescreve_sentimento(data, column, new_column, words, vector_replace):
    
    """Funcao que substitui palavras de uma coluna e retorna as labels desejadas.
    - data = dataset
    - column = a coluna que se deseja substituir as labels
    - new_column = coluna nova criada para a substituição
    - words = palavras antigas 
    - vector_replace = palavras a serem substituidas"""
    
    data[new_column] = data.iloc[:,column]
    for i in range(0,int(len(vector_replace))):
        data['Sentimento'] = data.iloc[:,int(data.shape[1]-1)].replace(words[i], vector_replace[i])
    return(data)

def emoji_lis(string):
    """Retornar a localização e emoji na lista de formato dic
    >>>emoji.emoji_lis("Oi, Eu estou tranks. 😁")
    >>>[{'location': 15, 'emoji': '😁'}]
    """
    _entities = []
    for pos,c in enumerate(string):
        if c in unicode_codes.UNICODE_EMOJI:
            _entities.append({
                "location":pos,
                "emoji": c
                })
    return _entities

def split_posts(data, columm):
    
    """funcao que divide um post em texto e emoji
    padroniza os textos
    retira emojis duplicados
    e devolve uma coluna com textos padronizados e outra coluna so com emojis"""
    
    for i in range(0,int(data.shape[0])):
        result_emojis = []
        text = str(data['Message'][i]).upper()
        emojis = emoji_lis(text)
        if len(emojis) == 0:
            result_emojis.append('')
        elif len(emojis) == 1:
            result_emojis.append(emoji_lis(text)[0]['emoji'])
        else:
            for j in range(0,len(emojis)):
                if j == 0:
                    result_emojis.append(emoji_lis(text)[j]['emoji'])
                else:
                    if emoji_lis(text)[j]['emoji'] != result_emojis[i]:
                        result_emojis[i] = result_emojis[i] + emoji_lis(text)[j]['emoji']
    data['Emojis'] = result_emojis
    data['Message'] = str(data['Message']).upper()
    re.sub('[^a-zA-Z0-9 \\\]', '', data['Message'])
    return(data)        

def explode_split(data, cid, csplit, split, name):
    """Função para replicar as mensagens com base em uma coluna com valores concatenados em lista
    Parâmetros
    ----------
    data : DataFrame
        Pandas DataFrame com dados do Sprinklr
    cid : str
        Nome da coluna utilizada como id único
    csplit : str
        Nome da coluna com valores para serem separados
    split : str
        Caractere usado para separar os valores
    name: str
        Nome da nova coluna criada com os valores separados
    
    Retorna
    -------
    DataFrame
        DataFrame com a nova coluna de valores separados e todas as replicações de linhas necessárias
    """
    splited = data[csplit].fillna('').apply(lambda x: x.split(split)).to_list()
    explode_df = pd.DataFrame(splited, index=data[cid])
    explode_df = explode_df.stack().reset_index([0, cid])
    explode_df.columns = [cid,name]

    new_data = data.merge(explode_df, on=cid, how='inner')
    new_data['Id'] = new_data.apply(lambda x: x[cid]+x[name], axis=1)

    return new_data

def gen_total(data, cid, columns):
    """Função criar linhas com valor 'Total' em todas as colunas de filtro para cada mensagem única
    Parâmetros
    ----------
    data : DataFrame
        Pandas DataFrame com dados do Sprinklr expandido
    cid : str
        Nome da coluna utilizada como id único
    columns : list[int]
        Posições das colunas de filtro
    
    Retorna
    -------
    DataFrame
        DataFrame com novas linhas com opção de 'Total' para os filtros
    """
    df = data.drop_duplicates(subset=[cid])
    df.iloc[:,columns] = 'Total'
    data = data.append(df)
    return data

def gen_combinations(row, columns):
    """Função para criar linhas com possíveis combinações de filtros considerando valores de cada coluna e 'Total'
        Considera apenas três colunas de filtro

    Parâmetros
    ----------
    row : Series
        Pandas Series
    columns : list[int]
        Posições das colunas de filtro usadas na combinação
    
    Retorna
    -------
    DataFrame
        DataFrame com novas linhas de combinações de valores para os filtros
    """
    new_row1, new_row2, new_row3 = [row.copy(),row.copy(),row.copy()]
    new_row1[columns[0]] = 'Total'
    new_row2[columns[1]] = 'Total'
    new_row3[columns] = 'Total'
    rows = pd.DataFrame([new_row1, new_row2, new_row3])
    return rows

def segment(data, columns_list):
    """Aplica as funções de combinações de opções de filtro em cada linha do conjunto original de dados

    Parâmetros
    ----------
    data : DataFrame
        Pandas DataFrame com dados do Sprinklr expandido
    columns_list : list[list[int]]
        Lista de combinações de posições das colunas de filtro usadas na combinação
    
    Retorna
    -------
    DataFrame
        DataFrame com todas as linhas de combinações de valores para os filtros
    """
    new_data = data.copy()
    for col in columns_list:
        df = data.apply(lambda x: gen_combinations(x, col), axis=1)
        df = pd.concat(df.to_list())
        new_data = new_data.append(df)
        
    new_data = new_data.drop_duplicates()
    new_data = gen_total(new_data, cid='UniversalMessageId', columns=[3,4,5])
    return(new_data)

def filter_data(df, args):
    """Filtra as linhas do datasets com base nos valores selecionados pelos widgets de específicas colunas

    Parâmetros
    ----------
    data : DataFrame
        Pandas DataFrame expandido com dados do Sprinklr
    args : dict
        dicionário contendo o nome das colunas filtro com chaves e as opções selecionadas nos widgets como valores
    Retorna
    -------
    DataFrame
        DataFrame com linhas filtradas de acordo com as seleções dos widgets
    """
    for key, value in args.items():
        if value == ['Todos']:
            continue
        df = df[df[key].isin(value)]
    return df

def filter_sentiment(data, metric_sentiment):
    """Filtra as linhas do dataset com base sentimento relacionado a métrica selecionada

    Parâmetros
    ----------
    data : DataFrame
        Pandas DataFrame expandido com dados do Sprinklr
    metric_sentiment : str
        Sentimento
    Retorna
    -------
    DataFrame
        DataFrame com linhas filtradas de acordo com as seleções dos widgets
    """
    if isinstance(metric_sentiment, str):
        metric_sentiment = [metric_sentiment]
    data = data[data.Sentimento.isin(metric_sentiment)]
    return data 

def make_dataset(data, metric_fun, metric_sentiment, month_start, month_end, editorial, category, social_network, product):
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
    top_data['recorte'] = top_data.post.apply(lambda x: x[:10])

    # Converte dataframes em column data source
    datasets = {'ts': ColumnDataSource(ts_data),
            'donut': ColumnDataSource(donut_data),
            'avg_donut': ColumnDataSource(avg_donut_data),
            'top': ColumnDataSource(top_data),
            'avg_top':avg_top_data}

    return datasets

def get_metric_attr(metric):
    """Constrói os datasets para cada tipo de gráfico utilizado no dashboard

    Parâmetros
    ----------
    metric : str
        Nome da métrica selecionada no widget

    Retorna
    -------
    dict
        Dicionário com duas chaves relacionadas à função que calcula a métrica e ao sentimento relacionado a ela.
    """
    metrics = {'positivity':(positivity,'Positivo'),
                'gradiente': (vetor_gradiente,'Negativo'),
                'post_health': (post_health,'Positivo'),
                'brand_health': (brand_health_monthly,['Positivo','Negativo']),
                'velocity': (velocity,'Negativo')}
                
    fun = metrics[metric][0]
    sentiment = metrics[metric][1]
    attr = {'fun':fun,
            'sentiment':sentiment}

    return attr

def get_multselect_options(data, var):
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
