from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pymongo
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Configurações
MONGO_URI         = "mongodb+srv://riotchristian04:atualle1@cluster0.zwuw5.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MQTT_BROKER_HOST  = "mqtt.eclipseprojects.io"
MQTT_BROKER_PORT  = 1883
MQTT_TOPIC        = "estado"
EMAIL_SENDER      = "attenua@atualle.com.br"
EMAIL_PASSWORD    = "Wwck$22xO4O#8V"
SMTP_HOST         = "smtp.hostinger.com"
SMTP_PORT         = 465

# Intervalos
START_HOUR   = 15
END_HOUR     = 20
INTERVAL_MIN = 30

def mongo_connect():
    client = pymongo.MongoClient(MONGO_URI)
    return client.attenua.reservas

def sendEmail(reserv):
    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_SENDER
    msg["To"]   = reserv["id_usuario"]
    msg["Subject"] = "Reserva Confirmada - ATTENUA CABINES ACÚSTICAS"
    html = f"""
    <html><body>
      <h1>Reserva Confirmada!</h1>
      <p>Cabine: {reserv['cabin_id']}</p>
      <p>Dia: {reserv['dia']}</p>
      <p>Hora: {reserv['hora']}</p>
      <p>Código de acesso: {reserv['senha_unica']}</p>
    </body></html>"""
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

@app.route('/')
def catalog():
    # hoje + próximos 4 dias
    today = datetime.now()
    dias = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
    return render_template('catalog.html', dias=dias)

@app.route('/api/available_slots/<date_iso>')
def available_slots(date_iso):
    # gera lista de slots
    slots = []
    for h in range(START_HOUR, END_HOUR + 1):
        for m in range(0, 60, INTERVAL_MIN):
            if h == END_HOUR and m > 0: break
            slots.append(f"{h:02d}:{m:02d}")
    col = mongo_connect()
    result = []
    for slot in slots:
        exists_conflict = any(
            ag['dia'] == date_iso and ag['hora'] == slot
            for doc in col.find() for ag in doc.get("agendamentos", [])
        )
        result.append({"slot": slot, "available": not exists_conflict})
    return jsonify(result)

@app.route('/available/<date_iso>/<slot>')
def available(date_iso, slot):
    col = mongo_connect()
    livres = []
    for cabine in col.find():
        conflito = any(
            ag['dia'] == date_iso and ag['hora'] == slot
            for ag in cabine.get("agendamentos", [])
        )
        if not conflito:
            livres.append({
              "id": cabine["id"],
              "nome": cabine["nome"],
              "imagem": cabine["imagem"],
              "valor_hora": cabine["valor_hora"]
            })
    return jsonify(livres)

@app.route('/reserve/<int:cabin_id>/<date_iso>/<slot>')
def show_reservation_form(cabin_id, date_iso, slot):
    return render_template('reservation.html',
                           cabin_id=cabin_id,
                           date_iso=date_iso,
                           slot=slot)

@app.route('/reserve', methods=["POST"])
def handle_reservation():
    form = request.form
    cabin_id = int(form["cabin_id"])
    date_iso = form["date_iso"]
    slot     = form["slot"]
    first    = form["first_name"]
    last     = form["last_name"]
    email    = form["email"]
    code     = secrets.token_hex(3)
    col      = mongo_connect()
    # evitar duplicação
    while col.find_one({"agendamentos.senha_unica": code}):
        code = secrets.token_hex(3)
    novo = {
        "dia": date_iso,
        "hora": slot,
        "qtde_horas": 1,
        "id_usuario": email,
        "first_name": first,
        "last_name": last,
        "senha_unica": code,
        "cabin_id": cabin_id
    }
    col.update_one({"id": cabin_id}, {"$push": {"agendamentos": novo}})
    sendEmail(novo)
    return render_template('reservation_success.html',
                           cabin_id=cabin_id,
                           date_iso=date_iso,
                           slot=slot,
                           code=code)

@app.route('/acessar')
def acessar():
    return render_template('acessar.html')

@app.route('/acessar', methods=["POST"])
def acessar_submit():
    code = request.form["code"]
    col  = mongo_connect()
    doc  = col.find_one({"agendamentos.senha_unica": code})
    if doc:
        # poderia enviar MQTT aqui
        return render_template('activate_success.html', code=code)
    return render_template('acessar.html', error="Código inválido.")

if __name__ == '__main__':
    app.run(debug=True)
