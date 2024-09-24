from flask import Flask, request
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .cred (se disponível)
load_dotenv('.cred')

# Configurações para conexão com o banco de dados usando variáveis de ambiente
config = {
    'host': os.getenv('DB_HOST', 'localhost'),  # Obtém o host do banco de dados da variável de ambiente
    'user': os.getenv('DB_USER'),  # Obtém o usuário do banco de dados da variável de ambiente
    'password': os.getenv('DB_PASSWORD'),  # Obtém a senha do banco de dados da variável de ambiente
    'database': os.getenv('DB_NAME', 'db_prep'),  # Obtém o nome do banco de dados da variável de ambiente
    'port': int(os.getenv('DB_PORT', 3306)),  # Obtém a porta do banco de dados da variável de ambiente
    'ssl_ca': os.getenv('SSL_CA_PATH')  # Caminho para o certificado SSL
}


# Função para conectar ao banco de dados
def connect_db():
    """Estabelece a conexão com o banco de dados usando as configurações fornecidas."""
    try:
        # Tenta estabelecer a conexão com o banco de dados usando mysql-connector-python
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            return conn
    except Error as err:
        # Em caso de erro, imprime a mensagem de erro
        print(f"Erro: {err}")
        return None


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return {"status": "API em execução"}, 200

@app.route('/clientes', methods=['POST'])
def clientes():
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    dado_cliente = request.json
    campos_obrigatorios = ['nome', 'email', 'cpf', 'senha']

    for campo in campos_obrigatorios:
        if campo not in dado_cliente:
            return {"erro": f"Campo '{campo}' é obrigatório."}, 400
        
    sql = "INSERT INTO tbl_clientes (nome, email, cpf, senha) VALUES (%s, %s, %s, %s)"
    values = tuple(dado_cliente[campo] for campo in campos_obrigatorios)

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, values)
            conn.commit()
            return {"mensagem": "cliente cadastrado com sucesso"}, 201
    except Error as err:
        return {"erro": f"Erro ao cadastrar cliente: {err}"}, 500
    finally:
        conn.close()

@app.route('/clientes/<int:id>', methods=['GET'])
def procurar_clientes(id):
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    sql = "SELECT * FROM tbl_clientes WHERE id = %s"
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, (id,))
            cliente = cursor.fetchone()
            if cliente:
                return cliente, 200
            return {"erro": "cliente não encontrado"}, 404
    except Error as err:
        return {"erro": f"Erro ao buscar cliente: {err}"}, 500
    finally:
        conn.close()

@app.route('/clientes', methods=['GET'])
def listar_clientes():
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    filtro_nome = request.args.get('nome')
    ordenar_por = request.args.get('ordenar_por', 'id')
    ordem = request.args.get('ordem', 'asc')

    sql = "SELECT * FROM tbl_clientes"
    params = []

    if filtro_nome:
        sql += " WHERE nome LIKE %s"
        params.append(f"%{filtro_nome}%")

    if ordenar_por not in ['id', 'nome', 'email', 'cpf', 'senha']:
        ordenar_por = 'id'
    if ordem not in ['asc', 'desc']:
        ordem = 'asc'

    sql += f" ORDER BY {ordenar_por} {ordem}"

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, params)
            clientes = cursor.fetchall()
            if clientes:
                return {"clientes": clientes}, 200
            return {"erro": "Nenhum cliente encontrado"}, 404
    except Error as err:
        return {"erro": f"Erro ao buscar clientes: {err}"}, 500
    finally:
        conn.close()


@app.route('/clientes/<int:cliente_id>', methods=['PUT'])
def atualizar_cliente(cliente_id):
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    dado_cliente = request.json
    campos_obrigatorios = ['nome', 'email', 'cpf', 'senha']

    for campo in campos_obrigatorios:
        if campo not in dado_cliente:
            return {"erro": f"Campo '{campo}' é obrigatório."}, 400

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM tbl_clientes WHERE id = %s", (cliente_id,))
            cliente_atual = cursor.fetchone()

            if not cliente_atual:
                return {"erro": "cliente não encontrado!"}, 404

            sql = "UPDATE tbl_clientes SET nome = %s, email = %s, cpf = %s, senha = %s WHERE id = %s"
            values = tuple(dado_cliente[campo] for campo in campos_obrigatorios) + (cliente_id,)

            cursor.execute(sql, values)
            conn.commit()

            return {"mensagem": "cliente atualizado com sucesso!"}, 200

    except Error as err:
        return {"erro": f"Erro ao atualizar cliente: {err}"}, 500
    finally:
        conn.close()

