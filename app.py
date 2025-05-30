from flask import Flask, flash, render_template, request, redirect, session, url_for, get_flashed_messages
from datetime import datetime, timedelta, date
import requests
import os

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
    converter_crypto,
    obter_historico_coingecko
)

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

app.jinja_env.cache = {} # Desabilita o cache Jinja, útil para desenvolvimento


@app.template_filter('format_number')
def format_number_filter(value, max_decimals=6):
    if value is None:
        return ""
    try:
        num = float(value)
        formatted = f"{num:.{max_decimals}f}"
        # Remove zeros à direita e o ponto decimal se não houver parte fracionária
        return formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted
    except (ValueError, TypeError):
        return str(value) # Retorna o valor original se não puder converter para float

@app.template_filter('format_brl')
def format_brl_filter(value):
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return "0.00" # Retorna padrão se não puder converter


print(f"DEBUG: Diretório de trabalho atual: {os.getcwd()}")
print(f"DEBUG: Caminho esperado do banco de dados: {os.path.join(os.getcwd(), 'usuarios.db')}")

init_db()

cache_data = {}
CACHE_DURATION_SECONDS = 1800

def get_cached_data(key, fetch_function, *args, **kwargs):
    if key in cache_data and datetime.now() < cache_data[key]['expiry']:
        print(f"DEBUG: Dados do cache para a chave '{key}' usados.")
        return cache_data[key]['data']
    try:
        print(f"DEBUG: Buscando novos dados para a chave '{key}'...")
        data = fetch_function(*args, **kwargs)
        if data is not None:
            cache_data[key] = {
                'data': data,
                'expiry': datetime.now() + timedelta(seconds=CACHE_DURATION_SECONDS)
            }
            print(f"DEBUG: Dados para a chave '{key}' armazenados em cache.")
        return data
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            flash("Opa! Estamos recebendo muitas requisições para os dados de criptomoedas no momento. Por favor, espere alguns minutos e tente novamente.", "error")
        else:
            flash(f"Ocorreu um erro ao buscar dados de API: {e.response.status_code} - {e.response.reason}", "error")
        print(f"[Erro] Falha na obtenção de dados via API: {e.response.status_code} {e.response.reason} para url: {e.request.url}")
        return None
    except requests.exceptions.RequestException as e:
        flash("Problema de conexão com a API de criptomoedas. Verifique sua internet ou tente novamente mais tarde.", "error")
        print(f"[Erro] Erro de conexão com API: {e}")
        return None
    except Exception as e:
        flash(f"Ocorreu um erro inesperado ao buscar dados: {str(e)}", "error")
        print(f"[Erro] Erro inesperado na função de cache: {e}")
        return None

def get_all_crypto_prices_cached(criptos_ids_list, vs_currency='brl'):
    prices = {}
    for crypto_id in criptos_ids_list:
        cache_key = f'price_{crypto_id}_{vs_currency}'
        price = get_cached_data(cache_key, get_crypto_price, crypto_id, vs_currency)
        prices[crypto_id] = price if price is not None else 0.0
    return prices

def format_date_from_db(date_value):
    if date_value is None: return "Data não fornecida"
    if isinstance(date_value, (datetime, date)): return date_value # Já é um objeto datetime/date
    if isinstance(date_value, str):
        possible_formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y']
        for fmt in possible_formats:
            try:
                # Se o formato incluir tempo, retorna datetime, senão date
                return datetime.strptime(date_value, fmt) if 'H' in fmt.upper() else datetime.strptime(date_value, fmt).date()
            except ValueError: continue
        print(f"ATENÇÃO: Formato de data de banco de dados não reconhecido: '{date_value}'")
        return "Formato de data inválido"
    print(f"ATENÇÃO: Tipo de dado de data inesperado do banco de dados: {type(date_value)} - {date_value}")
    return "Tipo de data inesperado"

