from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
import requests
import json
import datetime
import os
import mercadopago
import secrets

MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-698417925527845-042300-824e07ad45574df479088eebe0fad53c-726883686"
# Configure sua chave de acesso ao Mercado Pago
mp = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)

app = Flask(__name__)

# Caminho para o arquivo JSON de cabines
cabins_file = os.path.join(os.path.dirname(__file__), 'data', 'cabins.json')

# Função para carregar os dados do JSON
def load_cabins():
    with open(cabins_file, 'r') as file:
        cabins = json.load(file)
    return cabins

@app.route('/data/cabins.json')
def get_cabins_data():
    try:
        # Carregue o conteúdo do arquivo JSON
        with open('data/cabins.json', 'r') as json_file:
            data = json_file.read()
        # Transforme o conteúdo JSON em um objeto Python (dicionário)
        data_dict = json.loads(data)
        return jsonify(data_dict)
    except FileNotFoundError:
        # Se o arquivo não for encontrado, retorne uma resposta 404 (Not Found)
        return "Arquivo não encontrado", 404
    except Exception as e:
        # Se ocorrer um erro inesperado, retorne uma resposta 500 (Internal Server Error)
        return str(e), 500
    
@app.route('/')
def catalog():
    cabins = load_cabins()
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

    add_appointment(cabinId, clickedHour)

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
                "unit_price": produto_preco

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

def add_appointment(cabinId, clickedHour):
    # Parse the JSON data
    cabins_data = load_cabins()

    # Find the cabin with the given ID
    for cabin in cabins_data:
        if str(cabin['id']) == cabinId:
            # Extract the date and hour from clickedHour
            date, hour = clickedHour.split(' ')
            password = secrets.token_hex(3)

            # Create a new appointment dictionary
            new_appointment = {
                'dia': date,
                'hora': hour,
                'qtde_horas': 1,  # You can set the duration as needed
                'id_usuario': 1,  # Replace with the user ID
                'senha_unica': password,  # Replace with a generated password
                'pagamento': False  # Replace with a generated password
            }

            # Add the new appointment to the cabin's appointments
            cabin['agendamentos'].append(new_appointment)

            # Save the updated JSON data
            save_cabins_data(cabins_data)

            return 'Appointment added successfully'

    return 'Cabin not found'

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
            payment_status = payment_data.get('status')
            payment_reason = payment_data.get('reason')
            print("\n\noi\n")               
            print(payment_data)      
            print(payment_status)            
            print(payment_reason)            
            print("\n fui\n\n")            
            if payment_status == 'approved':
                if(payment_data.get('collection', {}).get('reason') == 'CABINE 1 14-10-2023 09:00'):
                    print("passou")                
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Resource URL not found'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

if __name__ == '__main__':
    app.run(debug=True)
