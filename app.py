from flask import Flask, render_template, request, redirect, url_for, jsonify
import pymongo
from bson import json_util
import secrets
from datetime import datetime
import pytz
import paho.mqtt.client as mqtt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuration
MONGO_URI = "mongodb+srv://riotchristian04:atualle1@cluster0.zwuw5.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MQTT_BROKER_HOST = "mqtt.eclipseprojects.io"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "estado"

# Initialize Flask app
app = Flask(__name__)

# --- Utility functions ---

def send_mqtt_message(payload):
    client = mqtt.Client()
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
    client.publish(MQTT_TOPIC, payload)
    client.disconnect()


def sendEmail(reserv):
    sender_email = "attenua@atualle.com.br"
    recipients = [sender_email, reserv['id_usuario']]
    password = "Wwck$22xO4O#8V"
    subject = "Reserva realizada com sucesso - ATTENUA CABINES ACÚSTICAS"
    message = f"""
    <html>
    <body>
      <h1>Reserva Confirmada</h1>
      <p>Cabine: {reserv['cabin_id']}</p>
      <p>Dia: {reserv['dia']}</p>
      <p>Hora: {reserv['hora']}</p>
      <p>Código de acesso: {reserv['senha_unica']}</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'html'))

    server = smtplib.SMTP_SSL("server51.srvlinux.info", 465)
    server.login(sender_email, password)
    server.sendmail(sender_email, recipients, msg.as_string())
    server.quit()


def mongo_connect():
    client = pymongo.MongoClient(MONGO_URI)
    try:
        client.admin.command('ping')
    except Exception as e:
        print("MongoDB connection error:", e)
    return client


def carregar():
    client = mongo_connect()
    db = client.attenua
    reservas = db.reservas
    return list(reservas.find({}))


def verificar_agendamento(agendamento):
    tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz)
    today_str = now.strftime('%d-%m-%Y')
    if today_str == agendamento['dia']:
        hour_str = now.strftime('%H')
        return hour_str == agendamento['hora'][:2]
    return False


def adicionar_agendamento(cabin_id, novo_agendamento):
    client = mongo_connect()
    db = client.attenua
    reservas = db.reservas

    # Generate unique code
    code = secrets.token_hex(3)
    while reservas.find_one({"agendamentos.senha_unica": code}):
        code = secrets.token_hex(3)
    novo_agendamento['senha_unica'] = code
    novo_agendamento['cabin_id'] = cabin_id

    # Persist
    result = reservas.update_one(
        {"id": cabin_id},
        {"$push": {"agendamentos": novo_agendamento}}
    )

    if result.modified_count:
        sendEmail(novo_agendamento)
        return code
    else:
        return None

# --- Routes ---

@app.route('/data/cabins')
def get_cabins_data():
    try:
        data = carregar()
        return jsonify(json.loads(json_util.dumps(data)))
    except Exception as e:
        return str(e), 500


@app.route('/')
def catalog():
    cabins = carregar()
    return render_template('catalog.html', cabins=cabins)


@app.route('/reserve/<int:cabin_id>/<dia>/<hora>')
def show_reservation_form(cabin_id, dia, hora):
    return render_template('reservation.html', cabin_id=cabin_id, dia=dia, hora=hora)


@app.route('/reserve', methods=['POST'])
def handle_reservation():
    cabin_id = int(request.form['cabin_id'])
    dia = request.form['dia']
    hora = request.form['hora']
    first = request.form['first_name']
    last = request.form['last_name']
    email = request.form['email']

    novo = {
        'dia': dia,
        'hora': hora,
        'qtde_horas': 1,
        'id_usuario': email,
        'first_name': first,
        'last_name': last
    }

    code = adicionar_agendamento(cabin_id, novo)
    if code:
        return render_template('reservation_success.html', cabin_id=cabin_id, dia=dia, hora=hora, senha=code)
    else:
        return "Erro ao reservar", 500


@app.route('/verificar_senha/<senha>')
def verificar_senha(senha):
    doc = None
    client = mongo_connect()
    db = client.attenua
    reservas = db.reservas
    doc = reservas.find_one({"agendamentos.senha_unica": senha})
    if doc:
        ag = next((a for a in doc['agendamentos'] if a['senha_unica'] == senha), None)
        if ag and verificar_agendamento(ag):
            send_mqtt_message(doc['id'])
            return "Liberado"
    return "Inválido", 404

@app.route('/available/<dia_iso>/<slot>')
def available(dia_iso, slot):
    """
    Recebe dia no formato yyyy-mm-dd e slot como “HH:MM”.
    Reformatamos para dd-mm-yyyy (como está no Mongo) e filtramos.
    """
    # Converte “2025-07-16” em “16-07-2025”
    ano, mes, dia = dia_iso.split('-')
    dia_fmt = f"{dia}-{mes}-{ano}"

    client = mongo_connect()
    db = client.attenua
    reservas = db.reservas.find({})

    livres = []
    for cabine in reservas:
        # verifica se já existe agendamento com mesmo dia e hora
        ocupada = any(
            ag['dia'] == dia_fmt and ag['hora'] == slot
            for ag in cabine.get('agendamentos', [])
        )
        if not ocupada:
            # remove campos internos antes de enviar
            cabine.pop('_id', None)
            cabine.pop('agendamentos', None)
            livres.append(cabine)

    return jsonify(livres)

if __name__ == '__main__':
    app.run(debug=True)
