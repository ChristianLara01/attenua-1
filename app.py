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
    # Extrai nome da cabine e remove prefixo
    raw_name    = reserv.get("nome", "")
    nome_cabine = raw_name.replace("CABINE ", "").strip()
    # Formata data de YYYY-MM-DD para DD/MM/AAAA
    data_format = datetime.strptime(reserv["dia"], "%Y-%m-%d").strftime("%d/%m/%Y")
    # Prefixa o código de acesso com o nome da cabine
    codigo_acesso = f"{nome_cabine}-{reserv['senha_unica']}"

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
    body {{ font-family: Arial, sans-serif; background:#f5f5f5; margin:0; padding:0; }}
    .container {{ max-width:600px; margin:20px auto; background:#fff;
                  border-radius:8px; box-shadow:0 4px 12px rgba(0,0,0,0.1); }}
    .header {{ background:#28a745; color:#fff; text-align:center; padding:20px; }}
    .header h1 {{ margin:0; font-size:1.8rem; }}
    .content {{ padding:20px; color:#333; line-height:1.5; }}
    .content p {{ margin:0.5rem 0; }}
    .content .highlight {{ font-weight:bold; color:#28a745; }}
    .links {{ padding:20px; text-align:center; background:#f0f0f0; }}
    .links a {{ margin:0.5rem; padding:10px 20px; background:#28a745;
                color:#fff; text-decoration:none; border-radius:4px; }}
    .footer {{ padding:20px; font-size:0.9rem; color:#555; text-align:center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header"><h1>Reserva Confirmada!</h1></div>
    <div class="content">
      <p>Olá <span class="highlight">{reserv['first_name']} {reserv['last_name']}</span>,</p>
      <p>Sua reserva foi confirmada com sucesso:</p>
      <p><strong>Sua cabine:</strong> <span class="highlight">{nome_cabine}</span></p>
      <p><strong>Data:</strong> <span class="highlight">{data_format}</span></p>
      <p><strong>Código de Acesso:</strong> <span class="highlight">{codigo_acesso}</span></p>
    </div>
    <div class="links">
      <a href="https://attenua.com.br" target="_blank">Visitar Attenua</a>
      <a href="https://atualle.com.br" target="_blank">Visitar Atualle</a>
    </div>
    <div class="footer">
      A Atualle é referência em soluções acústicas para ambientes modernos.<br>
      Obrigado por escolher a ATTENUA Cabines Acústicas!
    </div>
  </div>
</body>
</html>
"""
    msg.attach(MIMEText(html, "html"))
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
    cabine = col.find_one({"id": cabin_id})
    if not cabine:
        return "Cabine não encontrada", 404

    if request.method == "POST":
        first = request.form["first_name"]
        last  = request.form["last_name"]
        email = request.form["email"]

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
            "nome":        cabine["nome"]
        }
        col.update_one({"id": cabin_id}, {"$push": {"agendamentos": reserva}})

        try:
            send_email(reserva)
        except Exception as e:
            app.logger.error(f"Erro no envio de e-mail: {e}")

        # Prepara valores para template
        cabine_nome    = cabine["nome"].replace("CABINE ", "")
        data_formatada = datetime.strptime(date_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
        codigo_full    = f"{cabine_nome}-{code}"

        return render_template(
            'reservation_success.html',
            cabine_nome=cabine_nome,
            dia=data_formatada,
            hora=slot,
            codigo=codigo_full
        )

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
