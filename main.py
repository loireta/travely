from flask import Flask, jsonify, render_template, redirect, request, session, g
import mysql.connector

import boto3
from botocore.exceptions import NoCredentialsError

from werkzeug.utils import secure_filename
import uuid

import os
import datetime as dt
from datetime import datetime, date, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]

aws_access_key = 'SUA CHAVE DE ACESSO DO AMAZON AWS S3 AQUI'
aws_secret_access_key = 'SUA CHAVE SECRETA DO AMAZON AWS S3 AQUI'
bucket_name = 'NOME DO BUCKET DO AMAZON AWS S3 AQUI'

app = Flask(__name__)
app.secret_key = "travely"

datadehoje = datetime.now()

conexaoDB = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="Trevely"
)

ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1 )[1].lower() in ALLOWED_EXTENSIONS

s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key
)

@app.template_filter('format_date')
def format_date(value):
    return value.strftime('%d/%m/%Y')

@app.template_filter('format_hour')
def format_hour(value):
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours:02d}h {minutes:02d}min"
    elif hasattr(value, 'strftime'):
        return value.strftime('%Hh %Mmin')
    return value

@app.template_filter('format_hour_minute')
def format_hour(value):
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}"
    elif hasattr(value, 'strftime'):
        return value.strftime('%H:%M')
    return value

def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def verifica_sessao():
    return "login" in session and session['login']

def get_media_estrelas(id_passeio):
    cursorDB = conexaoDB.cursor()
    consulta_sql = '''
        SELECT AVG(estrelas) AS mediaEstrelas
        FROM avaliacaoP
        WHERE idPasseio = %s;
    '''
    cursorDB.execute(consulta_sql, (id_passeio,))
    media_estrelas = cursorDB.fetchone()
    cursorDB.close()
    
    return media_estrelas[0] if media_estrelas else None

def buscar_passeios_por_nome(event_name):
    cursorDB = conexaoDB.cursor()
    comandoSQL = f'''
        SELECT 
            p.idPasseio,
            p.nome AS nomePasseio,
            p.estadoPasseio,
            p.cidadePasseio,
            p.bairroEndPasseio,
            p.valor,
            c.nome AS categoria,
            p.descricaoPasseio
        FROM 
            agendamentos p
        JOIN 
            categoria c ON p.categoria = c.idCategoria
        WHERE 
            p.nome = %s;
    '''
    cursorDB.execute(comandoSQL, (event_name,))
    passeios = cursorDB.fetchall()
    cursorDB.close()
    return passeios

@app.route('/')
def home():
    cursorDB = conexaoDB.cursor()
    consultaAgendamentos = '''
        SELECT 
        ag.idAgendamento,
        ag.event_id,
        p.idPasseio,
        p.nome AS nomePasseio,
        p.estadoPasseio,
        p.cidadePasseio,
        p.bairroEndPasseio,
        p.valor,
        c.nome,
        p.descricaoPasseio,
        ag.qtdMaxTur,
        ag.dataAgendamento,
        ag.horaAgendamento,
        ag.duracaoAgendamento,
        GROUP_CONCAT(img.caminhoS3 SEPARATOR ','),
        (
            SELECT AVG(estrelas)
            FROM avaliacaoP
            WHERE avaliacaoP.idPasseio = p.idPasseio
        )
    FROM 
        agendamento ag
    JOIN 
        passeio p ON ag.idPasseio = p.idPasseio
    JOIN 
        categoria c ON p.categoria = c.idCategoria
    LEFT JOIN 
        imagens img ON p.idPasseio = img.idPasseio
    WHERE 
        ag.dataAgendamento >= CURDATE()
    GROUP BY 
        ag.idAgendamento
    ORDER BY 
        ag.idAgendamento DESC;
    '''
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(consultaAgendamentos)
    agendamentos = cursorDB.fetchall()

    consultaTop10 = '''
        SELECT 
            ag.idAgendamento,
            p.nome AS nomePasseio,
            ag.dataAgendamento,
            ag.horaAgendamento,
            MIN(img.caminhoS3),
            AVG(av.estrelas)
        FROM 
            agendamento ag
        JOIN 
            passeio p ON ag.idPasseio = p.idPasseio
        LEFT JOIN 
            imagens img ON p.idPasseio = img.idPasseio
        LEFT JOIN 
            avaliacaop av ON p.idPasseio = av.idPasseio
        WHERE 
            ag.dataAgendamento >= CURDATE()
        GROUP BY 
            ag.idAgendamento, p.nome, ag.dataAgendamento, ag.horaAgendamento
        ORDER BY 
            AVG(av.estrelas) DESC
        LIMIT 10;
    '''
    cursorDB.execute(consultaTop10)
    Top10 = cursorDB.fetchall()

    idUsuario = session.get('idUsuario')
    tipo_usuario = session.get('tipo')
    imgUsuario = session.get('imgUsuario')

    if tipo_usuario == 1:    
        return redirect("/homeGuia")


    if idUsuario:
        pesquisaUsuario = '''
            SELECT nome
            FROM usuario 
            WHERE idUsuario = %s
            '''
        cursorDB.execute(pesquisaUsuario, (idUsuario,))
        nomeLogado = cursorDB.fetchone()
    else:
        nomeLogado = None

    return render_template("home.html", agendamentos=agendamentos, tipo=tipo_usuario, idUsuario=idUsuario, imgUsuario=imgUsuario, nomeLogado=nomeLogado, Top10=Top10)

    

