import os
import pymongo
import pytz
import secrets
import smtplib
import paho.mqtt.client as mqtt
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

# --- Configurações ---
MONGO_URI    = "mongodb+srv://riotchristian04:atualle1@cluster0.zwuw5.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
INTERVAL_MIN = 30    # intervalo em minutos (ajuste fácil)
HOUR_START   = 9     # horário inicial
HOUR_END     = 19    # horário final (último slot: HOUR_END:30)

# MQTT
MQTT_HOST  = "mqtt.eclipseprojects.io"
MQTT_PORT  = 1883
MQTT_TOPIC = "estado"

# SMTP — preferencialmente via variáveis de ambiente
SMTP_HOST = os.getenv("SMTP_HOST", "server51.srvlinux.info")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER", "christian@atualle.com.br")
SMTP_PASS = os.getenv("SMTP_PASS", "@12Duda04")


def mongo_connect():
    """Retorna a coleção de reservas no MongoDB."""
    client = pymongo.MongoClient(MONGO_URI)
    return client.attenua.reservas


def send_mqtt_message(payload: str):
    """Publica payload no tópico MQTT para abrir a cabine."""
    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT)
    client.publish(MQTT_TOPIC, payload)
    client.disconnect()


def send_email(res, cabin_id):
    """
    Envia e‑mail de confirmação via SMTP SSL.
    res: dicionário com campos 'dia','hora','senha_unica','id_usuario'
    cabin_id: ID da cabine reservada
    """
    msg = MIMEMultipart("alternative")
    msg["From"]    = SMTP_USER
    msg["To"]      = res["id_usuario"]
    msg["Subject"] = "Reserva Confirmada - Attenua Cabines"

    html = f"""
    <html>
      <body>
        <h2>Reserva Confirmada!</h2>
        <p><strong>Cabine:</strong> {cabin_id}</p>
        <p><strong>Data:</strong>  {res['dia']}</p>
        <p><strong>Horário:</strong> {res['hora']}</p>
        <p><strong>Código:</strong> {res['senha_unica']}</p>
        <p>Apresente este código para liberar sua cabine automaticamente.</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


# --- Rotas ---

@app.route("/")
def index():
    """Página principal: seletor de data e horários."""
    return render_template(
        "index.html",
        hour_start=HOUR_START,
        hour_end=HOUR_END,
        interval=INTERVAL_MIN
    )


@app.route("/api/available/<date_iso>/<slot>")
def api_available(date_iso, slot):
    """
    Retorna JSON com as cabines LIVRES no date_iso (YYYY‑MM‑DD) e slot (HH:MM).
    """
    col = mongo_connect()
    livres = []
    for c in col.find():
        conflito = any(
            ag["dia"] == date_iso and ag["hora"] == slot
            for ag in c.get("agendamentos", [])
        )
        if not conflito:
            c.pop("_id", None)
            c.pop("agendamentos", None)
            livres.append(c)
    return jsonify(livres)


@app.route("/reserve/<int:cabin_id>/<date_iso>/<slot>")
def reserve_form(cabin_id, date_iso, slot):
    """Exibe o formulário para confirmar a reserva."""
    return render_template(
        "reservation.html",
        cabin_id=cabin_id,
        date_iso=date_iso,
        slot=slot
    )


@app.route("/reserve", methods=["POST"])
def reserve_submit():
    """Processa o formulário de reserva e envia e‑mail de confirmação."""
    cabin_id = int(request.form["cabin_id"])
    date_iso = request.form["date_iso"]    # YYYY-MM-DD
    slot     = request.form["slot"]        # HH:MM
    first    = request.form["first_name"]
    last     = request.form["last_name"]
    email    = request.form["email"]

    # Gera código único de 3 bytes hex
    code = secrets.token_hex(3)
    col  = mongo_connect()
    while col.find_one({"agendamentos.senha_unica": code}):
        code = secrets.token_hex(3)

    novo = {
        "dia"        : date_iso,
        "hora"       : slot,
        "qtde_horas" : 1,
        "id_usuario" : email,
        "first_name" : first,
        "last_name"  : last,
        "senha_unica": code
    }

    col.update_one(
        {"id": cabin_id},
        {"$push": {"agendamentos": novo}}
    )

    send_email(novo, cabin_id)

    return render_template(
        "reservation_success.html",
        cabin_id=cabin_id,
        date_iso=date_iso,
        slot=slot,
        code=code
    )


@app.route("/verify/<code>")
def verify_code(code):
    """
    Rota para ESP32 verificar código:
    - encontra o agendamento
    - valida se é o dia+hora atual
    - publica MQTT para abrir a cabine
    """
    col = mongo_connect()
    doc = col.find_one({"agendamentos.senha_unica": code})
    if not doc:
        return "INVALID", 404

    ag = next(a for a in doc["agendamentos"] if a["senha_unica"] == code)

    tz  = pytz.timezone("America/Sao_Paulo")
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    if f"{ag['dia']} {ag['hora']}" != now:
        return "EXPIRED", 403

    send_mqtt_message(str(doc["id"]))
    return "OK"


if __name__ == "__main__":
    app.run(debug=True)