@app.route('/clientes/<int:cliente_id>', methods=['DELETE'])
def delete_cliente(cliente_id):
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    sql_remove = "DELETE FROM tbl_clientes WHERE id = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tbl_clientes WHERE id = %s", (cliente_id,))
            if cursor.fetchone():
                cursor.execute(sql_remove, (cliente_id,))
                conn.commit()
                return {"mensagem": "cliente removido com sucesso"}, 200
            return {"erro": "cliente não encontrado"}, 404
    except Error as err:
        return {"erro": f"Erro ao buscar cliente: {err}"}, 500
    finally:
        conn.close()
    
@app.route('/produtos', methods=['POST'])
def produtos():

    # conectar colm a base
    conn = connect_db()
    produto_id = None

    if conn is None:
        resp = {"erro": "Erro ao conectar com o banco de dados"}
        return resp, 500
    
    dado_produto = request.json
    cursor = conn.cursor(dictionary=True)
    sql = "INSERT INTO tbl_produtos (nome, descrição, preco, qtd_em_estoque, fornecedor_id, custo_no_fornecedor) VALUES (%s, %s, %s, %s, %s,%s)"
    values = (dado_produto['nome'], dado_produto['descrição'], dado_produto['preco'], dado_produto['qtd_em_estoque'], dado_produto['fornecedor_id'], dado_produto['custo_no_fornecedor'])
    cursor.execute(sql, values)
    conn.commit()

    produto_id = cursor.lastrowid
    resp = "produto cadastrado com sucesso"

    cursor.close()
    conn.close()

    return resp, 201

@app.route('/produtos/<int:id>', methods=['GET'])
def procurar_produtos(id):
    """Busca um produto específico na tabela tbl_produtos pelo seu ID."""
    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor(dictionary=True)  # Adicionei dictionary=True para o retorno ser um dicionário
        sql = "SELECT * FROM tbl_produtos WHERE id = %s"  # Comando SQL para buscar um produto pelo ID

        try:
            # Executa o comando SQL com o ID fornecido
            cursor.execute(sql, (id,))
            # Recupera o resultado da consulta
            produto = cursor.fetchone()

            # Verifica se o produto foi encontrado e retorna os detalhes como JSON
            if produto:
                resp = {"id": produto['id'], "nome": produto['nome'], "descrição": produto['descrição'], "preco": produto['preco'],"qtd_em_estoque": produto['qtd_em_estoque'],"fornecedor_id": produto['fornecedor_id'],"custo_no_fornecedor":produto['custo_no_fornecedor']}
                return resp, 200  # Retorna o produto encontrado e o código de status 200 (OK)
            else:
                return {"erro": "produto não encontrado"}, 404  # Retorna uma mensagem de erro se não encontrar o produto
        except Error as err:
            # Em caso de erro na busca, retorna uma mensagem de erro
            return {"erro": f"Erro ao buscar produto: {err}"}, 500
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
    else:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

@app.route('/produtos', methods=['GET'])
def listar_produto():
    """Busca e exibe todos os produtos da tabela tbl_produtos."""
    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor(dictionary=True)  # Cria um cursor para executar comandos SQL e retorna resultados como dicionários
        sql = "SELECT * FROM tbl_produtos"  # Comando SQL para selecionar todos os produtos

        try:
            cursor.execute(sql)  # Executa o comando SQL sem parâmetros
            produtos = cursor.fetchall()  # Recupera todos os resultados da consulta

            # Verifica se encontrou produtos e retorna a lista
            if produtos:
                return {"produtos": produtos}, 200  # Retorna a lista de produtos como JSON
            else:
                return {"erro": "Nenhum produto encontrado"}, 404  # Retorna uma mensagem de erro se não encontrar produtos
        except Error as err:
            # Em caso de erro na busca, retorna uma mensagem de erro
            return {"erro": f"Erro ao buscar produtos: {err}"}, 500
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
    else:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

