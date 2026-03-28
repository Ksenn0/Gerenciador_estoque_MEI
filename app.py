from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import datetime
from uuid import UUID

load_dotenv()

app = Flask(__name__)
CORS(app)  # Permite chamadas do frontend

# Conexão com Supabase (use SERVICE ROLE apenas em ambiente seguro / backend)
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# ────────────────────────────────────────────────
# Função auxiliar: pega o ID do usuário logado pelo JWT
# ────────────────────────────────────────────────
def get_current_user_id():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise ValueError("Token não fornecido ou inválido")
    
    token = auth_header.split(" ")[1]
    try:
        user = supabase.auth.get_user(token)
        return user.user.id
    except Exception as e:
        raise ValueError(f"Token inválido: {str(e)}")

# ────────────────────────────────────────────────
# Função auxiliar: valida dados de movimentação
# ────────────────────────────────────────────────
def validar_movimentacao(data, tipo):
    if 'produto_id' not in data or 'quantidade' not in data:
        raise ValueError("Campos obrigatórios: produto_id e quantidade")
    
    try:
        # Converte para inteiro (não float)
        qtd = int(float(data['quantidade']))   # aceita "5.0" ou 5.0 ou "5"
        if qtd <= 0:
            raise ValueError(f"Quantidade deve ser positiva para {tipo}")
        return qtd
    except (TypeError, ValueError):
        raise ValueError("Quantidade deve ser um número positivo inteiro")

# ────────────────────────────────────────────────
# Função auxiliar: atualiza o estoque do produto
# ────────────────────────────────────────────────
def atualizar_estoque(produto_id, delta):
    """Atualiza o estoque de forma segura"""
    try:
        # Busca o estoque atual
        response = supabase.table('produtos') \
            .select('estoque_atual') \
            .eq('id', produto_id) \
            .execute()
        
        if not response.data:
            raise ValueError(f"Produto {produto_id} não encontrado")
        
        estoque_atual = response.data[0]['estoque_atual']
        novo_estoque = estoque_atual + delta

        print(f"[ATUALIZAR ESTOQUE] Produto: {produto_id} | Atual: {estoque_atual} → Novo: {novo_estoque} (delta: {delta})")

        # Atualiza
        update_response = supabase.table('produtos') \
            .update({'estoque_atual': novo_estoque}) \
            .eq('id', produto_id) \
            .execute()

        return novo_estoque

    except Exception as e:
        print(f"[ERRO ATUALIZAR ESTOQUE] {str(e)}")
        raise

# ────────────────────────────────────────────────
# Rotas de teste
# ────────────────────────────────────────────────
@app.route('/api/teste', methods=['GET'])
def teste():
    return jsonify({"mensagem": "Backend funcionando!"})

@app.route('/api/teste-post', methods=['POST'])
def teste_post():
    return jsonify({"mensagem": "POST recebido com sucesso!"}), 201

# ────────────────────────────────────────────────
# PRODUTOS
# ────────────────────────────────────────────────
@app.route('/api/produtos', methods=['GET', 'POST'])
def produtos():
    if request.method == 'GET':
        # código de listar_produtos aqui
        try:
            user_id = get_current_user_id()
        except ValueError as e:
            return jsonify({"error": str(e)}), 401

        status = request.args.get('status')
        query = supabase.table('produtos') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('nome')
        response = query.execute()
        produtos = response.data

        if status == 'critico':
            produtos = [p for p in produtos if p['estoque_atual'] <= p.get('estoque_minimo', 5)]
        elif status == 'normal':
            produtos = [p for p in produtos if p['estoque_atual'] > p.get('estoque_minimo', 5)]

        return jsonify(produtos)

    elif request.method == 'POST':
        # código de criar_produto aqui (com os prints de debug)
        print("=== Nova requisição POST /api/produtos ===")
        print("Headers recebidos:", dict(request.headers))

        try:
            user_id = get_current_user_id()
            print(f"User ID extraído com sucesso: {user_id}")
        except ValueError as e:
            print(f"ERRO AO PEGAR USER_ID: {str(e)}")
            return jsonify({"error": str(e)}), 401

        data = request.get_json(silent=True) or {}
        print("Dados recebidos no body:", data)

        novo_produto = {
            'user_id': user_id,
            'nome': data.get('nome', '').strip(),
            'categoria': data.get('categoria', '').strip() or None,
            'preco': float(data.get('preco', 0)),
            'estoque_atual': int(data.get('quantidade', 0)),  # ajustado para usar 'quantidade' do body
            'estoque_minimo': int(data.get('estoque_minimo', 5)),
            'foto_url': data.get('foto_url')
        }
        print("Objeto que vai ser inserido:", novo_produto)

        print("User ID do token:", user_id)
        print("Tipo do user_id:", type(user_id))
        print("Objeto completo antes do insert:", novo_produto)

        try:
            response = supabase.table('produtos').insert(novo_produto).execute()
            print("Inserção OK:", response.data)
            return jsonify(response.data[0] if response.data else {"mensagem": "Criado sem retorno"}), 201
        except Exception as e:
            print("ERRO NO INSERT:", str(e))
            return jsonify({"error": str(e)}), 500

