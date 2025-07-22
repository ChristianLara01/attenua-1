import logging
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pymongo
import paho.mqtt.client as mqtt
from flask import Flask, render_template, request, jsonify

# ——— Setup e logging ———
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# ——— Configurações de MongoDB ———
MONGO_URI = (
    "mongodb+srv://riotchristian04:atualle1"
    "@cluster0.zwuw5.mongodb.net/"
    "?retryWrites=true&w=majority&appName=Cluster0"
)
def mongo_connect():
    client = pymongo.MongoClient(MONGO_URI)
    return client.attenua.reservas

# ——— Configurações de SMTP ———
EMAIL_SENDER   = "christian@atualle.com.br"
EMAIL_PASSWORD = "@12Duda04"
SMTP_HOST      = "smtp.hostinger.com"
SMTP_PORT      = 465

# ——— Configurações MQTT ———
MQTT_BROKER_HOST = "mqtt.eclipseprojects.io"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC       = "cabine/01/open"

def send_mqtt_message(payload: str):
    client = mqtt.Client()
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
    client.publish(MQTT_TOPIC, payload)
    client.disconnect()

def dentro_do_periodo(agendamento: dict) -> bool:
    """
    Retorna True se o momento atual estiver entre
    agendamento['dia'] + ' ' + agendamento['hora']
    e +30 minutos.
    """
    inicio = datetime.strptime(
        f"{agendamento['dia']} {agendamento['hora']}",
        "%Y-%m-%d %H:%M"
    )
    fim = inicio + timedelta(minutes=30)
    agora = datetime.now()
    return inicio <= agora <= fim

def send_email(reserv: dict):
    # formata data de YYYY-MM-DD para DD/MM/YYYY
    year, month, day = reserv["dia"].split('-')
    date_fmt = f"{day}/{month}/{year}"

    msg = MIMEMultipart("alternative")
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = reserv["id_usuario"]
    msg["Subject"] = "Reserva Confirmada – ATTENUA CABINES ACÚSTICAS"

    html = f"""\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; margin:0; padding:0; }}
    .container {{ max-width:600px; margin:20px auto; background:#fff;
                  border-radius:8px; overflow:hidden;
                  box-shadow:0 4px 12px rgba(0,0,0,0.1); }}
    .header {{ background:#28a745; color:#fff; text-align:center; padding:20px; }}
    .header h1 {{ margin:0; font-size:1.8rem; }}
    .content {{ padding:20px; color:#333; line-height:1.5; }}
    .content p {{ margin:.5rem 0; }}
    .content .highlight {{ font-weight:bold; color:#28a745; }}
    .links {{ padding:20px; text-align:center; background:#f0f0f0; }}
    .links a {{ display:inline-block; margin:.5rem; padding:10px 20px;
                 background:#28a745; color:#fff; text-decoration:none;
                 border-radius:4px; font-size:.95rem; }}
    .footer {{ padding:20px; font-size:.9rem; color:#555; text-align:center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header"><h1>Reserva Confirmada!</h1></div>
    <div class="content">
      <p><span class="highlight">Sua cabine:</span> {reserv['nome']}</p>
      <p><span class="highlight">Data:</span> {date_fmt}</p>
      <p><span class="highlight">Horário:</span> {reserv['hora']}</p>
      <p><span class="highlight">Código de Acesso:</span> {reserv['senha_unica']}</p>
    </div>
    <div class="links">
      <a href="https://attenua.com.br" target="_blank">Visitar Attenua</a>
      <a href="https://atualle.com.br" target="_blank">Visitar Atualle</a>
    </div>
    <div class="footer">
      <p>A Atualle é referência em soluções acústicas, oferecendo cabines de alta qualidade para ambientes corporativos e residenciais.</p>
      <p>Obrigado por escolher a ATTENUA Cabines Acústicas!</p>
    </div>
  </div>
</body>
</html>
"""
    part = MIMEText(html, "html")
    msg.attach(part)

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

# ——— Rotas ———

@app.route('/')
def catalog():
    today = datetime.now()
    # só hoje + próximos 2 dias
    dias = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]
    return render_template('catalog.html', dias=dias)

@app.route('/api/available_slots/<date_iso>')
def available_slots(date_iso):
    START_HOUR, END_HOUR, INTERVAL = 15, 20, 30
    slots = []
    for h in range(START_HOUR, END_HOUR + 1):
        for m in range(0, 60, INTERVAL):
            if h == END_HOUR and m > 0:
                break
            slots.append(f"{h:02d}:{m:02d}")

    col = mongo_connect()
    cabins = list(col.find())
    result = []
    for slot in slots:
        free = any(
            all(
                ag["dia"] != date_iso or ag["hora"] != slot
                for ag in cabine.get("agendamentos", [])
            )
            for cabine in cabins
        )
        result.append({"slot": slot, "available": free})
    return jsonify(result)

@app.route('/available/<date_iso>/<slot>')
def available(date_iso, slot):
    col = mongo_connect()
    livres = []
    for cabine in col.find():
        conflito = any(
            ag["dia"] == date_iso and ag["hora"] == slot
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

@app.route('/reserve/<int:cabin_id>/<date_iso>/<slot>', methods=["GET","POST"])
def reserve(cabin_id, date_iso, slot):
    col = mongo_connect()
    cabine = col.find_one({"id": cabin_id})

    if request.method == "POST":
        first = request.form["first_name"]
        last  = request.form["last_name"]
        email = request.form["email"]

        # gera código: nomecabine + 6 hex
        code = secrets.token_hex(3)
        nome_simple = cabine["nome"].replace("CABINE ", "").strip().lower()
        full_code = f"{nome_simple}{code}"

        reserva = {
            "dia":         date_iso,
            "hora":        slot,
            "qtde_horas":  1,
            "id_usuario":  email,
            "first_name":  first,
            "last_name":   last,
            "senha_unica": full_code,
            "cabin_id":    cabin_id,
            "nome":        cabine["nome"]
        }
        col.update_one({"id": cabin_id}, {"$push": {"agendamentos": reserva}})
        try:
            send_email(reserva)
        except Exception as e:
            app.logger.error(f"Erro SMTP: {e}")

        return render_template(
            'reservation_success.html',
            cabin_name=cabine["nome"],
            dia=date_iso,
            hora=slot,
            senha=full_code
        )

    return render_template(
        'reservation.html',
        cabin_id=cabin_id,
        cabin_name=cabine["nome"],
        date_iso=date_iso,
        slot=slot
    )

@app.route('/acessar', methods=["GET","POST"])
def acessar():
    error = None

    if request.method == "POST":
        code = request.form["code"].strip().lower()
        col  = mongo_connect()
        doc  = col.find_one({"agendamentos.senha_unica": code})

        if not doc:
            error = "Código inválido."
        else:
            ag = next((a for a in doc["agendamentos"] if a["senha_unica"] == code), None)
            if not ag:
                error = "Código inválido."
            elif not dentro_do_periodo(ag):
                error = "Fora do horário da sua reserva."
            else:
                # tudo OK → abre a porta via MQTT
                send_mqtt_message(str(doc["id"]))
                return render_template('activate_success.html', code=code)

    return render_template('acessar.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)
