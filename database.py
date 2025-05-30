import sqlite3
from datetime import datetime

DATABASE_NAME = 'usuarios.db' # Mantendo o nome do seu arquivo de banco de dados

# Inicializa o banco de dados e cria as tabelas se elas não existirem
def init_db():
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()

            # Tabela de usuários: Armazena informações de login e saldo BRL
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    email TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    senha TEXT NOT NULL,
                    saldo_brl REAL DEFAULT 0.0
                )
            ''')

            # Tabela de carteira: Armazena as quantidades de criptomoedas de cada usuário
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS carteira (
                    email TEXT NOT NULL,
                    cripto_id TEXT NOT NULL, -- Ex: 'bitcoin', 'ethereum' (IDs CoinGecko em minúsculas)
                    quantidade REAL NOT NULL DEFAULT 0.0,
                    PRIMARY KEY (email, cripto_id),
                    FOREIGN KEY (email) REFERENCES usuarios(email)
                )
            ''')

            # Tabela de investimentos: Registra cada investimento feito
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS investimentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    cripto TEXT NOT NULL, -- ID da cripto investida (e.g., 'bitcoin')
                    valor REAL NOT NULL, -- Valor em BRL investido na compra
                    preco REAL NOT NULL, -- Preço da cripto no momento da compra (em BRL)
                    data TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')), -- Data/hora do investimento
                    FOREIGN KEY (email) REFERENCES usuarios(email)
                )
            ''')

            # Tabela de transações: Histórico de todas as operações (depósitos, saques, compras de cripto)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    tipo TEXT NOT NULL,   -- Ex: 'deposito', 'saque', 'investimento_compra', 'compra_cripto'
                    moeda TEXT NOT NULL,  -- 'BRL' ou ID da cripto (e.g., 'bitcoin')
                    valor REAL NOT NULL,
                    data TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')), -- Data/hora da transação
                    FOREIGN KEY (email) REFERENCES usuarios(email)
                )
            ''')

            # NOVA TABELA: historico_conversoes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historico_conversoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    moeda_origem TEXT NOT NULL,    -- Ex: 'BTC', 'USD'
                    valor_origem REAL NOT NULL,
                    moeda_destino TEXT NOT NULL,   -- Ex: 'BRL', 'ETH'
                    valor_destino REAL NOT NULL,
                    taxa_conversao REAL,           -- Taxa usada: 1 moeda_origem = X moeda_destino
                    data_conversao TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')), -- Data/hora da conversão
                    FOREIGN KEY (email) REFERENCES usuarios(email)
                )
            ''')

            conn.commit() # Salva as mudanças
            print("DEBUG: Banco de dados inicializado/verificado com sucesso.")
    except Exception as e:
        print(f"[Erro DB] Falha ao inicializar o banco de dados: {e}")

# Atualiza o saldo de uma moeda (BRL ou cripto) na carteira do usuário
def atualizar_saldo(email, moeda_ou_cripto_id, valor_delta):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            if moeda_ou_cripto_id.upper() == 'BRL':
                cursor.execute('UPDATE usuarios SET saldo_brl = saldo_brl + ? WHERE email = ?', (valor_delta, email))
            else:
                cripto_id_lower = moeda_ou_cripto_id.lower()
                cursor.execute(
                    'INSERT INTO carteira (email, cripto_id, quantidade) VALUES (?, ?, ?) '
                    'ON CONFLICT(email, cripto_id) DO UPDATE SET quantidade = quantidade + ?',
                    (email, cripto_id_lower, valor_delta, valor_delta)
                )
            conn.commit()
            return True
    except Exception as e:
        print(f"[Erro DB] Falha ao atualizar saldo para {moeda_ou_cripto_id}: {e}")
        return False

# Registra uma transação no histórico geral de transações
def registrar_transacao(email, tipo, moeda, valor):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transacoes (email, tipo, moeda, valor)
                VALUES (?, ?, ?, ?)
            ''', (email, tipo, moeda, valor))
            conn.commit()
            return True
    except Exception as e:
        print(f"[Erro DB] Falha ao registrar transação: {e}")
        return False

# Retorna o saldo atual de uma moeda (BRL ou cripto) específica para um usuário
def get_saldo(email, moeda_ou_cripto_id="BRL"):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            if moeda_ou_cripto_id.upper() == 'BRL':
                cursor.execute('SELECT saldo_brl FROM usuarios WHERE email = ?', (email,))
                resultado = cursor.fetchone()
                return resultado[0] if resultado else 0.0
            else:
                cursor.execute('SELECT quantidade FROM carteira WHERE email = ? AND cripto_id = ?', (email, moeda_ou_cripto_id.lower()))
                resultado = cursor.fetchone()
                return resultado[0] if resultado else 0.0
    except Exception as e:
        print(f"[Erro DB] Falha ao obter saldo para {moeda_ou_cripto_id}: {e}")
        return 0.0

