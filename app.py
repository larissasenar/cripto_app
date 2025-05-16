from flask import Flask, render_template, request, redirect, session
from database import (
    init_db,
    cadastrar_usuario,
    verificar_usuario,
    salvar_investimento,
    listar_investimentos,
)
from crypto_api import get_crypto_price, get_price_history, converter_crypto
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave_secreta"

# Inicializa o banco
init_db()

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

    preco = None
    historico = []
    resultado_conversao = None
    ganhos = []
    cripto = 'bitcoin'

    # POST - Investimento, conversão ou seleção de moeda
    if request.method == 'POST':
        if 'investir' in request.form:
            cripto = request.form['cripto']
            try:
                valor = float(request.form['valor'])
            except ValueError:
                valor = 0.0
            preco = get_crypto_price(cripto)
            if preco and valor > 0:
                salvar_investimento(email, cripto, valor, preco)

        elif 'converter' in request.form:
            de = request.form['de']
            para = request.form['para']
            resultado_conversao = converter_crypto(de, para)

        elif 'buscar' in request.form:
            cripto = request.form['cripto']

    # Coleta investimentos do usuário
    investimentos = listar_investimentos(email) or []

    # Cotação atual
    preco_atual = get_crypto_price(cripto) or 0.0

    # Histórico de preços para o gráfico
    historico_raw = get_price_history(cripto) or []
    historico = []
    for item in historico_raw:
        data_obj = item.get('data')
        preco_item = item.get('preco', 0.0)

        if isinstance(data_obj, datetime):
            data_formatada = data_obj.strftime('%d/%m')
        else:
            data_formatada = str(data_obj) if data_obj else ''

        historico.append({'data': data_formatada, 'preco': preco_item})

    # Cálculo de ganho/prejuízo por cripto
    for inv in investimentos:
        atual = get_crypto_price(inv.get('cripto', cripto))
        if atual is not None:
            ganho = round(atual - inv.get('preco', 0), 2)
            ganhos.append({
                'cripto': inv.get('cripto', cripto),
                'ganho': ganho
            })

    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    return render_template('dashboard.html',
                           investimentos=investimentos,
                           preco=preco_atual,
                           historico=historico,
                           resultado=resultado_conversao,
                           ganhos=ganhos,
                           cripto=cripto,
                           nome_usuario=nome_usuario,
                           data_hora=agora)

@app.route('/faq')
def faq():
    faq_perguntas = [
        {
            "pergunta": "O que é esta aplicação?",
            "resposta": "Esta aplicação permite que você invista em criptomoedas, acompanhe seus investimentos e visualize o histórico de preços das moedas."
        },
        {
            "pergunta": "Como funciona o investimento em criptomoedas?",
            "resposta": "Você pode comprar uma determinada quantidade de criptomoeda pelo preço atual e acompanhar o desempenho ao longo do tempo pelo histórico e ganhos."
        },
        {
            "pergunta": "As minhas informações estão seguras?",
            "resposta": "Sim, seus dados são armazenados localmente com segurança e usamos criptografia para proteger suas senhas."
        },
        {
            "pergunta": "O que são criptomoedas?",
            "resposta": "Criptomoedas são moedas digitais que utilizam tecnologia blockchain para garantir segurança e descentralização."
        },
        {
            "pergunta": "Posso perder dinheiro investindo em criptomoedas?",
            "resposta": "Sim, o mercado de criptomoedas é volátil e envolve riscos. Recomendamos investir com cautela e sempre estudar antes de aplicar seu dinheiro."
        },
        {
            "pergunta": "Como posso acompanhar meus investimentos?",
            "resposta": "Na dashboard, você pode ver seus investimentos atuais, o preço das criptomoedas e um gráfico com o histórico de preços."
        },
    ]
    return render_template('faq.html', faq_perguntas=faq_perguntas)


if __name__ == '__main__':
    app.run(debug=True)
