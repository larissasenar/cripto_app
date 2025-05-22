import sqlite3
from datetime import datetime

# Inicializa o banco e cria as tabelas se não existirem
def init_db():
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    email TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    senha TEXT NOT NULL
                )
            ''')
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
            conn.commit()
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")

# Cadastra um novo usuário se o e-mail ainda não estiver registrado
def cadastrar_usuario(nome, email, senha):
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM usuarios WHERE email = ?", (email,))
            if cursor.fetchone():
                return False  # Usuário já existe
            cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha))
            conn.commit()
            return True
    except Exception as e:
        print(f"Erro ao cadastrar usuário: {e}")
        return False

# Verifica se o e-mail e senha estão corretos
def verificar_usuario(email, senha):
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email, nome FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
            return cursor.fetchone()  # Retorna (email, nome) ou None
    except Exception as e:
        print(f"Erro ao verificar usuário: {e}")
        return None

# Salva um investimento feito pelo usuário
def salvar_investimento(email, cripto, valor, preco):
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()
            data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO investimentos (email, cripto, valor, preco, data)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, cripto, valor, preco, data))
            conn.commit()
    except Exception as e:
        print(f"Erro ao salvar investimento: {e}")

# Lista os investimentos do usuário com formatação
def listar_investimentos(email):
    try:
        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cripto, valor, preco, data
                FROM investimentos
                WHERE email = ?
                ORDER BY data DESC
            ''', (email,))
            rows = cursor.fetchall()
            return [{'cripto': r[0], 'valor': r[1], 'preco': r[2], 'data': r[3]} for r in rows]
    except Exception as e:
        print(f"Erro ao listar investimentos: {e}")
        return []
