import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
import pymongo
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import paho.mqtt.publish as publish
from functools import wraps

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
    cliente = pymongo.MongoClient(MONGO_URI)
    return cliente.attenua.reservas

# ——— Configurações de SMTP —————————————————
EMAIL_SENDER   = "atualle@atualle.com.br"
EMAIL_PASSWORD = "@12Duda04"
SMTP_HOST      = "smtp.hostinger.com"
SMTP_PORT      = 465

# ——— Configurações de MQTT —————————————————
MQTT_HOST       = "917a3939272f48c09215df8a39c82c46.s1.eu.hivemq.cloud"
MQTT_PORT       = 8883
MQTT_USER       = "attenua"
MQTT_PASS       = "Atualle1"

# ——— Fuso horário local (UTC–3) —————————————————
LOCAL_TZ_OFFSET = -3

def mqtt_publish_open(cabin_id: int):
    """
    Publica 'abrir' no tópico correspondente à cabine
    """
    topic = f"cabine/{cabin_id:02d}/open"
    authentication = {'username': MQTT_USER, 'password': MQTT_PASS}
    publish.single(
        topic=topic,
        payload="abrir",
        hostname=MQTT_HOST,
        port=MQTT_PORT,
        auth=authentication,
        tls={'insecure': True}
    )
    app.logger.info(f"MQTT → publicado 'abrir' em {topic}")

def send_email(reservation: dict):
    """
    Envia e‑mail HTML de confirmação com botão de Acessar Reserva
    """
    ano, mes, dia = reservation["dia"].split('-')
    data_formatada = f"{dia}/{mes}/{ano}"

    mensagem = MIMEMultipart("alternative")
    mensagem["From"]    = EMAIL_SENDER
    mensagem["To"]      = reservation["id_usuario"]
    mensagem["Subject"] = "Reserva Confirmada – ATTENUA CABINES ACÚSTICAS"

    html = f"""\
<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; background: #f5f5f5; margin:0; padding:0 }}
    .container {{ max-width:600px; margin:20px auto; background:#fff;
                  border-radius:8px; overflow:hidden;
                  box-shadow:0 4px 12px rgba(0,0,0,0.1) }}
    .header {{ background:#28a745; color:#fff; text-align:center; padding:20px }}
    .header h1 {{ margin:0; font-size:1.8rem }}
    .content {{ padding:20px; color:#333; line-height:1.5 }}
    .content p {{ margin:.5rem 0 }}
    .content .highlight {{ font-weight:bold; color:#28a745 }}
    .access-btn {{ padding:20px; text-align:center }}
    .access-btn a {{ display:inline-block; padding:12px 24px;
                     background:#0069d9; color:#fff;
                     text-decoration:none; border-radius:4px;
                     font-weight:bold }}
    .links {{ padding:20px; text-align:center; background:#f0f0f0 }}
    .links a {{ margin:.5rem; padding:10px 20px;
                background:#28a745; color:#fff;
                text-decoration:none; border-radius:4px;
                display:inline-block; }}
    .footer {{ padding:20px; font-size:.9rem; color:#555;
               text-align:center }}
  </style>
</head><body>
  <div class="container">
    <div class="header"><h1>Reserva Confirmada!</h1></div>
    <div class="content">
      <p><span class="highlight">Sua cabine:</span> {reservation['nome']}</p>
      <p><span class="highlight">Data:</span> {data_formatada}</p>
      <p><span class="highlight">Horário:</span> {reservation['hora']}</p>
      <p><span class="highlight">Código de Acesso:</span> {reservation['senha_unica']}</p>
    </div>
    <div class="access-btn">
      <a href="https://attenua.onrender.com/acessar?code={reservation['senha_unica']}"
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
    mensagem.attach(part)

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(mensagem)
    app.logger.info(f"E‑mail enviado para {reservation['id_usuario']}")

# ——— Autenticação Basic HTTP para /controle —————————————————

def check_password(password: str) -> bool:
    return password == "atualle1"

def authenticate() -> Response:
    return Response(
        "Autenticação necessária", 
        401, 
        {"WWW-Authenticate": 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_password(auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ——— Rotas principais ——————————————————

@app.route('/')
def catalog():
    hoje = datetime.now()
    proximos = [(hoje + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]
    return render_template('catalog.html', dias=proximos)

@app.route('/api/available_slots/<date_iso>')
def available_slots(date_iso):
    # (mantém seus horários customizados conforme feira ou default...)
    START_HOUR, END_HOUR, INTERVAL = 15, 20, 30
    slots = []
    h = START_HOUR
    m = 0
    while h < END_HOUR or (h == END_HOUR and m == 0):
        slots.append(f"{int(h):02d}:{m:02d}")
        m += INTERVAL
        if m >= 60:
            h += 1
            m -= 60
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
                "id": cabine["id"],
                "nome": cabine["nome"],
                "imagem": cabine["imagem"],
                "valor_hora": cabine["valor_hora"]
            })
    return jsonify(livres)

@app.route('/reserve/<int:cabin_id>/<date_iso>/<slot>', methods=["GET","POST"])
def reserve(cabin_id, date_iso, slot):
    col    = mongo_connect()
    cabine = col.find_one({"id": cabin_id})
    if request.method == "POST":
        first = request.form["first_name"]
        last  = request.form["last_name"]
        email = request.form["email"]
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
    error   = None
    prefill = request.args.get("code", "").strip().lower()
    if request.method == "POST":
        code = request.form["code"].strip().lower()
        doc  = mongo_connect().find_one({"agendamentos.senha_unica": code})
        if not doc:
            error = "Código inválido."
        else:
            ag = next(a for a in doc["agendamentos"] if a["senha_unica"] == code)
            dt_inicio = datetime.strptime(f"{ag['dia']} {ag['hora']}", "%Y-%m-%d %H:%M")
            dt_fim    = dt_inicio + timedelta(minutes=30)
            agora     = datetime.utcnow() + timedelta(hours=LOCAL_TZ_OFFSET)
            if dt_inicio <= agora <= dt_fim:
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
    return render_template('acessar.html', error=error, prefill=prefill)

# ——— Nova rota de controle —————————————————

@app.route('/controle')
@requires_auth
def controle():
    """
    Exibe painel com 8 botões para controle manual das 8 cabines.
    """
    return render_template('controle.html')

@app.route('/controle/abrir/<int:cabin_id>')
@requires_auth
def controle_abrir(cabin_id):
    """
    Publica 'abrir' pelo MQTT na cabine indicada e retorna ao painel.
    """
    mqtt_publish_open(cabin_id)
    return redirect(url_for('controle'))

if __name__ == '__main__':
    app.run(debug=True)
