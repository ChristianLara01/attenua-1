import logging
from flask import Flask, request, redirect, url_for
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
EMAIL_SENDER   = "atualle@atualle.com.br"
EMAIL_PASSWORD = "@12Duda04"
SMTP_HOST      = "smtp.hostinger.com"
SMTP_PORT      = 465

# ——— Configurações de MQTT —————————————————
MQTT_HOST       = "917a3939272f48c09215df8a39c82c46.s1.eu.hivemq.cloud"
MQTT_PORT       = 8883
MQTT_USER       = "attenua"
MQTT_PASS       = "Atualle1"

LOCAL_TZ_OFFSET = -3  # UTC–3

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
    year, month, day = reserv["dia"].split('-')
    date_fmt = f"{day}/{month}/{year}"
    msg = MIMEMultipart("alternative")
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = reserv["id_usuario"]
    msg["Subject"] = "Reserva Confirmada – ATTENUA CABINES ACÚSTICAS"

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
    .access-btn {{padding:20px;text-align:center}}
    .access-btn a {{display:inline-block;padding:12px 24px;
                    background:#0069d9;color:#fff;text-decoration:none;
                    border-radius:4px;font-weight:bold}}
    .links {{padding:20px;text-align:center;background:#f0f0f0}}
    .links a {{margin:.5rem;padding:10px 20px;background:#28a745;color:#fff;
               text-decoration:none;border-radius:4px;font-size:.95rem}}
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

# ——— Rotas principais ——————————————————

@app.route('/')
def catalog():
    today = datetime.now()
    dias = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1)]
    return render_template('catalog.html', dias=dias)

@app.route('/api/available_slots/<date_iso>')
def available_slots(date_iso):
    # ... sua lógica de feira/slots ...
    pass  # omitido para brevidade

@app.route('/available/<date_iso>/<slot>')
def available(date_iso, slot):
    # ... sua lógica ...
    pass

@app.route('/reserve/<int:cabin_id>/<date_iso>/<slot>', methods=["GET","POST"])
def reserve(cabin_id, date_iso, slot):
    # ... sua lógica ...
    pass

@app.route('/activate_success/<code>')
def activate_success(code):
    return render_template('activate_success.html', code=code)

@app.route('/acessar', methods=["GET","POST"])
def acessar():
    # ... sua lógica ...
    pass

# ——— Nova rota de controle protegido por senha ——————————————————

@app.route('/controle')
def controle():
    password = request.args.get('password', '')
    action   = request.args.get('action', '')
    cabin_id = request.args.get('cabin_id', '')

    # se não fornecer senha correta, exibe formulário de login
    if password != MQTT_PASS:
        return '''
        <h2>Login no Painel de Controle</h2>
        <form action="/controle" method="get">
          <input type="password" name="password" placeholder="Senha" required>
          <button type="submit">Entrar</button>
        </form>
        '''

    # se vier ação de abrir cabine
    msg = ''
    if action == 'open' and cabin_id.isdigit():
        try:
            mqtt_publish_open(int(cabin_id))
            msg = f'Cabine {cabin_id} acionada com sucesso.'
        except Exception:
            msg = 'Falha ao enviar comando MQTT.'

    # gera 8 botões de controle
    buttons = ''.join(f'''
      <form style="display:inline-block;margin:5px;" action="/controle" method="get">
        <input type="hidden" name="password" value="{password}">
        <input type="hidden" name="action"    value="open">
        <input type="hidden" name="cabin_id"  value="{i}">
        <button type="submit">Cabine {i:02d}</button>
      </form>
    ''' for i in range(1,9))

    return f'''
      <h1>Painel de Controle MQTT</h1>
      <p style="color:green;">{msg}</p>
      {buttons}
    '''

if __name__ == '__main__':
    app.run(debug=True)
