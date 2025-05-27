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
            # (não inclui BRL aqui, que fica na tabela usuarios)
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
                    data TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'utc')), -- Data/hora do investimento em UTC
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
                    data TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'utc')), -- Data/hora da transação em UTC
                    FOREIGN KEY (email) REFERENCES usuarios(email)
                )
            ''')

            conn.commit() # Salva as mudanças
    except Exception as e:
        print(f"[Erro] Falha ao inicializar o banco de dados: {e}")

# Atualiza o saldo de uma moeda (BRL ou cripto) na carteira do usuário
def atualizar_saldo(email, moeda_ou_cripto_id, valor_delta):
    """
    Atualiza o saldo de uma moeda/cripto para um usuário.
    valor_delta: O valor a ser adicionado (pode ser positivo ou negativo para subtrair).
    """
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()

            if moeda_ou_cripto_id.upper() == 'BRL':
                # Atualiza o saldo BRL na tabela de usuários
                cursor.execute('UPDATE usuarios SET saldo_brl = saldo_brl + ? WHERE email = ?', (valor_delta, email))
            else:
                # Para criptomoedas, insere ou atualiza a quantidade na tabela 'carteira'
                # O comando ON CONFLICT lida com o caso de a cripto já existir ou ser nova
                cripto_id_lower = moeda_ou_cripto_id.lower() # IDs de cripto devem ser consistentes (minúsculas)
                cursor.execute(
                    'INSERT INTO carteira (email, cripto_id, quantidade) VALUES (?, ?, ?) '
                    'ON CONFLICT(email, cripto_id) DO UPDATE SET quantidade = quantidade + ?',
                    (email, cripto_id_lower, valor_delta, valor_delta)
                )
            conn.commit()
            return True
    except Exception as e:
        print(f"[Erro] Falha ao atualizar saldo para {moeda_ou_cripto_id}: {e}")
        return False

# Registra uma transação no histórico geral de transações
def registrar_transacao(email, tipo, moeda, valor):
    """
    Registra uma transação no histórico do usuário.
    Tipo: 'deposito', 'saque', 'investimento_compra', 'compra_cripto', etc.
    Moeda: 'BRL' ou ID da cripto.
    Valor: O valor da transação.
    """
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            # A coluna 'data' usa um valor padrão na definição da tabela (strftime('%Y-%m-%d %H:%M:%S', 'now', 'utc'))
            # então não precisamos passar a data explicitamente no INSERT
            cursor.execute('''
                INSERT INTO transacoes (email, tipo, moeda, valor)
                VALUES (?, ?, ?, ?)
            ''', (email, tipo, moeda, valor))

            conn.commit()
            return True
    except Exception as e:
        print(f"[Erro] Falha ao registrar transação: {e}")
        return False

# Retorna o saldo atual de uma moeda (BRL ou cripto) específica para um usuário
def get_saldo(email, moeda_ou_cripto_id="BRL"):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()

            if moeda_ou_cripto_id.upper() == 'BRL':
                # Busca saldo BRL na tabela 'usuarios'
                cursor.execute('SELECT saldo_brl FROM usuarios WHERE email = ?', (email,))
                resultado = cursor.fetchone()
                return resultado[0] if resultado else 0.0 # Retorna 0.0 se não encontrar
            else:
                # Busca saldo de cripto na tabela 'carteira'
                cursor.execute('SELECT quantidade FROM carteira WHERE email = ? AND cripto_id = ?', (email, moeda_ou_cripto_id.lower()))
                resultado = cursor.fetchone()
                return resultado[0] if resultado else 0.0 # Retorna 0.0 se não encontrar
    except Exception as e:
        print(f"[Erro] Falha ao obter saldo para {moeda_ou_cripto_id}: {e}")
        return 0.0

# Retorna os últimos registros de transações para um usuário
def get_historico_transacoes(email, limite=10):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            # Ordena por data decrescente para mostrar as mais recentes primeiro
            cursor.execute('''
                SELECT tipo, moeda, valor, data
                FROM transacoes
                WHERE email = ?
                ORDER BY data DESC
                LIMIT ?
            ''', (email, limite))

            # Converte os resultados em uma lista de dicionários
            return [{
                'tipo': t[0],
                'moeda': t[1],
                'valor': t[2],
                'data': t[3]
            } for t in cursor.fetchall()]
    except Exception as e:
        print(f"[Erro] Falha ao obter histórico de transações: {e}")
        return []

# Retorna todas as moedas e saldos (BRL e criptos) de um usuário
def get_carteira_completa(email):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            carteira = {}
            
            # 1. Obter saldo BRL do usuário
            saldo_brl = get_saldo(email, 'BRL')
            carteira['BRL'] = saldo_brl

            # 2. Obter saldos de criptomoedas da tabela 'carteira'
            cursor.execute('''
                SELECT cripto_id, quantidade
                FROM carteira
                WHERE email = ?
            ''', (email,))
            for row in cursor.fetchall():
                carteira[row[0].upper()] = row[1] # Armazena com a sigla em maiúsculas (ex: 'BTC': 0.01)
            
            return carteira
    except Exception as e:
        print(f"[Erro] Falha ao obter carteira completa: {e}")
        return {}

# Cadastra um novo usuário no sistema
def cadastrar_usuario(nome, email, senha):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            # Verifica se o e-mail já existe
            cursor.execute('SELECT email FROM usuarios WHERE email = ?', (email,))
            if cursor.fetchone():
                return False # E-mail já cadastrado

            # Insere o novo usuário com um saldo inicial de BRL
            cursor.execute('INSERT INTO usuarios (email, nome, senha, saldo_brl) VALUES (?, ?, ?, ?)',
                           (email, nome, senha, 1000.00)) # Exemplo: 1000 BRL de saldo inicial
            
            conn.commit()
            return True
    except Exception as e:
        print(f"[Erro] Falha ao cadastrar usuário: {e}")
        return False

# Verifica as credenciais do usuário para login
def verificar_usuario(email, senha):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT email, nome FROM usuarios WHERE email = ? AND senha = ?', (email, senha))
            return cursor.fetchone() # Retorna (email, nome) se encontrar, senão None
    except Exception as e:
        print(f"[Erro] Falha ao verificar usuário: {e}")
        return None

# Salva um registro de investimento realizado pelo usuário
def salvar_investimento(email, cripto_id, valor_investido_brl, preco_compra_brl):
    """
    Salva um registro de investimento (compra) feito pelo usuário.
    cripto_id: ID da cripto (e.g., 'bitcoin').
    valor_investido_brl: Quantidade de BRL usada no investimento.
    preco_compra_brl: Preço da cripto no momento da compra (em BRL).
    """
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            # A coluna 'data' usa um valor padrão na definição da tabela
            cursor.execute('''
                INSERT INTO investimentos (email, cripto, valor, preco)
                VALUES (?, ?, ?, ?)
            ''', (email, cripto_id, valor_investido_brl, preco_compra_brl))
            conn.commit()
            return True
    except Exception as e:
        print(f"[Erro] Falha ao salvar investimento: {e}")
        return False

# Lista todos os investimentos feitos por um usuário
def listar_investimentos(email):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            # Ordena por data decrescente para mostrar os mais recentes primeiro
            cursor.execute('''
                SELECT cripto, valor, preco, data FROM investimentos WHERE email = ?
                ORDER BY data DESC
            ''', (email,))
            rows = cursor.fetchall()
            # Converte os resultados em uma lista de dicionários
            return [{
                'cripto': row[0],
                'valor': row[1],
                'preco': row[2],
                'data': row[3]
            } for row in rows]
    except Exception as e:
        print(f"[Erro] Falha ao listar investimentos: {e}")
        return []

# Função auxiliar para obter dados do usuário pelo email (útil para depuração ou outras operações)
def get_user_by_email(email):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email, nome, saldo_brl FROM usuarios WHERE email = ?", (email,))
            user_data = cursor.fetchone()
            if user_data:
                return {'email': user_data[0], 'nome': user_data[1], 'saldo_brl': user_data[2]}
            return None
    except Exception as e:
        print(f"[Erro] Falha ao obter usuário por email: {e}")
        return None