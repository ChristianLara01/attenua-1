from flask import Flask, request, jsonify
import mercadopago
import paho.mqtt.client as mqtt

# Configure estas credenciais com as fornecidas pelo Mercado Pago
CLIENT_ID = "698417925527845"
CLIENT_SECRET = "sjeML9fRWV9eJbKAa3c3doRVFVDulnIL"

# Seu token secreto para autenticação
SECRETO_MERCADO_PAGO = "APP_USR-698417925527845-042300-824e07ad45574df479088eebe0fad53c-726883686"

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

@app.route('/')
def hello_world():
    return 'Hello, Attenua!'

@app.route('/webhook', methods=['POST'])
def mercado_pago_webhook():
    # Verifique a autenticação usando as credenciais do Mercado Pago
    if not verificar_autenticacao(request):
        return 'Unauthorized', 401  # Não autorizado

    # Receba e processe os dados do webhook do Mercado Pago
    data = request.json
    # Aqui, você pode acessar as informações sobre a venda, como usuário, produto, valor, etc.
    
    # Exemplo: Imprimir os dados da venda no terminal
    print("Venda recebida do Mercado Pago:")
    print(data)

    # Responda ao webhook com sucesso
    return 'OK', 200

def verificar_autenticacao(request):
    # Verifique a autenticação usando as credenciais fornecidas no cabeçalho do pedido
    client_id = request.headers.get("X-Client-ID")
    client_secret = request.headers.get("X-Client-Secret")

    return client_id == CLIENT_ID and client_secret == CLIENT_SECRET

if __name__ == '__main__':
    app.run(debug=True)
