from flask import Flask, request, jsonify
import mercadopago

app = Flask(__name__)

MERCADO_PAGO_ACCESS_TOKEN = 'APP_USR-698417925527845-042300-824e07ad45574df479088eebe0fad53c-726883686'

sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)

@app.route('/')
def hello_world():
    return 'Hello, Attenua!'

# Rota para receber a webhook do Mercado Pago
@app.route('/webhook', methods=['POST'])
def webhook():

    
    request_data = request.json
    print(request_data)
    try:
        
        payment_data = request_data.get('data')
        payment_status = payment_data.get('status')
        payment_id = payment_data.get('id')
        
        if payment_status == 'approved':
            pass
        elif payment_status == 'pending':
            pass
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
