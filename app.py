from flask import Flask, flash, render_template, request, redirect, session, get_flashed_messages
from datetime import datetime

from database import (
    atualizar_saldo,
    get_carteira_completa,
    get_historico_transacoes,
    get_saldo,
    init_db,
    cadastrar_usuario,
    registrar_transacao,
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
init_db()

# ROTA PRINCIPAL
@app.route('/')
def home():
    return redirect('/dashboard') if 'usuario' in session else redirect('/login')


# LOGIN
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
            flash('Usuário ou senha inválidos.', 'error')
            return redirect('/login')

    return render_template('login.html')


# CADASTRO
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        if not nome or not email or not senha or not confirmar_senha:
            flash('Por favor, preencha todos os campos.', 'error')
        elif senha != confirmar_senha:
            flash('As senhas não coincidem.', 'error')
        else:
            sucesso = cadastrar_usuario(nome, email, senha)
            if sucesso:
                flash('Cadastro realizado com sucesso. Faça login.', 'success')
                return redirect('/login')
            else:
                flash('Usuário já existe.', 'error')

    return render_template('cadastro.html')


@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Você saiu da sua conta.', 'info')
    return redirect('/login')


# FUNÇÃO AUXILIAR
def calcular_saldo_brl(email):
    investimentos = listar_investimentos(email) or []
    saldo_total = 0.0

    for inv in investimentos:
        cripto = inv.get('cripto')
        valor_investido = inv.get('valor', 0.0)
        preco_compra = inv.get('preco', 1.0)
        quantidade = valor_investido / preco_compra if preco_compra > 0 else 0.0
        preco_atual = get_crypto_price(cripto) or 0.0
        saldo_total += quantidade * preco_atual

    return round(saldo_total, 2)


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

    # FORMULÁRIOS
    if request.method == 'POST':
        if 'investir' in request.form:
            cripto = request.form['cripto']
            try:
                valor = float(request.form['valor'])
                if valor <= 0:
                    flash("Valor do investimento deve ser positivo.", "error")
                else:
                    preco_atual = get_crypto_price(cripto)
                    salvar_investimento(email, cripto, valor, preco_atual)
                    flash(f"Investimento de R$ {valor:.2f} em {cripto.title()} realizado.", "success")
            except ValueError:
                flash("Valor inválido para investimento.", "error")

        elif 'converter' in request.form:
            de = request.form['de']
            para = request.form['para']
            resultado_conversao = converter_crypto(de, para)

        elif 'buscar' in request.form:
            cripto = request.form['cripto']

    # DADOS
    investimentos = listar_investimentos(email) or []
    preco_atual = get_crypto_price(cripto) or 0.0
    historico_raw = get_price_history(cripto) or []

    historico = [
        {
            'data': item.get('data').strftime('%d/%m') if isinstance(item.get('data'), datetime) else str(item.get('data')),
            'preco': item.get('preco', 0.0)
        }
        for item in historico_raw
    ]

    for inv in investimentos:
        atual = get_crypto_price(inv.get('cripto', cripto))
        if atual:
            ganho = round(atual - inv.get('preco', 0), 2)
            ganhos.append({'cripto': inv.get('cripto', cripto), 'ganho': ganho})

    carteira = {}
    for inv in investimentos:
        cripto_nome = inv.get('cripto')
        valor = inv.get('valor', 0.0)
        preco = inv.get('preco', 1.0)
        quantidade = valor / preco if preco > 0 else 0.0
        carteira[cripto_nome] = carteira.get(cripto_nome, 0.0) + quantidade

    labels, dados_grafico = obter_historico_coingecko(cripto_id=cripto)
    saldo_brl = calcular_saldo_brl(email)
    agora = datetime.now()

    return render_template('dashboard.html',
        saldo_brl=saldo_brl,
        nome_usuario=nome_usuario,
        preco=preco_atual,
        investimentos=investimentos,
        resultado=resultado_conversao,
        ganhos=ganhos,
        cripto=cripto,
        labels=labels,
        dados=dados_grafico,
        data=agora.strftime('%d/%m/%Y'),
        hora=agora.strftime('%H:%M:%S'),
        carteira=carteira,
        precos={cripto: preco_atual}
    )


# CARTEIRA DIGITAL
@app.route('/carteira', methods=['GET', 'POST'])
def carteira():
    if 'usuario' not in session:
        return redirect('/login')

    email = session['usuario']['email']

    if request.method == 'POST':
        try:
            valor = float(request.form['valor'])
            moeda = request.form.get('moeda', 'BRL')
            tipo_operacao = request.form.get('operacao')

            if tipo_operacao == 'deposito':
                atualizar_saldo(email, moeda, valor)
                registrar_transacao(email, 'deposito', moeda, valor)
                flash(f"Depósito de R$ {valor:.2f} realizado com sucesso!", "success")

            elif tipo_operacao == 'saque':
                saldo_atual = get_saldo(email, moeda)
                if saldo_atual >= valor:
                    atualizar_saldo(email, moeda, -valor)
                    registrar_transacao(email, 'saque', moeda, valor)
                    flash(f"Saque de R$ {valor:.2f} realizado com sucesso!", "success")
                else:
                    flash("Saldo insuficiente para esta operação.", "error")

            else:
                flash("Tipo de operação inválido.", "error")

        except ValueError:
            flash("Valor inválido.", "error")
        except Exception as e:
            flash(f"Erro na operação: {str(e)}", "error")

        return redirect('/carteira')

    saldo_brl = get_saldo(email, 'BRL')
    historico = get_historico_transacoes(email)
    carteira_completa = get_carteira_completa(email)
    precos = {moeda: get_crypto_price(moeda) if moeda != 'BRL' else 1 for moeda in carteira_completa.keys()}

    return render_template('carteira.html',
        saldo_brl=saldo_brl,
        historico=historico,
        carteira=carteira_completa,
        precos=precos
    )


# FAQ
@app.route('/faq')
def faq():
    faq_perguntas = [
        {"pergunta": "O que é esta aplicação?", "resposta": "Permite investir em criptomoedas, acompanhar investimentos e visualizar histórico de preços."},
        {"pergunta": "Como funciona o investimento?", "resposta": "Você compra uma quantidade de criptomoeda e acompanha seu valor ao longo do tempo."},
        {"pergunta": "Minhas informações estão seguras?", "resposta": "Sim. Os dados são armazenados localmente com segurança e as senhas são criptografadas."},
        {"pergunta": "O que são criptomoedas?", "resposta": "São moedas digitais baseadas em blockchain, seguras e descentralizadas."},
        {"pergunta": "Posso perder dinheiro?", "resposta": "Sim. O mercado é volátil. Invista com cautela."},
        {"pergunta": "Como acompanho meus investimentos?", "resposta": "Na dashboard você vê os preços atuais, histórico gráfico e seus ganhos."},
    ]
    return render_template('faq.html', faq_perguntas=faq_perguntas)


# INICIAR SERVIDOR
if __name__ == "__main__":
    app.run(debug=True)
