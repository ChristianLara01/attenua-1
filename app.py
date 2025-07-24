import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
import pymongo
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import paho.mqtt.publish as publish

# ——— Setup e logging —————————————————
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# ——— Configurações de MongoDB —————————————————
MONGO_URI = (
    "mongodb+srv://riotchristian04:atualle1"
    "@cluster0.zwuw5.mongodb.net/"
    "?retryWrites=true&w=majority&appName=Cluster0"
)
def mongo_connect():
    client = pymongo.MongoClient(MONGO_URI)
    return client.attenua.reservas

# ——— Configurações de SMTP —————————————————
EMAIL_SENDER   = "christian@atualle.com.br"
EMAIL_PASSWORD = "@12Duda04"
SMTP_HOST      = "smtp.hostinger.com"
SMTP_PORT      = 465

# ——— Configurações de MQTT —————————————————
MQTT_HOST       = "917a3939272f48c09215df8a39c82c46.s1.eu.hivemq.cloud"
MQTT_PORT       = 8883
MQTT_USER       = "attenua"
MQTT_PASS       = "Atualle1"
# no longer a single topic, we'll build per-cabin

# ——— Fuso horário local (UTC–3) —————————————————
LOCAL_TZ_OFFSET = -3

def mqtt_publish_open(cabin_id: int):
    """Publish 'abrir' to the topic for the given cabin_id."""
    topic = f"cabine/{cabin_id:02d}/open"
    auth = {'username': MQTT_USER, 'password': MQTT_PASS}
    publish.single(
        topic=topic,
        payload="abrir",
        hostname=MQTT_HOST,
        port=MQTT_PORT,
        auth=auth,
        tls={'insecure': True}
    )
    app.logger.info(f"MQTT → publicado 'abrir' em {topic}")

