import pandas as pd, numpy as np, os, re, sys
from emoji import unicode_codes
from datetime import datetime

def direcionamento(data):
    """Função para replicar as mensagens com base em uma coluna com valores concatenados em lista
    Parâmetros
    ----------
    data : DataFrame
        Pandas DataFrame com dados do Sprinklr

    Retorna
    -------
    DataFrame
        DataFrame com a nova coluna de porcentagem de positivos
    """
    pct = data.groupby('Month')['Sentimento'].value_counts().groupby(level=group).apply(lambda x:x / float(x.sum()))
    pct.name = 'Percent'
    data = data.merge(pct, on=['Month','Sentimento'], right_index=True)
    return data
   
def media_movel(data, metric, lag):
    
    """funcao calcula a média movel de acordo com o cruzamento das variáveis"""
    
    aux = data[metric].rolling(window=lag).mean().round(2)
    
    return(aux)

def percent(data):
    """Calcula a porcentagem de menssagens de acordo com o sentimento
    Parâmetros
    ----------
    data : DataFrame
        Pandas DataFrame com dados do Sprinklr expandido

    Retorna
    -------
    DataFrame
        DataFrame com coluna contendo os valores das porcentagens de cada sentimento
    """
    col = data.columns[0]
    volume = data.groupby('Sentimento')[col].count()
    pct = pd.DataFrame(round(100 * volume/volume.sum(),2)).reset_index().rename(columns={col:'TotalPercent'})
    pct.columns = ['label','value']
    
    return pct

def percent_avg(data):
    """Calcula a média móvel anual e a média anual da porcentagem de menssagens de acordo com o sentimento
    Parâmetros
    ----------
    data : DataFrame
        Pandas DataFrame com dados do Sprinklr expandido

    Retorna
    -------
    DataFrame
        DataFrame com colunas contendo os valores das médias móvel e anual
    """
    col = data.columns[0]
    volume = data.groupby(['Month','Sentimento'])[col].count()
    pct = volume.groupby(level=0).apply(lambda x: 100 * x / float(x.sum())).reset_index().rename(columns={col:'Percent'})
    
    pct = pct.sort_values(['Sentimento','Month'])
    pct['MAVG'] = pd.DataFrame(pct.groupby('Sentimento').apply(lambda x: media_movel(x, 'Percent', 12))).reset_index(level='Sentimento')['Percent']

    pct['Year'] = pct.Month.apply(lambda x: str(x)[:4])
    avg = pct.groupby(['Year','Sentimento']).Percent.mean().round(2).reset_index().rename(columns={'Percent':'MediaAnual'})
    pct = pct.merge(avg, on=['Year','Sentimento'])
    
    return pct

def vetor_gradiente(data):
    """Função  para calcular a métrica do vetor gradiente
    ----------
    data : DataFrame
        Pandas DataFrame com dados do Sprinklr

    Retorna
    -------
    DataFrame
        DataFrame com a nova coluna de porcentagem de positivos
    """
    negative = data[data['Sentimento']=='Negativo']
    cont = negative['Month'].value_counts().reset_index().rename(columns={'index':'Month','Month':'Contagem'}).sort_values('Month')
    cont['Contagem_shift'] = cont.Contagem.shift()
    cont['Gradiente'] = round(cont.Contagem/cont.Contagem_shift,2)
    cont = cont.drop(['Contagem','Contagem_shift'], axis=1)
    cont['GMAVG'] = media_movel(cont, 'Gradiente', 12)
    cont.columns = ['time','metric','norm']

    return(cont)
  
def get_accel(serie):
    old = serie.shift(1)
    change = serie/old-1
    return change

