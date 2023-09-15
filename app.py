from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

MERCADO_PAGO_ACCESS_TOKEN = 'APP_USR-698417925527845-042300-824e07ad45574df479088eebe0fad53c-726883686'

@app.route('/')
def hello_world():
    return 'Hello, Attenua!'

# Rota para receber a webhook do Mercado Pago
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        request_data = request.json
        print(request_data)
        
        # Extract the resource URL from the request data
        resource_url = request_data.get('resource')
        
        if resource_url:
            # Retrieve the payment information from the resource URL
            response = requests.get(resource_url)
            payment_data = response.json()
            
            payment_status = payment_data.get('status')
            payment_id = payment_data.get('id')
            transaction_amount = payment_data.get('transaction_amount')
            payment_method_id = payment_data.get('payment_method_id')
            payer = payment_data.get('payer')
            transaction_details = payment_data.get('transaction_details')
            
            print(f'Payment ID: {payment_id}')
            print(f'Payment Status: {payment_status}')
            print(f'Transaction Amount: {transaction_amount}')
            print(f'Payment Method ID: {payment_method_id}')
            print(f'Payer: {payer}')
            print(f'Transaction Details: {transaction_details}')
            
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Resource URL not found'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
