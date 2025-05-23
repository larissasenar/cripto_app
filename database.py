import sqlite3
from datetime import datetime

# Cria as tabelas no banco de dados SQLite
def init_db():
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()

            # Tabela de usuários
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    email TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    senha TEXT NOT NULL
                )
            ''')

            # Tabela de investimentos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS investimentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    cripto TEXT NOT NULL,
                    valor REAL NOT NULL,
                    preco REAL NOT NULL,
                    data TEXT NOT NULL,
                    FOREIGN KEY (email) REFERENCES usuarios(email)
                )
            ''')

            # Tabela de carteira
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS carteira (
                    email TEXT NOT NULL,
                    moeda TEXT NOT NULL,
                    saldo REAL NOT NULL DEFAULT 0,
                    PRIMARY KEY (email, moeda),
                    FOREIGN KEY (email) REFERENCES usuarios(email)
                )
            ''')

            # Tabela de transações
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    tipo TEXT NOT NULL,  -- Ex: 'deposito', 'saque', 'compra', 'venda'
                    moeda TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data TEXT NOT NULL,
                    FOREIGN KEY (email) REFERENCES usuarios(email)
                )
            ''')

            conn.commit()
    except Exception as e:
        print(f"[Erro] Falha ao inicializar o banco de dados: {e}")

# Atualiza o saldo da moeda na carteira do usuário
def atualizar_saldo(email, moeda, valor):
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT saldo FROM carteira WHERE email = ? AND moeda = ?', (email, moeda))
            resultado = cursor.fetchone()

            if resultado:
                novo_saldo = resultado[0] + valor
                if novo_saldo < 0:
                    print("[Erro] Saldo insuficiente.")
                    return False

                cursor.execute('UPDATE carteira SET saldo = ? WHERE email = ? AND moeda = ?', (novo_saldo, email, moeda))
            else:
                if valor < 0:
                    print("[Erro] Não é possível iniciar carteira com saldo negativo.")
                    return False

                cursor.execute('INSERT INTO carteira (email, moeda, saldo) VALUES (?, ?, ?)', (email, moeda, valor))

            conn.commit()
            return True
    except Exception as e:
        print(f"[Erro] Falha ao atualizar saldo: {e}")
        return False

# Registra uma transação no histórico
def registrar_transacao(email, tipo, moeda, valor):
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()
            data = datetime.utcnow().isoformat(sep=' ', timespec='seconds')

            cursor.execute('''
                INSERT INTO transacoes (email, tipo, moeda, valor, data)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, tipo, moeda, valor, data))

            conn.commit()
            return True
    except Exception as e:
        print(f"[Erro] Falha ao registrar transação: {e}")
        return False

# Retorna o saldo atual de uma moeda específica
def get_saldo(email, moeda="BRL"):
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT saldo FROM carteira WHERE email = ? AND moeda = ?', (email, moeda))
            resultado = cursor.fetchone()
            return resultado[0] if resultado else 0.0
    except Exception as e:
        print(f"[Erro] Falha ao obter saldo: {e}")
        return 0.0

# Retorna os últimos registros de transações (default 10)
def get_historico_transacoes(email, limite=10):
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT tipo, moeda, valor, data
                FROM transacoes
                WHERE email = ?
                ORDER BY datetime(data) DESC
                LIMIT ?
            ''', (email, limite))

            return [{
                'tipo': t[0],
                'moeda': t[1],
                'valor': t[2],
                'data': t[3]
            } for t in cursor.fetchall()]
    except Exception as e:
        print(f"[Erro] Falha ao obter histórico de transações: {e}")
        return []

# Retorna todas as moedas e saldos do usuário
def get_carteira_completa(email):
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT moeda, saldo
                FROM carteira
                WHERE email = ?
                ORDER BY saldo DESC
            ''', (email,))

            return {moeda: saldo for moeda, saldo in cursor.fetchall()}
    except Exception as e:
        print(f"[Erro] Falha ao obter carteira completa: {e}")
        return {}

# Funções para usuários (já existentes no seu app)

def cadastrar_usuario(nome, email, senha):
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT email FROM usuarios WHERE email = ?', (email,))
            if cursor.fetchone():
                return False
            cursor.execute('INSERT INTO usuarios (email, nome, senha) VALUES (?, ?, ?)', (email, nome, senha))
            conn.commit()
            return True
    except Exception as e:
        print(f"[Erro] Falha ao cadastrar usuário: {e}")
        return False

def verificar_usuario(email, senha):
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT email, nome FROM usuarios WHERE email = ? AND senha = ?', (email, senha))
            return cursor.fetchone()
    except Exception as e:
        print(f"[Erro] Falha ao verificar usuário: {e}")
        return None

def salvar_investimento(email, cripto, valor, preco):
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()
            data = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
            cursor.execute('''
                INSERT INTO investimentos (email, cripto, valor, preco, data)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, cripto, valor, preco, data))
            conn.commit()
            return True
    except Exception as e:
        print(f"[Erro] Falha ao salvar investimento: {e}")
        return False

def listar_investimentos(email):
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cripto, valor, preco, data FROM investimentos WHERE email = ?
                ORDER BY datetime(data) DESC
            ''', (email,))
            rows = cursor.fetchall()
            return [{
                'cripto': row[0],
                'valor': row[1],
                'preco': row[2],
                'data': row[3]
            } for row in rows]
    except Exception as e:
        print(f"[Erro] Falha ao listar investimentos: {e}")
        return []
