# Cripto Invest App 🚀

## Descrição

O **Cripto Invest App** é uma aplicação web desenvolvida em Python com Flask, projetada para simular o gerenciamento de uma carteira de investimentos em criptomoedas. A plataforma permite aos usuários acompanhar cotações em tempo real, visualizar gráficos interativos do histórico de preços, realizar conversões de valores entre diferentes moedas, registrar e acompanhar investimentos simulados, além de consultar uma seção de FAQ para esclarecer dúvidas.

Este projeto foi criado com fins educacionais para demonstrar a aplicação de tecnologias web no desenvolvimento de uma plataforma financeira simulada.

## Status do Projeto

🚧 **Em Desenvolvimento / Concluído para Fins Acadêmicos** 🚧

*(Defina o status atual do seu projeto. Ex: "Concluído para apresentação da disciplina X", "Em desenvolvimento ativo", "Versão 1.0 estável")*

## 📸 Screenshots / Demonstração

*(É altamente recomendável adicionar screenshots da aplicação aqui ou um link para um vídeo de demonstração curta – talvez o mesmo vídeo que você está preparando!)*

* **Exemplo:**
  * [Link para Vídeo de Demonstração](#) *(Substitua pelo link do seu vídeo)*
  * ![Screenshot do Dashboard](https://placehold.co/600x400/007bff/ffffff?text=Dashboard+CriptoApp)
  * ![Screenshot do Gráfico](https://placehold.co/600x400/28a745/ffffff?text=Gráfico+de+Preços)

## ✨ Funcionalidades Principais

* **Autenticação de Usuários:**
  * Cadastro de novos usuários.
  * Login seguro com gerenciamento de sessão.
  * Logout.
* **Dashboard Interativo:**
  * Visualização do saldo em BRL e saldo total da carteira simulada.
  * Exibição das cotações atuais das principais criptomoedas (ex: Bitcoin, Ethereum, Litecoin, Dogecoin, Cardano) obtidas via API (CoinGecko) com sistema de cache para otimização.
* **Gráficos de Preços Históricos:**
  * Gráficos interativos (Chart.js) para análise do histórico de preços de diferentes criptomoedas.
  * Seleção de diferentes períodos de visualização (ex: 7, 15, 30 dias).
  * Exibição de preço máximo e mínimo no período.
* **Conversor de Moedas:**
  * Ferramenta para converter valores entre diferentes criptomoedas e moedas fiduciárias (ex: BTC para BRL, USD para ETH) utilizando cotações atuais.
  * Histórico das conversões realizadas pelo usuário.
* **Gerenciamento de Carteira e Operações Simuladas:**
  * Visualização detalhada da carteira do usuário com os saldos de BRL e de cada criptomoeda possuída.
  * Simulação de depósitos e saques em BRL.
* **Simulação de Investimentos:**
  * Funcionalidade para "comprar" criptomoedas utilizando o saldo simulado em BRL.
  * Cálculo da quantidade de cripto adquirida com base na cotação do momento.
  * Listagem dos investimentos realizados, incluindo detalhes como cripto, valor investido, preço de compra e data.
  * Cálculo e exibição de ganhos/perdas simulados para cada investimento.
* **Histórico de Transações:**
  * Registro detalhado de todas as operações financeiras: depósitos, saques, compras de cripto.
* **FAQ (Perguntas Frequentes):**
  * Seção informativa com respostas para dúvidas comuns sobre a aplicação e o mercado de criptomoedas.
* **Design Responsivo:**
  * Layout adaptável para uma boa experiência de usuário em desktops, tablets e dispositivos móveis.
  * Sidebar de navegação com menu "hamburger" em telas menores.

## 🛠️ Tecnologias Utilizadas

* **Backend:**
  * **Python 3**
  * **Flask:** Microframework web para desenvolvimento da API e lógica do servidor.
  * **Jinja2:** Motor de templates para renderização dinâmica de HTML.
* **Frontend:**
  * **HTML5**
  * **CSS3** (com foco em responsividade)
  * **JavaScript:** Para interatividade e manipulação do DOM.
  * **Chart.js:** Biblioteca para criação de gráficos interativos.
  * **Font Awesome:** Para ícones vetoriais.
  * *(Opcional, se usou)* **Tailwind CSS:** Framework CSS utility-first para estilização rápida.
* **Banco de Dados:**
  * **SQLite:** Banco de dados relacional leve, baseado em arquivo, para persistência de dados (usuários, carteiras, transações, etc.).
* **APIs Externas:**
  * **CoinGecko API:** Para obtenção de dados de cotações de criptomoedas e históricos de preços.
* **Outros:**
  * Ambiente Virtual Python (`venv`)
  * `requests` (biblioteca Python para requisições HTTP)

## 📋 Pré-requisitos

Antes de começar, garanta que você tem o Python 3 e o pip instalados no seu sistema.

* Python 3 (versão 3.6 ou superior recomendada)
* pip (gerenciador de pacotes Python)
* Git (para clonar o repositório)

## 🚀 Como Executar

Siga os passos abaixo para configurar e executar a aplicação localmente:

1. **Clone o repositório:**

    ```bash
    git clone [https://github.com/larissasenar/cripto_app.git](https://github.com/larissasenar/cripto_app.git)
    cd cripto_app 
    ```

    *(Nota: o nome da pasta pode ser `cripto-invest-app` ou `cripto_app` dependendo de como você o clonou/nomeou)*

2. **Crie e ative um ambiente virtual:**
    * No Linux/macOS:

        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

    * No Windows:

        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3. **Instale as dependências:**
    Com o ambiente virtual ativado, instale as bibliotecas Python necessárias:

    ```bash
    pip install -r requirements.txt
    ```

    *(Certifique-se de que o arquivo `requirements.txt` está atualizado com todas as dependências, como Flask, requests, etc.)*

4. **Inicialize o Banco de Dados (se necessário):**
    A aplicação deve criar o banco de dados SQLite (`usuarios.db`) automaticamente na primeira execução através da função `init_db()` em `app.py`.

5. **Execute a aplicação Flask:**

    ```bash
    flask run
    ```

    *(Alternativamente, se você tiver um bloco `if __name__ == '__main__': app.run(debug=True)` em `app.py`, pode usar `python app.py`)*

6. **Acesse no navegador:**
    Abra seu navegador e acesse: `http://127.0.0.1:5000/` ou `http://localhost:5000/`

## 📂 Estrutura de Arquivos Principal

cripto_app/
├── app.py                # Lógica principal da aplicação Flask, rotas
├── database.py           # Funções para interação com o banco de dados SQLite
├── crypto_api.py         # Funções para interação com a API CoinGecko
├── requirements.txt      # Lista de dependências Python
├── usuarios.db           # Arquivo do banco de dados SQLite (gerado automaticamente)
├── static/               # Arquivos estáticos
│   ├── css/
│   │   └── style.css     # Estilos CSS personalizados
│   ├── js/
│   │   └── script.js     # Scripts JavaScript
│   └── images/           # Imagens e ícones (se houver)
├── templates/            # Arquivos HTML com templates Jinja2
│   ├── layout.html       # Template base
│   ├── login.html
│   ├── cadastro.html
│   ├── dashboard.html
│   ├── faq.html
│   └── video_explicativo.html # Página para o vídeo
└── README.md             # Este arquivo

## 🤝 Como Contribuir (Opcional)

Se este fosse um projeto aberto, aqui estariam as instruções para contribuição. Como é um projeto acadêmico, esta seção pode ser omitida ou adaptada.

Exemplo:
"Contribuições são bem-vindas! Para sugestões ou melhorias:

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona NovaFuncionalidade'`)
4. Push para a Branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request"

## 👤 Autor

* **Larissa Sena**
  * Email: `larissasenar@gmail.com`
  * GitHub: [larissasenar](https://github.com/larissasenar)
  * *(Opcional: Link do LinkedIn)*

## 📜 Licença (Opcional)

*(Se você quiser adicionar uma licença, como MIT, Apache 2.0, etc. Para projetos acadêmicos, muitas vezes não é necessário, mas é uma boa prática para projetos abertos.)*

Exemplo:
"Este projeto está licenciado sob a Licença MIT - veja o arquivo `LICENSE.md` para detalhes."

---

**⚠️ Aviso:**
Esta aplicação foi desenvolvida para fins educacionais e de demonstração. **Não deve ser utilizada como uma plataforma de investimento real** sem uma auditoria de segurança completa e a implementação de medidas de segurança robustas adequadas para aplicações financeiras. As operações realizadas são simuladas e não envolvem transações financeiras reais.