@app.route("/cadastrarGuia", methods=['POST'])
def cadGuia():
    creds = main()

    nome = request.form['nome']
    cpf_cnpj = request.form['cpf_cnpj']
    telefone = request.form['telefone']
    data_nascimento = request.form['data_nascimento']
    cep = request.form['cep']
    cidadeEndUser = request.form['cidadeEndUser']
    estadoEndUser = request.form['estadoEndUser']
    bairroEndUser = request.form['bairroEndUser']
    ruaEndUser = request.form['ruaEndUser']
    numEndUser = request.form['numEndUser']
    email = request.form['email']
    senha = request.form['senha']
    cadastur = request.form['cadastur']
    chavePix = request.form['chavePix']

    tipo = True


    

    if 'imagem' not in request.files:
        return render_template('error.html', msg="Nenhuma imagem fornecida.")

    imagem = request.files['imagem']

    if imagem.filename == '':
        return render_template('error.html', msg="Nenhuma imagem selecionada.")

    if not allowed_file(imagem.filename):
        return render_template('error.html', msg="Tipo de arquivo não suportado. Apenas PNG, JPG e JPEG são aceitos.")

    try:
        comandoSQL_usuario = """
            INSERT INTO usuario (nome, cpfCnpj, numTelefone, dataNasc, cepEndUser, cidadeUser, estadoEndUser, bairroEndUser, ruaEndUser, numEndUser, email, senha, tipo) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores_usuario = (nome, cpf_cnpj, telefone, data_nascimento, cep, cidadeEndUser, estadoEndUser, bairroEndUser, ruaEndUser, numEndUser, email, senha, tipo)

        cursorDB = conexaoDB.cursor()
        cursorDB.execute(comandoSQL_usuario, valores_usuario)
        

        id_usuario = cursorDB.lastrowid

        comandoSQLadUsuario = f"""
            INSERT INTO adUsuario (Trabalho, Lingua, Descricao, idUsuario) 
            VALUES ('Não informado', 'Portugues','Não informado', {id_usuario})
        """
        cursorDB.execute(comandoSQLadUsuario)
        conexaoDB.commit()

        nome_arquivo = secure_filename(imagem.filename)
        new_filename = uuid.uuid4().hex + '.' + imagem.filename.rsplit('.', 1)[1].lower()
        nome_objeto = f'imagens/{new_filename}'

        s3_client.upload_fileobj(imagem, bucket_name, nome_objeto)
        imagem_url = f"https://{bucket_name}.s3.amazonaws.com/{nome_objeto}"

        cursorDB.execute('''
            SELECT idImagem FROM imagemUsuario WHERE idUsuario = %s
        ''', (id_usuario,))
        imagem_existente = cursorDB.fetchone()

        if imagem_existente:
            cursorDB.execute('''
                UPDATE imagemUsuario 
                SET nomeArquivo = %s, caminhoS3 = %s
                WHERE idUsuario = %s
            ''', (nome_arquivo, imagem_url, id_usuario))
        else:
            cursorDB.execute('''
                INSERT INTO imagemUsuario (nomeArquivo, caminhoS3, idUsuario)
                VALUES (%s, %s, %s)
            ''', (nome_arquivo, imagem_url, id_usuario))

        conexaoDB.commit()

    except Exception as e:
        print(f"Erro ao fazer upload da imagem para o S3: {str(e)}")
        conexaoDB.rollback()
        return render_template('error.html', msg="Erro ao fazer upload da imagem para o S3.")

    try:
        service = build("calendar", "v3", credentials=creds)
        calendar = {
            'summary': f'{id_usuario} - {nome}',
            'timeZone': 'America/Los_Angeles'
        }

        created_calendar = service.calendars().insert(body=calendar).execute()
        calendar_id = created_calendar['id']
        print(f"Calendário criado com ID: {calendar_id}")

    except HttpError as error:
        print(f"Erro ao criar calendário no Google Calendar: {error}")
        return render_template('error.html', msg="Erro ao criar calendário no Google Calendar.")

    comandoSQL_adGuia = """
        INSERT INTO adGuia (cadastur, chavePix, idUsuario, calendar_id) 
        VALUES (%s, %s, %s, %s)
    """
    valores_adGuia = (cadastur, chavePix, id_usuario, calendar_id)
    cursorDB.execute(comandoSQL_adGuia, valores_adGuia)
    conexaoDB.commit()


    idUsuario = session.get('idUsuario')
    tipo_usuario = session.get('tipo')
    imgUsuario = session.get('imgUsuario')

    if idUsuario:
        pesquisaUsuario = '''
            SELECT nome
            FROM usuario 
            WHERE idUsuario = %s
            '''
        cursorDB.execute(pesquisaUsuario, (idUsuario,))
        nomeLogado = cursorDB.fetchone()
    else:
        nomeLogado = None


    cursorDB.close()

    return redirect('/login')


@app.route('/adm')
def adm():
    cursorDB = conexaoDB.cursor()

    if not verifica_sessao(): 
        return render_template('/login.html')
    
    cursorDB = conexaoDB.cursor()

    idUsuario = session.get('idUsuario')
    tipo_usuario = session.get('tipo')

    if tipo_usuario == 0:
        return redirect('/home')

    comandoSQL1 = f'SELECT nome FROM usuario WHERE idUsuario = {idUsuario}'
    cursorDB.execute(comandoSQL1)
    nomeGuia = cursorDB.fetchone()


    comandoSQL = f'''
    SELECT p.*, MIN(img.caminhoS3)
    FROM passeio p
    LEFT JOIN imagens img ON p.idPasseio = img.idPasseio
    WHERE p.idGuia = {idUsuario}
    GROUP BY p.idPasseio
    ORDER BY p.idPasseio DESC
    '''
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    passeios = cursorDB.fetchall()

    imgUsuario = session.get('imgUsuario')

    if idUsuario:
        pesquisaUsuario = '''
            SELECT nome
            FROM usuario 
            WHERE idUsuario = %s
            '''
        cursorDB.execute(pesquisaUsuario, (idUsuario,))
        nomeLogado = cursorDB.fetchone()
    else:
        nomeLogado = None

    cursorDB.close()
    return render_template("adm.html",passeios=passeios,idUsuario=idUsuario, imgUsuario=imgUsuario, tipo=tipo_usuario, nomeLogado=nomeLogado, nomeGuia=nomeGuia)

@app.route("/cadPasseio", methods=['POST'])
def cadpasseio():
    nome = request.form['nome']
    estadoPasseio = request.form['estadoPasseio']
    cidadePasseio = request.form['cidadePasseio']
    bairroEndPasseio = request.form['bairroEndPasseio']
    valor = request.form['valor']
    categoria = request.form['categoria']
    descricaoPasseio = request.form['descricao']
    
    idGuia = session.get('idUsuario')  

    if idGuia is None:
        return render_template('error.html', msg="ID do Guia não fornecido ou usuário não autenticado.")
    
    if 'imagem' not in request.files:
        return render_template('error.html', msg="Nenhuma imagem fornecida.")

    imagens = request.files.getlist('imagem')
    uploaded_files = []

    comandoSQL = '''
    INSERT INTO passeio (nome, estadoPasseio, cidadePasseio, bairroEndPasseio, valor, categoria, descricaoPasseio, idGuia)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    '''
    valores = (nome, estadoPasseio, cidadePasseio, bairroEndPasseio, valor, categoria, descricaoPasseio, idGuia)
    
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL, valores)

    idPasseio = cursorDB.lastrowid 
    
    if imagens:
        for file in imagens:
            try:
                if file.filename == '':
                    return render_template('error.html', msg="Nenhum arquivo selecionado.")
                if not allowed_file(file.filename):
                    return render_template('error.html', msg="Arquivo não suportado. Somente imagens são aceitas.")
                
                nome_arquivo = secure_filename(file.filename)
                
                new_filename = uuid.uuid4().hex +  '.'+ file.filename.rsplit('.', 1)[1].lower()
                
                nome_objeto = f'imagens/{new_filename}'
                s3_client.upload_fileobj(file, bucket_name, nome_objeto)
                imagem_url = f"https://{bucket_name}.s3.amazonaws.com/{nome_objeto}"
                uploaded_files.append(nome_arquivo)

                comandoSQL_imagem = '''
                INSERT INTO imagens (nomeArquivo, caminhoS3, idPasseio)
                VALUES (%s, %s, %s)
                '''
                valores_imagem = (new_filename, imagem_url, idPasseio)
                cursorDB = conexaoDB.cursor()
                cursorDB.execute(comandoSQL_imagem, valores_imagem)
            except Exception as e:
                print(f"Erro ao fazer upload: {str(e)}")
                return render_template('error.html', msg="Erro ao fazer upload da imagem para o S3.")
            try:
                conexaoDB.commit()
            except mysql.connector.IntegrityError as err:
                print(f"Error: {err}")
                conexaoDB.rollback()
                return render_template('error.html', msg="Erro de integridade ao tentar cadastrar o passeio.")
            finally:
                idUsuario = session.get('idUsuario')
                tipo_usuario = session.get('tipo')
                imgUsuario = session.get('imgUsuario')

                if idUsuario:
                    pesquisaUsuario = '''
                        SELECT nome
                        FROM usuario 
                        WHERE idUsuario = %s
                        '''
                    cursorDB.execute(pesquisaUsuario, (idUsuario,))
                    nomeLogado = cursorDB.fetchone()
                else:
                    nomeLogado = None
                cursorDB.close()


        return redirect('/adm')

@app.route('/agendarPasseio/<int:id>', methods=['POST'])
def agendarPasseio(id):
    creds = main()

    service = build("calendar", "v3", credentials=creds)
    idUsuario = session.get('idUsuario')

    dataAgendamento = request.form['dataAgendamento']
    horaAgendamento = request.form['horaAgendamento']
    duracao = int(request.form['duracao'])
    qtdMaxTur = request.form['qtdMaxTur']

    comandoSQL = f'SELECT * FROM passeio WHERE idPasseio = {id}'
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    passeio = cursorDB.fetchone()

    hora_final = (dt.datetime.strptime(f'{dataAgendamento} {horaAgendamento}', '%Y-%m-%d %H:%M')
                  + dt.timedelta(hours=duracao)).strftime('%Y-%m-%dT%H:%M:%S')

    parametrosApi = '''
    SELECT g.calendar_id
    FROM adGuia g
    JOIN passeio p ON g.idUsuario = p.idGuia
    WHERE p.idPasseio = %s;
    '''
    cursorDB.execute(parametrosApi, (passeio[0],))
    api = cursorDB.fetchone()

    try:
        calendar_id = api[0]
        evento = {
        'summary': f'{passeio[1]}',
        'location': f'{passeio[4]} - {passeio[3]}/{passeio[2]}',  
        'description': 'Turistas:',
        'start': {
            'dateTime': f'{dataAgendamento}T{horaAgendamento}:00',
            'timeZone': 'America/Sao_Paulo',
        },
        'end': {
            'dateTime': hora_final,
            'timeZone': 'America/Sao_Paulo',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

        event = service.events().insert(calendarId=calendar_id, body=evento).execute()
        event_id = event['id']
    except HttpError as error:
        print(f"Erro ao criar evento: {error}")

    cursorDB = conexaoDB.cursor()
    comandoInsert = '''
        INSERT INTO agendamento (qtdMaxTur, dataAgendamento, horaAgendamento, idPasseio, idGuiaAg, duracaoAgendamento, event_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    '''
    cursorDB.execute(comandoInsert, (qtdMaxTur, dataAgendamento, horaAgendamento, id, idUsuario, duracao, event_id))
    conexaoDB.commit()
    cursorDB.close()
    return redirect('/home')

@app.route("/cadastrar", methods=['GET', 'PUT', 'DELETE', 'PATCH'])
def handle_wrong_methods():
    return redirect('/') 

@app.route("/cadpasseio")
def novopasseio():
    tipo_usuario = session.get('tipo')
    if not verifica_sessao(): 
        return render_template('login.html')
    
    cursorDB = conexaoDB.cursor()
    comandoSQL_categorias = "SELECT idCategoria, nome FROM categoria"
    cursorDB.execute(comandoSQL_categorias)
    categorias = cursorDB.fetchall()

    idUsuario = session.get('idUsuario')
    imgUsuario = session.get('imgUsuario')

    if idUsuario:
        pesquisaUsuario = '''
            SELECT nome
            FROM usuario 
            WHERE idUsuario = %s
            '''
        cursorDB.execute(pesquisaUsuario, (idUsuario,))
        nomeLogado = cursorDB.fetchone()
    else:
        nomeLogado = None

    cursorDB.close()
    
    return render_template("cadPasseio.html",tipo=tipo_usuario, categorias=categorias, idUsuario=idUsuario, imgUsuario=imgUsuario, nomeLogado=nomeLogado)

@app.route('/login')
def login():
    if not verifica_sessao(): 
        return render_template('/login.html')
    else: 
        return redirect("/adm")

@app.route('/redirecionarGuia', methods=['GET'])
def redirecionar_guia():
    return redirect('/cadGuia')

@app.route('/cadGuia')
def cad_guia():
    return render_template('cadGuia.html')

@app.route('/redirecionarTurista', methods=['GET'])
def redirecionar_turista():
    return redirect('/cadTurista')

@app.route('/cadTurista')
def cad_turista():
    return render_template('cadTurista.html')

@app.route('/logout')
def logout():
    if verifica_sessao():
        session.clear() 
    
    return redirect('/')

@app.route("/acesso", methods=['POST'])
def acesso():
    usuario_informado = request.form['usuario']
    senha_informado = request.form['senha']

    if not usuario_informado or not senha_informado:
        return render_template('login.html', msg="Todos os campos são obrigatórios!")

    cursorDB = conexaoDB.cursor()
    comandoSQL = "SELECT * FROM usuario WHERE email = %s AND senha = %s"
    cursorDB.execute(comandoSQL, (usuario_informado, senha_informado))
    resultado = cursorDB.fetchone() 

    if resultado:
        pesquisaImgUsuario = "SELECT caminhoS3  FROM imagemusuario WHERE idUsuario = %s;"
        cursorDB.execute(pesquisaImgUsuario, (resultado[0],))
        imgUsuario = cursorDB.fetchone() 

        session['login'] = True 
        session['idUsuario'] = resultado[0]
        session['imgUsuario'] = imgUsuario

        cursorDB.close()

        if resultado[13]:  
            session['tipo'] = True
        else:
            session['tipo'] = False

        return redirect('/adm')
    else:
        return render_template('login.html', msg="O usuário ou senha estão incorretos")

@app.route('/deletar/<int:id>')
def excluir(id):
    if not verifica_sessao():  
        return render_template('/login.html')
    
    comandoSQL_buscar_passeio = '''
        SELECT idPasseio 
        FROM passeio 
        WHERE  idPasseio= %s
    '''

    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL_buscar_passeio, (id,))
    id_passeio = cursorDB.fetchone()

    if id_passeio:
        comandoSQL_deletar_imagens = '''
            DELETE FROM imagens
            WHERE idPasseio = %s
        '''
        cursorDB.execute(comandoSQL_deletar_imagens, (id_passeio[0],))

    comandoSQL_deletar_passeio = '''
        DELETE FROM passeio
        WHERE idPasseio = %s
    '''

    cursorDB.execute(comandoSQL_deletar_passeio, (id,))
    conexaoDB.commit()
    cursorDB.close()
    return redirect('/adm')

@app.route('/detalhes/<int:id>', methods=['GET', 'POST'])
def detalhes(id):   
    cursorDB = conexaoDB.cursor()

    if request.method == 'POST':
        qtdTurAg = int(request.form.get('qtdTurAg', 1))
        
        pesquisaValor = f'SELECT p.valor FROM agendamento a JOIN passeio p ON a.idPasseio = p.idPasseio WHERE a.idAgendamento = {id};'
        cursorDB.execute(pesquisaValor)
        valor_passeio = cursorDB.fetchone()[0]

        total = valor_passeio * qtdTurAg
    else:
        pesquisaValor = f'SELECT p.valor FROM agendamento a JOIN passeio p ON a.idPasseio = p.idPasseio WHERE a.idAgendamento = {id};'
        cursorDB.execute(pesquisaValor)
        valor_passeio = cursorDB.fetchone()[0]
        total = valor_passeio
        qtdTurAg = 1

    pesquisaAgendamento = f'''SELECT 
        ag.idAgendamento,
        ag.event_id,
        p.idPasseio,
        p.nome,
        p.estadoPasseio,
        p.cidadePasseio,
        p.bairroEndPasseio,
        p.valor,
        c.nome,
        p.descricaoPasseio,
        ag.qtdMaxTur,
        ag.dataAgendamento,
        ag.horaAgendamento,
        ag.duracaoAgendamento,
        ag.idGuiaAg
    FROM 
        agendamento ag
    JOIN 
        passeio p ON ag.idPasseio = p.idPasseio
    JOIN 
        categoria c ON p.categoria = c.idCategoria 
    WHERE 
        idAgendamento = {id};'''
    cursorDB.execute(pesquisaAgendamento)
    agendamento = cursorDB.fetchone()

    media_estrelas = get_media_estrelas(agendamento[2]) 

    pesquisaImagem = f'''
        SELECT
            *
        FROM
            imagens
        WHERE 
            idPasseio = {agendamento[2]};
    '''
    cursorDB.execute(pesquisaImagem)
    imgsPasseio = cursorDB.fetchall()

    pesquisaGuia = f'SELECT * FROM usuario WHERE idUsuario = {agendamento[14]}'
    cursorDB.execute(pesquisaGuia)
    dadosGuia = cursorDB.fetchone()
    
    pesquisaImagemGuia = f'''
        SELECT 
        iu.caminhoS3 AS fotoGuia
    FROM 
        agendamento ag
    JOIN 
        imagemusuario iu ON iu.idUsuario = ag.idGuiaAg
    WHERE 
        ag.idAgendamento = {id}

    '''
    cursorDB.execute(pesquisaImagemGuia)
    imgGuia = cursorDB.fetchone()

    pesquisaAgendamentos = '''
        SELECT 
            ag.idAgendamento,
            ag.event_id,
            p.idPasseio,
            p.nome AS nomePasseio,
            p.estadoPasseio,
            p.cidadePasseio,
            p.bairroEndPasseio,
            p.valor,
            c.nome,
            p.descricaoPasseio,
            ag.qtdMaxTur,
            ag.dataAgendamento,
            ag.horaAgendamento,
            ag.duracaoAgendamento,
            GROUP_CONCAT(img.caminhoS3 SEPARATOR ','),
            (
                SELECT AVG(estrelas)
                FROM avaliacaoP
                WHERE avaliacaoP.idPasseio = p.idPasseio
            ) AS mediaEstrelas
        FROM 
            agendamento ag
        JOIN 
            passeio p ON ag.idPasseio = p.idPasseio
        JOIN 
            categoria c ON p.categoria = c.idCategoria
        LEFT JOIN 
            imagens img ON p.idPasseio = img.idPasseio
        WHERE 
            ag.dataAgendamento >= CURDATE()
        GROUP BY 
            ag.idAgendamento
        ORDER BY 
            ag.idAgendamento DESC;
        '''
    cursorDB.execute(pesquisaAgendamentos)
    maisAgendamentos = cursorDB.fetchall()

    pesquisaAvaliacao = f'''
        SELECT 
            avaliacaoP.dataAvaliacao,
            avaliacaoP.descricaoAvaliacao,
            avaliacaoP.estrelas, 
            usuario.nome, 
            usuario.cidadeUser, 
            usuario.estadoEndUser,
            imagemusuario.caminhoS3,
            avaliacaoP.usuarioAvaliador
        FROM 
            avaliacaoP
        JOIN 
            usuario ON avaliacaoP.usuarioAvaliador = usuario.idUsuario
        LEFT JOIN 
            imagemusuario ON usuario.idUsuario = imagemusuario.idUsuario
        WHERE 
            avaliacaoP.idPasseio = {agendamento[2]};
        '''
    cursorDB.execute(pesquisaAvaliacao)
    avaliacoes = cursorDB.fetchall()

    tipo_usuario = session.get('tipo')

    idUsuario = session.get('idUsuario')
    imgUsuario = session.get('imgUsuario')

    if idUsuario:
        pesquisaUsuario = '''
            SELECT nome
            FROM usuario 
            WHERE idUsuario = %s
            '''
        cursorDB.execute(pesquisaUsuario, (idUsuario,))
        nomeLogado = cursorDB.fetchone()
    else:
        nomeLogado = None

    cursorDB.close()

    return render_template(
        "detalhes.html", 
        agendamento=agendamento, 
        maisAgendamentos=maisAgendamentos, 
        imgsPasseio=imgsPasseio, 
        tipo=tipo_usuario, 
        guia=dadosGuia, 
        total=total, 
        qtdTurAg=qtdTurAg, 
        valor=valor_passeio, 
        avaliacoes=avaliacoes, 
        media_estrelas=media_estrelas, 
        id=id,
        idUsuario=idUsuario,
        imgUsuario=imgUsuario,
        nomeLogado=nomeLogado,
        imgGuia=imgGuia
    )

@app.route("/cadastrarTurista", methods=['POST'])
def cadTurista():
    nome = request.form['nome']
    cpf_cnpj = request.form['cpf_cnpj']
    telefone = request.form['telefone']
    data_nascimento = request.form['data_nascimento']
    cep = request.form['cep']
    cidadeEndUser = request.form['cidadeEndUser']
    estadoEndUser = request.form['estadoEndUser']    
    ruaEndUser = request.form['ruaEndUser']
    bairroEndUser = request.form['bairroEndUser']
    numEndUser = request.form['numEndUser']
    email = request.form['email']
    senha = request.form['senha']

    cursorDB = conexaoDB.cursor()

    if not all([nome, cpf_cnpj, telefone, data_nascimento, cep, cidadeEndUser, estadoEndUser, bairroEndUser, ruaEndUser, bairroEndUser, numEndUser, email, senha]):
        return render_template('cadTurista.html', msg="Todos os campos são obrigatórios!")

    tipo = False

    comandoSQL_usuario = """
        INSERT INTO usuario (nome, cpfCnpj, numTelefone, dataNasc, cepEndUser, cidadeUser, estadoEndUser, bairroEndUser, ruaEndUser, numEndUser, email, senha, tipo) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    valores_usuario = (nome, cpf_cnpj, telefone, data_nascimento, cep, cidadeEndUser, estadoEndUser, bairroEndUser, ruaEndUser, numEndUser, email, senha, tipo)
    cursorDB.execute(comandoSQL_usuario, valores_usuario)
    conexaoDB.commit()

    id_usuario = cursorDB.lastrowid

    comandoSQLadUsuario = f"""
            INSERT INTO adUsuario (Trabalho, Lingua, Descricao, idUsuario) 
            VALUES ('Não informado', 'Portugues','Não informado', {id_usuario})
        """
    cursorDB.execute(comandoSQLadUsuario)
    conexaoDB.commit()

    cursorDB.close()
    return redirect('/login')