# ────────────────────────────────────────────────
# MOVIMENTAÇÕES (VERSÃO FINAL - CONSISTENTE)
# ────────────────────────────────────────────────

@app.route('/api/movimentacoes/entrada', methods=['POST'])
def registrar_entrada():
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        qtd = int(float(data.get('quantidade', 0)))
        if qtd <= 0:
            return jsonify({"error": "Quantidade deve ser positiva"}), 400

        produto_id = data['produto_id']
        observacao = data.get('observacao', '').strip()

        print(f"[ENTRADA] Iniciando - Produto: {produto_id} | Qtd: {qtd}")

        mov = {
            'user_id': user_id,
            'produto_id': produto_id,
            'tipo': 'entrada',
            'quantidade': qtd,
            'observacao': observacao
        }

        supabase.table('movimentacoes').insert(mov).execute()
        print("[ENTRADA] Movimentação inserida")

        atualizar_estoque(produto_id, qtd)
        print(f"[ENTRADA SUCESSO] +{qtd} unidades")

        return jsonify({"success": True, "mensagem": f"Entrada de {qtd} unidades registrada"}), 201

    except Exception as e:
        print(f"[ERRO ENTRADA] {str(e)}")
        return jsonify({"error": str(e)}), 400


@app.route('/api/movimentacoes/saida', methods=['POST'])
def registrar_saida():
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        qtd = int(float(data.get('quantidade', 0)))
        if qtd <= 0:
            return jsonify({"error": "Quantidade deve ser positiva"}), 400

        produto_id = data['produto_id']
        observacao = data.get('observacao', '').strip()

        print(f"[SAÍDA] Iniciando - Produto: {produto_id} | Qtd: {qtd}")

        mov = {
            'user_id': user_id,
            'produto_id': produto_id,
            'tipo': 'saida',
            'quantidade': qtd,
            'observacao': observacao
        }

        supabase.table('movimentacoes').insert(mov).execute()
        print("[SAÍDA] Movimentação inserida")

        atualizar_estoque(produto_id, -qtd)
        print(f"[SAÍDA SUCESSO] -{qtd} unidades")

        return jsonify({"success": True, "mensagem": f"Saída de {qtd} unidades registrada"}), 201

    except Exception as e:
        print(f"[ERRO SAÍDA] {str(e)}")
        return jsonify({"error": str(e)}), 400


