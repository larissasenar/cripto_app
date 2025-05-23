import requests
from datetime import datetime
import time
from typing import Optional, List, Tuple, Dict

# Cache para preços atuais e históricos (tempo em segundos)
cache_precos: Dict[str, Dict] = {}
cache_historico: Dict[str, Dict] = {}
tempo_cache = 60  # tempo de cache em segundos


def get_crypto_price(cripto: str, moeda: str = "usd") -> Optional[float]:
    """
    Retorna o preço atual de uma criptomoeda em relação à moeda especificada.
    
    Args:
        cripto: Nome do identificador da criptomoeda (ex: 'bitcoin').
        moeda: Moeda para conversão (ex: 'usd', 'brl').

    Returns:
        Preço atual como float ou None em caso de erro.
    """
    agora = time.time()
    cache_key = f"{cripto}_{moeda}"
    if cache_key in cache_precos and (agora - cache_precos[cache_key]['tempo'] < tempo_cache):
        return cache_precos[cache_key]['preco']

    try:
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={cripto}&vs_currencies={moeda}'
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        preco = dados.get(cripto, {}).get(moeda)
        if preco is not None:
            cache_precos[cache_key] = {'preco': preco, 'tempo': agora}
        return preco
    except Exception as e:
        print(f"[Erro] Falha ao buscar preço de {cripto}: {e}")
        return None


def get_price_history(cripto: str, dias: int = 7, moeda: str = "usd") -> List[Dict[str, str]]:
    """
    Retorna histórico de preços de uma criptomoeda nos últimos dias.

    Args:
        cripto: Nome do identificador da criptomoeda (ex: 'bitcoin').
        dias: Quantidade de dias a serem buscados.
        moeda: Moeda para conversão.

    Returns:
        Lista de dicionários com data e preço.
    """
    agora = time.time()
    cache_key = f"{cripto}_{moeda}_{dias}"
    if cache_key in cache_historico and (agora - cache_historico[cache_key]['tempo'] < tempo_cache):
        return cache_historico[cache_key]['dados']

    try:
        url = f'https://api.coingecko.com/api/v3/coins/{cripto}/market_chart?vs_currency={moeda}&days={dias}'
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        lista_precos = []

        for item in dados.get('prices', []):
            timestamp = item[0] / 1000  # converter de milissegundos
            data_formatada = datetime.fromtimestamp(timestamp).strftime('%d/%m')
            preco = round(item[1], 2)
            lista_precos.append({'data': data_formatada, 'preco': preco})

        cache_historico[cache_key] = {'dados': lista_precos, 'tempo': agora}
        return lista_precos
    except Exception as e:
        print(f"[Erro] Falha ao buscar histórico de {cripto}: {e}")
        return []


def converter_crypto(de: str, para: str) -> Optional[float]:
    """
    Converte o valor de uma criptomoeda para outra.

    Args:
        de: Identificador da criptomoeda de origem (ex: 'bitcoin').
        para: Moeda de destino (ex: 'brl').

    Returns:
        Valor convertido como float ou None em caso de erro.
    """
    try:
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={de}&vs_currencies={para}'
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        return dados.get(de, {}).get(para)
    except Exception as e:
        print(f"[Erro] Falha na conversão de {de} para {para}: {e}")
        return None


def obter_historico_coingecko(cripto_id: str = 'bitcoin', dias: int = 30) -> Tuple[List[str], List[float]]:
    """
    Obtém histórico de preços de uma criptomoeda para visualização em gráficos.

    Args:
        cripto_id: Nome do identificador da criptomoeda.
        dias: Número de dias do histórico.

    Returns:
        Tupla contendo:
            - Lista de datas formatadas.
            - Lista de preços correspondentes.
    """
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
        precos = dados.get('prices', [])

        labels = []
        valores = []

        for timestamp, valor_preco in precos:
            data = datetime.utcfromtimestamp(timestamp / 1000).strftime('%d/%m')
            labels.append(data)
            valores.append(round(valor_preco, 2))

        return labels, valores
    except Exception as e:
        print(f"[Erro] Falha ao obter histórico do CoinGecko: {e}")
        return [], []
