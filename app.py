from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pymongo
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
CORS(app)

# ——— Configurações ———
MONGO_URI      = "mongodb+srv://riotchristian04:atualle1@cluster0.zwuw5.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
EMAIL_SENDER   = "attenua@atualle.com.br"
EMAIL_PASSWORD = "Wwck$22xO4O#8V"
SMTP_HOST      = "server51.srvlinux.info"
SMTP_PORT      = 465

START_HOUR   = 15
END_HOUR     = 20
INTERVAL_MIN = 30

def mongo_connect():
    client = pymongo.MongoClient(MONGO_URI)
    return client.attenua.reservas

def sendEmail(reserv):
    msg = MIMEMultipart("alternative")
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = reserv["id_usuario"]
    msg["Subject"] = "Reserva Confirmada – ATTENUA CABINES ACÚSTICAS"
    html = f"""
    <html><body>
      <h1>Reserva Confirmada!</h1>
      <p>Cabine: {reserv['cabin_id']}</p>
      <p>Data: {reserv['dia']}</p>
      <p>Hora: {reserv['hora']}</p>
      <p>Código de acesso: {reserv['senha_unica']}</p>
    </body></html>
    """
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

@app.route('/')
def catalog():
    today = datetime.now()
    dias = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
    return render_template('catalog.html', dias=dias)

@app.route('/api/available_slots/<date_iso>')
def available_slots(date_iso):
    # gera lista de slots
    slots = []
    for h in range(START_HOUR, END_HOUR + 1):
        for m in range(0, 60, INTERVAL_MIN):
            if h == END_HOUR and m > 0:
                break
            slots.append(f"{h:02d}:{m:02d}")

    col = mongo_connect()
    cabins = list(col.find())

    result = []
    for slot in slots:
        # verifica se há ao menos uma cabine livre nesse slot
        any_free = False
        for cabine in cabins:
            # procura conflito nessa cabine
            conflito = any(
                ag["dia"] == date_iso and ag["hora"] == slot
                for ag in cabine.get("agendamentos", [])
            )
            if not conflito:
                any_free = True
                break
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

@app.route('/reserve/<int:cabin_id>/<date_iso>/<slot>', methods=["GET", "POST"])
def reserve(cabin_id, date_iso, slot):
    col = mongo_connect()

    if request.method == "POST":
        form  = request.form
        first = form["first_name"]
        last  = form["last_name"]
        email = form["email"]

        # Gera código único
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
        try:
            sendEmail(reserva)
        except Exception as e:
            app.logger.error(f"Falha ao enviar e‑mail: {e}")

        return render_template(
            'reservation_success.html',
            cabin_id=cabin_id,
            date_iso=date_iso,
            slot=slot,
            code=code
        )

    # GET → exibe o formulário de reserva
    return render_template(
        'reservation.html',
        cabin_id=cabin_id,
        date_iso=date_iso,
        slot=slot
    )

@app.route('/acessar', methods=["GET", "POST"])
def acessar():
    error = None
    if request.method == "POST":
        code = request.form["code"]
        col  = mongo_connect()
        doc  = col.find_one({"agendamentos.senha_unica": code})
        if doc:
            return render_template('activate_success.html', code=code)
        error = "Código inválido."
    return render_template('acessar.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)
