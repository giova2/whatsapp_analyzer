from flask import Flask, jsonify, render_template, request
import pandas as pd
from itertools import islice

from pathlib import Path
from werkzeug.utils import secure_filename
import sys
from datetime import datetime

from .functions import *

ALLOWED_EXTENSIONS = {'txt'}

app = Flask(__name__)

ChatFileFirstPart = "Chat de WhatsApp con "
ExportExtension = "txt"
cabeceras_index = 'messengers'
msgs_index = 'msgs'


def take(n, iterable):
    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def get_input_chats():
    return render_template('info_chats.html')

@app.route('/chats', methods=['POST'])
def chats():
    FileChat = request.files['file']
    
    if FileChat and allowed_file(FileChat.filename):
        dir_chats = 'chats/'
        chatFileName = dir_chats + secure_filename(FileChat.filename) 
        FileChat.save(chatFileName)
        dir_path_chats = Path(dir_chats)
        # for FChat in dir_chats.glob('*.'+ExportExtension):
        file = open(chatFileName, mode='r', encoding="utf8")
        data = file.read()
        file.close()
        resultados = estadisticas(data)
        return render_template('show_info.html', title="Analizador Whatsapp chats", chat=FileChat, resultados=resultados)
    return '<div style="display: flex;justify-content: center;align-items: center;height: 100%;"><h2>El archivo debe ser .txt</h2></div>'

@app.route('/chats_consola', methods=['GET'])
def chats_consola():
    dir_chats = Path('chats/')
    for name in dir_chats.glob('*.txt'):
        print(str(name), file=sys.stderr)
        with open(name, mode='r', encoding="utf8") as chat:
            for line in chat:
                print(line, file=sys.stderr)
        print('*********************', file=sys.stderr)
    return 'Hecho'

def estadisticas(data):
    dicc_messengers_msgs = get_gross_data(data)
    users_list = get_users(dicc_messengers_msgs[cabeceras_index])
    datos_usuarios = data_estructure_usuarios(users_list)
    datos_usuarios['contador_mensajes'] = len(dicc_messengers_msgs[msgs_index])
    datos_usuarios['usuarios'] = users_list
    fecha_ultimo_mensaje = datetime(1970, 1, 1)
    print(dicc_messengers_msgs[cabeceras_index])
    index = 0
    for each in dicc_messengers_msgs[cabeceras_index]:
        esta_fecha = convertir_a_fecha(each[0], each[1])
        diferencia = esta_fecha - fecha_ultimo_mensaje
        user_name = each[2].strip().lower().replace(' ', '_')
        # diferencia.total_seconds() //3600 traduce la cantidad de segundos en horas
        if diferencia.total_seconds() // 3600 >= 15 or fecha_ultimo_mensaje == datetime(1970, 1, 1):
            datos_usuarios[user_name]['arranco_conversacion'] += 1
            datos_usuarios[user_name]['mensajes_arranque'].append(each[0]+' '+each[1] +' - '+ dicc_messengers_msgs[msgs_index][index])
        fecha_ultimo_mensaje = esta_fecha
        date_msg,hour_msg,user_msg = dicc_messengers_msgs[cabeceras_index][index]
        datos_usuarios['mensajes'].append((user_msg.strip().lower().replace(' ', '_'), date_msg+' '+hour_msg+' - '+dicc_messengers_msgs[msgs_index][index]))
        index += 1
    # users_list = map(lambda x: x.strip().lower().replace(' ', '_'), users_list)
    # para cada uno de los usuarios de la conversacion obtenemos los mensajes enviados
    who_sent_what = {}
    for user_name in users_list:
        who_sent_what[user_name] = {'fecha': [], 'hora': [], 'usuario': [], 'mensajes': []}
    # para cada indice en el array de mensajes
    for index_msg in range(len(dicc_messengers_msgs[msgs_index])):
        cabecera_mensaje = dicc_messengers_msgs[cabeceras_index][index_msg]
        user_name = cabecera_mensaje[2].strip().lower().replace(' ', '_')
        who_sent_what[user_name]['fecha'].append(cabecera_mensaje[0])
        who_sent_what[user_name]['hora'].append(cabecera_mensaje[1])
        who_sent_what[user_name]['usuario'].append(cabecera_mensaje[2])
        who_sent_what[user_name]['mensajes'].append(dicc_messengers_msgs[msgs_index][index_msg]) #obtaining the message mentioned after sender
    # Now in the following code we will be creating a Dataframe with messengers as the column names and messages as the values.
    dfs = {}
    for user_name in users_list:
        dfs[user_name] = pd.DataFrame([who_sent_what[user_name]['fecha'],who_sent_what[user_name]['hora'],who_sent_what[user_name]['usuario'],who_sent_what[user_name]['mensajes']]) # creamos un DataFrame a partir del array de arrays que acabamos de armar
        dfs[user_name] = dfs[user_name].transpose()   # trasponemos la matriz para dejar los arrays como columnas
        dfs[user_name].columns = ['fecha', 'hora', 'usuario', 'mensajes'] # +list(users_list) # colocamos nombres a las columnass
    emoji_dict={}
    for user_name in users_list:
        datos_usuarios[user_name]['contador_mensajes'] = len(dfs[user_name]['mensajes'])
        emoji_dict[user_name] = extraer_emojis(dfs[user_name]['mensajes'])
        emoji_df = pd.DataFrame(emoji_dict[user_name])
        datos_usuarios[user_name]['contador_emojis'] = emoji_df[0].value_counts()[:5] # imprime los 5 emojis más enviados
        
        multimedia_files = dfs[user_name]['mensajes'].value_counts()['<Multimedia omitido>'] # cuenta la cantidad de archivos multimedia compartidos
        datos_usuarios[user_name]['contador_mensajes_multimedia'] = multimedia_files

        dfs[user_name]['mensajes'].apply(acumulador_palabras, args=(datos_usuarios, user_name))
        dfs[user_name]['mensajes'].apply(acumulador_sitios, args=(datos_usuarios,))
        datos_usuarios[user_name]['palabras_mas_usadas'] = dict(sorted(datos_usuarios[user_name]['palabras_mas_usadas'].items(), key = lambda kv:kv[1], reverse = True))
        dfs[user_name]['fecha'].apply(acumulador_dia_mensajes, args=(datos_usuarios, user_name))
        dfs[user_name]['hora'].apply(acumulador_hora_mensajes, args=(datos_usuarios, user_name))
        if datos_usuarios[user_name]['contador_mensajes'] > 0:
            datos_usuarios[user_name]['promedio_largo_mensajes'] = round(datos_usuarios[user_name]['contador_caracteres'] / datos_usuarios[user_name]['contador_mensajes'])
        datos_usuarios[user_name]['palabras_mas_usadas'] = dict(take(6, datos_usuarios[user_name]['palabras_mas_usadas'].items()))
        print('\n\n\n\n\n\n\n\n\n************* acumulador ****************\n\n\n\n\n\n')
        print(datos_usuarios)
        
    # sys.exit()
    datos_usuarios['maximo_dia_mensajes'] = indice_del_maximo(datos_usuarios['dia_mensajes'])
    datos_usuarios['maximo_hora_mensajes'] = indice_del_maximo(datos_usuarios['hora_mensajes'])
    datos_usuarios['maximo_sitio_compartido'] = indice_del_maximo_diccionario(datos_usuarios['sitios_mas_compartidos'])
    # definimos el patrón para extraer las horas en los mensajes

    return datos_usuarios

