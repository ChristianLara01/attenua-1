from flask import Flask, render_template, request, redirect, url_for, jsonify
import pymongo
import secrets
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# MongoDB Connection
def mongo_connect():
    client = pymongo.MongoClient("mongodb+srv://attenua:agendamento@attenua.qypnpl.mongodb.net/?retryWrites=true&w=majority&appName=attenua")
    db = client["attenua"]
    return db["cabines"]

# Home page
@app.route('/')
def index():
    today = datetime.now()
    dias = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
    return render_template("index.html", dias=dias)

# Cabines disponíveis para determinado dia e hora
@app.route('/available/<date>/<slot>')
def available(date, slot):
    col = mongo_connect()
    cabines = list(col.find({}))
    disponiveis = []

    for cabine in cabines:
        conflitos = [
            ag for ag in cabine.get("agendamentos", [])
            if ag["dia"] == date and ag["hora"] == slot
        ]
        if not conflitos:
            disponiveis.append({
                "id": cabine["id"],
                "nome": cabine["nome"],
                "imagem": cabine["imagem"],
                "image_class": cabine.get("image_class", ""),
                "valor_hora": cabine["valor_hora"]
            })
    return jsonify(disponiveis)

# Página de reserva por cabine
@app.route('/reserve/<int:cabin_id>/<date>/<slot>')
def reserve_form(cabin_id, date, slot):
    return render_template("reservation.html", cabin_id=cabin_id, date=date, slot=slot)

# Envio de e-mail
def send_email(dados, cabine_nome):
    msg = MIMEText(f"""
Olá {dados['first_name']} {dados['last_name']},

Sua reserva na {cabine_nome} foi confirmada.

Dia: {dados['dia']}
Horário: {dados['hora']}
Código de acesso: {dados['senha_unica']}

Atenciosamente,
Equipe Attenua
""")
    msg["Subject"] = "Confirmação de Reserva - Attenua"
    msg["From"] = "christian@atualle.com.br"
    msg["To"] = dados["id_usuario"]

    try:
        server = smtplib.SMTP_SSL('smtp.hostinger.com', 465)
        server.login("christian@atualle.com.br", "@12Duda04")
        server.send_message(msg)
        server.quit()
        print("Email enviado.")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# Submissão da reserva
@app.route('/reserve/submit', methods=["POST"])
def reserve_submit():
    col = mongo_connect()
    data = request.form
    cabine_id = int(data["cabin_id"])
    date = data["date"]
    slot = data["slot"]
    first = data["first_name"]
    last = data["last_name"]
    email = data["email"]

    code = secrets.token_hex(3)
    while col.find_one({"agendamentos.senha_unica": code}):
        code = secrets.token_hex(3)

    reserva = {
        "dia": date,
        "hora": slot,
        "qtde_horas": 1,
        "id_usuario": email,
        "first_name": first,
        "last_name": last,
        "senha_unica": code,
        "cabin_id": cabine_id
    }

    col.update_one({"id": cabine_id}, {"$push": {"agendamentos": reserva}})
    cabine = col.find_one({"id": cabine_id})
    send_email(reserva, cabine["nome"])

    return render_template("reservation_success.html", code=code, cabine=cabine["nome"], date=date, slot=slot)

# Página para ativar cabine
@app.route('/activate')
def activate():
    return render_template("activate.html")

# Submissão do código para ativar a cabine
@app.route('/activate/submit', methods=["POST"])
def activate_submit():
    code = request.form["access_code"]
    col = mongo_connect()
    cabine = col.find_one({"agendamentos.senha_unica": code})
    if cabine:
        return render_template("activate_success.html", cabine=cabine["nome"])
    else:
        return render_template("activate.html", error="Código inválido.")

if __name__ == '__main__':
    app.run(debug=True)
