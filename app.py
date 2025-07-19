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

    html = f"""
    <html><body>
      <h1>Reserva Confirmada!</h1>
      <p><strong>Cabine:</strong> {reserv['cabin_id']}</p>
      <p><strong>Data:</strong> {reserv['dia']}</p>
      <p><strong>Hora:</strong> {reserv['hora']}</p>
      <p><strong>Código de acesso:</strong> {reserv['senha_unica']}</p>
    </body></html>
    """
    msg.attach(MIMEText(html, "html"))

    app.logger.info(f"Conectando ao SMTP {SMTP_HOST}:{SMTP_PORT} como {EMAIL_SENDER}")
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
    app.logger.info(f"E‑mail enviado para {reserv['id_usuario']}")

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
