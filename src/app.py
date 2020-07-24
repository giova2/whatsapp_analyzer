from flask import Flask, jsonify, render_template, request
from pathlib import Path
from werkzeug.utils import secure_filename
import sys
from datetime import datetime
import re

app = Flask(__name__)

ChatFileFirstPart = "Chat de WhatsApp con "
ExportExtension = "txt"


@app.route('/', methods=['GET'])
def get_input_chats():
    return render_template('info_chats.html')

@app.route('/chats', methods=['POST'])
def chats():
    FileChat = request.files['file']
    dir_chats = 'chats/'
    chatFileName = dir_chats + secure_filename(FileChat.filename) 
    FileChat.save(chatFileName)
    dir_path_chats = Path(dir_chats)
    # for FChat in dir_chats.glob('*.'+ExportExtension):
    users_conversacion = parse_user_from_file(str(chatFileName))
    # users_conversacion = parse_user_from_file(str(chatFileName))
    resultados = estadisticas(chatFileName, users_conversacion)
    # resultados['contador_mensajes'] -= 1
    return render_template('show_info.html', title="Analizador Whatsapp chats", chat=FileChat, resultados=resultados, usuarios=users_conversacion)

@app.route('/chats_consola', methods=['GET'])
def chats_consola():
    dir_chats = Path('chats/')
    for name in dir_chats.glob('*.txt'):
        print(str(name), file=sys.stderr)
        with open(name) as chat:
            line = chat.read()
            print(line, file=sys.stderr)
        print('*********************', file=sys.stderr)
    return 'Hecho'


def parse_user(url_archivo):
    sin_parte_delantera = url_archivo[url_archivo.find(ChatFileFirstPart)+len(ChatFileFirstPart):]
    return sin_parte_delantera[:sin_parte_delantera.find("."+ExportExtension)].replace(' ', '_')

def parse_user_from_file(url_archivo):
    usuarios = []
    with open(url_archivo) as chat:
        for line in chat:
            if es_mensaje(line):
                data = datos_relevantes(line)
                if data['usuario'] not in usuarios:
                    usuarios.append(data['usuario'])
    return usuarios

def estadisticas(url, arr_usuarios):
    datos_usuarios = data_estructure_usuarios(arr_usuarios)
    fecha_ultimo_mensaje = datetime(1970, 1, 1)
    # coloco un array de 24 posiciones para ir sumando las horas en las cuales se enviaron los mensajes
    hora_mensajes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # {'lun':0, 'mar':0, 'mier':0, 'jue':0, 'vie':0, 'sab':0, 'dom':0}
    contador_dia_mensajes = [0, 0, 0, 0, 0, 0, 0]
    with open(url) as chat:
        for line in chat:  # esto es lo mismo que hacer for line in chat.readlines():
            # if datos_usuarios['contador_mensajes'] > 0:
            if es_mensaje(line):
                data = datos_relevantes(line)
                index_user = data['usuario']
                datos_usuarios = contadores_usuario(datos_usuarios, data)

                hora_mensajes[data['fecha'].hour] += 1
                contador_dia_mensajes[data['fecha'].weekday()] += 1
                diferencia = data['fecha'] - fecha_ultimo_mensaje
                # diferencia.total_seconds() //3600 traduce la cantidad de segundos en horas
                if diferencia.total_seconds() // 3600 >= 15 or datos_usuarios['contador_mensajes'] == 0:
                    datos_usuarios[index_user]['arranco_conversacion'] += 1
                    datos_usuarios[index_user]['mensajes_arranque'].append(line)
                fecha_ultimo_mensaje = data['fecha']
                datos_usuarios['mensajes'].append((index_user, line))
                datos_usuarios['contador_mensajes'] += 1
        for user in arr_usuarios:
            if datos_usuarios[user]['contador_mensajes'] != 0:
                datos_usuarios[user]['promedio_largo_mensajes'] = round(datos_usuarios[user]['contador_caracteres'] / datos_usuarios[user]['contador_mensajes'])
            palabra = indice_del_maximo_diccionario(datos_usuarios[user]['palabras_mas_usadas'])
            datos_usuarios[user]['cantidad_palabra_mas_usada'] = datos_usuarios[user]['palabras_mas_usadas'][palabra]
            datos_usuarios[user]['palabras_mas_usadas']['-cumplen-requisito-'] = 0
            for key in datos_usuarios[user]['palabras_mas_usadas'].keys():
                if datos_usuarios[user]['palabras_mas_usadas'][key] >= datos_usuarios['minimo_considerable_palabra_usada']:
                    datos_usuarios[user]['palabras_mas_usadas']['-cumplen-requisito-'] = + 1
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    datos_usuarios['maximo_sitio_visitado'] = indice_del_maximo_diccionario(datos_usuarios['sitios_mas_compartidos'])
    datos_usuarios['maximo_hora_mensajes'] = indice_del_maximo(hora_mensajes)
    datos_usuarios['maximo_dia_mensajes'] = indice_del_maximo(contador_dia_mensajes)
    datos_usuarios['hora_mensajes'] = hora_mensajes
    index = 0
    for cantidad_mensajes_en_el_dia in contador_dia_mensajes:
        datos_usuarios['dia_mensajes'].append(cantidad_mensajes_en_el_dia)
        index += 1
    return datos_usuarios


def acumulador_palabras(mensaje, acumulador):
    arr_palabras = re.compile(r'\W+', re.UNICODE).split(mensaje)
    for palabra in arr_palabras:
        palabra = palabra.lower()
        palabra = palabra.strip()
        if palabra != '':
            acumulador[palabra] = acumulador[palabra] + \
                1 if palabra in acumulador else 1
    return acumulador


