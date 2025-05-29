import requests
from datetime import datetime
from typing import Optional, List, Tuple, Dict

# Mapeamento de IDs comuns para os IDs da CoinGecko
# Ex: 'btc' -> 'bitcoin', 'brl' -> 'brazilian-real'
# Este mapa é usado para garantir que as requisições à API CoinGecko usem os IDs corretos.
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


# URL base para a API CoinGecko
BASE_URL_COINGECKO = "https://api.coingecko.com/api/v3"

def get_crypto_price(cripto_id: str, vs_currency: str = "brl") -> Optional[float]:
    """
    Retorna o preço atual de uma criptomoeda em relação à moeda especificada.
    Usa fallback de preço simulado se a API CoinGecko falhar.
    """
    cg_crypto_id = COINGECKO_IDS.get(cripto_id.lower())
    if not cg_crypto_id:
        print(f"Erro: ID da criptomoeda '{cripto_id}' não reconhecido ou mapeado.")
        return None
    
    try:
        url = f'{BASE_URL_COINGECKO}/simple/price?ids={cg_crypto_id}&vs_currencies={vs_currency.lower()}'
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        preco = dados.get(cg_crypto_id, {}).get(vs_currency.lower())
        return preco
    except requests.exceptions.RequestException as e:
        print(f"[Erro] Falha na API, usando preço simulado para {cripto_id}: {e}")
        precos_simulados = {
            'bitcoin': 600000,
            'ethereum': 15000,
            'litecoin': 500,
            'dogecoin': 1.25,
            'cardano': 2,
            'binancecoin': 3000,
            'solana': 700,
            'matic-network': 5,
            'tether': 5,
            'usd-coin': 5,
            'brazilian-real': 1,
            'usd': 5,
            'eur': 6
        }
        return precos_simulados.get(cg_crypto_id, 100)  # valor padrão se não encontrar
    except Exception as e:
        print(f"[Erro] Erro inesperado ao buscar preço de {cripto_id}: {e}")
        precos_simulados = {
            'bitcoin': 600000,
            'ethereum': 15000,
            'litecoin': 500,
            'dogecoin': 1.25,
            'cardano': 2,
            'binancecoin': 3000,
            'solana': 700,
            'matic-network': 5,
            'tether': 5,
            'usd-coin': 5,
            'brazilian-real': 1,
            'usd': 5,
            'eur': 6
        }
        return precos_simulados.get(cg_crypto_id, 100)


def get_price_history(cripto_id: str, dias: int = 7, moeda: str = "brl") -> List[Dict[str, str]]:
    """
    Retorna histórico de preços de uma criptomoeda nos últimos dias.
    Faz uma requisição direta à API CoinGecko.

    Args:
        cripto_id: Identificador da criptomoeda (ex: 'bitcoin'). Será mapeado para ID da CoinGecko.
        dias: Quantidade de dias a serem buscados para o histórico.
        moeda: Moeda para conversão (ex: 'brl').

    Returns:
        Lista de dicionários, cada um com 'data' (formatada) e 'preco'.
    Raises:
        requests.exceptions.RequestException: Em caso de falha na requisição HTTP.
        Exception: Para outros erros inesperados.
    """
    cg_cripto_id = COINGECKO_IDS.get(cripto_id.lower())
    if not cg_cripto_id:
        print(f"Erro: ID da criptomoeda '{cripto_id}' não reconhecido ou mapeado para histórico.")
        return []
    
    try:
        url = f'{BASE_URL_COINGECKO}/coins/{cg_cripto_id}/market_chart?vs_currency={moeda.lower()}&days={dias}'
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        lista_precos = []

        for item in dados.get('prices', []):
            timestamp = item[0] / 1000 
            data_formatada = datetime.fromtimestamp(timestamp).strftime('%d/%m') # Formato DD/MM
            preco = round(item[1], 2)
            lista_precos.append({'data': data_formatada, 'preco': preco})

        return lista_precos
    except requests.exceptions.RequestException as e:
        print(f"[Erro] Falha ao buscar histórico de {cripto_id}: {e}")
        raise e 
    except Exception as e:
        print(f"[Erro] Erro inesperado ao buscar histórico de {cripto_id}: {e}")
        raise e 


