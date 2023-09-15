from flask import Flask, request, jsonify
import mercadopago

app = Flask(__name__)

# Configure suas credenciais de produção (Access Token)
MERCADO_PAGO_ACCESS_TOKEN = 'APP_USR-698417925527845-042300-824e07ad45574df479088eebe0fad53c-726883686'

# Inicialize o objeto de pagamento do Mercado Pago
mp = mercadopago.MP(MERCADO_PAGO_ACCESS_TOKEN)

@app.route('/')
def hello_world():
    return 'Hello, Attenua!'

# Rota para receber a webhook do Mercado Pago
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        request_data = request.json
        
        # Use a biblioteca mercadopago para verificar a autenticidade da webhook
        if mp.validate_webhook(request.data):
            # A webhook é autêntica, você pode processar os dados do pagamento aqui
            payment_data = request_data.get('data')
            payment_status = payment_data.get('status')
            payment_id = payment_data.get('id')
            
            # Execute o código de acordo com o status do pagamento (aprovado, pendente, etc.)
            if payment_status == 'approved':
                # O pagamento foi aprovado, faça o que for necessário
                # (por exemplo, atualize um banco de dados, envie um e-mail de confirmação, etc.)
                pass
            elif payment_status == 'pending':
                # O pagamento está pendente, faça o que for necessário
                pass
            # Outros casos podem ser tratados aqui
            
            # Responda com sucesso para confirmar a recepção da webhook
            return jsonify({'status': 'success'}), 200
        else:
            # As credenciais não coincidem, não processe a webhook
            return jsonify({'status': 'unauthorized'}), 401
    except Exception as e:
        # Lida com erros
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
