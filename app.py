"""
PROJETO ACADÊMICO - CRIPTO INVEST
Este é um projeto de estudo:
- Desenvolvimento web com Flask
- Integração com APIs de criptomoedas
- Bancos de dados SQLite
- Autenticação de usuários
- Visualização de dados em gráficos
"""


from flask import Flask, render_template, request, redirect, session
from datetime import datetime

from database import (
    init_db,
    cadastrar_usuario,
    verificar_usuario,
    salvar_investimento,
    listar_investimentos,
)

from crypto_api import (
    get_crypto_price,
    get_price_history,
    converter_crypto,
    obter_historico_coingecko
)

app = Flask(__name__)
app.secret_key = "chave_secreta"

# Inicializa o banco de dados
init_db()

# ROTAS PRINCIPAIS

@app.route('/')
def home():
    if 'usuario' in session:
        return redirect('/dashboard')
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = verificar_usuario(email, senha)

        if usuario:
            session['usuario'] = {'email': usuario[0], 'nome': usuario[1]}
            return redirect('/dashboard')
        else:
            return render_template('login.html', erro='Usuário ou senha inválidos')

    return render_template('login.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    erro = None
    sucesso = None

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        if not nome or not email or not senha or not confirmar_senha:
            erro = 'Por favor, preencha todos os campos.'
        elif senha != confirmar_senha:
            erro = 'As senhas não coincidem.'
        else:
            sucesso = cadastrar_usuario(nome, email, senha)
            if sucesso:
                return render_template('login.html', sucesso='Cadastro realizado com sucesso. Faça login.')
            else:
                erro = 'Usuário já existe.'

    return render_template('cadastro.html', erro=erro, sucesso=sucesso)


@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect('/login')



# DASHBOARD


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'usuario' not in session:
        return redirect('/login')

    usuario = session.get('usuario')
    if not isinstance(usuario, dict):
        session.pop('usuario', None)
        return redirect('/login')

    email = usuario.get('email', '')
    nome_usuario = usuario.get('nome', '')
    cripto = 'bitcoin'
    resultado_conversao = None
    ganhos = []

    # Ações do formulário
    if request.method == 'POST':
        if 'investir' in request.form:
            cripto = request.form['cripto']
            try:
                valor = float(request.form['valor'])
            except ValueError:
                valor = 0.0

            preco_atual = get_crypto_price(cripto)
            if preco_atual and valor > 0:
                salvar_investimento(email, cripto, valor, preco_atual)

        elif 'converter' in request.form:
            de = request.form['de']
            para = request.form['para']
            resultado_conversao = converter_crypto(de, para)

        elif 'buscar' in request.form:
            cripto = request.form['cripto']

    # Dados do usuário
    investimentos = listar_investimentos(email) or []
    preco_atual = get_crypto_price(cripto) or 0.0

    # Histórico para o gráfico
    historico_raw = get_price_history(cripto) or []
    historico = []
    for item in historico_raw:
        data_obj = item.get('data')
        preco_item = item.get('preco', 0.0)

        data_formatada = (
            data_obj.strftime('%d/%m') if isinstance(data_obj, datetime) else str(data_obj)
        )
        historico.append({'data': data_formatada, 'preco': preco_item})

    # Cálculo de ganhos/prejuízos
    for inv in investimentos:
        atual = get_crypto_price(inv.get('cripto', cripto))
        if atual is not None:
            ganho = round(atual - inv.get('preco', 0), 2)
            ganhos.append({
                'cripto': inv.get('cripto', cripto),
                'ganho': ganho
            })

    agora = datetime.now()
    data_formatada = agora.strftime('%d/%m/%Y')
    hora_formatada = agora.strftime('%H:%M:%S')

    # Gráfico com dados externos (CoinGecko)
    labels, dados_grafico = obter_historico_coingecko(cripto_id=cripto)

    return render_template('dashboard.html',
        nome_usuario=nome_usuario,
        preco=preco_atual,
        investimentos=investimentos,
        resultado=resultado_conversao,
        ganhos=ganhos,
        cripto=cripto,
        labels=labels,
        dados=dados_grafico,
        data=data_formatada,
        hora=hora_formatada
    )

# FAQ - Perguntas Frequentes


@app.route('/faq')
def faq():
    faq_perguntas = [
        {
            "pergunta": "O que é esta aplicação?",
            "resposta": "Permite investir em criptomoedas, acompanhar investimentos e visualizar histórico de preços."
        },
        {
            "pergunta": "Como funciona o investimento?",
            "resposta": "Você compra uma quantidade de criptomoeda e acompanha seu valor ao longo do tempo."
        },
        {
            "pergunta": "Minhas informações estão seguras?",
            "resposta": "Sim. Os dados são armazenados localmente com segurança e as senhas são criptografadas."
        },
        {
            "pergunta": "O que são criptomoedas?",
            "resposta": "São moedas digitais baseadas em blockchain, seguras e descentralizadas."
        },
        {
            "pergunta": "Posso perder dinheiro?",
            "resposta": "Sim. O mercado é volátil. Invista com cautela."
        },
        {
            "pergunta": "Como acompanho meus investimentos?",
            "resposta": "Na dashboard você vê os preços atuais, histórico gráfico e seus ganhos."
        },
    ]
    return render_template('faq.html', faq_perguntas=faq_perguntas)


# INICIAR SERVIDOR

if __name__ == "__main__":
    app.run(debug=True)

# FIM