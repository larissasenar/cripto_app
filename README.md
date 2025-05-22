# Cripto Invest App

## Descrição

Cripto Invest App é uma aplicação web para gerenciar investimentos em criptomoedas. Permite acompanhar cotações em tempo real, visualizar gráficos de histórico de preços, converter valores entre moedas e consultar um FAQ com perguntas frequentes.

## Funcionalidades

- Dashboard com cotação atual de criptomoedas (Bitcoin, Ethereum, Litecoin, Dogecoin).
- Gráfico interativo de preços usando Chart.js.
- Conversor simples de valores entre moedas.
- Histórico de investimentos registrados.
- FAQ com perguntas frequentes.
- Layout responsivo para desktop e dispositivos móveis.
- Sidebar com menu acessível, incluindo botão hamburger para mobile.
- Proteção básica para exibição de dados do usuário.

## Tecnologias utilizadas

- Python 3
- Flask
- Jinja2 para templates
- Chart.js para gráficos
- HTML5 e CSS3 com responsividade
- Font Awesome para ícones

## Como executar

1. Clone este repositório:
git clone https://github.com/seu-usuario/cripto-invest-app.git
cd cripto-invest-app

2. Crie um ambiente virtual e ative:
python3 -m venv venv
source venv/bin/activate # Linux/macOS
venv\Scripts\activate # Windows

3. Instale as dependências:
pip install -r requirements.txt

4. Execute a aplicação:
flask run


5. Acesse `http://localhost:5000` no navegador.

## Estrutura de arquivos

- `app.py` — aplicação Flask principal
- `templates/` — arquivos HTML com Jinja2
- `static/` — CSS, JS, imagens e ícones
- `README.md` — este arquivo

## Contato

Para dúvidas ou sugestões, abra uma issue ou entre em contato via email: larissasenar@gmail.com

---

**Aviso:** Esta aplicação é para fins educacionais e não deve ser usada como plataforma de investimento real sem auditoria e segurança adequada.
