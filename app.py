from flask import Flask, request, jsonify
import mercadopago
import paho.mqtt.client as mqtt

app = Flask(__name__)

# Replace with your actual Mercado Pago access tokens
PIX_ACCESS_TOKEN = "TEST-3a597b67-449d-487c-a857-934adc3e5539"
CARD_ACCESS_TOKEN = "TEST-698417925527845-042300-1fdc5423d40616fc01f8290f4ae0edcf-726883686"

# Configure Mercado Pago SDKs
pix_sdk = mercadopago.SDK(PIX_ACCESS_TOKEN)
card_sdk = mercadopago.SDK(CARD_ACCESS_TOKEN)

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

# Pix Payment Endpoint
@app.route('/pix-payment', methods=['POST'])
def pix_payment():
    # Replace with actual user-submitted or dynamically obtained data
    transaction_amount = float(request.json.get("transaction_amount"))
    product_description = request.json.get("description")
    payer_email = request.json.get("payer_email")
    payer_first_name = request.json.get("payer_first_name")
    payer_last_name = request.json.get("payer_last_name")
    cpf_number = request.json.get("cpf_number")
    zip_code = request.json.get("zip_code")
    street_name = request.json.get("street_name")
    street_number = request.json.get("street_number")
    neighborhood = request.json.get("neighborhood")
    city = request.json.get("city")
    state = request.json.get("state")

    payment_data = {
        "transaction_amount": transaction_amount,
        "description": product_description,
        "payment_method_id": "pix",
        "payer": {
            "email": payer_email,
            "first_name": payer_first_name,
            "last_name": payer_last_name,
            "identification": {
                "type": "CPF",
                "number": cpf_number
            },
            "address": {
                "zip_code": zip_code,
                "street_name": street_name,
                "street_number": street_number,
                "neighborhood": neighborhood,
                "city": city,
                "federal_unit": state
            }
        }
    }

    payment_response = pix_sdk.payment().create(payment_data)
    payment = payment_response["response"]

    # Send the payment value to MQTT
    send_mqtt_message(f"Payment completed: {payment['transaction_amount']}")

    return jsonify({"message": "Pix payment completed", "payment_info": payment})

# Credit/Debit Card Payment Endpoint
@app.route('/card-payment', methods=['POST'])
def card_payment():
    # Replace with actual user-submitted or dynamically obtained data
    transaction_amount = float(request.json.get("transaction_amount"))
    token = request.json.get("token")
    product_description = request.json.get("description")
    installments = int(request.json.get("installments"))
    payer_email = request.json.get("payer_email")
    identification_type = request.json.get("identification_type")
    identification_number = request.json.get("identification_number")
    cardholder_name = request.json.get("cardholder_name")

    payment_data = {
        "transaction_amount": transaction_amount,
        "token": token,
        "description": product_description,
        "installments": installments,
        "payment_method_id": "credit_card",  # Replace with the actual payment method
        "payer": {
            "email": payer_email,
            "identification": {
                "type": identification_type,
                "number": identification_number
            },
            "first_name": cardholder_name
        }
    }

    payment_response = card_sdk.payment().create(payment_data)
    payment = payment_response["response"]

    # Send the payment value to MQTT
    send_mqtt_message(f"Payment completed: {payment['transaction_amount']}")

    return jsonify({"message": "Card payment completed", "payment_info": payment})

if __name__ == '__main__':
    app.run()
