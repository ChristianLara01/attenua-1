from flask import Flask, request, jsonify
import mercadopago
import paho.mqtt.client as mqtt


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
    received_secret = request.headers.get("Authorization")
    
    if received_secret != f"Bearer {SECRETO_MERCADO_PAGO}":
        return 'Unauthorized', 401  # Não autorizado
    
    # Get the JSON data from the incoming POST request
    webhook_data = request.json

    # Print the JSON data to the terminal
    print("Pagamento recebido de Mercado Pago:")
    print(webhook_data)
    send_mqtt_message("Pagou")

    # Optionally, you can process the webhook data here as needed

    return 'OK', 200  # Return a response to acknowledge receipt

if __name__ == '__main__':
    app.run(debug=True)
