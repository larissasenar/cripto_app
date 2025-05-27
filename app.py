from flask import Flask, flash, render_template, request, redirect, session, url_for, get_flashed_messages
from datetime import datetime, timedelta, date
import time
import requests

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
app.secret_key = "uma_chave_muito_secreta_e_aleatoria_para_o_flask_session_e_flash"
init_db()

cache_data = {}
CACHE_DURATION_SECONDS = 1800

def get_cached_data(key, fetch_function, *args, **kwargs):
    if key in cache_data and datetime.now() < cache_data[key]['expiry']:
        return cache_data[key]['data']

    data = fetch_function(*args, **kwargs)
    if data is not None:
        cache_data[key] = {
            'data': data,
            'expiry': datetime.now() + timedelta(seconds=CACHE_DURATION_SECONDS)
        }
    return data

def get_all_crypto_prices_cached(criptos_ids_list, vs_currency='brl'):
    prices = {}
    for crypto_id in criptos_ids_list:
        cache_key = f'price_{crypto_id}_{vs_currency}'
        price = get_cached_data(cache_key, get_crypto_price, crypto_id, vs_currency)
        prices[crypto_id] = price if price is not None else 0.0
    return prices

def format_date_from_db(date_value):
    if date_value is None:
        return "Data não fornecida"

    if isinstance(date_value, (datetime, date)):
        return date_value

    if isinstance(date_value, str):
        possible_formats = [
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y'
        ]
        for fmt in possible_formats:
            try:
                if ' ' in fmt:
                    return datetime.strptime(date_value, fmt)
                else:
                    return datetime.strptime(date_value, fmt).date()
            except ValueError:
                continue
        print(f"ATENÇÃO: Formato de data de banco de dados não reconhecido: '{date_value}'")
        return "Formato de data inválido"

    print(f"ATENÇÃO: Tipo de dado de data inesperado do banco de dados: {type(date_value)} - {date_value}")
    return "Tipo de data inesperado"


@app.route('/')
def home():
    return redirect('/dashboard') if 'usuario' in session else redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario' in session:
        return redirect('/dashboard')

    if request.method == 'POST':
        email = request.form['email'].strip()
        senha = request.form['senha']
        usuario = verificar_usuario(email, senha)

        if usuario:
            session['usuario'] = {'email': usuario[0], 'nome': usuario[1]}
            flash('Login realizado com sucesso!', 'success')
            return redirect('/dashboard')
        else:
            flash('Usuário ou senha inválidos.', 'error')
            return render_template('login.html', email_prefilled=email)

    return render_template('login.html', email_prefilled='')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if 'usuario' in session:
        return redirect('/dashboard')

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        if not nome or not email or not senha or not confirmar_senha:
            flash('Por favor, preencha todos os campos.', 'error')
        elif senha != confirmar_senha:
            flash('As senhas não coincidem.', 'error')
        elif len(senha) < 6:
            flash('A senha deve ter no mínimo 6 caracteres.', 'error')
        else:
            sucesso = cadastrar_usuario(nome, email, senha)
            if sucesso:
                flash('Cadastro realizado com sucesso. Faça login.', 'success')
                return redirect('/login')
            else:
                flash('Este e-mail já está cadastrado.', 'error')
    return render_template('cadastro.html')