@app.route('/api/vendas', methods=['POST'])
def registrar_venda():
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        qtd = int(float(data.get('quantidade', 0)))
        if qtd <= 0:
            return jsonify({"error": "Quantidade deve ser positiva"}), 400

        if not data.get('preco_unitario') or not data.get('cliente'):
            return jsonify({"error": "Campos obrigatórios: preco_unitario e cliente"}), 400

        produto_id = data['produto_id']
        cliente = data['cliente'].strip()
        preco_unitario = float(data['preco_unitario'])
        observacao = data.get('observacao', '').strip()

        print(f"[VENDA] Iniciando - Produto: {produto_id} | Qtd: {qtd} | Cliente: {cliente}")

        mov = {
            'user_id': user_id,
            'produto_id': produto_id,
            'tipo': 'venda',
            'quantidade': qtd,
            'preco_unitario': preco_unitario,
            'cliente': cliente,
            'observacao': observacao
        }

        supabase.table('movimentacoes').insert(mov).execute()
        print("[VENDA] Movimentação inserida")

        atualizar_estoque(produto_id, -qtd)
        print(f"[VENDA SUCESSO] -{qtd} unidades")

        return jsonify({
            "success": True, 
            "mensagem": f"Venda de {qtd} unidades para {cliente} registrada com sucesso"
        }), 201

    except Exception as e:
        print(f"[ERRO VENDA] {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/api/vendas', methods=['GET'])
def listar_vendas():
    try:
        user_id = get_current_user_id()
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    response = supabase.table('movimentacoes') \
        .select('*, produtos(nome)') \
        .eq('user_id', user_id) \
        .eq('tipo', 'venda') \
        .order('created_at', desc=True) \
        .execute()

    return jsonify(response.data)

# ────────────────────────────────────────────────
# DASHBOARD / HOME
# ────────────────────────────────────────────────
@app.route('/api/home', methods=['GET'])
def home():
    try:
        user_id = get_current_user_id()
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    mes_atual = datetime.now().strftime('%Y-%m')
    inicio_mes = f"{mes_atual}-01"
    # fim_mes aproximado (pode melhorar com calendar)
    fim_mes = f"{mes_atual}-31"

    # Total de produtos
    total_prod = supabase.table('produtos') \
        .select('count', count='exact') \
        .eq('user_id', user_id) \
        .execute().count or 0

    # Estoque crítico
    produtos = supabase.table('produtos') \
        .select('estoque_atual, estoque_minimo') \
        .eq('user_id', user_id) \
        .execute().data
    critico = sum(1 for p in produtos if p['estoque_atual'] <= p.get('estoque_minimo', 5))

    # Vendas e faturamento do mês
    vendas_mes = supabase.table('movimentacoes') \
        .select('quantidade, preco_unitario') \
        .eq('user_id', user_id) \
        .eq('tipo', 'venda') \
        .gte('created_at', inicio_mes) \
        .lt('created_at', fim_mes) \
        .execute().data

    faturamento = sum(
        v['quantidade'] * (v.get('preco_unitario') or 0)
        for v in vendas_mes
    )

    # Últimas 3 vendas
    ultimas = supabase.table('movimentacoes') \
        .select('*, produtos(nome)') \
        .eq('user_id', user_id) \
        .eq('tipo', 'venda') \
        .order('created_at', desc=True) \
        .limit(3) \
        .execute().data

    return jsonify({
        "total_produtos": total_prod,
        "faturamento_mes": round(faturamento, 2),
        "estoque_critico": critico,
        "vendas_no_mes": len(vendas_mes),
        "ultimas_vendas": ultimas
    })
    
# ====================== AUTENTICAÇÃO ======================
@app.route('/api/cadastro', methods=['POST'])
def cadastro():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email e senha são obrigatórios"}), 400
    
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        return jsonify({
            "mensagem": "Usuário criado com sucesso! Verifique seu email.",
            "user": response.user
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email e senha são obrigatórios"}), 400
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Correção: converter o objeto user para dicionário
        user_dict = {
            "id": response.user.id,
            "email": response.user.email,
            "email_confirmed_at": response.user.email_confirmed_at,
            "created_at": response.user.created_at,
            "last_sign_in_at": response.user.last_sign_in_at
        }
        
        return jsonify({
            "access_token": response.session.access_token,
            "user": user_dict   # agora é um dicionário simples
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 401
    
#==================== RELATORIOS ===================================    
@app.route('/api/relatorio', methods=['GET'])
def relatorio():
    try:
        user_id = get_current_user_id()
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    # Vendas do mês atual
    response = supabase.table('movimentacoes') \
        .select('*, produtos(nome)') \
        .eq('user_id', user_id) \
        .eq('tipo', 'venda') \
        .order('created_at', desc=True) \
        .execute()

    return jsonify({
        "vendas": response.data,
        "total_vendas": len(response.data)
    })

# ────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)