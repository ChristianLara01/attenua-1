import logging
from flask import Flask, render_template, request, jsonify
import pymongo
import secrets
import smtplib
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

def send_email(reserv):
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
      <p><span class="highlight">Data e Horário:</span> {reserv['dia']} às {reserv['hora']}</p>
      <p><span class="highlight">Código de Acesso:</span> {reserv['senha_unica']}</p>
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

@app.route('/api/available_slots/<date_iso>')
def available_slots(date_iso):
    START_HOUR, END_HOUR, INTERVAL = 15, 20, 30
    slots = []
    for h in range(START_HOUR, END_HOUR + 1):
        for m in range(0, 60, INTERVAL):
            if h == END_HOUR and m > 0: break
            slots.append(f"{h:02d}:{m:02d}")

    col = mongo_connect()
    cabins = list(col.find())
    result = []
    for slot in slots:
        any_free = any(
            all(
                ag["dia"] != date_iso or ag["hora"] != slot
                for ag in cabine.get("agendamentos", [])
            )
            for cabine in cabins
        )
        result.append({"slot": slot, "available": any_free})
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

    if request.method == "POST":
        app.logger.info(f"POST /reserve → cabin={cabin_id}, date={date_iso}, slot={slot}")
        first = request.form["first_name"]
        last  = request.form["last_name"]
        email = request.form["email"]
        app.logger.info(f"Dados do form: {first} {last} {email}")

        code = secrets.token_hex(3)
        while col.find_one({"agendamentos.senha_unica": code}):
            code = secrets.token_hex(3)
        app.logger.info(f"Código gerado: {code}")

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
        app.logger.info("Reserva salva no MongoDB")

        try:
            send_email(reserva)
        except Exception as e:
            app.logger.error(f"Erro SMTP: {e}")

        return render_template(
            'reservation_success.html',
            cabin_id=cabin_id,
            dia=date_iso,
            hora=slot,
            senha=code
        )

    app.logger.info(f"GET /reserve → cabine={cabin_id} em {date_iso} às {slot}")
    return render_template(
        'reservation.html',
        cabin_id=cabin_id,
        date_iso=date_iso,
        slot=slot
    )

@app.route('/acessar', methods=["GET","POST"])
def acessar():
    error = None
    if request.method == "POST":
        code = request.form["code"]
        doc  = mongo_connect().find_one({"agendamentos.senha_unica": code})
        if doc:
            return render_template('activate_success.html', code=code)
        error = "Código inválido."
    return render_template('acessar.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)