@app.route('/produtos/<int:produto_id>', methods=['PUT'])
def atualizar_produto(produto_id):
    """Atualiza os dados de um produto existente na tabela tbl_produtos."""
    conn = connect_db()  # Conecta ao banco de dados
    if conn:
        cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
        dado_produto = request.json  # Obtém os dados enviados no corpo da requisição

        # Verifica se os dados 'nome' e 'ano' estão no JSON recebido
        if 'nome' not in dado_produto or 'descrição' not in dado_produto or 'preco' not in dado_produto or 'qtd_em_estoque' not in dado_produto or 'fornecedor_id' not in dado_produto or 'custo_no_fornecedor' not in dado_produto:
            return {"erro": "Dados inválidos, verifique se os dados necessários foram fornecidos"}, 400

        sql = "UPDATE tbl_produtos SET nome = %s, descrição = %s, preco = %s, qtd_em_estoque = %s, fornecedor_id = %s, custo_no_fornecedor = %s WHERE id = %s"  # Comando SQL para atualizar o produto
        values = (dado_produto['nome'], dado_produto['descrição'], dado_produto['preco'], dado_produto['qtd_em_estoque'], dado_produto['fornecedor_id'], dado_produto['custo_no_fornecedor'], produto_id)  # Dados a serem atualizados

        try:
            # Executa o comando SQL com os valores fornecidos
            cursor.execute(sql, values)
            # Confirma a transação no banco de dados
            conn.commit()

            # Verifica se alguma linha foi afetada (atualizada)
            if cursor.rowcount > 0:
                return {"mensagem": "produto atualizado com sucesso!"}, 200
            else:
                return {"erro": "produto não encontrado!"}, 404
        except Error as err:
            # Em caso de erro na atualização, retorna a mensagem de erro
            return {"erro": f"Erro ao atualizar produto: {err}"}, 500
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
    else:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500
    
@app.route('/produtos/<int:produto_id>', methods=['DELETE'])
def delete_produto(produto_id):
    """Remove um usuário da tabela tbl_produtos e suas referências em outras tabelas."""    
    conn = connect_db()  # Conecta ao banco de dados

    if conn:
        cursor = conn.cursor(dictionary=True)  # Adiciona dictionary=True para retorno como dicionário

        # Comando SQL para buscar um usuário pelo ID
        sql_select = "SELECT * FROM tbl_produtos WHERE id = %s"
        # Comando SQL para remover o usuário
        sql_remove_produto = "DELETE FROM tbl_produtos WHERE id = %s"

        try:
            # Executa o comando SQL com o ID fornecido
            cursor.execute(sql_select, (produto_id,))
            produto = cursor.fetchone()

            # Verifica se o usuário foi encontrado
            if produto:
                # Remove o usuário
                cursor.execute(sql_remove_produto, (produto_id,))
                conn.commit()

                resp = {"mensagem": "produto removido com sucesso"}
                return resp, 200  # Retorna mensagem de sucesso e o código de status 200 (OK)
            else:
                return {"erro": "produto não encontrado"}, 404  # Retorna mensagem de erro se não encontrar o usuário
        except Error as err:
            # Em caso de erro, retorna uma mensagem de erro
            return {"erro": f"Erro ao buscar produto: {err}"}, 500
        finally:
            # Fecha o cursor e a conexão para liberar recursos
            cursor.close()
            conn.close()
    else:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    
