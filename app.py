from flask import Flask, request, jsonify, render_template
import requests
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

app = Flask(__name__)

# Sua chave da API do Mercado Pago
MERCADO_PAGO_ACCESS_TOKEN = 'APP_USR-698417925527845-042300-824e07ad45574df479088eebe0fad53c-726883686'
# Sua chave da API do Google Maps
api_key = "AIzaSyCuzKLRuerHBHR9ArHvJm5HzpD7E_Ap170"

@app.route('/produtos')
def produtos():
    return render_template('produtos.html')
    
@app.route('/')
def home():
    return 'hi'
    
@app.route('/home/<json_data>', methods=['POST', 'GET'])
def homedata(json_data):
    try:
        data = jsonify(eval(json_data))
        print(json_data)
        return render_template(jsonify({'response': data}))
    except Exception as e:
        return render_template(jsonify({'error': 'Erro ao processar JSON'}), 400)

@app.route('/mapa')
def mapa():
    produto_selecionado = request.args.get('produto')
    # Lógica para determinar o ponto no mapa com base no produto selecionado
    # Você pode usar um dicionário ou outra estrutura de dados para mapear produtos para coordenadas

    # Suponha que você tenha um dicionário que mapeie produtos para coordenadas
    coordenadas = {
        'produto1': {"lat": -25.503600050960685, "lng": -49.16696527260166},
        'produto2': {"lat": ...},
        'produto3': {"lat": ...},
        'produto4': {"lat": ...},
        'produto5': {"lat": ...},
    }

    ponto = coordenadas.get(produto_selecionado)

    if ponto:
        return render_template('mapa.html', ponto=ponto, api_key=api_key)
    else:
        return "Produto não encontrado", 404

# Rota para receber a webhook do Mercado Pago
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        request_data = request.json
        print(request_data)
        
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
            payment_id = payment_data.get('id')
            if(payment_data.get('collection', {}).get('external_reference') == 'ca1' and payment_data.get('collection', {}).get('status') == 'approved'):
                send_mqtt_message("1")
            print(payment_data)
            
            if payment_status == 'approved':
                print("\n\naprovou\n\n")
                pass
            elif payment_status == 'pending':
                print("\n\naguardando\n\n")
                pass
            
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Resource URL not found'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