def acumulador_sitios(mensaje, acumulador):
    regex = re.compile(
        r'(https?://|/)'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    encontrado = regex.search(mensaje)
    if encontrado != None:
        substr = mensaje[encontrado.start():]
        aux_arr = substr.split('/')
        substr = '/' + \
            aux_arr[1] if aux_arr[1] != '' else aux_arr[0]+'//'+aux_arr[2]
        acumulador[substr] = acumulador[substr] + \
            1 if substr in acumulador else 1
    return acumulador


def contadores_usuario(datos_usuarios, data):
    index_user = data['usuario']
    datos_usuarios[index_user]['contador_mensajes'] += 1
    datos_usuarios[index_user]['contador_palabras'] += data['cantidad_palabras']
    datos_usuarios[index_user]['contador_caracteres'] += data['largo_mensaje']
    datos_usuarios['sitios_mas_compartidos'] = acumulador_sitios(data['mensaje'], datos_usuarios['sitios_mas_compartidos'])
    datos_usuarios[index_user]['palabras_mas_usadas'] = acumulador_palabras(data['mensaje'], datos_usuarios[index_user]['palabras_mas_usadas'])
    return datos_usuarios


def data_estructure_usuarios(usuarios):
    arr_datos_usuario = {}
    arr_datos_usuario['mensajes'] = []
    arr_datos_usuario['contador_mensajes'] = 0
    # coloco un array de 24 posiciones para ir sumando las horas en las cuales se enviaron los mensajes
    arr_datos_usuario['hora_mensajes'] = []
    # {'lun':0, 'mar':0, 'mier':0, 'jue':0, 'vie':0, 'sab':0, 'dom':0}
    arr_datos_usuario['dia_mensajes'] = []
    arr_datos_usuario['maximo_dia_mensajes'] = 0
    arr_datos_usuario['maximo_hora_mensajes'] = 0
    arr_datos_usuario['sitios_mas_compartidos'] = {}
    arr_datos_usuario['minimo_considerable_palabra_usada'] = 5
    for usuario in usuarios:
        arr_datos_usuario[usuario] = {
            'contador_mensajes': 0,
            'contador_palabras': 0,
            'contador_caracteres': 0,
            'promedio_largo_mensajes': 0,
            'arranco_conversacion': 0,
            'mensajes_arranque': [],
            'palabras_mas_usadas': {},
            'cantidad_palabra_mas_usada': 0
        }
    return arr_datos_usuario

# devuelve una estructura con varios datos del mensaje que necesitaremos para realizar la estadística


def datos_relevantes(line):
    # separo fecha y hora de usuario y mensaje  12/12/2222 22:40 - Franco:....
    cabecera_y_mensaje = line.split('-')
    # realizo un recorte del mensaje por  el segundo arg que sería ' Franco:...' quedandome con los caracteres que van desde el ppio hasta ':'
    usuario = cabecera_y_mensaje[1][:cabecera_y_mensaje[1].find(':')]
    # realizo un recorte para quedarme con el mensaje en si
    mensaje = cabecera_y_mensaje[1][cabecera_y_mensaje[1].find(':'):].strip()
    # quito los espacios de alrededor y reemplazo los espacios por '_'
    usuario = usuario.strip().replace(' ', '_')
    fecha = cabecera_y_mensaje[0].split(' ')
    hora = fecha[1]
    fecha = fecha[0]
    return {'fecha': convertir_a_fecha(fecha, hora), 'usuario': usuario, 'mensaje': mensaje,
            'largo_mensaje': len(mensaje), 'cantidad_palabras': len(mensaje.split(' '))}
    # quitamos la parte delantera del chat donde se indica la fecha y el nombre de usuario para usar esto para la estadistica

# verificamos que el string sea un mensaje




def es_mensaje(string):
    # Para que sea mensaje tiene que tener este formato 12/12/2222 22:40 - Franco:....
    # => arr_datos = ['12/12/2222', '22:40', '-', 'Franco:...'
    fecha_mensaje = string.split('-')
    if len(fecha_mensaje) >= 2:
        arr_datos = fecha_mensaje[0].split(' ')
        fecha = ''
        hora = ''
        if len(arr_datos) > 2:
            fecha = arr_datos[0]
            hora = arr_datos[1]
            mensaje = fecha_mensaje[1]
            es_fecha = re.compile(
                r'([1-2][0-9]|3[0-1]|[1-9])/([1-9]|1[0-2])/([0-9][0-9])')
            es_hora = re.compile(r'([0-1][0-9]|2[0-3]):([0-5][0-9])')
            if es_fecha.match(fecha) != None and es_hora.match(hora) != None and mensaje.find(':') > -1:
                return True
    return False


def convertir_a_fecha(str_fecha, str_hora):
    fecha = str_fecha.split('/')  # fecha = ['12', '12', '2222']
    fecha = datetime(int(fecha[0]), int(fecha[1]), int(fecha[2]))
    hora = str_hora.split(':')  # dado que el formato es 'dd/mm/aa hh:mm -...'
    return datetime(fecha.day, fecha.month, fecha.year, int(hora[0]), int(hora[1]))


def indice_del_maximo_diccionario(dicc):
    maximo = 0
    key_max = ''
    for key in dicc.keys():
        if dicc[key] > maximo:
            maximo = dicc[key]
            key_max = key
    return key_max


def indice_del_maximo(arr):
    maximo = 0
    for valor in arr:
        if valor > maximo:
            maximo = valor
    return arr.index(maximo)


if(__name__ == '__main__'):
    app.run(host="0.0.0.0", port="4000", debug=True)