# Retorna os últimos registros de transações para um usuário
def get_historico_transacoes(email, limite=10):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.row_factory = sqlite3.Row # Para retornar dicionários
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, tipo, moeda, valor, data
                FROM transacoes
                WHERE email = ?
                ORDER BY data DESC
                LIMIT ?
            ''', (email, limite))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[Erro DB] Falha ao obter histórico de transações: {e}")
        return []

# Retorna todas as moedas e saldos (BRL e criptos) de um usuário
def get_carteira_completa(email):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            carteira = {}
            saldo_brl = get_saldo(email, 'BRL') # Reutiliza a função get_saldo
            carteira['BRL'] = saldo_brl
            cursor.execute('SELECT cripto_id, quantidade FROM carteira WHERE email = ?', (email,))
            for row in cursor.fetchall():
                carteira[row[0].upper()] = row[1]
            return carteira
    except Exception as e:
        print(f"[Erro DB] Falha ao obter carteira completa: {e}")
        return {}

# Cadastra um novo usuário no sistema
def cadastrar_usuario(nome, email, senha):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT email FROM usuarios WHERE email = ?', (email,))
            if cursor.fetchone():
                return False # E-mail já cadastrado
            cursor.execute('INSERT INTO usuarios (email, nome, senha, saldo_brl) VALUES (?, ?, ?, ?)',
                           (email, nome, senha, 1000.00)) # Exemplo: 1000 BRL de saldo inicial
            conn.commit()
            return True
    except Exception as e:
        print(f"[Erro DB] Falha ao cadastrar usuário: {e}")
        return False

# Verifica as credenciais do usuário para login
def verificar_usuario(email, senha):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            # Idealmente, a senha seria hashed e verificada com hash, não em texto plano
            cursor.execute('SELECT email, nome FROM usuarios WHERE email = ? AND senha = ?', (email, senha))
            return cursor.fetchone()
    except Exception as e:
        print(f"[Erro DB] Falha ao verificar usuário: {e}")
        return None

# Salva um registro de investimento realizado pelo usuário
def salvar_investimento(email, cripto_id, valor_investido_brl, preco_compra_brl):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO investimentos (email, cripto, valor, preco)
                VALUES (?, ?, ?, ?)
            ''', (email, cripto_id.lower(), valor_investido_brl, preco_compra_brl)) # Salva cripto_id em minúsculas
            conn.commit()
            return True
    except Exception as e:
        print(f"[Erro DB] Falha ao salvar investimento: {e}")
        return False

# Lista todos os investimentos feitos por um usuário
def listar_investimentos(email):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.row_factory = sqlite3.Row # Para retornar dicionários
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, cripto, valor, preco, data FROM investimentos WHERE email = ?
                ORDER BY data DESC
            ''', (email,))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[Erro DB] Falha ao listar investimentos: {e}")
        return []

# --- NOVAS FUNÇÕES PARA HISTÓRICO DE CONVERSÕES ---

def registrar_historico_conversao(email, moeda_origem, valor_origem, moeda_destino, valor_destino, taxa_conversao):
    """
    Registra uma conversão realizada no histórico do usuário.
    """
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            # A coluna 'data_conversao' usa um valor padrão na definição da tabela
            cursor.execute('''
                INSERT INTO historico_conversoes (email, moeda_origem, valor_origem, moeda_destino, valor_destino, taxa_conversao)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (email, moeda_origem.upper(), valor_origem, moeda_destino.upper(), valor_destino, taxa_conversao))
            conn.commit()
            print(f"DEBUG: Conversão de {valor_origem} {moeda_origem} para {valor_destino} {moeda_destino} registrada para {email}.")
            return True
    except Exception as e:
        print(f"[Erro DB] Falha ao registrar histórico de conversão: {e}")
        return False

def get_historico_conversoes(email, limite=10):
    """
    Retorna os últimos registros de conversões para um usuário.
    """
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.row_factory = sqlite3.Row # Para retornar dicionários
            cursor = conn.cursor()
            # Ordena por data decrescente para mostrar as mais recentes primeiro
            cursor.execute('''
                SELECT id, moeda_origem, valor_origem, moeda_destino, valor_destino, taxa_conversao, data_conversao
                FROM historico_conversoes
                WHERE email = ?
                ORDER BY data_conversao DESC
                LIMIT ?
            ''', (email, limite))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[Erro DB] Falha ao obter histórico de conversões: {e}")
        return []

# Função auxiliar para obter dados do usuário pelo email (útil para depuração ou outras operações)
def get_user_by_email(email):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.row_factory = sqlite3.Row # Para retornar dicionários
            cursor = conn.cursor()
            cursor.execute("SELECT email, nome, saldo_brl FROM usuarios WHERE email = ?", (email,))
            user_data = cursor.fetchone()
            return dict(user_data) if user_data else None
    except Exception as e:
        print(f"[Erro DB] Falha ao obter usuário por email: {e}")
        return None

# Certifique-se de chamar init_db() uma vez ao iniciar a aplicação,
# por exemplo, no seu app.py antes de iniciar o servidor Flask.
# init_db() # Removido daqui para evitar chamadas múltiplas se este arquivo for importado várias vezes.
            # Chame em app.py