@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Você saiu da sua conta.', 'info')
    return redirect('/login')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'usuario' not in session:
        flash('Por favor, faça login para acessar o dashboard.', 'info')
        return redirect('/login')

    usuario = session.get('usuario')
    if not isinstance(usuario, dict) or 'email' not in usuario:
        session.pop('usuario', None)
        flash('Sessão inválida ou expirada. Faça login novamente.', 'error')
        return redirect('/login')

    email = usuario.get('email', '')
    nome_usuario = usuario.get('nome', '')

    cripto_selecionada = request.args.get('cripto', 'bitcoin')
    periodo_selecionado = request.args.get('periodo', '30')
    resultado_conversao = None

    if request.method == 'POST':
        if 'buscar' in request.form:
            cripto_selecionada = request.form.get('cripto', 'bitcoin')
            periodo_selecionado = request.form.get('periodo', '30')
            return redirect(url_for('dashboard', _anchor='grafico', cripto=cripto_selecionada, periodo=periodo_selecionado))

        elif 'investir' in request.form:
            cripto_invest = request.form.get('cripto')
            valor_str = request.form.get('valor')

            if not valor_str:
                flash("Por favor, insira um valor para investir.", "error")
                return redirect(url_for('dashboard', _anchor='investir'))
            try:
                valor = float(valor_str)
                if valor <= 0:
                    flash("O valor do investimento deve ser positivo.", "error")
                    return redirect(url_for('dashboard', _anchor='investir'))
            except ValueError:
                flash("Valor inválido para investimento. Use apenas números.", "error")
                return redirect(url_for('dashboard', _anchor='investir'))

            saldo_brl_atual = get_saldo(email, 'BRL')
            if saldo_brl_atual is None: saldo_brl_atual = 0.0

            if saldo_brl_atual < valor:
                flash(f"Saldo BRL insuficiente (R$ {saldo_brl_atual:.2f}) para investir R$ {valor:.2f}.", "error")
                return redirect(url_for('dashboard', _anchor='investir'))

            preco_atual_invest = get_cached_data(
                f'price_{cripto_invest}_brl',
                get_crypto_price,
                cripto_invest, 'brl'
            )

            if preco_atual_invest is None or preco_atual_invest == 0:
                flash(f"Não foi possível obter a cotação atual de {cripto_invest.title()}. Tente novamente mais tarde.", "error")
                return redirect(url_for('dashboard', _anchor='investir'))

            quantidade_adquirida = valor / preco_atual_invest

            atualizar_saldo(email, 'BRL', -valor)
            atualizar_saldo(email, cripto_invest, quantidade_adquirida)
            
            registrar_transacao(email, 'investimento_compra', 'BRL', valor)
            registrar_transacao(email, 'compra_cripto', cripto_invest, quantidade_adquirida)

            salvar_investimento(email, cripto_invest, valor, preco_atual_invest)

            flash(f"Investimento de R$ {valor:.2f} em {cripto_invest.title()} realizado. Você adquiriu {quantidade_adquirida:.6f} unidades.", "success")
            return redirect(url_for('dashboard', _anchor='investir'))

        elif 'converter' in request.form:
            from_moeda = request.form.get('de', '').lower().strip()
            to_moeda = request.form.get('para', '').lower().strip()
            valor_conversor_str = request.form.get('valor_conversor')

            if not valor_conversor_str:
                flash('Por favor, insira um valor para converter.', 'error')
                return redirect(url_for('dashboard', _anchor='conversor'))
            try:
                valor_conversor = float(valor_conversor_str)
                if valor_conversor <= 0:
                    flash('O valor para conversão deve ser positivo.', 'error')
                    return redirect(url_for('dashboard', _anchor='conversor'))
            except ValueError:
                flash('Valor inválido para conversão. Por favor, insira um número.', 'error')
                return redirect(url_for('dashboard', _anchor='conversor'))

            rate = get_cached_data(
                f'conversion_rate_{from_moeda}_to_{to_moeda}',
                converter_crypto,
                from_moeda,
                to_moeda
            )

            if rate is not None and rate > 0:
                converted_amount = valor_conversor * rate
                resultado_conversao = f"{valor_conversor:.6f} {from_moeda.upper()} = {converted_amount:.6f} {to_moeda.upper()}"
                flash(f"Conversão: {resultado_conversao}", "success")
            else:
                flash("Não foi possível realizar a conversão. Verifique as moedas (use siglas como BTC, ETH, BRL, USD) ou tente novamente.", "error")
                resultado_conversao = None
            return redirect(url_for('dashboard', _anchor='conversor'))

        elif 'operacao' in request.form:
            try:
                valor_operacao_str = request.form.get('valor')
                moeda_operacao = request.form.get('moeda', 'BRL').upper()
                tipo_operacao = request.form.get('operacao')

                if not valor_operacao_str:
                    flash("Por favor, insira um valor para a operação.", "error")
                    return redirect(url_for('dashboard', _anchor='carteira'))
                valor_operacao = float(valor_operacao_str)
                if valor_operacao <= 0:
                    flash("O valor da operação deve ser positivo.", "error")
                    return redirect(url_for('dashboard', _anchor='carteira'))

                if tipo_operacao == 'deposito':
                    atualizar_saldo(email, moeda_operacao, valor_operacao)
                    registrar_transacao(email, 'deposito', moeda_operacao, valor_operacao)
                    flash(f"Depósito de R$ {valor_operacao:.2f} realizado com sucesso!", "success")

                elif tipo_operacao == 'saque':
                    saldo_atual_moeda = get_saldo(email, moeda_operacao)
                    if saldo_atual_moeda is None: saldo_atual_moeda = 0.0

                    if saldo_atual_moeda >= valor_operacao:
                        atualizar_saldo(email, moeda_operacao, -valor_operacao)
                        registrar_transacao(email, 'saque', moeda_operacao, valor_operacao)
                        flash(f"Saque de R$ {valor_operacao:.2f} realizado com sucesso!", "success")
                    else:
                        flash(f"Saldo {moeda_operacao} insuficiente (R$ {saldo_atual_moeda:.2f}) para realizar o saque de R$ {valor_operacao:.2f}.", "error")
                else:
                    flash("Tipo de operação inválido.", "error")

            except ValueError:
                flash("Valor inválido para operação. Insira um número.", "error")
            except Exception as e:
                flash(f"Erro na operação: {str(e)}", "error")
            
            return redirect(url_for('dashboard', _anchor='carteira'))


    saldo_brl_display = get_saldo(email, 'BRL')
    if saldo_brl_display is None: saldo_brl_display = 0.0

    criptos_para_cotacao = ['bitcoin', 'ethereum', 'litecoin', 'dogecoin', 'cardano', 'solana']
    precos_atuais_cached = get_all_crypto_prices_cached(criptos_para_cotacao, 'brl')

    precos_para_template = precos_atuais_cached.copy()
    precos_para_template['BRL'] = 1.0

    investimentos_raw = listar_investimentos(email) or []
    investimentos = []
    for inv in investimentos_raw:
        inv_copy = inv.copy()
        inv_copy['data'] = format_date_from_db(inv_copy.get('data'))
        investimentos.append(inv_copy)

    ganhos = []
    for inv in investimentos:
        cripto_nome = inv.get('cripto')
        valor_investido_original = inv.get('valor', 0.0)
        preco_compra_original = inv.get('preco', 0.0)

        if cripto_nome in precos_atuais_cached and precos_atuais_cached[cripto_nome] is not None and preco_compra_original > 0:
            preco_atual_da_cripto = precos_atuais_cached[cripto_nome]
            quantidade_adquirida = valor_investido_original / preco_compra_original
            
            ganho_calculado = (preco_atual_da_cripto - preco_compra_original) * quantidade_adquirida
            ganhos.append({'cripto': cripto_nome.title(), 'ganho': ganho_calculado})
        else:
            ganhos.append({'cripto': cripto_nome.title(), 'ganho': 0.0, 'status': 'Preço indisponível ou compra inválida'})

    saldo_total_simulado = saldo_brl_display
    
    carteira_completa_para_calculo = get_carteira_completa(email)
    for moeda_id, quantidade in carteira_completa_para_calculo.items():
        if moeda_id.upper() == 'BRL':
            continue
        
        crypto_id_lower = moeda_id.lower()
        preco_atual_cripto = precos_atuais_cached.get(crypto_id_lower)
        
        if preco_atual_cripto is not None:
            saldo_total_simulado += quantidade * preco_atual_cripto
        else:
            print(f"AVISO: Preço atual de {moeda_id} indisponível para cálculo do saldo total simulado.")


    labels_grafico, dados_grafico = get_cached_data(
        f'history_{cripto_selecionada}_{periodo_selecionado}_brl',
        obter_historico_coingecko,
        cripto_id=cripto_selecionada,
        days=int(periodo_selecionado)
    ) or ([], [])

    historico_transacoes_raw = get_historico_transacoes(email) or []
    historico_transacoes = []
    for trans in historico_transacoes_raw:
        trans_copy = trans.copy()
        trans_copy['data'] = format_date_from_db(trans_copy.get('data'))
        historico_transacoes.append(trans_copy)

    carteira_completa_display = get_carteira_completa(email)

    agora = datetime.now()

    return render_template('dashboard.html',
        saldo_brl=saldo_brl_display,
        saldo_total_simulado=saldo_total_simulado,
        nome_usuario=nome_usuario,
        precos=precos_para_template,
        investimentos=investimentos,
        resultado=resultado_conversao,
        ganhos=ganhos,
        cripto=cripto_selecionada,
        labels=labels_grafico,
        dados=dados_grafico,
        periodo=periodo_selecionado,
        data=agora.strftime('%d/%m/%Y'),
        hora=agora.strftime('%H:%M:%S'),
        carteira=carteira_completa_display,
        isinstance=isinstance,
        datetime=datetime,
        date=date
    )