@app.route("/confirmaPag/<int:id>", methods=['GET', 'POST'])
def confirmaPag(id):
    cursorDB = conexaoDB.cursor()

    if not verifica_sessao(): 
        return render_template('/login.html')
    
    pesquisaAgendamento = f'''
        SELECT 
            ag.idAgendamento,
            ag.event_id,
            p.idPasseio,
            p.nome,
            p.estadoPasseio,
            p.cidadePasseio,
            p.bairroEndPasseio,
            p.valor,
            c.nome,
            p.descricaoPasseio,
            ag.qtdMaxTur,
            ag.dataAgendamento,
            ag.horaAgendamento,
            ag.duracaoAgendamento,
            ag.idGuiaAg,
            MIN(img.caminhoS3)
        FROM 
            agendamento ag
        JOIN 
            passeio p ON ag.idPasseio = p.idPasseio
        JOIN 
            categoria c ON p.categoria = c.idCategoria
        LEFT JOIN 
            imagens img ON p.idPasseio = img.idPasseio
        WHERE 
            ag.idAgendamento = {id}
        GROUP BY 
            ag.idAgendamento, p.idPasseio, c.idCategoria;
    '''
    cursorDB.execute(pesquisaAgendamento)
    agendamento = cursorDB.fetchone()  
 

    pesquisaImagem = f'''
        SELECT
            caminhoS3
        FROM
            imagens
        WHERE 
            idPasseio = {agendamento[2]}
        LIMIT 1;
    '''
    cursorDB.execute(pesquisaImagem)
    imgsPasseio = cursorDB.fetchone()
    
    media_estrelas = get_media_estrelas(agendamento[2]) 

    if request.method == 'POST':
        qtdTurAg = int(request.form.get('qtdTurAg', 1))
        total = agendamento[7] * qtdTurAg

    else:
        comandoSQL = f'SELECT p.valor FROM agendamento a JOIN passeio p ON a.idPasseio = p.idPasseio WHERE a.idAgendamento = {id};'
        cursorDB.execute(comandoSQL)
        valor_passeio = cursorDB.fetchone()[0]
        total = valor_passeio
        qtdTurAg = 1
    

    idUsuario = session.get('idUsuario')
    tipo_usuario = session.get('tipo')
    imgUsuario = session.get('imgUsuario')

    if idUsuario:
        pesquisaUsuario = '''
            SELECT nome
            FROM usuario 
            WHERE idUsuario = %s
            '''
        cursorDB.execute(pesquisaUsuario, (idUsuario,))
        nomeLogado = cursorDB.fetchone()
    else:
        nomeLogado = None


    cursorDB.close()
    return render_template("confirmaPag.html", imgsPasseio=imgsPasseio , agendamento=agendamento, total=total, qtdTurAg=qtdTurAg, media_estrelas=media_estrelas, idUsuario=idUsuario, imgUsuario=imgUsuario, tipo=tipo_usuario, nomeLogado=nomeLogado)