@app.route('/')
def home():
    return redirect('/dashboard') if 'usuario' in session else redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario' in session: return redirect('/dashboard')
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        print(f"DEBUG: Tentativa de login para o email: {email}")
        usuario_db = verificar_usuario(email, senha)
        if usuario_db:
            session['usuario'] = {'email': usuario_db[0], 'nome': usuario_db[1]} # Assumindo que verificar_usuario retorna (email, nome)
            flash('Login realizado com sucesso!', 'success')
            print(f"DEBUG: Login bem-sucedido para {email}. Redirecionando para dashboard.")
            return redirect('/dashboard')
        else:
            flash('Usuário ou senha inválidos.', 'error')
            print(f"DEBUG: Login falhou para {email}.")
            return render_template('login.html', email_prefilled=email)
    return render_template('login.html', email_prefilled='')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if 'usuario' in session: return redirect('/dashboard')
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        print(f"DEBUG: Tentativa de cadastro para o email: {email}")
        if not nome or not email or not senha or not confirmar_senha: flash('Por favor, preencha todos os campos.', 'error')
        elif senha != confirmar_senha: flash('As senhas não coincidem.', 'error')
        elif len(senha) < 6: flash('A senha deve ter no mínimo 6 caracteres.', 'error')
        else:
            sucesso = cadastrar_usuario(nome, email, senha)
            if sucesso:
                flash('Cadastro realizado com sucesso. Faça login.', 'success')
                print(f"DEBUG: Usuário {email} cadastrado com sucesso. Redirecionando para login.")
                return redirect('/login')
            else: # Assumindo que cadastrar_usuario retorna False se email já existe ou outro erro de DB
                flash('Este e-mail já está cadastrado ou ocorreu um erro no cadastro.', 'error')
                print(f"DEBUG: Falha no cadastro: e-mail {email} já existe ou erro no DB.")
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Você saiu da sua conta.', 'info')
    print("DEBUG: Usuário deslogado.")
    return redirect('/login')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'usuario' not in session:
        flash('Por favor, faça login para acessar o dashboard.', 'info')
        print("DEBUG: Usuário não logado, redirecionando para login.")
        return redirect('/login')

    usuario_session = session.get('usuario')
    if not isinstance(usuario_session, dict) or 'email' not in usuario_session:
        session.pop('usuario', None)
        flash('Sessão inválida ou expirada. Faça login novamente.', 'error')
        print("DEBUG: Sessão inválida ou expirada, redirecionando para login.")
        return redirect('/login')

    email = usuario_session.get('email', '')
    nome_usuario = usuario_session.get('nome', '')
    print(f"DEBUG: Acessando dashboard para o usuário: {email}")

    cripto_selecionada = request.args.get('cripto', 'bitcoin')
    periodo_selecionado = request.args.get('periodo', '30')
    
    resultado_conversao = None
    # Para repopular o formulário do conversor
    converter_form_data = {
        'valor_conversor': request.form.get('valor_conversor', ''), # Inicializa com valor do post se houver
        'de': request.form.get('de', ''),
        'para': request.form.get('para', '')
    }

    if request.method == 'POST':
        print(f"DEBUG: Requisição POST recebida. Form data: {request.form}")

        if 'buscar' in request.form:
            cripto_selecionada = request.form.get('cripto', 'bitcoin')
            periodo_selecionado = request.form.get('periodo', '30')
            print(f"DEBUG: Busca de gráfico para {cripto_selecionada} ({periodo_selecionado} dias).")
            return redirect(url_for('dashboard', _anchor='grafico', cripto=cripto_selecionada, periodo=periodo_selecionado))

        elif 'investir' in request.form:
            cripto_invest = request.form.get('cripto', '')
            valor_str = request.form.get('valor', '')
            print(f"DEBUG: Tentativa de investimento: cripto={cripto_invest}, valor_str={valor_str}")

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
            print(f"DEBUG: Saldo BRL atual para investimento: {saldo_brl_atual:.2f}")

            if saldo_brl_atual < valor:
                flash(f"Saldo BRL insuficiente (R$ {saldo_brl_atual:.2f}) para investir R$ {valor:.2f}.", "error")
                return redirect(url_for('dashboard', _anchor='investir'))

            preco_atual_invest = get_cached_data(
                f'price_{cripto_invest}_brl',
                get_crypto_price,
                cripto_invest, 'brl'
            )
            print(f"DEBUG: Preço atual de {cripto_invest}: {preco_atual_invest}")

            if preco_atual_invest is None or preco_atual_invest == 0:
                flash(f"Não foi possível obter a cotação atual de {cripto_invest.title()}. Tente novamente mais tarde.", "error")
                return redirect(url_for('dashboard', _anchor='investir'))
            
            quantidade_adquirida = valor / preco_atual_invest
            print(f"DEBUG: Atualizando saldo BRL (-{valor:.2f}) e {cripto_invest} (+{quantidade_adquirida:.6f}) para {email}.")
            atualizar_saldo(email, 'BRL', -valor)
            atualizar_saldo(email, cripto_invest, quantidade_adquirida)

            print(f"DEBUG: Registrando transações para investimento de {valor:.2f} BRL em {cripto_invest}.")
            registrar_transacao(email, 'investimento_compra', 'BRL', valor)
            registrar_transacao(email, 'compra_cripto', cripto_invest, quantidade_adquirida)

            print(f"DEBUG: Salvando investimento: {cripto_invest}, {valor:.2f} BRL, preço {preco_atual_invest:.2f}.")
            salvar_investimento(email, cripto_invest, valor, preco_atual_invest)
            flash(f"Investimento de R$ {valor:.2f} em {cripto_invest.title()} realizado. Você adquiriu {app.jinja_env.filters['format_number'](quantidade_adquirida)} unidades.", "success")
            return redirect(url_for('dashboard', _anchor='investir'))

        elif 'converter' in request.form:
            from_moeda = request.form.get('de', '').lower().strip()
            to_moeda = request.form.get('para', '').lower().strip()
            valor_conversor_str = request.form.get('valor_conversor', '')

            # Atualiza os valores do formulário para repopulação em caso de erro ou para exibição
            converter_form_data['de'] = from_moeda
            converter_form_data['para'] = to_moeda
            converter_form_data['valor_conversor'] = valor_conversor_str
            
            print(f"DEBUG: Tentativa de conversão: {valor_conversor_str} de {from_moeda} para {to_moeda}.")

            if not valor_conversor_str or not from_moeda or not to_moeda:
                flash('Por favor, preencha todos os campos do conversor.', 'error')
                # Não redireciona, para manter os dados do formulário e exibir o erro na mesma página
            else:
                try:
                    valor_conversor_num = float(valor_conversor_str) # Renomeado para evitar conflito com var externa
                    if valor_conversor_num <= 0:
                        flash('O valor para conversão deve ser positivo.', 'error')
                    else:
                        rate = get_cached_data(
                            f'conversion_rate_{from_moeda}_to_{to_moeda}',
                            converter_crypto,
                            from_moeda,
                            to_moeda
                        )
                        print(f"DEBUG: Taxa de conversão de {from_moeda} para {to_moeda}: {rate}")

                        if rate is not None and rate > 0:
                            converted_amount = valor_conversor_num * rate
                            
                            val_orig_formatted = app.jinja_env.filters['format_number'](valor_conversor_num)
                            if to_moeda.upper() == 'BRL':
                                converted_amt_formatted = app.jinja_env.filters['format_brl'](converted_amount)
                                resultado_conversao = f"{val_orig_formatted} {from_moeda.upper()} = R$ {converted_amt_formatted}"
                            else:
                                converted_amt_formatted = app.jinja_env.filters['format_number'](converted_amount)
                                resultado_conversao = f"{val_orig_formatted} {from_moeda.upper()} = {converted_amt_formatted} {to_moeda.upper()}"
                            
                            flash(f"Conversão: {resultado_conversao}", "success")
                        else:
                            resultado_conversao = None # Garante que não haja resultado antigo
                            # Se get_cached_data/converter_crypto não flashou erro específico da API, flash um genérico
                            # Verifica se já existe uma mensagem de erro para não duplicar
                            has_error_flash = any(m[1] == 'error' for m in get_flashed_messages(with_categories=True, category_filter=['error']))
                            if not has_error_flash:
                                flash(f'Não foi possível obter a taxa de conversão de {from_moeda.upper()} para {to_moeda.upper()}. Verifique as moedas ou tente mais tarde.', 'error')
                except ValueError:
                    flash('Valor inválido para conversão. Por favor, insira um número.', 'error')
            # A renderização ocorrerá no final da função dashboard, passando resultado_conversao e converter_form_data

        elif 'operacao' in request.form:
            try:
                valor_operacao_str = request.form.get('valor', '')
                moeda_operacao = request.form.get('moeda', 'BRL').upper()
                tipo_operacao = request.form.get('operacao', '')
                print(f"DEBUG: Tentativa de operação: tipo={tipo_operacao}, moeda={moeda_operacao}, valor_str={valor_operacao_str}")

                if not valor_operacao_str:
                    flash("Por favor, insira um valor para a operação.", "error")
                    return redirect(url_for('dashboard', _anchor='carteira'))
                
                valor_operacao = float(valor_operacao_str)
                if valor_operacao <= 0:
                    flash("O valor da operação deve ser positivo.", "error")
                    return redirect(url_for('dashboard', _anchor='carteira'))

                if tipo_operacao == 'deposito':
                    print(f"DEBUG: Realizando depósito de {valor_operacao:.2f} {moeda_operacao} para {email}.")
                    atualizar_saldo(email, moeda_operacao, valor_operacao)
                    registrar_transacao(email, 'deposito', moeda_operacao, valor_operacao)
                    flash(f"Depósito de R$ {app.jinja_env.filters['format_brl'](valor_operacao) if moeda_operacao == 'BRL' else app.jinja_env.filters['format_number'](valor_operacao) + ' ' + moeda_operacao} realizado com sucesso!", "success")
                elif tipo_operacao == 'saque':
                    saldo_atual_moeda = get_saldo(email, moeda_operacao)
                    if saldo_atual_moeda is None: saldo_atual_moeda = 0.0
                    print(f"DEBUG: Saldo atual de {moeda_operacao} para saque: {saldo_atual_moeda:.2f}.")
                    
                    if saldo_atual_moeda >= valor_operacao:
                        print(f"DEBUG: Realizando saque de {valor_operacao:.2f} {moeda_operacao} para {email}.")
                        atualizar_saldo(email, moeda_operacao, -valor_operacao)
                        registrar_transacao(email, 'saque', moeda_operacao, valor_operacao)
                        flash(f"Saque de R$ {app.jinja_env.filters['format_brl'](valor_operacao) if moeda_operacao == 'BRL' else app.jinja_env.filters['format_number'](valor_operacao) + ' ' + moeda_operacao} realizado com sucesso!", "success")
                    else:
                        format_func = app.jinja_env.filters['format_brl'] if moeda_operacao == 'BRL' else app.jinja_env.filters['format_number']
                        flash(f"Saldo {moeda_operacao} insuficiente ({format_func(saldo_atual_moeda)}) para realizar o saque de {format_func(valor_operacao)}.", "error")
                else:
                    flash("Tipo de operação inválido.", "error")
            except ValueError:
                flash("Valor inválido para operação. Insira um número.", "error")
            except Exception as e:
                flash(f"Erro na operação: {str(e)}", "error")
                print(f"ERRO CRÍTICO na operação da carteira: {e}")
            return redirect(url_for('dashboard', _anchor='carteira'))

    # Lógica GET e dados para o template (comum a GET e POST que não redirecionou)
    saldo_brl_display = get_saldo(email, 'BRL')
    if saldo_brl_display is None: saldo_brl_display = 0.0
    print(f"DEBUG: Saldo BRL para exibição: {saldo_brl_display:.2f}")

    criptos_para_cotacao = ['bitcoin', 'ethereum', 'litecoin', 'dogecoin', 'cardano'] # Adicione outras conforme necessário
    precos_atuais_cached = get_all_crypto_prices_cached(criptos_para_cotacao, 'brl')
    print(f"DEBUG: Preços atuais cacheados: {precos_atuais_cached}")

    precos_para_template = precos_atuais_cached.copy()
    precos_para_template['BRL'] = 1.0 # Para consistência no conversor e exibição

    investimentos_raw = listar_investimentos(email) or []
    investimentos = []
    for inv_dict_raw in investimentos_raw:
        inv_copy = inv_dict_raw.copy()
        inv_copy['data'] = format_date_from_db(inv_copy.get('data'))
        investimentos.append(inv_copy)
    print(f"DEBUG: Investimentos carregados: {investimentos}")

    ganhos = []
    for inv_dict_item in investimentos:
        cripto_nome = inv_dict_item.get('cripto')
        valor_investido_original = inv_dict_item.get('valor', 0.0)
        preco_compra_original = inv_dict_item.get('preco', 0.0)
        
        if cripto_nome and cripto_nome.lower() in precos_atuais_cached and \
           precos_atuais_cached[cripto_nome.lower()] is not None and preco_compra_original > 0:
            preco_atual_da_cripto = precos_atuais_cached[cripto_nome.lower()]
            quantidade_adquirida = valor_investido_original / preco_compra_original
            ganho_calculado = (preco_atual_da_cripto - preco_compra_original) * quantidade_adquirida
            ganhos.append({'cripto': cripto_nome.title(), 'ganho': ganho_calculado})
        else:
            ganhos.append({'cripto': cripto_nome.title() if cripto_nome else "Desconhecido", 'ganho': 0.0, 'status': 'Preço indisponível ou compra inválida'})
    print(f"DEBUG: Ganhos calculados: {ganhos}")

    saldo_total_simulado = saldo_brl_display
    carteira_completa_para_calculo = get_carteira_completa(email) or {}
    print(f"DEBUG: Carteira completa para cálculo do saldo total: {carteira_completa_para_calculo}")
    for moeda_id, quantidade in carteira_completa_para_calculo.items():
        if moeda_id.upper() == 'BRL': continue
        
        crypto_id_lower = moeda_id.lower()
        preco_atual_cripto = precos_atuais_cached.get(crypto_id_lower)
        if preco_atual_cripto is not None:
            saldo_total_simulado += quantidade * preco_atual_cripto
        else:
            print(f"AVISO: Preço atual de {moeda_id} indisponível para cálculo do saldo total simulado.")
    print(f"DEBUG: Saldo total simulado final: {saldo_total_simulado:.2f}")

    labels_grafico, dados_grafico = [], []
    try:
        cached_history = get_cached_data(
            f'history_{cripto_selecionada}_{periodo_selecionado}_brl',
            obter_historico_coingecko,
            cripto_id=cripto_selecionada,
            days=int(periodo_selecionado),
            vs_currency='brl' # Adicionado explicitamente
        )
        if cached_history:
            labels_grafico, dados_grafico = cached_history
        else:
            print("DEBUG: Não foi possível obter dados para o gráfico. Verifique as flash messages.")
            # A função get_cached_data já pode ter emitido um flash. Adicionar um se não houver.
            if not any(m[1] == 'error' or m[1] == 'warning' for m in get_flashed_messages(with_categories=True)):
                 flash("Não foi possível carregar os dados do gráfico para a criptomoeda selecionada. Isso pode ocorrer devido a um erro de API ou limite de requisições.", "warning")
    except Exception as e:
        flash(f"Ocorreu um erro ao carregar o histórico do gráfico: {str(e)}", "error")
        print(f"[Erro] Erro ao carregar histórico do gráfico: {e}")

    historico_transacoes_raw = get_historico_transacoes(email) or []
    historico_transacoes_processado = []
    for trans in historico_transacoes_raw:
        trans_copy = trans.copy()
        trans_copy['data'] = format_date_from_db(trans_copy.get('data'))
        historico_transacoes_processado.append(trans_copy)
    print(f"DEBUG: Histórico de transações processado para exibição: {historico_transacoes_processado}")

    carteira_completa_display = get_carteira_completa(email) or {}
    print(f"DEBUG: Carteira completa para exibição: {carteira_completa_display}")

    agora = datetime.now()

    return render_template('dashboard.html',
                            precos=precos_para_template,
                            cripto=cripto_selecionada,
                            saldo_brl=saldo_brl_display,
                            saldo_total_simulado=saldo_total_simulado,
                            nome_usuario=nome_usuario,
                            investimentos=investimentos,
                            resultado=resultado_conversao,
                            ganhos=ganhos,
                            labels=labels_grafico,
                            dados=dados_grafico,
                            periodo=periodo_selecionado,
                            data_atual=agora.strftime('%d/%m/%Y'),
                            hora_atual=agora.strftime('%H:%M:%S'),
                            carteira=carteira_completa_display,
                            isinstance=isinstance, 
                            datetime=datetime,   
                            date=date,          
                            historico_transacoes_app=historico_transacoes_processado,
                            converter_form_data=converter_form_data
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

@app.route('/projeto')
def projeto():
    return render_template('projeto.html')

if __name__ == "__main__":
    app.run(debug=True)