from flask import Flask, request, jsonify
import mercadopago
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

@app.route('/')
def hello_world():
    return 'Hello, Attenua!'

@app.route('/webhook', methods=['POST'])
def mercado_pago_webhook():
    # Get the JSON data from the incoming POST request
    webhook_data = request.json

    # Print the JSON data to the terminal
    print("Pagamento recebido de Mercado Pago:")
    print(webhook_data)
    send_mqtt_message("Pagou"):

    # Optionally, you can process the webhook data here as needed

    return 'OK', 200  # Return a response to acknowledge receipt

if __name__ == '__main__':
    app.run()
