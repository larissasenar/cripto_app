import sqlite3
from datetime import datetime

# Inicializa o banco e cria as tabelas se não existirem
def init_db():
    try:
        conn = sqlite3.connect('usuarios.db')
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
                email TEXT,
                cripto TEXT,
                valor REAL,
                preco REAL,
                data TEXT
            )
        ''')
        conn.commit()
    finally:
        conn.close()

# Cadastra um novo usuário se o e-mail ainda não estiver registrado
def cadastrar_usuario(nome, email, senha):
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM usuarios WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return False  # Usuário já existe
    cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha))
    conn.commit()
    conn.close()
    return True

# Verifica se o e-mail e senha estão corretos
def verificar_usuario(email, senha):
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute("SELECT email, nome FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
    usuario = cursor.fetchone()
    conn.close()
    return usuario  # Retorna (email, nome) ou None

# Salva um investimento feito pelo usuário
def salvar_investimento(email, cripto, valor, preco):
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    data = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO investimentos (email, cripto, valor, preco, data)
        VALUES (?, ?, ?, ?, ?)
    ''', (email, cripto, valor, preco, data))
    conn.commit()
    conn.close()

# Lista os investimentos do usuário com formatação
def listar_investimentos(email):
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT cripto, valor, preco, data
        FROM investimentos
        WHERE email = ?
        ORDER BY data DESC
    ''', (email,))
    rows = cursor.fetchall()
    conn.close()
    return [{'cripto': r[0], 'valor': r[1], 'preco': r[2], 'data': r[3]} for r in rows]