@app.route('/faq')
def faq():
    faq_perguntas = [
        {"pergunta": "O que é esta aplicação?", "resposta": "É uma plataforma simulada para gerenciar seus ativos digitais, acompanhar investimentos e visualizar o histórico de preços das criptomoedas."},
        {"pergunta": "Como funciona o investimento?", "resposta": "Você pode usar seu saldo em BRL para 'comprar' criptomoedas simuladas e acompanhar seus ganhos/perdas com base em preços de mercado reais."},
        {"pergunta": "Minhas informações estão seguras?", "resposta": "Sim. Seus dados são armazenados localmente e, em um ambiente de produção real, as senhas seriam criptografadas para máxima segurança."},
        {"pergunta": "O que são criptomoedas?", "resposta": "São moedas digitais e descentralizadas que utilizam criptografia para garantir a segurança das transações e controlar a criação de novas unidades."},
        {"pergunta": "Posso perder dinheiro real?", "resposta": "Não. Este é um ambiente de simulação. Você não está investindo dinheiro real e não pode perder ou ganhar valor monetário de verdade. O objetivo é simular o mercado e aprender."},
        {"pergunta": "Como acompanho meus investimentos?", "resposta": "No painel principal, você pode ver seu saldo total simulado, a cotação atual das criptomoedas, gráficos de preços históricos, seu histórico de investimentos e o cálculo de ganhos/perdas."},
        {"pergunta": "O conversor é em tempo real?", "resposta": "Sim, o conversor utiliza dados de cotação atualizados de uma API externa para fornecer taxas de câmbio próximas do tempo real para as moedas suportadas."},
    ]
    return render_template('faq.html', faq_perguntas=faq_perguntas)


if __name__ == "__main__":
    app.run(debug=True)