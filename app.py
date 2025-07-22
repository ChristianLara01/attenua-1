import logging
from flask import Flask, render_template, request, jsonify
import pymongo
import secrets
import smtplib
import paho.mqtt.publish as publish
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "cabine/01/open"

def send_email(reserv, nome_cabine):
    msg = MIMEMultipart("alternative")
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = reserv["id_usuario"]
    msg["Subject"] = "Reserva Confirmada – ATTENUA CABINES ACÚSTICAS"

    data_formatada = datetime.strptime(reserv['dia'], "%Y-%m-%d").strftime("%d/%m/%Y")
    codigo_acesso = f"{nome_cabine.upper()}-{reserv['senha_unica']}"

    html = f"""\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      font-family: Arial, sans-serif;
      background-color: #f5f5f5;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 600px;
      margin: 20px auto;
      background: #ffffff;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    .header {{
      background: #28a745;
      color: #ffffff;
      text-align: center;
      padding: 20px;
    }}
    .header h1 {{
      margin: 0;
      font-size: 1.8rem;
    }}
    .content {{
      padding: 20px;
      color: #333333;
      line-height: 1.5;
    }}
    .content p {{
      margin: 0.5rem 0;
    }}
    .content .highlight {{
      font-weight: bold;
      color: #28a745;
    }}
    .links {{
      padding: 20px;
      text-align: center;
      background: #f0f0f0;
    }}
    .links a {{
      display: inline-block;
      margin: 0.5rem;
      padding: 10px 20px;
      background: #28a745;
      color: #ffffff;
      text-decoration: none;
      border-radius: 4px;
      font-size: 0.95rem;
    }}
    .footer {{
      padding: 20px;
      font-size: 0.9rem;
      color: #555555;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Reserva Confirmada!</h1>
    </div>
    <div class="content">
      <p>Olá <span class="highlight">{reserv['first_name']} {reserv['last_name']}</span>,</p>
      <p>Sua reserva foi confirmada com sucesso:</p>
      <p><span class="highlight">Sua cabine:</span> {nome_cabine}</p>
      <p><span class="highlight">Data:</span> {data_formatada}</p>
      <p><span class="highlight">Horário:</span> {reserv['hora']}</p>
      <p><span class="highlight">Código de Acesso:</span> {codigo_acesso}</p>
    </div>
    <div class="links">
      <a href="https://attenua.com.br" target="_blank">Visitar Attenua</a>
      <a href="https://atualle.com.br" target="_blank">Visitar Atualle</a>
    </div>
    <div class="footer">
      <p>A Atualle é uma empresa referência em soluções acústicas, oferecendo cabines de alta qualidade para ambientes corporativos e residenciais.</p>
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
    dias = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
    return render_template('catalog.html', dias=dias)

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
    if request.method == "POST":
        first = request.form["first_name"]
        last  = request.form["last_name"]
        email = request.form["email"]

        code = secrets.token_hex(3)
        while col.find_one({"agendamentos.senha_unica": code}):
            code = secrets.token_hex(3)

        reserva = {
            "dia":         date_iso,
            "hora":        slot,
            "qtde_horas":  1,
            "id_usuario":  email,
            "first_name":  first,
            "last_name":   last,
            "senha_unica": code,
            "cabin_id":    cabin_id
        }
        col.update_one({"id": cabin_id}, {"$push": {"agendamentos": reserva}})

        cabine = col.find_one({"id": cabin_id})
        nome_cabine = cabine["nome"].replace("CABINE ", "")

        try:
            send_email(reserva, nome_cabine)
        except Exception as e:
            app.logger.error(f"Erro SMTP: {e}")

        return render_template(
            'reservation_success.html',
            cabin_id=cabin_id,
            dia=date_iso,
            hora=slot,
            senha=code
        )

    return render_template('reservation.html', cabin_id=cabin_id, date_iso=date_iso, slot=slot)

@app.route('/acessar', methods=["GET","POST"])
def acessar():
    error = None
    if request.method == "POST":
        code = request.form["code"]
        col  = mongo_connect()
        cabines = list(col.find({"agendamentos.senha_unica": code}))

        for cabine in cabines:
            for ag in cabine.get("agendamentos", []):
                if ag["senha_unica"] == code:
                    dia_hora_str = f"{ag['dia']} {ag['hora']}"
                    ag_dt = datetime.strptime(dia_hora_str, "%Y-%m-%d %H:%M")
                    now = datetime.now()

                    if abs((ag_dt - now).total_seconds()) <= 1800:
                        try:
                            publish.single(MQTT_TOPIC, payload="abrir", hostname=MQTT_BROKER, port=MQTT_PORT)
                            return render_template('activate_success.html', code=code)
                        except Exception as e:
                            error = "Erro ao enviar comando MQTT."
                            app.logger.error(e)
                    else:
                        error = "Fora do horário permitido (30 minutos da reserva)."
                    break
            if error: break
        else:
            error = "Código inválido."
    return render_template('acessar.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)