def velocity(data):
    """Calcula a métrica de parâmetro de crise diária

    Parâmetros
    ----------
    data : DataFrame
        Pandas DataFrame com dados do Sprinklr expandido e filtrado

    Retorna
    -------
    DataFrame
        DataFrame com as colunas de velocidade diária e velocidade média diárias
    """
    col = data.columns[0]
    negative = data[data.Sentimento == 'Negativo']
    
    volume = negative.groupby('Day')[col].count() 
    acceleration = get_accel(volume)
    velocity = pd.DataFrame(volume*acceleration).round(2).rename(columns={col:'VelocidadeDiária'}).reset_index()

    avg = media_movel(velocity, 'VelocidadeDiária',30)
    accel_avg = get_accel(avg)
    velocity['VelocidadeMédia'] = avg*accel_avg
    velocity.columns = ['time','metric','norm']

    return velocity

def positivity(data):
    """Calcula a métrica de grau de positivdade para cada mês

    Parâmetros
    ----------
    data : DataFrame
        Pandas DataFrame com dados do Sprinklr expandido e filtrado

    Retorna
    -------
    DataFrame
        DataFrame com as colunas de positividade e média móvel
    """
    col = data.columns[0]
    positive = data[data.Sentimento == 'Positivo']

    volume = positive.groupby('Month')[col].count()
    volume = volume.reset_index().rename(columns={col:'Volume'})
    
    volume['MAVG'] = media_movel(volume, 'Volume', 12)
    volume['Positivity'] = round(volume['Volume']/volume['MAVG'],2)
    
    volume['PMAVG'] = media_movel(volume, 'Positivity', 12)
    gp = volume.drop(columns=['Volume','MAVG'])
    gp.columns = ['time','metric','norm']

    return gp

def brand_health_txengages(data):
    
    """Função para importar o dataset do Sprinklr e calcular a metrica de saude da marca
    ----------
    
    data : dataframe feito através da biblioteca pandas do python
        
    Parâmetros : 
    ----------
    
        data = dataframe com as seguintes colunas. O dataframe já vai vir com a limpeza da base e com o filtro do sentimento, a saber: positivo ou negativo.
    
    Retorna :
    -------
    DataFrame
        DataFrame com as colunas de post e engajamento
    """
    
    # conjunto de redes sociais usadas
    network = np.unique(data.SocialNetwork)
    weights = [[3,2,1] for i in range(len(network))]
    engages = [['shares','comments','likes'] for i in range(len(network))]

    # criando os subsets e calculando os engajamentos para cada rede social
    for i in range(0, len(network)):
        eng = networks_engages(data, weights[i], engages[i], network[i])

        if i == 0:
            net = eng
        else:
            net = pd.concat([net, eng])
    data = net.loc[:,['Message','tx_engages','SocialNetwork']]
    data['tx_engages'] = round(data['tx_engages'],2) 
    data = data.drop_duplicates()
    data.columns = ['post','score','net']

    return(data)

def brand_health_monthly(data):
    
    """Função para importar o dataset do Sprinklr e calcular a metrica de saude da marca
    ----------
    
    data : dataframe feito através da biblioteca pandas do python
        
    Parâmetros : 
    ----------
    
        data = dataframe com as seguintes colunas. O dataframe já vai vir com a limpeza da base
    
    Retorna :
    -------
    DataFrame
        DataFrame com as colunas de data e metrica saude da marca
    """
    
    # retirando os neutros
    data = data.loc[data.Sentimento != 'Neutro',]

    # subsets de sentimentos
    negativo = data.loc[data.Sentimento == 'Negativo',]
    positivo = data.loc[data.Sentimento == 'Positivo',]

    # pegando todas as redes sociais
    network = np.unique(data.SocialNetwork)
    weights = [[3,2,1] for i in range(len(network))]
    engages = [['shares','comments','likes'] for i in range(len(network))]

    # criando os subsets e calculando os engajamentos para cada rede social
    for i in range(0, len(network)):
        pos = networks_engages(positivo, weights[i], engages[i], network[i])
        neg = networks_engages(negativo, weights[i], engages[i], network[i])

        if i == 0:
            net = pd.concat([neg, pos])
        else:
            net = pd.concat([net, pos])
            net = pd.concat([net, neg])

    # calculando a saude da marca        
    data = net

    time = data.loc[data.Sentimento == 'Positivo',].groupby(['Month'])['tx_engages'].mean().reset_index(drop=False).iloc[:,0]
    saude_marca = minmax(data.loc[data.Sentimento == 'Positivo',].groupby(['Month'])['tx_engages'].mean().reset_index(drop=False).iloc[:,1] - data.loc[data.Sentimento == 'Negativo',].groupby(['Month'])['tx_engages'].mean().reset_index(drop=False).iloc[:,1])
    data = pd.DataFrame(time)
    data['metric'] = round(saude_marca,2)
    data['norm'] = media_movel(data, 'metric', 12)
    data = data.rename(columns={'Month':'time'})
    
    return(data)