@app.route("/confirmarGrupoPasseio/<int:id>/<int:qtdTurAg>", methods=['POST'])
def confirmarGrupoPasseio(id, qtdTurAg):
    creds = main()
    cursorDB = conexaoDB.cursor()

    service = build("calendar", "v3", credentials=creds)

    idTurista = session.get('idUsuario')  

    pago = 0

    pesquisaGrupoPasseio = f'''
    SELECT ag.idGuiaAg, p.valor
    FROM agendamento ag 
    JOIN passeio p ON ag.idPasseio = p.idPasseio 
    WHERE ag.idAgendamento = {id};
    '''
    cursorDB.execute(pesquisaGrupoPasseio)
    idGuiaAg_valorPasseio = cursorDB.fetchone()
    total = idGuiaAg_valorPasseio[1] * qtdTurAg 

    insertGrupoPasseio = '''
    INSERT INTO grupopasseios (idAgendamento, idTuristaAg, idGuiaAg, qtdTurGpAgendamento, pago, vTotal)
    VALUES (%s, %s, %s, %s, %s, %s);
    '''
    cursorDB.execute(insertGrupoPasseio, (id, idTurista, idGuiaAg_valorPasseio[0], qtdTurAg, int(pago), total))
    conexaoDB.commit()


    pesquisasNomeTur = 'SELECT nome,email FROM usuario WHERE idUsuario = %s'
    cursorDB.execute(pesquisasNomeTur, (idTurista,))
    usuario = cursorDB.fetchone()

    parametrosApi = f'''
        SELECT 
            ag.event_id, 
            g.calendar_id
        FROM 
            agendamento ag
        JOIN 
            adGuia g ON ag.idGuiaAg = g.idUsuario
        WHERE 
            ag.idAgendamento = {id};
    '''
    cursorDB.execute(parametrosApi)
    api = cursorDB.fetchone()

    try:
        eventDescricaoAnt = service.events().get(calendarId=api[1], eventId=api[0]).execute()

        convidados_atuais = eventDescricaoAnt.get('attendees', [])

        novo_convidado = {
            'email': usuario[1]  
        }
        convidados_atuais.append(novo_convidado)

        event_patch = {
            'attendees': convidados_atuais
        }

        service.events().patch(
            calendarId=api[1],
            eventId=api[0],
            body=event_patch
        ).execute()


    except Exception as e:
        return f"Erro ao atualizar evento: {str(e)}"
    
    cursorDB.close()
    return redirect("/home")