def send_email(reserv: dict):
    """Send HTML confirmation with an 'Acessar Minha Reserva' button."""
    # format date DD/MM/YYYY
    year, month, day = reserv["dia"].split('-')
    date_fmt = f"{day}/{month}/{year}"

    msg = MIMEMultipart("alternative")
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = reserv["id_usuario"]
    msg["Subject"] = "Reserva Confirmada – ATTENUA CABINES ACÚSTICAS"

    # build the HTML body
    html = f"""\
<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
  <style>
    body {{font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:0}}
    .container {{max-width:600px;margin:20px auto;background:#fff;border-radius:8px;
                 overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.1)}}
    .header {{background:#28a745;color:#fff;text-align:center;padding:20px}}
    .header h1 {{margin:0;font-size:1.8rem}}
    .content {{padding:20px;color:#333;line-height:1.5}}
    .content p {{margin:.5rem 0}}
    .content .highlight {{font-weight:bold;color:#28a745}}
    .links {{padding:20px;text-align:center;background:#f0f0f0}}
    .links a {{display:inline-block;margin:.5rem;padding:10px 20px;
               background:#28a745;color:#fff;text-decoration:none;
               border-radius:4px;font-size:.95rem}}
    .access-btn {{padding:20px;text-align:center}}
    .access-btn a {{display:inline-block;padding:12px 24px;
                    background:#0069d9;color:#fff;text-decoration:none;
                    border-radius:4px;font-weight:bold}}
    .footer {{padding:20px;font-size:.9rem;color:#555;text-align:center}}
  </style>
</head><body>
  <div class="container">
    <div class="header"><h1>Reserva Confirmada!</h1></div>
    <div class="content">
      <p><span class="highlight">Sua cabine:</span> {reserv['nome']}</p>
      <p><span class="highlight">Data:</span> {date_fmt}</p>
      <p><span class="highlight">Horário:</span> {reserv['hora']}</p>
      <p><span class="highlight">Código de Acesso:</span> {reserv['senha_unica']}</p>
    </div>
    <div class="access-btn">
      <a href="https://attenua.onrender.com/acessar?code={reserv['senha_unica']}"
         target="_blank">Acessar Minha Reserva</a>
    </div>
    <div class="links">
      <a href="https://attenua.com.br" target="_blank">Visitar Attenua</a>
      <a href="https://atualle.com.br" target="_blank">Visitar Atualle</a>
    </div>
    <div class="footer">
      <p>A Atualle é referência em soluções acústicas, oferecendo cabines de alta qualidade.</p>
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
    app.logger.info(f"E-mail enviado para {reserv['id_usuario']}")

# ——— Rotas ——————————————————

@app.route('/')
def catalog():
    today = datetime.now()
    # only today + next 2 days
    dias = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]
    return render_template('catalog.html', dias=dias)

@app.route('/api/available_slots/<date_iso>')
def available_slots(date_iso):
    START_HOUR, END_HOUR, INTERVAL = 15, 20, 30
    slots = [f"{h:02d}:{m:02d}"
             for h in range(START_HOUR, END_HOUR+1)
             for m in range(0, 60, INTERVAL)
             if not (h==END_HOUR and m>0)]
    col    = mongo_connect()
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
    col    = mongo_connect()
    livres = []
    for cabine in col.find():
        conflito = any(
            ag["dia"] == date_iso and ag["hora"] == slot
            for ag in cabine.get("agendamentos", [])
        )
        if not conflito:
            livres.append({
                "id":         cabine["id"],
                "nome":       cabine["nome"],
                "imagem":     cabine["imagem"],
                "valor_hora": cabine["valor_hora"]
            })
    return jsonify(livres)

@app.route('/reserve/<int:cabin_id>/<date_iso>/<slot>', methods=["GET","POST"])
def reserve(cabin_id, date_iso, slot):
    col    = mongo_connect()
    cabine = col.find_one({"id": cabin_id})
    if request.method == "POST":
        # collect form
        first = request.form["first_name"]
        last  = request.form["last_name"]
        email = request.form["email"]

        # build 6‑hex code + cabin name
        code_simple = secrets.token_hex(3)
        nome_simple = cabine["nome"].replace("CABINE ", "").strip().lower()
        full_code   = f"{nome_simple}{code_simple}"

        reserva = {
            "dia":          date_iso,
            "hora":         slot,
            "qtde_horas":   1,
            "id_usuario":   email,
            "first_name":   first,
            "last_name":    last,
            "senha_unica":  full_code,
            "cabin_id":     cabin_id,
            "nome":         cabine["nome"]
        }
        col.update_one({"id": cabin_id}, {"$push": {"agendamentos": reserva}})
        app.logger.info("Reserva salva no MongoDB")

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

@app.route('/activate_success/<code>')
def activate_success(code):
    return render_template('activate_success.html', code=code)

@app.route('/acessar', methods=["GET","POST"])
def acessar():
    error = None
    prefill = request.args.get("code", "").strip().lower()
    if request.method == "POST":
        code = request.form["code"].strip().lower()
        doc  = mongo_connect().find_one({"agendamentos.senha_unica": code})
        if not doc:
            error = "Código inválido."
        else:
            # find that specific agendamento
            ag = next(a for a in doc["agendamentos"] if a["senha_unica"] == code)
            # parse start + end window
            dt_inicio = datetime.strptime(f"{ag['dia']} {ag['hora']}", "%Y-%m-%d %H:%M")
            dt_fim    = dt_inicio + timedelta(minutes=30)
            now       = datetime.utcnow() + timedelta(hours=LOCAL_TZ_OFFSET)
            if dt_inicio <= now <= dt_fim:
                try:
                    mqtt_publish_open(ag["cabin_id"])
                except Exception as e:
                    app.logger.error(f"Erro MQTT: {e}")
                    error = "Falha ao liberar a cabine. Tente novamente."
                else:
                    return redirect(url_for('activate_success', code=code))
            else:
                error = (f"Fora do horário de agendamento. "
                         f"Sua reserva é em {ag['dia']} às {ag['hora']}.")
    # render form, passing along any prefill from query
    return render_template('acessar.html', error=error, prefill=prefill)

if __name__ == '__main__':
    app.run(debug=True)
