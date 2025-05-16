
import requests

def get_crypto_price(cripto):
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={cripto}&vs_currencies=usd'
    try:
        resposta = requests.get(url)
        dados = resposta.json()
        return dados[cripto]['usd']
    except:
        return None

def get_price_history(cripto):
    url = f'https://api.coingecko.com/api/v3/coins/{cripto}/market_chart?vs_currency=usd&days=7'
    try:
        resposta = requests.get(url)
        dados = resposta.json()
        return dados['prices']
    except:
        return []

def converter_crypto(de, para):
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={de}&vs_currencies={para}'
    try:
        resposta = requests.get(url)
        dados = resposta.json()
        return dados[de][para]
    except:
        return None