@app.route('/listaPasseios')
def lista():
    
    cursorDB = conexaoDB.cursor()
    if not verifica_sessao(): 
        return render_template('/login.html')

    idUsuario = session.get('idUsuario')
    tipo_usuario = session.get('tipo')

    if tipo_usuario == 1:
        
        cursorDB = conexaoDB.cursor()
        consultaAgendamentos = '''
        SELECT 
            ag.idAgendamento,
            ag.event_id,
            p.idPasseio,
            p.nome,
            p.estadoPasseio,
            p.cidadePasseio,
            p.bairroEndPasseio,
            p.valor,
            c.nome,
            p.descricaoPasseio,
            ag.qtdMaxTur,
            ag.idAgendamento,
            ag.dataAgendamento,
            ag.horaAgendamento,
            ag.duracaoAgendamento,
            u.nome,
            MIN(img.caminhoS3),
            SUM(gp.qtdTurGpAgendamento),
            adg.calendar_id
        FROM 
            agendamento ag
        JOIN 
            passeio p ON ag.idPasseio = p.idPasseio
        JOIN 
            categoria c ON p.categoria = c.idCategoria
        JOIN 
            usuario u ON p.idGuia = u.idUsuario
        LEFT JOIN
            imagens img ON p.idPasseio = img.idPasseio
        LEFT JOIN
            grupoPasseios gp ON ag.idAgendamento = gp.idAgendamento
        LEFT JOIN
            adguia adg ON u.idUsuario = adg.idUsuario  -- Fazendo o JOIN com a tabela adguia para obter calendar_id
        WHERE 
            p.idGuia = %s AND ag.dataAgendamento >= CURDATE()
        GROUP BY 
            ag.idAgendamento,
            ag.event_id,
            p.idPasseio,
            p.nome,
            p.estadoPasseio,
            p.cidadePasseio,
            p.bairroEndPasseio,
            p.valor,
            c.nome,
            p.descricaoPasseio,
            ag.qtdMaxTur,
            ag.idAgendamento,
            ag.dataAgendamento,
            ag.horaAgendamento,
            ag.duracaoAgendamento,
            u.nome,
            adg.calendar_id  -- Adicionando o campo calendar_id no GROUP BY
        ORDER BY 
            ag.idAgendamento DESC;

        '''
        cursorDB.execute(consultaAgendamentos, (idUsuario,))
        agendamentos = cursorDB.fetchall()


        agendamentos_com_grupos = []

        for agendamento in agendamentos:
            idAgendamento = agendamento[0]

            cursorDB.execute('''
                SELECT 
                    u.nome, 
                    gp.qtdTurGpAgendamento, 
                    gp.pago,
                    gp.idGrupoPasseios,
                    u.numTelefone,
                    gp.vTotal
                FROM 
                    grupoPasseios gp
                JOIN 
                    usuario u ON gp.idTuristaAg = u.idUsuario
                WHERE 
                    gp.idAgendamento = %s;
            ''', (idAgendamento,))
            grupos = cursorDB.fetchall()

            cursorDB.execute('''
                SELECT 
                    u.nome, 
                    gp.qtdTurGpAgendamento, 
                    gp.pago,
                    gp.idGrupoPasseios,
                    u.numTelefone,
                    gp.vTotal
                FROM 
                    grupoPasseios gp
                JOIN 
                    usuario u ON gp.idTuristaAg = u.idUsuario
                WHERE 
                    gp.idAgendamento = %s AND gp.pago = 1;
            ''', (idAgendamento,))
            grupos_pagos = cursorDB.fetchall()

            total_valor_pagos = sum([grupo[5] for grupo in grupos_pagos])

            total_turistas_pagos = sum([grupo[1] for grupo in grupos_pagos])
 

            agendamentos_com_grupos.append({
                'agendamento': agendamento,
                'grupos': grupos,
                'grupos_pagos': grupos_pagos,
                'total_valor_pagos': total_valor_pagos,
                'total_turistas_pagos': total_turistas_pagos
            })

        cursorDB.execute('''
            SELECT 
                ag.idAgendamento,
                ag.dataAgendamento,
                ag.horaAgendamento,
                p.nome
            FROM 
                agendamento ag
            JOIN 
                passeio p ON ag.idPasseio = p.idPasseio
            WHERE 
                ag.dataAgendamento >= CURDATE()
            ORDER BY 
                ag.dataAgendamento, ag.horaAgendamento;
        ''')
        todos_agendamentos_guia = cursorDB.fetchall()

        imgUsuario = session.get('imgUsuario')

        if idUsuario:
            pesquisaUsuario = '''
                SELECT nome
                FROM usuario 
                WHERE idUsuario = %s
                '''
            cursorDB.execute(pesquisaUsuario, (idUsuario,))
            nomeLogado = cursorDB.fetchone()
        else:
            nomeLogado = None        

        cursorDB.close()

        return render_template("/listaPasseios.html", agendamentos_com_grupos=agendamentos_com_grupos, tipo=tipo_usuario, todos_agendamentos_guia=todos_agendamentos_guia, idUsuario=idUsuario, imgUsuario=imgUsuario, nomeLogado=nomeLogado)


    elif tipo_usuario == 0:
        cursorDB = conexaoDB.cursor()
        consultaGrupos = '''
        SELECT 
            gp.idGrupoPasseios,
            p.nome,
            ag.dataAgendamento,
            ag.horaAgendamento,
            AVG(av.estrelas),
            gp.vTotal,
            MIN(img.caminhoS3),
            p.idPasseio
        FROM 
            grupopasseios gp
        JOIN 
            agendamento ag ON gp.idAgendamento = ag.idAgendamento
        JOIN 
            passeio p ON ag.idPasseio = p.idPasseio
        LEFT JOIN 
            avaliacaop av ON p.idPasseio = av.idPasseio
        LEFT JOIN
            imagens img ON p.idPasseio = img.idPasseio
        WHERE 
            gp.idTuristaAg = %s
        GROUP BY 
            p.idPasseio, 
            ag.idAgendamento,
            gp.idGrupoPasseios
        ORDER BY 
            ag.dataAgendamento DESC, 
            ag.horaAgendamento DESC;
        '''
        cursorDB.execute(consultaGrupos, (idUsuario,))
        grupos = cursorDB.fetchall()

        grupo_status = []

        for grupo in grupos:
            idGrupoPasseio = grupo[0]
            grupo_list = list(grupo)
    
            dataAgendamento = grupo_list[2]
            
            if isinstance(dataAgendamento, date):
                dataAgendamento = datetime.combine(dataAgendamento, datetime.min.time())
            else:
                dataAgendamento = datetime.strptime(dataAgendamento, '%Y-%m-%d')

            grupo_list[2] = dataAgendamento

            grupo = tuple(grupo_list)

            cursorDB.execute('''
            SELECT 
                gp.pago,
                gp.vTotal,
                u.nome,
                u.numTelefone,
                ag.dataAgendamento,
                ag.idGuiaAg,
                u2.numTelefone,
                ag.event_id,
                imgUsuario.caminhoS3 AS caminhoImagemGuia
            FROM 
                grupoPasseios gp
            JOIN 
                usuario u ON gp.idGuiaAg = u.idUsuario
            JOIN
                agendamento ag ON gp.idAgendamento = ag.idAgendamento
            LEFT JOIN
                usuario u2 ON gp.idTuristaAg = u2.idUsuario
            LEFT JOIN
                imagemUsuario imgUsuario ON ag.idGuiaAg = imgUsuario.idUsuario
            WHERE 
                gp.idGrupoPasseios = %s;

            ''', (idGrupoPasseio,))
            status = cursorDB.fetchall()

            grupo_status.append({
                'grupo': grupo,
                'status': status,
            })

        imgUsuario = session.get('imgUsuario')

        if idUsuario:
            pesquisaUsuario = '''
                SELECT nome
                FROM usuario 
                WHERE idUsuario = %s
                '''
            cursorDB.execute(pesquisaUsuario, (idUsuario,))
            nomeLogado = cursorDB.fetchone()
        else:
            nomeLogado = None        
        
        cursorDB.close()
        return render_template("/listaPasseios.html", grupo_status=grupo_status, datadehoje=datadehoje, idUsuario=idUsuario, imgUsuario=imgUsuario, tipo=tipo_usuario, nomeLogado=nomeLogado)

@app.route('/reagendarGrupo', methods=['POST'])
def reagendarGrupo():
    idGrupoPasseios = request.form.get('idGrupoPasseios')
    novo_agendamento = request.form.get('novo_agendamento')

    if not idGrupoPasseios or not novo_agendamento:
        return "Dados incompletos para reagendamento", 400

    creds = main()  
    service = build("calendar", "v3", credentials=creds)

    cursorDB = conexaoDB.cursor()

    try:
        cursorDB.execute('''
            SELECT u.email
            FROM grupoPasseios gp
            JOIN usuario u ON gp.idTuristaAg = u.idUsuario
            WHERE gp.idGrupoPasseios = %s;
        ''', (idGrupoPasseios,))
        usuario = cursorDB.fetchone()

        if not usuario:
            return "Turista não encontrado", 404

        email_turista = usuario[0]

        cursorDB.execute('''
            SELECT ag.event_id, adg.calendar_id 
            FROM agendamento ag 
            JOIN adguia adg ON ag.idGuiaAg = adg.idUsuario
            WHERE ag.idAgendamento = (
                SELECT gp.idAgendamento FROM grupoPasseios gp WHERE gp.idGrupoPasseios = %s
            );
        ''', (idGrupoPasseios,))
        evento_antigo = cursorDB.fetchone()

        if evento_antigo:
            evento_id_antigo, calendar_id_antigo = evento_antigo
            evento_antigo_data = service.events().get(calendarId=calendar_id_antigo, eventId=evento_id_antigo).execute()
            convidados = evento_antigo_data.get('attendees', [])

            convidados_atualizados = [convidado for convidado in convidados if convidado['email'] != email_turista]

            service.events().patch(
                calendarId=calendar_id_antigo,
                eventId=evento_id_antigo,
                body={'attendees': convidados_atualizados}
            ).execute()

        cursorDB.execute('''
            SELECT ag.event_id, adg.calendar_id
            FROM agendamento ag
            JOIN adguia adg ON ag.idGuiaAg = adg.idUsuario
            WHERE ag.idAgendamento = %s;
        ''', (novo_agendamento,))
        evento_novo = cursorDB.fetchone()

        if evento_novo:
            evento_id_novo, calendar_id_novo = evento_novo
            evento_novo_data = service.events().get(calendarId=calendar_id_novo, eventId=evento_id_novo).execute()
            novos_convidados = evento_novo_data.get('attendees', [])
            novos_convidados.append({'email': email_turista})

            service.events().patch(
                calendarId=calendar_id_novo,
                eventId=evento_id_novo,
                body={'attendees': novos_convidados}
            ).execute()

        comandoValorPasseioSQL = '''
            SELECT p.valor, gp.qtdTurGpAgendamento
            FROM grupoPasseios gp
            JOIN agendamento ag ON gp.idAgendamento = ag.idAgendamento
            JOIN passeio p ON ag.idPasseio = p.idPasseio
            WHERE gp.idGrupoPasseios = %s;
        '''
        cursorDB.execute(comandoValorPasseioSQL, (idGrupoPasseios,))
        valor_passeio, quantidade_pessoas = cursorDB.fetchone()

        valor_total = valor_passeio * quantidade_pessoas

        cursorDB.execute('''
            UPDATE grupoPasseios 
            SET idAgendamento = %s, vTotal = %s
            WHERE idGrupoPasseios = %s;
        ''', (novo_agendamento, valor_total, idGrupoPasseios))
        conexaoDB.commit()
        cursorDB.close()

        return redirect('/listaPasseios')

    except Exception as e:
        conexaoDB.rollback()
        return f"Erro ao reagendar evento: {str(e)}", 500

    finally:
        cursorDB.close()

