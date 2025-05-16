
from flask import Flask, render_template, request, redirect, session, url_for
from database import init_db, cadastrar_usuario, verificar_usuario, salvar_investimento, listar_investimentos
from crypto_api import get_crypto_price, get_price_history, converter_crypto
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave_secreta"

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
        if verificar_usuario(email, senha):
            session['usuario'] = email
            return redirect('/dashboard')
        else:
            return render_template('login.html', erro='Usuário ou senha inválidos')
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        if cadastrar_usuario(email, senha):
            return redirect('/login')
        else:
            return render_template('cadastro.html', erro='Usuário já existe')
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect('/login')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'usuario' not in session:
        return redirect('/login')

    preco = None
    historico = []
    resultado_conversao = None
    ganhos = []
    cripto = 'bitcoin'

    if request.method == 'POST':
        if 'investir' in request.form:
            cripto = request.form['cripto']
            valor = float(request.form['valor'])
            preco = get_crypto_price(cripto)
            if preco:
                salvar_investimento(session['usuario'], cripto, valor, preco)
        elif 'converter' in request.form:
            de = request.form['de']
            para = request.form['para']
            resultado_conversao = converter_crypto(de, para)
        elif 'buscar' in request.form:
            cripto = request.form['cripto']

    investimentos = listar_investimentos(session['usuario'])
    preco_atual = get_crypto_price(cripto)
    historico = get_price_history(cripto)

    for inv in investimentos:
        atual = get_crypto_price(inv['cripto'])
        if atual:
            ganho = round(atual - inv['preco'], 2)
            ganhos.append({'cripto': inv['cripto'], 'ganho': ganho})

    return render_template('dashboard.html', investimentos=investimentos, preco=preco_atual,
                           historico=historico, resultado=resultado_conversao, ganhos=ganhos, cripto=cripto)

if __name__ == '__main__':
    app.run(debug=True)
