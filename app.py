from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def mercado_pago_webhook():
    # Get the JSON data from the incoming POST request
    webhook_data = request.json

    # Print the JSON data to the terminal
    print("Received POST request from Mercado Pago:")
    print(webhook_data)

    # Optionally, you can process the webhook data here as needed

    return 'OK', 200  # Return a response to acknowledge receipt

if __name__ == '__main__':
    app.run()
