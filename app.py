import logging
import secrets
import smtplib
import pymongo
from flask import Flask, render_template, request, jsonify
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
    """
    Envia email formatado:
      - Sua cabine: nome (sem "CABINE "), capitalizado
      - Data: dd/mm/aaaa
      - Código de acesso: nomecabine + código de 6 hex dígitos (minúsculo, sem espaços)
      - Links e propaganda para Attenua e Atualle
    """
    # extrai nome da cabine, remove prefixo "CABINE "
    raw_name    = reserv.get("nome", "")
    nome_cabine = raw_name.replace("CABINE ", "").strip().lower()
    # formata data yyyy-mm-dd → dd/mm/aaaa
    data_iso    = reserv["dia"]
    data_fmt    = datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    # monta código completo
    codigo_full = f"{nome_cabine}{reserv['senha_unica']}".lower()

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
    body {{ margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif }}
    .container {{ max-width:600px;margin:20px auto;background:#fff;border-radius:8px;
                  box-shadow:0 4px 12px rgba(0,0,0,0.1);overflow:hidden }}
    .header {{ background:#28a745;color:#fff;text-align:center;padding:20px }}
    .header h1 {{ margin:0;font-size:1.8rem }}
    .content {{ padding:20px;color:#333;line-height:1.5 }}
    .content p {{ margin:.5rem 0 }}
    .content .highlight {{ font-weight:bold;color:#28a745 }}
    .links {{ padding:20px;text-align:center;background:#f0f0f0 }}
    .links a {{ margin:.5rem;padding:10px 20px;background:#28a745;color:#fff;
               text-decoration:none;border-radius:4px;font-size:.95rem }}
    .footer {{ padding:20px;font-size:.9rem;color:#555;text-align:center }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Reserva Confirmada!</h1>
    </div>
    <div class="content">
      <p>Olá <span class="highlight">{reserv['first_name']} {reserv['last_name']}</span>,</p>
      <p>Sua reserva foi realizada com sucesso:</p>
      <p><strong>Sua cabine:</strong> <span class="highlight">{nome_cabine.title()}</span></p>
      <p><strong>Data:</strong> <span class="highlight">{data_fmt}</span></p>
      <p><strong>Código de Acesso:</strong> <span class="highlight">{codigo_full}</span></p>
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
    """Página inicial: próximos 5 dias."""
    today = datetime.now()
    dias = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
    return render_template('catalog.html', dias=dias)

@app.route('/available/<date_iso>/<slot>')
def available(date_iso, slot):
    """
    Retorna JSON das cabines disponíveis no dia (yyyy-mm-dd) e horário (HH:MM).
    """
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
    """
    GET: exibe formulário de dados.
    POST: persiste reserva, envia e-mail e mostra página de sucesso.
    """
    col = mongo_connect()
    cabine = col.find_one({"id": cabin_id})
    if not cabine:
        return "Cabine não encontrada", 404

    if request.method == "POST":
        first = request.form["first_name"]
        last  = request.form["last_name"]
        email = request.form["email"]

        code = secrets.token_hex(3)
        while col.find_one({"agendamentos.senha_unica": code}):
            code = secrets.token_hex(3)

        reserva = {
            "dia":          date_iso,
            "hora":         slot,
            "qtde_horas":   1,
            "id_usuario":   email,
            "first_name":   first,
            "last_name":    last,
            "senha_unica":  code,
            "nome":         cabine["nome"]
        }
        col.update_one({"id": cabin_id}, {"$push": {"agendamentos": reserva}})

        try:
            send_email(reserva)
        except Exception as e:
            app.logger.error(f"Erro no envio de email: {e}")

        # passa para template sucesso formatado
        nome_simples = cabine["nome"].replace("CABINE ", "").title()
        data_fmt     = datetime.strptime(date_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
        codigo_full  = f"{cabine['nome'].replace('CABINE ', '').lower()}{code}"

        return render_template(
            'reservation_success.html',
            cabine=nome_simples,
            dia=data_fmt,
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
    """
    Tela para usuário inserir código e ativar cabine.
    """
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