@app.route("/<int:id>/pago", methods=['POST'])
def altPago(id):
    if not verifica_sessao(): 
        return render_template('/login.html')

    comandoSQL = 'UPDATE grupoPasseios SET pago = TRUE WHERE idGrupoPasseios = %s'
    
    try:
        cursorDB = conexaoDB.cursor()
        cursorDB.execute(comandoSQL, (id,))
        conexaoDB.commit()
    except mysql.connector.IntegrityError as err:
        print(f"Error: {err}")
        conexaoDB.rollback()
        return render_template('error.html', msg="Erro de integridade ao tentar cadastrar o passeio.")
    finally:
        cursorDB.close()
    
    return redirect('/listaPasseios')

@app.route("/<int:id>/deletarGrupoPasseio", methods=['POST'])
def deletarGrupoPasseio(id):
    if not verifica_sessao():
        return render_template('/login.html')

    creds = main()  
    service = build("calendar", "v3", credentials=creds)

    cursorDB = conexaoDB.cursor()
    cursorDB.execute('''
        SELECT gp.idAgendamento, u.email
        FROM grupoPasseios gp
        JOIN usuario u ON gp.idTuristaAg = u.idUsuario
        WHERE gp.idGrupoPasseios = %s;
    ''', (id,))
    grupo_passeio = cursorDB.fetchone()

    if not grupo_passeio:
        return "Grupo de passeio não encontrado", 404

    id_agendamento, email_turista = grupo_passeio

    cursorDB.execute('''
        SELECT ag.event_id, adg.calendar_id
        FROM agendamento ag
        JOIN adguia adg ON ag.idGuiaAg = adg.idUsuario
        WHERE ag.idAgendamento = %s;
    ''', (id_agendamento,))
    agendamento = cursorDB.fetchone()

    if not agendamento:
        return "Agendamento não encontrado", 404
    
    event_id, id_guia_ag = agendamento

    if event_id:
        evento_data = service.events().get(calendarId=id_guia_ag, eventId=event_id).execute()
        convidados_atualizados = [convidado for convidado in evento_data.get('attendees', []) if convidado['email'] != email_turista]
        service.events().patch(
            calendarId=id_guia_ag,
            eventId=event_id,
            body={'attendees': convidados_atualizados}
        ).execute()

    cursorDB.execute('DELETE FROM grupoPasseios WHERE idGrupoPasseios = %s', (id,))
    conexaoDB.commit()
    cursorDB.close()
    return redirect('/listaPasseios')
        
@app.route('/avaliacaoP/<int:id>', methods=['GET', 'POST'])
def avaliacaoP(id):    
    if request.method == 'POST':
        cursorDB = conexaoDB.cursor()
        estrelas = int(request.form['estrelas'])
        descricao = request.form['descricao']
        idUsuario = session.get('idUsuario') 

        if idUsuario is None:
            return render_template('error.html', msg="Usuário não autenticado.")


        if not estrelas:
            return render_template('error.html', msg="Por favor, selecione uma quantidade de estrelas.")

        comandoSQL = '''
        INSERT INTO avaliacaop (dataAvaliacao, descricaoAvaliacao, idPasseio, estrelas, usuarioAvaliador)
        VALUES (NOW(), %s, %s, %s, %s);
        '''
        valores = (descricao, id, estrelas, idUsuario)

        cursorDB.execute(comandoSQL, valores)
        conexaoDB.commit()
        cursorDB.close()
    return redirect('/historico')


@app.route('/perfilUsuario/<int:idUsuario>')
def perfil_usuario(idUsuario):
    cursorDB = conexaoDB.cursor()

    comandoSQL = '''
    SELECT 
        idUsuario,
        nome,
        cpfCnpj,
        numTelefone,
        dataNasc,
        cepEndUser,
        cidadeUser,
        estadoEndUser,
        bairroEndUser,
        ruaEndUser,
        numEndUser,
        email,
        tipo
    FROM 
        usuario 
    WHERE 
        idUsuario = %s
    '''
    
    cursorDB = conexaoDB.cursor()

    cursorDB.execute(comandoSQL, (idUsuario,))
    usuario = cursorDB.fetchone()

    pesquisaImagemPerfil = '''
    SELECT 
        caminhoS3
    FROM 
        imagemUsuario
    WHERE 
        idUsuario = %s;
    '''
    cursorDB.execute(pesquisaImagemPerfil, (idUsuario,))
    imagem_result = cursorDB.fetchone()

    imagem = imagem_result[0] if imagem_result else None

    pesquisaEstrelasGuia ='''
        SELECT
            u.nome,
            COUNT(DISTINCT ap.idAvaliacaoP),
            AVG(ap.estrelas),
            COUNT(DISTINCT ag.idAgendamento)
        FROM
            usuario u
        JOIN
            passeio p ON p.idGuia = u.idUsuario
        LEFT JOIN
            avaliacaop ap ON ap.idPasseio = p.idPasseio
        LEFT JOIN
            agendamento ag ON ag.idPasseio = p.idPasseio
        WHERE
            u.idUsuario = %s
            AND ag.dataAgendamento >= CURDATE()
        GROUP BY
            u.idUsuario;
        '''
    cursorDB.execute(pesquisaEstrelasGuia, (idUsuario,))
    med_Estrelas = cursorDB.fetchone()


    if usuario[12] == 1:
        cursorDB = conexaoDB.cursor()

        pesquisaAvaliacoesDoGuia = '''
            SELECT 
                avaliacaoP.dataAvaliacao,
                avaliacaoP.descricaoAvaliacao,
                avaliacaoP.estrelas, 
                usuario.nome, 
                usuario.cidadeUser, 
                usuario.estadoEndUser,
                imagemusuario.caminhoS3,
                avaliacaoP.usuarioAvaliador
            FROM 
                avaliacaoP
            JOIN 
                passeio ON avaliacaoP.idPasseio = passeio.idPasseio
            JOIN 
                usuario ON avaliacaoP.usuarioAvaliador = usuario.idUsuario
            LEFT JOIN 
                imagemusuario ON usuario.idUsuario = imagemusuario.idUsuario
            WHERE 
                passeio.idGuia = %s;
            '''
        cursorDB.execute(pesquisaAvaliacoesDoGuia, (idUsuario,))
        avaliacoes = cursorDB.fetchall()
    
        consultaAgendamentosGuia = '''
            SELECT 
                ag.idAgendamento,
                ag.event_id,
                p.idPasseio,
                p.nome AS nomePasseio,
                p.estadoPasseio,
                p.cidadePasseio,
                p.bairroEndPasseio,
                p.valor,
                c.nome AS nomeCategoria,
                p.descricaoPasseio,
                ag.qtdMaxTur,
                ag.dataAgendamento,
                ag.horaAgendamento,
                ag.duracaoAgendamento,
                GROUP_CONCAT(img.caminhoS3 SEPARATOR ',') AS imagens,
                (
                    SELECT AVG(estrelas)
                    FROM avaliacaoP
                    WHERE avaliacaoP.idPasseio = p.idPasseio
                ) AS mediaEstrelas
            FROM 
                agendamento ag
            JOIN 
                passeio p ON ag.idPasseio = p.idPasseio
            JOIN 
                categoria c ON p.categoria = c.idCategoria
            LEFT JOIN 
                imagens img ON p.idPasseio = img.idPasseio
            WHERE 
                ag.dataAgendamento >= CURDATE()
                AND p.idGuia = %s
            GROUP BY 
                ag.idAgendamento
            ORDER BY 
                ag.idAgendamento DESC;
            '''
        cursorDB = conexaoDB.cursor()
        cursorDB.execute(consultaAgendamentosGuia, (idUsuario,))
        agendamentos = cursorDB.fetchall()

    else:
        pesquisaAvaliacoesTurista = '''
            SELECT 
                avaliacaop.dataAvaliacao,
                avaliacaop.descricaoAvaliacao,
                avaliacaop.estrelas,
                passeio.nome AS nome_passeio,
                passeio.cidadePasseio,
                passeio.estadoPasseio
            FROM 
                avaliacaop
            JOIN 
                passeio ON avaliacaop.idPasseio = passeio.idPasseio
            WHERE 
                avaliacaop.usuarioAvaliador = %s;
            '''
        cursorDB.execute(pesquisaAvaliacoesTurista, (idUsuario,))
        avaliacoes = cursorDB.fetchall()

        consultaTodosAgendamentos = '''
        SELECT 
            ag.idAgendamento,
            ag.event_id,
            p.idPasseio,
            p.nome AS nomePasseio,
            p.estadoPasseio,
            p.cidadePasseio,
            p.bairroEndPasseio,
            p.valor,
            c.nome,
            p.descricaoPasseio,
            ag.qtdMaxTur,
            ag.dataAgendamento,
            ag.horaAgendamento,
            ag.duracaoAgendamento,
            GROUP_CONCAT(img.caminhoS3 SEPARATOR ',') AS imagens,
            (
                SELECT AVG(estrelas)
                FROM avaliacaoP
                WHERE avaliacaoP.idPasseio = p.idPasseio
            ) AS mediaEstrelas
        FROM 
            agendamento ag
        JOIN 
            passeio p ON ag.idPasseio = p.idPasseio
        JOIN 
            categoria c ON p.categoria = c.idCategoria
        LEFT JOIN 
            imagens img ON p.idPasseio = img.idPasseio
        WHERE 
            ag.dataAgendamento >= CURDATE()
        GROUP BY 
            ag.idAgendamento
        ORDER BY 
            ag.idAgendamento DESC;
        '''
        cursorDB = conexaoDB.cursor()
        cursorDB.execute(consultaTodosAgendamentos)
        agendamentos = cursorDB.fetchall()
    
    pesquisaAdUsuario ='''
        SELECT *
        FROM adusuario
        WHERE idUsuario = %s;
        '''
    cursorDB.execute(pesquisaAdUsuario, (idUsuario,))
    adicional = cursorDB.fetchone()

    idUsuarioLogado = session.get('idUsuario')
    tipo = session.get('tipo')
    imgUsuario = session.get('imgUsuario')

    if idUsuarioLogado:
        pesquisaUsuario = '''
            SELECT nome
            FROM usuario 
            WHERE idUsuario = %s
            '''
        cursorDB.execute(pesquisaUsuario, (idUsuarioLogado,))
        nomeLogado = cursorDB.fetchone()
    else:
        nomeLogado = None   

    cursorDB.close()
    
    return render_template('perfilUsuario.html', usuario=usuario, avaliacoes=avaliacoes, imagem=imagem, med_Estrelas=med_Estrelas, idUsuario=idUsuarioLogado, idUsuarioTela=idUsuario, tipo=tipo, agendamentos=agendamentos, adicional=adicional, nomeLogado=nomeLogado, imgUsuario=imgUsuario)