@app.route('/carrinhos', methods=['POST'])
def carrinhos():
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    dado_carrinho = request.json
    if 'produto_id' not in dado_carrinho or 'quantidade' not in dado_carrinho or 'cliente_id' not in dado_carrinho:
        return {"erro": "Dados inválidos"}, 400

    # Verificar a quantidade em estoque
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT qtd_em_estoque FROM tbl_produtos WHERE id = %s", (dado_carrinho['produto_id'],))
            produto = cursor.fetchone()

            if not produto:
                return {"erro": "Produto não encontrado"}, 404

            qtd_em_estoque = produto['qtd_em_estoque']  # Altere 'qtd_em_estoque' se necessário
            if dado_carrinho['quantidade'] > qtd_em_estoque:
                return {"erro": "Quantidade solicitada excede o qtd_em_estoque disponível"}, 400

            # Inserir no carrinho
            sql = "INSERT INTO tbl_carrinhos (produto_id, quantidade, cliente_id) VALUES (%s, %s, %s)"
            values = (dado_carrinho['produto_id'], dado_carrinho['quantidade'], dado_carrinho['cliente_id'])
            cursor.execute(sql, values)

            # Atualizar o qtd_em_estoque do produto
            novo_qtd_em_estoque = qtd_em_estoque - dado_carrinho['quantidade']
            cursor.execute("UPDATE tbl_produtos SET qtd_em_estoque = %s WHERE id = %s", (novo_qtd_em_estoque, dado_carrinho['produto_id']))

            conn.commit()
            return {"mensagem": "Carrinho cadastrado com sucesso"}, 201

    except Error as err:
        return {"erro": f"Erro ao processar o carrinho: {err}"}, 500
    finally:
        conn.close()


@app.route('/carrinhos/<int:id>', methods=['GET'])
def procurar_carrinhos(id):
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    sql = "SELECT * FROM tbl_carrinhos WHERE id = %s"
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, (id,))
            carrinho = cursor.fetchone()
            if carrinho:
                return carrinho, 200
            return {"erro": "carrinho não encontrado"}, 404
    except Error as err:
        return {"erro": f"Erro ao buscar carrinho: {err}"}, 500
    finally:
        conn.close()

@app.route('/carrinhos', methods=['GET'])
def listar_carrinhos():
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    filtro_produto_id = request.args.get('produto_id')
    ordenar_por = request.args.get('ordenar_por', 'id')
    ordem = request.args.get('ordem', 'asc')

    sql = "SELECT * FROM tbl_carrinhos"
    params = []

    if filtro_produto_id:
        sql += " WHERE produto_id LIKE %s"
        params.append(f"%{filtro_produto_id}%")

    if ordenar_por not in ['id', 'produto_id', 'quantidade']:
        ordenar_por = 'id'
    if ordem not in ['asc', 'desc']:
        ordem = 'asc'

    sql += f" ORDER BY {ordenar_por} {ordem}"

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, params)
            carrinhos = cursor.fetchall()
            if carrinhos:
                return {"carrinhos": carrinhos}, 200
            return {"erro": "Nenhum carrinho encontrado"}, 404
    except Error as err:
        return {"erro": f"Erro ao buscar carrinhos: {err}"}, 500
    finally:
        conn.close()


@app.route('/carrinhos/<int:carrinho_id>', methods=['PUT'])
def atualizar_carrinho(carrinho_id):
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    dado_carrinho = request.json
    if 'produto_id' not in dado_carrinho or 'quantidade' not in dado_carrinho:
        return {"erro": "Dados inválidos"}, 400

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM tbl_carrinhos WHERE id = %s", (carrinho_id,))
            carrinho_atual = cursor.fetchone()

            if not carrinho_atual:
                return {"erro": "carrinho não encontrado!"}, 404

            sql = "UPDATE tbl_carrinhos SET produto_id = %s, quantidade = %s WHERE id = %s"
            values = (dado_carrinho['produto_id'], dado_carrinho['quantidade'], carrinho_id)

            cursor.execute(sql, values)
            conn.commit()

            return {"mensagem": "carrinho atualizado com sucesso!"}, 200

    except Error as err:
        return {"erro": f"Erro ao atualizar carrinho: {err}"}, 500
    finally:
        conn.close()

@app.route('/carrinhos/<int:carrinho_id>', methods=['DELETE'])
def delete_carrinho(carrinho_id):
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    sql_remove = "DELETE FROM tbl_carrinhos WHERE id = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tbl_carrinhos WHERE id = %s", (carrinho_id,))
            if cursor.fetchone():
                cursor.execute(sql_remove, (carrinho_id,))
                conn.commit()
                return {"mensagem": "carrinho removido com sucesso"}, 200
            return {"erro": "carrinho não encontrado"}, 404
    except Error as err:
        return {"erro": f"Erro ao buscar carrinho: {err}"}, 500
    finally:
        conn.close()