def post_health(data):
    
    """Função para importar o dataset do Sprinklr e calcular a metrica de saude do post
    ----------
    
    data : dataframe feito através da biblioteca pandas do python
        
    Parâmetros : 
    ----------
    
        data = dataframe com as seguintes colunas. O dataframe já vai vir com a limpeza da base
    
    Retorna :
    -------
    DataFrame
        DataFrame com as colunas de data e metrica saude do post
    """
    
    # subsets de sentimentos
    data = data.loc[data.Sentimento == 'Positivo',]

    # pegando todas as redes sociais
    network = np.unique(data.SocialNetwork)
    weights = [[3,2,1] for i in range(len(network))]
    engages = [['shares','comments','likes'] for i in range(len(network))]

    # criando os subsets e calculando os engajamentos para cada rede social
    for i in range(0, len(network)):
        pos = networks_engages(data, weights[i], engages[i], network[i])

        if i == 0:
            net = pos
        else:
            net = pd.concat([net, pos])

    # calculando a saude da marca        
    data = net

    time = data.loc[data.Sentimento == 'Positivo',].groupby(['Month'])['tx_engages'].mean().reset_index(drop=False).iloc[:,0]
    saude_post = minmax(data.loc[data.Sentimento == 'Positivo',].groupby(['Month'])['tx_engages'].mean().reset_index(drop=False).iloc[:,1])
    data = pd.DataFrame(time)
    data['metric'] = round(saude_post,2)
    data['norm'] = media_movel(data, 'metric', 12)
    data = data.rename(columns={'Month':'time'})
    
    return(data)

def minmax(x):
    x = pd.Series(x)
    y = (x - np.min(x))/(np.max(x) - np.min(x))
    return y

def networks_engages(data, weights, engages, network):

    """Função para importar o dataset do Sprinklr e calcular a metrica engajamento para cada rede social
    ----------
    data : dataframe
        
    Parâmetros : 
    ----------
        data = dataframe
        weights = pesos para cada engajamento
        engages = colunas de engajamentos
        network = rede social a ser filtrada
    
    Retorna :
    -------
    DataFrame
        DataFrame com a coluna de engajamento do post
    """
        
    # filtrando pela rede social
    networks = data.loc[data.SocialNetwork == network]
    
    # agrupando pelas id's das menções para não ter problemas de repetição
    aux = networks.groupby('UniversalMessageId').sum()
    aux['UniversalMessageId'] = aux.index
    aux = aux.reset_index(drop=True)
    
    # inserindo as menções no dataset agrupado
    aux = aux.merge(networks[['UniversalMessageId','Message']], on='UniversalMessageId',how='left')
    
    # calculo da tx de engajamento
    result_tx = (np.dot(aux.loc[:,engages], weights)/aux.loc[:,'alcance'])*100
    
    # inserindo na base
    aux['tx_engages'] = result_tx
    networks = networks.merge(aux[['UniversalMessageId','tx_engages']], on='UniversalMessageId',how='left')
    
    return(networks)