@app.route('/editUsuario/<int:id>', methods=['POST'])
def edit_usuario(id):
    cursorDB = conexaoDB.cursor()

    comandoSQL_buscar = '''
        SELECT nome, cpfCnpj, numTelefone, dataNasc, cepEndUser, cidadeUser, estadoEndUser, bairroEndUser, ruaEndUser, numEndUser, email, senha
        FROM usuario
        WHERE idUsuario = %s
    '''
    cursorDB.execute(comandoSQL_buscar, (id,))
    dados_atuais = cursorDB.fetchone()

    nome = request.form.get('nome') or dados_atuais[0]
    cpf_cnpj = request.form.get('cpfCnpj') or dados_atuais[1]
    num_telefone = request.form.get('numTelefone') or dados_atuais[2]
    data_nasc = request.form.get('dataNasc') or dados_atuais[3]
    cep_end_user = request.form.get('cepEndUser') or dados_atuais[4]
    cidade_user = request.form.get('cidadeUser') or dados_atuais[5]
    estado_end_user = request.form.get('estadoEndUser') or dados_atuais[6]
    bairro_end_user = request.form.get('bairroEndUser') or dados_atuais[7]
    rua_end_user = request.form.get('ruaEndUser') or dados_atuais[8]
    num_end_user = request.form.get('numEndUser') or dados_atuais[9]
    email = request.form.get('email') or dados_atuais[10]
    senha = request.form.get('senha') or dados_atuais[11]

    comandoSQL_update = '''
        UPDATE usuario
        SET nome = %s, cpfCnpj = %s, numTelefone = %s, dataNasc = %s, cepEndUser = %s,
            cidadeUser = %s, estadoEndUser = %s, bairroEndUser = %s, ruaEndUser = %s,
            numEndUser = %s, email = %s, senha = %s
        WHERE idUsuario = %s
    '''
    valores_update = (nome, cpf_cnpj, num_telefone, data_nasc, cep_end_user, cidade_user, estado_end_user, bairro_end_user, rua_end_user, num_end_user, email, senha, id)
    cursorDB.execute(comandoSQL_update, valores_update)
    conexaoDB.commit()
    cursorDB.close()

    return redirect(f'/perfilUsuario/{id}')

@app.route('/editAdUsuario/<int:id>', methods=['POST'])
def edit_ad_usuario(id):
    cursorDB = conexaoDB.cursor()
    comandoSQL_buscar = '''
        SELECT Trabalho, Lingua, Descricao
        FROM adusuario
        WHERE idUsuario = %s  -- alterei para procurar pelo idUsuario, supondo que a relação seja por idUsuario
    '''
    cursorDB.execute(comandoSQL_buscar, (id,))
    dados_atuais = cursorDB.fetchone()

    if dados_atuais is None:
        return f"Erro: Nenhum registro encontrado para o usuário com id {id}"

    trabalho = request.form.get('trabalho') or dados_atuais[0]
    lingua = request.form.get('lingua') or dados_atuais[1]
    descricao = request.form.get('descricao') or dados_atuais[2]

    if 'imagem' not in request.files:
        return render_template('error.html', msg="Nenhuma imagem fornecida.")

    imagem = request.files['imagem']

    if imagem.filename == '':
        return render_template('error.html', msg="Nenhuma imagem selecionada.")

    if not allowed_file(imagem.filename):
        return render_template('error.html', msg="Tipo de arquivo não suportado. Apenas PNG, JPG e JPEG são aceitos.")

    try:
        comandoSQL_update = '''
            UPDATE adusuario
            SET Trabalho = %s, Lingua = %s, Descricao = %s
            WHERE idUsuario = %s
        '''
        valores_update = (trabalho, lingua, descricao, id)
        cursorDB.execute(comandoSQL_update, valores_update)
        
        conexaoDB.commit()

        nome_arquivo = secure_filename(imagem.filename)
        new_filename = uuid.uuid4().hex + '.' + imagem.filename.rsplit('.', 1)[1].lower()
        nome_objeto = f'imagens/{new_filename}'

        s3_client.upload_fileobj(imagem, bucket_name, nome_objeto)
        imagem_url = f"https://{bucket_name}.s3.amazonaws.com/{nome_objeto}"

        cursorDB.execute('''SELECT idImagem FROM imagemUsuario WHERE idUsuario = %s''', (id,))
        imagem_existente = cursorDB.fetchone()

        if imagem_existente:
            cursorDB.execute('''
                UPDATE imagemUsuario 
                SET nomeArquivo = %s, caminhoS3 = %s 
                WHERE idUsuario = %s
            ''', (nome_arquivo, imagem_url, id))
        else:
            cursorDB.execute('''
                INSERT INTO imagemUsuario (nomeArquivo, caminhoS3, idUsuario)
                VALUES (%s, %s, %s)
            ''', (nome_arquivo, imagem_url, id))

        conexaoDB.commit()
        
    except Exception as e:
        print(f"Erro ao fazer upload da imagem para o S3: {str(e)}")
        conexaoDB.rollback()
        return render_template('error.html', msg="Erro ao fazer upload da imagem para o S3.")

    cursorDB.close()

    return redirect(f'/perfilUsuario/{id}')