def data_estructure_usuarios(usuarios):
    arr_datos_usuario = {}
    arr_datos_usuario['mensajes'] = []
    arr_datos_usuario['contador_mensajes'] = 0 #hecho
    # coloco un array de 24 posiciones para ir sumando las horas en las cuales se enviaron los mensajes
    arr_datos_usuario['hora_mensajes'] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # hecho
    # {'lun':0, 'mar':0, 'mier':0, 'jue':0, 'vie':0, 'sab':0, 'dom':0}
    arr_datos_usuario['dia_mensajes'] = [0, 0, 0, 0, 0, 0, 0] # hecho
    arr_datos_usuario['maximo_dia_mensajes'] = 0    #hecho
    arr_datos_usuario['maximo_hora_mensajes'] = 0   #hecho
    arr_datos_usuario['sitios_mas_compartidos'] = {} #hecho
    arr_datos_usuario['maximo_sitio_compartido'] = '' #hecho
    arr_datos_usuario['minimo_considerable_palabra_usada'] = 5
    for usuario in usuarios:
        arr_datos_usuario[usuario] = {
            'contador_mensajes': 0, #hecho
            'contador_mensajes_multimedia': 0,#hecho
            'contador_emojis': 0, #hecho
            'contador_palabras': 0, #hecho
            'contador_caracteres': 0, #hecho
            'dia_mensajes': [0, 0, 0, 0, 0, 0, 0], #hecho
            'hora_mensajes' : [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], #hecho
            'promedio_largo_mensajes': 0, #hecho
            'arranco_conversacion': 0, #hecho
            'mensajes_arranque': [],  #hecho
            'palabras_mas_usadas': {}, #hecho (falta ordenar)
            'cantidad_palabra_mas_usada': 0
        }
    return arr_datos_usuario


if(__name__ == '__main__'):
    app.run(host="0.0.0.0", port="4000", debug=True)