def converter_crypto(from_id: str, to_id: str, testar: bool = False) -> Optional[float]:
    """
    Converte o valor de uma moeda/cripto para outra, retornando a taxa de conversão.
    Lida com conversões Crypto<->Fiat e Crypto<->Crypto de forma inteligente.

    Args:
        from_id: ID da moeda/cripto de origem (ex: 'btc', 'brl', 'ethereum').
        to_id: ID da moeda/cripto de destino (ex: 'eth', 'usd', 'bitcoin').
        testar: Se True, retorna valor simulado caso API falhe (útil para testes).

    Returns:
        Taxa de conversão (1 FROM_ID = X TO_ID) como float ou None em caso de erro/moeda não suportada.
    Raises:
        requests.exceptions.RequestException: Em caso de falha na requisição HTTP (se testar=False).
        Exception: Para outros erros inesperados (se testar=False).
    """
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
                price_to_fiat_in_usd = get_crypto_price(to_cg_id, 'usd')
                return 1 / price_to_fiat_in_usd if price_to_fiat_in_usd else None
            elif to_cg_id == 'usd':
                return get_crypto_price(from_cg_id, 'usd')
            else:
                from_fiat_in_usd = get_crypto_price(from_cg_id, 'usd')
                to_fiat_in_usd = get_crypto_price(to_cg_id, 'usd')
                if from_fiat_in_usd is not None and to_fiat_in_usd is not None and to_fiat_in_usd != 0:
                    return from_fiat_in_usd / to_fiat_in_usd
                else:
                    print(f"Erro: Não foi possível obter preços em USD para conversão Fiat-Fiat entre {from_id} e {to_id}.")
                    return None

        elif is_from_fiat and not is_to_fiat:
            crypto_price_in_fiat = get_crypto_price(to_cg_id, from_cg_id)
            if crypto_price_in_fiat is not None and crypto_price_in_fiat != 0:
                return 1 / crypto_price_in_fiat
            else:
                print(f"Erro: Não foi possível obter o preço de {to_id} em {from_id} para conversão Fiat-Crypto.")
                return None

        elif not is_from_fiat and is_to_fiat:
            return get_crypto_price(from_cg_id, to_cg_id)

        else:  # Crypto para Crypto
            from_crypto_price_brl = get_crypto_price(from_cg_id, 'brl')
            to_crypto_price_brl = get_crypto_price(to_cg_id, 'brl')

            if from_crypto_price_brl is not None and to_crypto_price_brl is not None and to_crypto_price_brl != 0:
                return from_crypto_price_brl / to_crypto_price_brl
            else:
                print(f"Erro: Não foi possível obter preços em BRL para conversão Crypto-Crypto entre {from_id} e {to_id}.")
                return None

    except requests.exceptions.RequestException as e:
        print(f"[Erro] Falha na conversão de {from_id} para {to_id}: {e}")
        if testar:
            print("[Teste] Retornando valor simulado por falha na API.")
            return 42.0
        else:
            raise e
    except Exception as e:
        print(f"[Erro] Erro inesperado na conversão de {from_id} para {to_id}: {e}")
        if testar:
            print("[Teste] Retornando valor simulado por erro inesperado.")
            return 42.0
        else:
            raise e

    return None


def obter_historico_coingecko(cripto_id: str = 'bitcoin', days: int = 30) -> Tuple[List[str], List[float]]:
    """
    Obtém histórico de preços de uma criptomoeda para visualização em gráficos.
    Faz uma requisição direta à API CoinGecko.

    Args:
        cripto_id: Identificador da criptomoeda (ex: 'bitcoin'). Será mapeado para ID da CoinGecko.
        days: Número de dias do histórico.

    Returns:
        Tupla contendo:
            - Lista de labels de datas formatadas (para o eixo X do gráfico).
            - Lista de valores de preços correspondentes (para o eixo Y do gráfico).
    Raises:
        requests.exceptions.RequestException: Em caso de falha na requisição HTTP (incluindo 429 Too Many Requests).
        Exception: Para outros erros inesperados.
    """
    cg_cripto_id = COINGECKO_IDS.get(cripto_id.lower())
    if not cg_cripto_id:
        print(f"Erro: ID da criptomoeda '{cripto_id}' não reconhecido ou mapeado para histórico do CoinGecko.")
        return [], []

    try:
        url = f'{BASE_URL_COINGECKO}/coins/{cg_cripto_id}/market_chart'
        params = {
            'vs_currency': 'brl', 
            'days': days,
            'interval': 'daily'
        }

        resposta = requests.get(url, params=params, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        precos = dados.get('prices', [])

        labels = []
        valores = []

        for timestamp, valor_preco in precos:
            data = datetime.fromtimestamp(timestamp / 1000).strftime('%d/%m')
            labels.append(data)
            valores.append(round(valor_preco, 2))

        return labels, valores
    except requests.exceptions.RequestException as e:
        print(f"[Erro] Falha ao obter histórico do CoinGecko para {cripto_id}: {e}")
        raise e 
    except Exception as e:
        print(f"[Erro] Erro inesperado ao obter histórico do CoinGecko para {cripto_id}: {e}")
        raise e 