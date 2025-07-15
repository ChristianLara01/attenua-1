from flask import Flask, render_template, jsonify, request
import pymongo
import pytz
from datetime import datetime
import secrets
import paho.mqtt.client as mqtt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

# --- Configuração ---
MONGO_URI       = "mongodb+srv://riotchristian04:atualle1@cluster0.zwuw5.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
INTERVAL_MIN    = 30    # intervalo em minutos (ajuste fácil)
HOUR_START      = 9     # horário inicial
HOUR_END        = 19    # horário final (ultima slot: HOUR_END:30)
MQTT_HOST       = "mqtt.eclipseprojects.io"
MQTT_PORT       = 1883
MQTT_TOPIC      = "estado"
EMAIL_SENDER    = "attenua@atualle.com.br"
EMAIL_PASS      = "Wwck$22xO4O#8V"
SMTP_SERVER     = "server51.srvlinux.info"
SMTP_PORT       = 465

# Conexão ao Mongo
def mongo_connect():
    client = pymongo.MongoClient(MONGO_URI)
    return client.attenua.reservas

# Página inicial
@app.route('/')
def index():
    return render_template('index.html',
                           hour_start=HOUR_START,
                           hour_end=HOUR_END,
                           interval=INTERVAL_MIN)

# API: cabines livres em um dia+slot
@app.route('/api/available/<date_iso>/<slot>')
def api_available(date_iso, slot):
    # Converte 'YYYY-MM-DD' -> 'DD-MM-YYYY'
    ano, mes, dia = date_iso.split('-')
    dia_fmt = f"{dia}-{mes}-{ano}"
    col = mongo_connect()
    livres = []
    for c in col.find():
        conflito = any(
            ag['dia'] == dia_fmt and ag['hora'] == slot
            for ag in c.get('agendamentos', [])
        )
        if not conflito:
            c.pop('_id', None)
            c.pop('agendamentos', None)
            livres.append(c)
    return jsonify(livres)

# Página de formulário de reserva
@app.route('/reserve/<int:cabin_id>/<date_iso>/<slot>')
def reserve_form(cabin_id, date_iso, slot):
    return render_template('reservation.html',
                           cabin_id=cabin_id,
                           date_iso=date_iso,
                           slot=slot)

# Processa a reserva
@app.route('/reserve', methods=['POST'])
def reserve_submit():
    cabin_id   = int(request.form['cabin_id'])
    date_iso   = request.form['date_iso']
    slot       = request.form['slot']
    first      = request.form['first_name']
    last       = request.form['last_name']
    email      = request.form['email']

    # gera data no formato 'DD-MM-YYYY'
    ano, mes, dia = date_iso.split('-')
    dia_fmt = f"{dia}-{mes}-{ano}"

    # gera código único
    code = secrets.token_hex(3)
    col = mongo_connect()
    # evita duplicação de código
    while col.find_one({"agendamentos.senha_unica": code}):
        code = secrets.token_hex(3)

    novo = {
        'dia': dia_fmt,
        'hora': slot,
        'qtde_horas': 1,
        'id_usuario': email,
        'first_name': first,
        'last_name': last,
        'senha_unica': code
    }

    # salva no Mongo
    col.update_one({'id': cabin_id}, {'$push': {'agendamentos': novo}})

    # envia e-mail de confirmação
    send_email(novo, cabin_id)

    return render_template('reservation_success.html',
                           cabin_id=cabin_id,
                           date_iso=date_iso,
                           slot=slot,
                           code=code)

# Função de envio de e-mail
def send_email(res, cabin_id):
    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_SENDER
    msg['To']   = res['id_usuario']
    msg['Subject'] = 'Reserva Confirmada - Attenua Cabines'
    body = f"""
    <h1>Reserva Confirmada!</h1>
    <p>Cabine: {cabin_id}</p>
    <p>Data: {res['dia']}</p>
    <p>Horário: {res['hora']}</p>
    <p>Código de acesso: {res['senha_unica']}</p>
    """
    msg.attach(MIMEText(body, 'html'))
    s = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    s.login(EMAIL_SENDER, EMAIL_PASS)
    s.sendmail(EMAIL_SENDER, res['id_usuario'], msg.as_string())
    s.quit()

# Rota para ESP32 verificar código
@app.route('/verify/<code>')
def verify_code(code):
    col = mongo_connect()
    doc = col.find_one({'agendamentos.senha_unica': code})
    if not doc:
        return 'INVALID', 404
    ag = next(a for a in doc['agendamentos'] if a['senha_unica']==code)
    # valida horário
    tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz).strftime('%d-%m-%Y %H:00')
    if f"{ag['dia']} {ag['hora']}" != now:
        return 'EXPIRED', 403
    # envia MQTT para abrir cabine
    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT)
    client.publish(MQTT_TOPIC, str(doc['id']))
    client.disconnect()
    return 'OK'

if __name__ == '__main__':
    app.run(debug=True)
