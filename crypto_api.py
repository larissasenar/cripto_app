import requests
from datetime import datetime
import time

# Cache para preços atuais e históricos (tempo em segundos)
cache_precos = {}
cache_historico = {}
tempo_cache = 60  # tempo de cache em segundos

def get_crypto_price(cripto):
    agora = time.time()
    if cripto in cache_precos and (agora - cache_precos[cripto]['tempo'] < tempo_cache):
        return cache_precos[cripto]['preco']

    try:
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={cripto}&vs_currencies=usd'
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        preco = dados.get(cripto, {}).get('usd')
        if preco is not None:
            cache_precos[cripto] = {'preco': preco, 'tempo': agora}
        return preco
    except Exception as e:
        print(f"Erro ao buscar preço de {cripto}: {e}")
        return None

def get_price_history(cripto):
    agora = time.time()
    if cripto in cache_historico and (agora - cache_historico[cripto]['tempo'] < tempo_cache):
        return cache_historico[cripto]['dados']

    try:
        url = f'https://api.coingecko.com/api/v3/coins/{cripto}/market_chart?vs_currency=usd&days=7'
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        lista_precos = []

        for item in dados.get('prices', []):
            timestamp = item[0] / 1000  # converter milissegundos para segundos
            data_formatada = datetime.fromtimestamp(timestamp).strftime('%d/%m')
            preco = round(item[1], 2)
            lista_precos.append({'data': data_formatada, 'preco': preco})

        cache_historico[cripto] = {'dados': lista_precos, 'tempo': agora}
        return lista_precos
    except Exception as e:
        print(f"Erro ao buscar histórico de {cripto}: {e}")
        return []

def converter_crypto(de, para):
    try:
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={de}&vs_currencies={para}'
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        return dados.get(de, {}).get(para)
    except Exception as e:
        print(f"Erro ao converter {de} para {para}: {e}")
        return None

def obter_historico_coingecko(cripto_id='bitcoin', dias=30):
    try:
        url = f'https://api.coingecko.com/api/v3/coins/{cripto_id}/market_chart'
        params = {
            'vs_currency': 'brl',
            'days': dias,
            'interval': 'daily'
        }

        resposta = requests.get(url, params=params, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        precos = dados['prices']  # Lista de [timestamp, preco]

        labels = []
        valores = []

        for timestamp, valor_preco in precos:
            data = datetime.utcfromtimestamp(timestamp / 1000).strftime('%d/%m')
            labels.append(data)
            valores.append(round(valor_preco, 2))

        return labels, valores
    except Exception as e:
        print(f"Erro ao obter histórico do CoinGecko: {e}")
        return [], []
