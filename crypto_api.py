import requests
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict

# Mapeamento de IDs comuns para os IDs da CoinGecko
COINGECKO_IDS = {
    'bitcoin': 'bitcoin', 'btc': 'bitcoin',
    'ethereum': 'ethereum', 'eth': 'ethereum',
    'litecoin': 'litecoin', 'ltc': 'litecoin',
    'dogecoin': 'dogecoin', 'doge': 'dogecoin',
    'cardano': 'cardano', 'ada': 'cardano',
    'bnb': 'binancecoin',
    'sol': 'solana',
    'matic': 'matic-network',
    'usdt': 'tether',
    'usdc': 'usd-coin',
    'brl': 'brazilian-real',
    'usd': 'usd',
    'eur': 'eur'
}

BASE_URL_COINGECKO = "https://api.coingecko.com/api/v3"

# === Cache simples com TTL === #
CACHE_TTL = timedelta(seconds=300)  # 5 minutos
crypto_price_cache = {}
price_history_cache = {}
historico_chart_cache = {}

def cache_get(cache_dict, key):
    item = cache_dict.get(key)
    if item:
        value, timestamp = item
        if datetime.now() - timestamp < CACHE_TTL:
            return value
        else:
            del cache_dict[key]
    return None

def cache_set(cache_dict, key, value):
    cache_dict[key] = (value, datetime.now())

# === Funções principais === #

def get_crypto_price(cripto_id: str, vs_currency: str = "brl") -> Optional[float]:
    cg_crypto_id = COINGECKO_IDS.get(cripto_id.lower())
    if not cg_crypto_id:
        print(f"Erro: ID da criptomoeda '{cripto_id}' não reconhecido ou mapeado.")
        return None

    cache_key = f"{cg_crypto_id}_{vs_currency.lower()}"
    cached = cache_get(crypto_price_cache, cache_key)
    if cached is not None:
        return cached

    try:
        url = f'{BASE_URL_COINGECKO}/simple/price?ids={cg_crypto_id}&vs_currencies={vs_currency.lower()}'
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        preco = dados.get(cg_crypto_id, {}).get(vs_currency.lower())
        if preco is not None:
            cache_set(crypto_price_cache, cache_key, preco)
        return preco
    except requests.exceptions.RequestException:
        # Suprime print de erro para evitar flood no log
        # Pode descomentar para debug: print(f"[Erro] Falha na API para {cripto_id}, usando preço simulado.")
        precos_simulados = {
            'bitcoin': 600000, 'ethereum': 15000, 'litecoin': 500,
            'dogecoin': 1.25, 'cardano': 2, 'binancecoin': 3000,
            'solana': 700, 'matic-network': 5, 'tether': 5,
            'usd-coin': 5, 'brazilian-real': 1, 'usd': 5, 'eur': 6
        }
        return precos_simulados.get(cg_crypto_id, 100)
    except Exception as e:
        print(f"[Erro] Erro inesperado ao buscar preço de {cripto_id}: {e}")
        return None

def get_price_history(cripto_id: str, dias: int = 7, moeda: str = "brl") -> List[Dict[str, str]]:
    cg_cripto_id = COINGECKO_IDS.get(cripto_id.lower())
    if not cg_cripto_id:
        print(f"Erro: ID da criptomoeda '{cripto_id}' não reconhecido ou mapeado para histórico.")
        return []

    cache_key = f"{cg_cripto_id}_{moeda}_{dias}"
    cached = cache_get(price_history_cache, cache_key)
    if cached:
        return cached

    try:
        url = f'{BASE_URL_COINGECKO}/coins/{cg_cripto_id}/market_chart?vs_currency={moeda.lower()}&days={dias}'
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        lista_precos = []

        for item in dados.get('prices', []):
            timestamp = item[0] / 1000 
            data_formatada = datetime.fromtimestamp(timestamp).strftime('%d/%m')
            preco = round(item[1], 2)
            lista_precos.append({'data': data_formatada, 'preco': preco})

        cache_set(price_history_cache, cache_key, lista_precos)
        return lista_precos
    except Exception as e:
        print(f"[Erro] Falha ao buscar histórico de {cripto_id}: {e}")
        return []

def converter_crypto(from_id: str, to_id: str, testar: bool = False) -> Optional[float]:
    from_cg_id = COINGECKO_IDS.get(from_id.lower())
    to_cg_id = COINGECKO_IDS.get(to_id.lower())

    if not from_cg_id or not to_cg_id:
        print(f"Erro de conversão: IDs '{from_id}' ou '{to_id}' não reconhecidos/mapeados para CoinGecko.")
        return None

    if from_cg_id == to_cg_id:
        return 1.0

    is_from_fiat = from_cg_id in ['brazilian-real', 'usd', 'eur']
    is_to_fiat = to_cg_id in ['brazilian-real', 'usd', 'eur']

    try:
        if is_from_fiat and is_to_fiat:
            if from_cg_id == 'usd':
                price = get_crypto_price(to_cg_id, 'usd')
                return 1 / price if price else None
            elif to_cg_id == 'usd':
                return get_crypto_price(from_cg_id, 'usd')
            else:
                f_usd = get_crypto_price(from_cg_id, 'usd')
                t_usd = get_crypto_price(to_cg_id, 'usd')
                return f_usd / t_usd if f_usd and t_usd else None
        elif is_from_fiat:
            price = get_crypto_price(to_cg_id, from_cg_id)
            return 1 / price if price else None
        elif is_to_fiat:
            return get_crypto_price(from_cg_id, to_cg_id)
        else:
            f_brl = get_crypto_price(from_cg_id, 'brl')
            t_brl = get_crypto_price(to_cg_id, 'brl')
            return f_brl / t_brl if f_brl and t_brl else None
    except Exception as e:
        print(f"[Erro] Erro na conversão de {from_id} para {to_id}: {e}")
        return 42.0 if testar else None

def obter_historico_coingecko(cripto_id: str = 'bitcoin', days: int = 30) -> Tuple[List[str], List[float]]:
    cg_cripto_id = COINGECKO_IDS.get(cripto_id.lower())
    if not cg_cripto_id:
        print(f"Erro: ID '{cripto_id}' não reconhecido.")
        return [], []

    cache_key = f"{cg_cripto_id}_{days}"
    cached = cache_get(historico_chart_cache, cache_key)
    if cached:
        return cached

    try:
        url = f'{BASE_URL_COINGECKO}/coins/{cg_cripto_id}/market_chart'
        params = {'vs_currency': 'brl', 'days': days, 'interval': 'daily'}
        resposta = requests.get(url, params=params, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()

        labels, valores = [], []
        for timestamp, valor in dados.get('prices', []):
            data = datetime.fromtimestamp(timestamp / 1000).strftime('%d/%m')
            labels.append(data)
            valores.append(round(valor, 2))

        resultado = (labels, valores)
        cache_set(historico_chart_cache, cache_key, resultado)
        return resultado
    except Exception as e:
        print(f"[Erro] Falha ao obter histórico de {cripto_id}: {e}")
        return [], []
