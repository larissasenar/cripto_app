import os
import sqlite3
from datetime import datetime

DB_NAME = 'usuarios.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    email TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
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
    print("Banco criado com sucesso.")

def reset_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Arquivo {DB_NAME} removido.")
    else:
        print(f"Arquivo {DB_NAME} não existe. Criando novo banco.")
    init_db()

if __name__ == "__main__":
    reset_db()