@app.route('/sobrenos')
def sobre_nos():
    cursorDB = conexaoDB.cursor()

    idUsuario = session.get('idUsuario')
    tipo_usuario = session.get('tipo')
    imgUsuario = session.get('imgUsuario')

    if idUsuario:
        pesquisaUsuario = '''
            SELECT nome
            FROM usuario 
            WHERE idUsuario = %s
            '''
        cursorDB.execute(pesquisaUsuario, (idUsuario,))
        nomeLogado = cursorDB.fetchone()
    else:
        nomeLogado = None

    cursorDB.close()

    return render_template('sobrenos.html', tipo=tipo_usuario, idUsuario=idUsuario, imgUsuario=imgUsuario, nomeLogado=nomeLogado)

@app.route('/historico')
def historico():
    cursorDB = conexaoDB.cursor()

    if not verifica_sessao(): 
        return render_template('/login.html')
    
    cursorDB = conexaoDB.cursor()

    idUsuario = session.get('idUsuario')
    tipo_usuario = session.get('tipo')

    if tipo_usuario == 1:
        return redirect('/home')

    comandoSQL1 = f'SELECT nome FROM usuario WHERE idUsuario = {idUsuario}'
    cursorDB.execute(comandoSQL1)
    nomeGuia = cursorDB.fetchone()


    consultaSQL = '''
        SELECT 
            p.nome,
            MIN(img.caminhoS3),
            ag.dataAgendamento,
            ag.horaAgendamento,
            ag.idGuiaAg,
            u.nome,
            p.idPasseio
        FROM 
            agendamento ag
        JOIN 
            passeio p ON ag.idPasseio = p.idPasseio
        LEFT JOIN 
            imagens img ON p.idPasseio = img.idPasseio
        JOIN
            grupoPasseios gp ON ag.idAgendamento = gp.idAgendamento
        JOIN
            usuario u ON ag.idGuiaAg = u.idUsuario
        WHERE 
            gp.idTuristaAg = %s
            AND ag.dataAgendamento < CURDATE()
            AND gp.pago = 1
        GROUP BY 
            ag.idAgendamento, p.idPasseio
        ORDER BY 
            ag.dataAgendamento DESC;
    '''

    cursorDB.execute(consultaSQL, (idUsuario,))
    agendamentos = cursorDB.fetchall()

    imgUsuario = session.get('imgUsuario')

    if idUsuario:
        pesquisaUsuario = '''
            SELECT nome
            FROM usuario 
            WHERE idUsuario = %s
            '''
        cursorDB.execute(pesquisaUsuario, (idUsuario,))
        nomeLogado = cursorDB.fetchone()
    else:
        nomeLogado = None

    cursorDB.close()
    return render_template("historico.html",agendamentos=agendamentos,idUsuario=idUsuario, imgUsuario=imgUsuario, tipo=tipo_usuario, nomeLogado=nomeLogado, nomeGuia=nomeGuia)

@app.route('/homeGuia')
def homeGuia():
    cursorDB = conexaoDB.cursor()

    if not verifica_sessao(): 
        return render_template('/login.html')

    idUsuario = session.get('idUsuario')
    tipo_usuario = session.get('tipo')
    
    imgUsuario = session.get('imgUsuario')

    if idUsuario:
        pesquisaUsuario = '''
            SELECT nome
            FROM usuario 
            WHERE idUsuario = %s
            '''
        cursorDB.execute(pesquisaUsuario, (idUsuario,))
        nomeLogado = cursorDB.fetchone()
    else:
        nomeLogado = None
    return render_template("home-guia.html", imgUsuario=imgUsuario,tipo=tipo_usuario, nomeLogado=nomeLogado)


@app.route('/pesquisaPasseios')
def pesquisa_passeios():
    query = request.args.get('query', '')

    if not query:
        return render_template('error.html', msg="Por favor, insira uma palavra para buscar.")

    cursorDB = conexaoDB.cursor()

    comandoSQL = '''
        SELECT 
            ag.idAgendamento,
            ag.event_id,
            p.idPasseio,
            p.nome AS nomePasseio,
            p.estadoPasseio,
            p.cidadePasseio,
            p.bairroEndPasseio,
            p.valor,
            c.nome AS nomeCategoria,
            p.descricaoPasseio,
            ag.qtdMaxTur,
            ag.dataAgendamento,
            ag.horaAgendamento,
            ag.duracaoAgendamento,
            GROUP_CONCAT(img.caminhoS3 SEPARATOR ',') AS imagens,
            (
                SELECT AVG(estrelas)
                FROM avaliacaoP
                WHERE avaliacaoP.idPasseio = p.idPasseio
            ) AS mediaAvaliacoes
        FROM 
            agendamento ag
        JOIN 
            passeio p ON ag.idPasseio = p.idPasseio
        JOIN 
            categoria c ON p.categoria = c.idCategoria
        LEFT JOIN 
            imagens img ON p.idPasseio = img.idPasseio
        WHERE 
            ag.dataAgendamento >= CURDATE()
            AND p.nome LIKE %s
        GROUP BY 
            ag.idAgendamento
        ORDER BY 
            ag.idAgendamento DESC;

    '''
    like_query = f"%{query}%"
    cursorDB.execute(comandoSQL, (like_query,))
    agendamentos = cursorDB.fetchall()


    idUsuario = session.get('idUsuario')
    tipo_usuario = session.get('tipo')
    
    imgUsuario = session.get('imgUsuario')

    if idUsuario:
        pesquisaUsuario = '''
            SELECT nome
            FROM usuario 
            WHERE idUsuario = %s
            '''
        cursorDB.execute(pesquisaUsuario, (idUsuario,))
        nomeLogado = cursorDB.fetchone()
    else:
        nomeLogado = None

    cursorDB.close()

    return render_template('pesquisa.html', agendamentos=agendamentos, query=query, idUsuario=idUsuario, nomeLogado=nomeLogado, tipo_usuario=tipo_usuario, imgUsuario=imgUsuario)


# --------------------------------------------------------
# --------------------------------------------------------
# --------------------------------------------------------



@app.route('/editPasseio/<int:id>', methods=['GET'])
def editarPasseio(id):
    if not verifica_sessao(): 
        return render_template('/login.html')
    
    comandoSQL = f'SELECT * FROM passeio WHERE idPasseio = {id}'
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    passeios = cursorDB.fetchone()

    idUsuario = session.get('idUsuario')
    tipo_usuario = session.get('tipo')
    imgUsuario = session.get('imgUsuario')

    if idUsuario:
        pesquisaUsuario = '''
            SELECT nome
            FROM usuario 
            WHERE idUsuario = %s
            '''
        cursorDB.execute(pesquisaUsuario, (idUsuario,))
        nomeLogado = cursorDB.fetchone()
    else:
        nomeLogado = None


    cursorDB.close()
    return render_template('editPasseio.html', passeio=passeios)

@app.route('/<int:id>/editadoPasseio', methods=['POST'])
def editadoPasseio(id):
    comandoSQL = f"SELECT * FROM passeio WHERE idPasseio = {id}"
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    passeio_atual = cursorDB.fetchone()

    nome = request.form['nome'] if request.form['nome'] else passeio_atual[1]
    estadoPasseio = request.form['estadoPasseio'] if request.form['estadoPasseio'] else passeio_atual[2]
    cidadePasseio = request.form['cidadePasseio'] if request.form['cidadePasseio'] else passeio_atual[3]
    bairroEndPasseio = request.form['bairroEndPasseio'] if request.form['bairroEndPasseio'] else passeio_atual[4]
    qtdPessoas = request.form['qtdPessoas'] if request.form['qtdPessoas'] else passeio_atual[5]
    valor = request.form['valor'] if request.form['valor'] else passeio_atual[6]
    tempoPasseio = request.form['tempoPasseio'] if request.form['tempoPasseio'] else passeio_atual[7]
    descricaoPasseio = request.form['descricao'] if request.form['descricao'] else passeio_atual[9]

    comandoSQL_update = '''
    UPDATE passeio 
    SET nome = %s, estadoPasseio = %s, cidadePasseio = %s, bairroEndPasseio = %s, qtdPessoas = %s, valor = %s, tempoPasseio = %s,  descricaoPasseio = %s
    WHERE idPasseio = %s
    '''
    valores = (nome, estadoPasseio, cidadePasseio, bairroEndPasseio, qtdPessoas, valor, tempoPasseio, descricaoPasseio, id)

    try:
        cursorDB.execute(comandoSQL_update, valores)
        conexaoDB.commit()
    except mysql.connector.IntegrityError as err:
        print(f"Error: {err}")
        conexaoDB.rollback()
        return render_template('error.html', msg="Erro de integridade ao tentar cadastrar o passeio.")
    finally:
        cursorDB.close()
    
    return redirect('/adm')

@app.errorhandler(405)
def erro405(error):
    return redirect("/")

@app.errorhandler(404)
def erro404(error):
    return redirect("/")

app.run(host='0.0.0.0', port=5000, debug = True)