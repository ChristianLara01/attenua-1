from flask import Flask, render_template, request, jsonify, redirect
from flask_mail import Mail, Message
import pymongo
import secrets
import datetime
from bson.objectid import ObjectId

app = Flask(__name__)

# Configurações de e-mail (Hostinger)
app.config['MAIL_SERVER'] = 'smtp.hostinger.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'christian@atualle.com.br'
app.config['MAIL_PASSWORD'] = '@12Duda04'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = ('Attenua', 'christian@atualle.com.br')
mail = Mail(app)

# Conexão com MongoDB
def mongo_connect():
    client = pymongo.MongoClient("mongodb+srv://attenua:agendamento@attenua.qypnpl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    return client['attenua']['cabines']

@app.route('/')
def home():
    today = datetime.date.today()
    dias = [(today + datetime.timedelta(days=i)).isoformat() for i in range(5)]
    return render_template('index.html', dias=dias)

@app.route('/available/<date>/<hora>')
def available(date, hora):
    col = mongo_connect()
    cabines = list(col.find({}, {'_id': 0}))
    for c in cabines:
        ags = c.get('agendamentos', [])
        for a in ags:
            if a['dia'] == date and a['hora'] == hora:
                c['disponivel'] = False
                break
        else:
            c['disponivel'] = True
    cabines_disponiveis = [c for c in cabines if c['disponivel']]
    return jsonify(cabines_disponiveis)

@app.route('/reserve/<int:cabin_id>/<date>/<hora>')
def reserve(cabin_id, date, hora):
    return render_template('reserve.html', cabin_id=cabin_id, date=date, hora=hora)

@app.route('/submit', methods=['POST'])
def reserve_submit():
    cabin_id = int(request.form['cabin_id'])
    date = request.form['date']
    hora = request.form['hora']
    email = request.form['email']
    first = request.form['first_name']
    last = request.form['last_name']
    code = secrets.token_hex(3)

    col = mongo_connect()
    while col.find_one({"agendamentos.senha_unica": code}):
        code = secrets.token_hex(3)

    novo = {
        'dia': date,
        'hora': hora,
        'qtde_horas': 1,
        'id_usuario': email,
        'first_name': first,
        'last_name': last,
        'senha_unica': code,
        'cabin_id': cabin_id
    }

    col.update_one({'id': cabin_id}, {'$push': {'agendamentos': novo}})
    
    # Envia e-mail
    try:
        msg = Message("Confirmação de Reserva - Attenua", recipients=[email])
        msg.body = f"""
Olá, {first} {last}!

Sua reserva foi confirmada:
- Data: {date}
- Horário: {hora}
- Cabine ID: {cabin_id}
- Código de Acesso: {code}

Use esse código para ativar sua cabine no horário reservado.

Atenciosamente,
Equipe Attenua
"""
        mail.send(msg)
    except Exception as e:
        print("Erro ao enviar e-mail:", e)

    return render_template('success.html', code=code)

@app.route('/acesso')
def acesso():
    return render_template('acesso.html')

@app.route('/ativar', methods=['POST'])
def ativar():
    codigo = request.form['codigo']
    col = mongo_connect()
    cabine = col.find_one({"agendamentos.senha_unica": codigo})
    if cabine:
        return render_template('ativada.html', cabine=cabine, codigo=codigo)
    else:
        return render_template('erro.html', mensagem="Código inválido ou inexistente.")

if __name__ == '__main__':
    app.run(debug=True)
