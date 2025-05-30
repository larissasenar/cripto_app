from crypto_api import get_crypto_price

preco = get_crypto_price("bitcoin", "brl")
print(f"Preço do BTC em BRL: {preco}")