@app.route('/carrinhos/cliente/<int:cliente_id>', methods=['GET'])
def listar_carrinhos_cliente(cliente_id):
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    sql = "SELECT * FROM tbl_carrinhos WHERE cliente_id = %s"
    
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, (cliente_id,))
            carrinho = cursor.fetchall()
            if carrinho:
                return {"carrinho": carrinho}, 200
            return {"erro": "Nenhum carrinho encontrado para este cliente"}, 404
    except Error as err:
        return {"erro": f"Erro ao buscar carrinho do cliente: {err}"}, 500
    finally:
        conn.close()

@app.route('/pedidos', methods=['POST'])
def pedidos():
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    dado_pedido = request.json
    campos_obrigatorios = ['cliente_id', 'carrinho_id', 'data_hora', 'status']

    for campo in campos_obrigatorios:
        if campo not in dado_pedido:
            return {"erro": f"Campo '{campo}' é obrigatório."}, 400
        
    sql = "INSERT INTO tbl_pedidos (cliente_id, carrinho_id, data_hora, status) VALUES (%s, %s, %s, %s)"
    values = tuple(dado_pedido[campo] for campo in campos_obrigatorios)

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, values)
            conn.commit()
            return {"mensagem": "pedido cadastrado com sucesso"}, 201
    except Error as err:
        return {"erro": f"Erro ao cadastrar pedido: {err}"}, 500
    finally:
        conn.close()

@app.route('/pedidos/<int:id>', methods=['GET'])
def procurar_pedidos(id):
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    sql = "SELECT * FROM tbl_pedidos WHERE id = %s"
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, (id,))
            pedido = cursor.fetchone()
            if pedido:
                return pedido, 200
            return {"erro": "pedido não encontrado"}, 404
    except Error as err:
        return {"erro": f"Erro ao buscar pedido: {err}"}, 500
    finally:
        conn.close()

@app.route('/pedidos', methods=['GET'])
def listar_pedidos():
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    filtro_cliente_id = request.args.get('cliente_id')
    filtro_carrinho_id = request.args.get('carrinho_id')
    ordenar_por = request.args.get('ordenar_por', 'id')
    ordem = request.args.get('ordem', 'asc')

    sql = "SELECT * FROM tbl_pedidos"
    params = []

    if filtro_cliente_id:
        sql += " WHERE nome LIKE %s"
        params.append(f"%{filtro_cliente_id}%")

    if filtro_carrinho_id:
        sql += " WHERE nome LIKE %s"
        params.append(f"%{filtro_carrinho_id}%")

    if ordenar_por not in ['id', 'cliente_id', 'carrinho_id', 'data_hora', 'status']:
        ordenar_por = 'id'
    if ordem not in ['asc', 'desc']:
        ordem = 'asc'

    sql += f" ORDER BY {ordenar_por} {ordem}"

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, params)
            pedidos = cursor.fetchall()
            if pedidos:
                return {"pedidos": pedidos}, 200
            return {"erro": "Nenhum pedido encontrado"}, 404
    except Error as err:
        return {"erro": f"Erro ao buscar pedidos: {err}"}, 500
    finally:
        conn.close()

@app.route('/pedidos/cliente/<int:cliente_id>', methods=['GET'])
def listar_pedidos_cliente(cliente_id):
    conn = connect_db()
    if not conn:
        return {"erro": "Erro ao conectar com o banco de dados"}, 500

    sql = "SELECT * FROM tbl_pedidos WHERE cliente_id = %s"
    
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, (cliente_id,))
            pedidos = cursor.fetchall()
            if pedidos:
                return {"pedidos": pedidos}, 200
            return {"erro": "Nenhum pedido encontrado para este cliente"}, 404
    except Error as err:
        return {"erro": f"Erro ao buscar pedidos do cliente: {err}"}, 500
    finally:
        conn.close()

if __name__ == '__main__':
      
    app.run(debug=True)