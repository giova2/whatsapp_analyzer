from datetime import datetime
import re


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
