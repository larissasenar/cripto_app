# 💰 CriptoInvestApp

**CriptoInvestApp** é uma aplicação web desenvolvida em **Python com Flask**, projetada para **simular o gerenciamento de uma carteira de investimentos em criptomoedas**.

A plataforma permite aos usuários:

- Acompanhar **cotações em tempo real**
- Visualizar **gráficos interativos**
- Realizar **conversões de moedas**
- Simular **investimentos**
- Consultar **FAQ**
- Gerenciar saldo simulado
- Acompanhar o histórico de transações

🔗 **Acesse agora:** [https://criptoinvestapp.onrender.com](https://criptoinvestapp.onrender.com)

---

## 🎯 Objetivo

Este projeto foi criado **com fins educacionais** para demonstrar a aplicação de **tecnologias web** no desenvolvimento de uma plataforma **financeira simulada**.

---

## ✨ Funcionalidades Principais

### 🔐 Autenticação de Usuários

- Cadastro de novos usuários
- Login seguro com gerenciamento de sessão
- Logout

### 📊 Dashboard Interativo

- Visualização do saldo em BRL e saldo total da carteira simulada
- Cotações atuais de Bitcoin, Ethereum, Litecoin, Dogecoin, Cardano via API CoinGecko (com cache)

### 📈 Gráficos de Preços Históricos

- Gráficos com **Chart.js**
- Seleção de períodos: 7, 15, 30 dias
- Exibição de preços máximo e mínimo

### 💱 Conversor de Moedas

- Conversões entre criptomoedas e moedas fiduciárias
- Histórico de conversões do usuário

### 💼 Gerenciamento de Carteira Simulada

- Saldo detalhado em BRL e cripto
- Simulação de depósitos e saques

### 📥 Simulação de Investimentos

- Compra simulada de criptomoedas com saldo em BRL
- Histórico com cripto, valor, preço de compra, data e ganhos/perdas simulados

### 📑 Histórico de Transações

- Registro completo de depósitos, saques e compras

### ❓ FAQ

- Respostas para dúvidas comuns sobre o app e o mercado

### 📱 Design Responsivo

- Layout adaptável (desktop, tablet e celular)
- Navegação com sidebar e menu "hamburger"

---

## 🛠️ Tecnologias Utilizadas

### 🔧 Backend

- **Python 3**
- **Flask** – microframework web
- **Jinja2** – renderização de templates

### 🎨 Frontend

- **HTML5**, **CSS3**
- **JavaScript**
- **Chart.js** – gráficos interativos
- **Font Awesome** – ícones vetoriais

### 💾 Banco de Dados

- **SQLite** – banco leve baseado em arquivo

### 🌐 APIs Externas

- **CoinGecko API** – dados de cripto em tempo real

### ⚙️ Outros

- Ambiente virtual Python (`venv`)
- Biblioteca `requests` para chamadas HTTP

---

## 🚀 Como Executar

Siga os passos abaixo para configurar e executar a aplicação localmente:

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/larissasenar/cripto_app.git
   cd cripto_app
   ```

   *(Nota: o nome da pasta pode ser `cripto-invest-app` ou `cripto_app` dependendo de como você clonou/nomeou)*

2. **Crie e ative um ambiente virtual:**

   - **Linux/macOS:**

     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

   - **Windows:**

     ```bash
     python -m venv venv
     .\venv\Scripts\activate
     ```

3. **Instale as dependências:**

   ```bash
   pip install -r requirements.txt
   ```

   *(Certifique-se de que o arquivo `requirements.txt` está atualizado)*

4. **Inicialize o Banco de Dados (se necessário):**
   O banco `usuarios.db` é criado automaticamente na primeira execução via `init_db()`.

5. **Execute a aplicação Flask:**

   ```bash
   flask run
   ```

   *(Ou `python app.py` se houver `if __name__ == '__main__'`)*

6. **Acesse no navegador:**

   ```
   http://127.0.0.1:5000/
   ```

---

## 📂 Estrutura de Arquivos Principal

```
cripto_app/
├── app.py                  # Lógica principal Flask
├── database.py             # Interações com SQLite
├── crypto_api.py           # Comunicação com CoinGecko API
├── requirements.txt        # Dependências do projeto
├── usuarios.db             # Banco de dados SQLite (gerado automaticamente)
├── static/
│   ├── css/
│   │   └── style.css       # Estilos personalizados
│   ├── js/
│   │   └── script.js       # Scripts JS
│   └── images/             # Imagens (se houver)
├── templates/
│   ├── layout.html
│   ├── login.html
│   ├── cadastro.html
│   ├── dashboard.html
│   ├── faq.html
│   └── video_explicativo.html
└── README.md               # Este arquivo
```

---

## ⚠️ Aviso

Esta aplicação foi desenvolvida para **fins educacionais e de demonstração**.  
**Não deve ser utilizada como uma plataforma de investimento real** sem uma auditoria de segurança completa e a implementação de medidas de segurança robustas adequadas para aplicações financeiras.  
As operações realizadas são **simuladas** e não envolvem transações financeiras reais.

---

## 📬 Contato

Desenvolvido por **Larissa Senar**  
📧 Email: <larissasenar@gmail.com>

---
