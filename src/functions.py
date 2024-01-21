import re
import emoji
from datetime import datetime
import pdb

cabeceras_index = 'messengers'
msgs_index = 'msgs'

def get_gross_data(data):
    # con este patron obtenemos una 3-tupla con los valores fecha,hora,usuario 
    pattern = re.compile(r'\n(\d+\/\d+\/\d+),\s+(\d+:\d+)\s+-\s(.*?):\s(.*)', re.UNICODE)
    # utilizamos este patron para separar cada uno de los mensajes
    # pattern_messages = re.compile('\n(\d+\/\d+\/\d+\s\d+:\d+\s+-\s+[a-zA-Z0-9]+\s?[a-zA-Z0-9]+\s?[a-zA-Z0-9]+)\s?:\s+')
    pattern_messages = re.compile(r'\n\d+\/\d+\/\d+,\s+\d+:\d+\s+-\s+.+\s?:\s+', re.UNICODE)
    cabeceras = re.findall(pattern, data)
    messages_split = pattern_messages.split(data)
    messages_split.pop(0) # descartamos el primer elemento porque lo que obtenemos es el mensaje de aviso de whatsapp que en realidad no debe contarse como mensaje en si mismo dado que ningún usuario del chat lo esta enviando 
    if(len(messages_split) != len(cabeceras)):
        raise NameError('La cantidad de mensajes y cabeceras son diferentes')
    # lo que se hace con pattern.split es separar el archivo de texto en un array tomando como 
    # parámetro de separación
    # la captura obtenida con la expresión regular (la captura es lo que está entre paréntesis)
    return {cabeceras_index: cabeceras, msgs_index: messages_split}

#cuenta los mensajes que envió cada usuario
def get_users(messengers):
    users = []
    for each in messengers:
        user_name = each[2].strip().lower().replace(' ', '_') # dado que las tuplas son (fecha, hora, usuario)
        if user_name not in users:
            print('\n user_name: ', user_name)
            users.append(user_name)
    return users



def acumulador_dia_mensajes(fecha, datos_usuarios, user_name):
    fecha_formateada = convertir_a_fecha(fecha)
    datos_usuarios['dia_mensajes'][fecha_formateada.weekday()] += 1
    datos_usuarios[user_name]['dia_mensajes'][fecha_formateada.weekday()] += 1

def acumulador_hora_mensajes(hora, datos_usuarios, user_name):
    pure_hour = int(hora.split(':')[0])
    datos_usuarios['hora_mensajes'][pure_hour] += 1
    datos_usuarios[user_name]['hora_mensajes'][pure_hour] += 1

def extraer_emojis(df_column):
    emojis=[]
    for string in df_column: #my_df[columnname]:
        my_str = str(string)
        for each in my_str:
            if each in emoji.EMOJI_DATA:
                emojis.append(each)
    return emojis

def acumulador_palabras(mensaje, datos_usuarios, user_name): #acumulador_palabras, acumulador_palabras_usadas, acumulador_caracteres):
    if mensaje != '<Multimedia omitido>':
        datos_usuarios[user_name]['contador_caracteres'] += len(mensaje)
        arr_palabras = re.compile(r'\W+', re.UNICODE).split(mensaje)
        for palabra in arr_palabras:
            palabra = palabra.lower()
            palabra = palabra.strip()
            if palabra != '':
                datos_usuarios[user_name]['contador_palabras'] += 1 
                datos_usuarios[user_name]['palabras_mas_usadas'][palabra] = datos_usuarios[user_name]['palabras_mas_usadas'][palabra] + 1 if palabra in datos_usuarios[user_name]['palabras_mas_usadas'] and len(palabra) > 1 else 1
    # return [acumulador_palabras_usadas,acumulador_palabras,acumulador_caracteres]


def acumulador_sitios(mensaje, datos_usuarios):
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
        datos_usuarios['sitios_mas_compartidos'][substr] = datos_usuarios['sitios_mas_compartidos'][substr] + \
            1 if substr in datos_usuarios['sitios_mas_compartidos'] else 1
    return datos_usuarios['sitios_mas_compartidos']

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

def convertir_a_fecha(str_fecha, str_hora='00:01'):
    fecha = str_fecha.split('/')  # fecha = ['12', '12', '2222']
    # datetime espera los sigs args YYYY, MM, DD, HH, mm, ss,...
    fecha = datetime(int('20'+fecha[2]), int(fecha[1]), int(fecha[0]))
    hora = str_hora.split(':')  # dado que el formato es 'dd/mm/aa hh:mm -...'
    return datetime(fecha.year, fecha.month, fecha.day, int(hora[0]), int(hora[1]))


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