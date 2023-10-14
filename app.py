from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
import requests
import json
import datetime
import os
import mercadopago
import secrets
import base64
import pymongo
from bson import json_util  # Importe o json_util do módulo bson

token = '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'
owner = 'ChristianLara01'
repo = 'attenua-1'

MONGO_URI = "mongodb+srv://attenua:agendamento@attenua.qypnplu.mongodb.net/"
MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-698417925527845-042300-824e07ad45574df479088eebe0fad53c-726883686"
# Configure sua chave de acesso ao Mercado Pago
mp = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)

#Mongo configurações
def mongo_connect():
    client = pymongo.MongoClient(MONGO_URI)
    try:
        client.admin.command('ping')
        print("Conectado ao MongoDB!")
    except Exception as e:
        print(e)
    return client

def carregar():
    client = mongo_connect()
    db = client.attenua
    reservas = db.reservas
    # Use the find method to retrieve data from the collection
    cursor = reservas.find({})
    # Convert the cursor to a list of JSON objects
    data = [doc for doc in cursor]
    return data

def salvar():
    client = mongo_connect()
    db = client.attenua
    reservas = db.reservas
    # Use the find method to retrieve data from the collection
    cursor = reservas.find({})
    # Convert the cursor to a list of JSON objects
    data = [doc for doc in cursor]
    return data

app = Flask(__name__)

@app.route('/data/cabins.json')
def get_cabins_data():
    try:
        cabins = carregar()
        # Convertemos os ObjectId para strings para torná-los serializáveis
        cabins_json = json.loads(json_util.dumps(cabins))
        return jsonify(cabins_json)
    except FileNotFoundError:
        # Se o arquivo não for encontrado, retorne uma resposta 404 (Not Found)
        return "Arquivo não encontrado", 404
    except Exception as e:
        # Se ocorrer um erro inesperado, retorne uma resposta 500 (Internal Server Error)
        return str(e), 500
    
@app.route('/')
def catalog():
    cabins = carregar()
    return render_template('catalog.html', cabins=cabins)

@app.route('/reserve/<int:cabin_id>')
def reserve(cabin_id):
    return render_template('reservation.html', cabin_id=cabin_id)

@app.route('/agendar/<dia>')
def agendar(dia):
    # Aqui você pode usar o parâmetro "dia" para exibi-lo na tela ou realizar outras ações necessárias
    return f'Dia selecionado: {dia}'


@app.route('/<cabinId>/<clickedHour>', methods=['GET'])
def pagamento(cabinId, clickedHour):

    #add_appointment(cabinId, clickedHour, False)

    # Informações do produto
    print(cabinId)
    print(clickedHour)
    produto_nome = "CABINE " +  cabinId + " " + clickedHour
    produto_preco = 0.02

    # Crie uma preferência de pagamento
    preference_data = {
        "items": [
            {
                "title": produto_nome,
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": produto_preco,
                "codigo": "xxxxxx"

            }
        ],
        "back_urls": {
            "success": "http://seusite.com/sucesso",
            "failure": "http://seusite.com/erro",
            "pending": "http://seusite.com/pendente"
        }
    }
    preference = mp.preference().create(preference_data)
    # Redirecione o usuário para a página de pagamento do Mercado Pago
    return redirect(preference['response']['init_point'])

# Save the JSON data back to the file
def save_cabins_data(cabins_data):
    with open('data/cabins.json', 'w') as file:
        json.dump(cabins_data, file, indent=4)

# Rota para receber a webhook do Mercado Pago
@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    try:
        request_data = request.json
        
        # Extract the resource URL from the request data
        resource_url = request_data.get('resource')
        
        if resource_url:
            # Configure os cabeçalhos para incluir o token de acesso
            headers = {
                'Authorization': f'Bearer {MERCADO_PAGO_ACCESS_TOKEN}'
            }
            
            # Retrieve the payment information from the resource URL
            response = requests.get(resource_url, headers=headers)
            payment_data = response.json()
            payment_status = payment_data.get('collection', {}).get('status')
            payment_reason = payment_data.get('collection', {}).get('reason')

            # Split the string by spaces
            parts = payment_reason.split()

            # Extract the cabinId and clickedHour
            cabinId = parts[1]  # "CABINE 1" is the second part (index 1)
            clickedHour = parts[2] + " " + parts[3]  # "14-10-2023 09:00" is parts 2 and 3

            print(payment_data)                      
            if payment_status == 'approved':
                if(payment_data.get('collection', {}).get('reason') == 'CABINE 1 14-10-2023 09:00'):
                    print("passou")                      
                    #add_appointment(cabinId, clickedHour, True)              
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Resource URL not found'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

if __name__ == '__main__':
    app.run(debug=True)
