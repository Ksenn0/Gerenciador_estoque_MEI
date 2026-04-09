# Gerenciador de Estoque para MEI
## Sistema simples e prático para Microempreendedores Individuais (MEI) controlarem estoque, vendas e faturamento.
## Desenvolvido em dupla para facilitar o dia a dia de pequenos negócios.

# ✨ Funcionalidades

Cadastro e listagem de produtos
Controle de estoque (entradas, saídas e vendas)
Dashboard com:
Total de produtos
Faturamento do mês
Produtos em estoque crítico
Últimas vendas

Filtro de produtos por status (crítico / normal)

## 🛠️ Tecnologias Utilizadas

| Parte       | Tecnologia                  |
|-------------|-----------------------------|
| Backend     | Python + Flask              |
| Banco       | Supabase (PostgreSQL)       |
| Autenticação| Supabase Auth               |
| Frontend    | HTML5, CSS3 e JavaScript puro |

## 📁 Estrutura do Projeto
```bash
  Gerenciador_estoque_MEI/
  ├── app.py                    # Backend (Flask)
  ├── requirements.txt
  ├── Procfile                  # Para deploy (Heroku/Railway)
  ├── .gitignore
  ├── .vscode/                  # Configurações do VS Code
  ├── frontEnd/                 # HTML, CSS e JS
  │   ├── index.html
  │   ├── css/
  │   └── js/
  └── README.md
```
## 🚀 Como Executar Localmente
1. Backend
   ```bash
    # Clone o repositório
    git clone https://github.com/Ksenn0/Gerenciador_estoque_MEI.git
    cd Gerenciador_estoque_MEI
    
    # Crie ambiente virtual (recomendado)
    python -m venv venv
    
    # Ative o ambiente
    # Windows:
    venv\Scripts\activate
    # Linux / Mac:
    source venv/bin/activate
    
    # Instale as dependências
    pip install -r requirements.txt
    
    # Configure as variáveis de ambiente
    cp .env.example .env
   ```

Edite o arquivo .env:
```bash
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_KEY=sua_chave_aqui          # Service Role Key (recomendado para MVP)
   ```
### Rode o servidor
  ```bash
   python app.py
```
O backend ficará disponível em: http://127.0.0.1:5000

2. Frontend
Abra a pasta frontEnd e execute o index.html com Live Server (extensão do VS Code) ou diretamente no navegador.

## 🔑 Principais Rotas da API

| Método | Rota                          | Descrição                              |
|--------|-------------------------------|----------------------------------------|
| GET    | `/api/teste`                  | Testa se o backend está funcionando    |
| GET    | `/api/produtos`               | Lista todos os produtos do usuário     |
| POST   | `/api/produtos`               | Cria um novo produto                   |
| POST   | `/api/movimentacoes/entrada`  | Registra entrada de estoque            |
| POST   | `/api/movimentacoes/saida`    | Registra saída de estoque              |
| POST   | `/api/vendas`                 | Registra uma venda                     |
| GET    | `/api/home`                   | Dados para o dashboard                 |

Todas as rotas protegidas por autenticação JWT do Supabase (header Authorization: Bearer <token>).

## 🔐 Autenticação

Utiliza autenticação do Supabase Auth
O token deve ser enviado em todas as requisições autenticadas
Atualmente recomenda-se usar Service Role Key no backend durante o desenvolvimento (ignora RLS)

## 📊 Banco de Dados (Supabase)
Principais tabelas:

produtos
movimentacoes

## 👥 Equipe

Backend & Supabase: Kauann Senna (Ksenn0)
Frontend: [Nome do seu amigo]

📄 Licença
Este projeto é para uso pessoal e aprendizado. Fique à vontade para estudar e modificar.
