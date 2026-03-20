from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

# Conexão supabase
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)

# Rota de teste
@app.route('/api/teste', methods=['GET'])
def teste():
    return jsonify({"mensagem": "Back-end Flask + Supabase funcionando!"})

# Listar produtos do usuário logado
@app.route('/api/produtos', methods=['GET'])
def listar_produtos():
    # Pegar token do Header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"Error": "Token não fornecido"}), 401
    token = auth_header.split(" ")[1]
    
    # Verifica token com supabase
    try:
        user = supabase.auth.get_user(token)
        user_id = user.user.id
    except Exception as e:
        return jsonify({"error": "Token inválido"}), 401
    
    # Buscar produto
    response = supabase.table('produtos') \
        .select('*') \
        .eq('user_id', user_id) \
        .execute()
        
    if hasattr(response, 'error') and response.error:
        return jsonify({"error", response.error.mensage}), 500
    
    return jsonify(response.data)
                
# Rodar servidor
if __name__ == '__main__':
    app.run(debug=True, port=5000)