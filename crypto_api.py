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
        resposta = requests.get(url)
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
        resposta = requests.get(url)
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
        resposta = requests.get(url)
        resposta.raise_for_status()
        dados = resposta.json()
        return dados.get(de, {}).get(para)
    except Exception as e:
        print(f"Erro ao converter {de} para {para}: {e}")
        return None


# Exemplo de uso (pode remover na versão final)
if __name__ == '__main__':
    cripto = 'bitcoin'
    preco = get_crypto_price(cripto)
    historico = get_price_history(cripto)
    conversao = converter_crypto('bitcoin', 'ethereum')

    print(f"Preço atual de {cripto}: {preco}")
    print(f"Histórico de preços de {cripto}: {historico}")
    print(f"Conversão de {cripto} para ethereum: {conversao}")
