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
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_BROKER_HOST = "mqtt.eclipseprojects.io"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "estado"
# Function to send MQTT message

def send_mqtt_message(payload):
    client = mqtt.Client()
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
    client.publish(MQTT_TOPIC, payload)
    client.disconnect()

token = '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'
owner = 'ChristianLara01'
repo = 'attenua-1'

MONGO_URI = "mongodb+srv://attenua:agendamento@attenua.qypnplu.mongodb.net/"
MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-698417925527845-042300-824e07ad45574df479088eebe0fad53c-726883686"
# Configure sua chave de acesso ao Mercado Pago
mp = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)

def sendEmail(dia, hora, senha, recipients):
    
    # Email configuration
    sender_email = "attenua@atualle.com.br"
    password = "Wwck$22xO4O#8V"
    subject = "Reserva realizada com sucesso - ATTENUA CABINES ACÚSTICAS"
    message = f"""
        <html>
        <head>
            <style>
                /* Define the card style */
                .card {{
                    background-color: #f3f3f3;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 20px;
                    font-family: Arial, sans-serif;
                }}
                .card h1 {{
                    color: #333;
                    font-size: 24px;
                }}
                .card p {{
                    color: #666;
                    font-size: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Reserva realizada com sucesso - ATTENUA CABINES ACÚSTICAS</h1>
                <p>Sua reserva ATTENUA foi realizada com sucesso!</p>
                <p>Dia: {dia}</p>
                <p>Hora: {hora}</p>
                <p>Senha: {senha}</p>
                <p>Guarde sua senha e utilize para liberar o acesso à sua cabine no momento da utilização.</p>
                <p>Atenciosamente, ATTENUA CABINES ACÚSTICAS</p>
            </div>
        </body>
        </html>
        """

    # Create the MIME object
    msg = MIMEMultipart("alternative")
    msg['From'] = sender_email
    msg['Subject'] = subject

    # Set 'To' header with multiple recipients
    msg['To'] = ', '.join(recipients)

    # Attach the message to the MIME object
    msg.attach(MIMEText(message, 'html'))

    # Establish a connection to the SMTP server
    smtp_server = "server51.srvlinux.info"
    smtp_port = 465  # Port for SMTPS (SSL/TLS)

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)  # Use SMTP_SSL for SSL/TLS
        server.login(sender_email, password)

        # Send the email
        server.sendmail(sender_email, recipients, msg.as_string())

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        server.quit()  # Close the connection

#Mongo configurações
def mongo_connect():
    client = pymongo.MongoClient(MONGO_URI)
    try:
        client.admin.command('ping')
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

def abrir(senha_inserida):
    client = mongo_connect()
    db = client.attenua
    reservas = db.reservas

    # Use a função find com uma consulta para encontrar documentos com a senha única correspondente
    cursor = reservas.find({"agendamentos.senha_unica": senha_inserida})

    # Converta o cursor em uma lista de objetos JSON
    data = [doc for doc in cursor]
    if data or senha_inserida == "attenua":
        send_mqtt_message("1")

def adicionar_agendamento(id_cabin, novo_agendamento):
    # Connect to MongoDB
    client = mongo_connect()
    db = client.attenua
    reservas = db.reservas

    # Define the filter condition to find the document with the specified id
    filter_condition = {"id": id_cabin}

    # Define the update operation to push the new agendamento to the "agendamentos" array
    update_operation = {
        "$push": {
            "agendamentos": novo_agendamento
        }
    }

    # Update the document with the new agendamento
    result = reservas.update_one(filter_condition, update_operation)

    if result.modified_count > 0:
        return "Agendamento adicionado com sucesso."
    else:
        return "Cabin não encontrado ou agendamento não adicionado."

app = Flask(__name__)

@app.route('/data/cabins')
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


@app.route('/acessar')
def acesso():
    return render_template('acessar.html')

@app.route('/reserve/<int:cabin_id>')
def reserve(cabin_id):
    return render_template('reservation.html', cabin_id=cabin_id)

@app.route('/agendar/<dia>')
def agendar(dia):
    # Aqui você pode usar o parâmetro "dia" para exibi-lo na tela ou realizar outras ações necessárias
    return f'Dia selecionado: {dia}'


@app.route('/<cabinId>/<clickedHour>/<valor_hora>/<email>', methods=['GET'])
def pagamento(cabinId, clickedHour, valor_hora, email):

    #add_appointment(cabinId, clickedHour, False)

    # Informações do produto
    produto_nome = "CABINE " +  cabinId + " " + clickedHour + " " + email

    # Crie uma preferência de pagamento
    preference_data = {
        "items": [
            {
                "title": produto_nome,
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(valor_hora),

            }
        ],
        "back_urls": {
            "success": "http://attenua.com.br/",
            "failure": "http://attenua.com.br/",
            "pending": "http://attenua.com.br/"
        },
        "payer": {
            "email": email  # Inclui o e-mail do comprador
        },
        "payment_methods": {
            "excluded_payment_methods": [
                {"id": "bolbradesco"},  # Exclui o boleto bancário
                {"id": "bank_transfer"}  # Exclui transferência bancária
            ],
            "excluded_payment_types": [
                {"id": "atm"},  # Exclui pagamento em caixas eletrônicos
                {"id": "ticket"}  # Exclui pagamento com ticket
            ]
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
            print(payment_data)
            payment_status = payment_data.get('collection', {}).get('status')
            payment_reason = payment_data.get('collection', {}).get('reason')

            # Split the string by spaces
            parts = payment_reason.split()
            # Extract the cabinId and clickedHour
            cabinId = parts[1]  # "CABINE 1" is the second part (index 1)
            clickedHour = parts[2] + " " + parts[3]  # "14-10-2023 09:00" is parts 2 and 3
            email = parts[4]
                     
            if payment_status == 'approved':
                #if(payment_data.get('collection', {}).get('reason') == 'CABINE {cabinId} {clickedHour}'):
                # Usage example
                senha = secrets.token_hex(3)
                novo_agendamento = {
                    "dia": parts[2],
                    "hora": parts[3],
                    "qtde_horas": 1,
                    "id_usuario": 3,
                    "senha_unica": senha
                }
                resultado = adicionar_agendamento(1, novo_agendamento)
                # List of recipient email addresses
                recipients = ["attenua@atualle.com.br", email]

                # Call the function to send the email to multiple recipients
                sendEmail(parts[2], parts[3], senha, recipients)
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Resource URL not found'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/verificar_senha/<senha_inserida>', methods=['GET'])
def verificar_senha(senha_inserida):
    abrir(senha_inserida)
    return "Senha recebida no servidor"
    

if __name__ == '__main__':
    app.run(debug=True)
