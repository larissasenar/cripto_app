
import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    email TEXT PRIMARY KEY,
                    senha TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS investimentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    cripto TEXT,
                    valor REAL,
                    preco REAL,
                    data TEXT)''')
    conn.commit()
    conn.close()

def cadastrar_usuario(email, senha):
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO usuarios (email, senha) VALUES (?, ?)", (email, senha))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def verificar_usuario(email, senha):
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE email=? AND senha=?", (email, senha))
    resultado = c.fetchone()
    conn.close()
    return resultado

def salvar_investimento(email, cripto, valor, preco):
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    data = datetime.now().strftime('%Y-%m-%d')
    c.execute("INSERT INTO investimentos (email, cripto, valor, preco, data) VALUES (?, ?, ?, ?, ?)", 
              (email, cripto, valor, preco, data))
    conn.commit()
    conn.close()

def listar_investimentos(email):
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute("SELECT cripto, valor, preco, data FROM investimentos WHERE email=?", (email,))
    rows = c.fetchall()
    conn.close()
    return [{'cripto': r[0], 'valor': r[1], 'preco': r[2], 'data': r[3]} for r in rows]
