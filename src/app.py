from flask import Flask, jsonify, render_template, request
import estadisticas
import constants
import users
from pathlib import Path
from werkzeug.utils import secure_filename
import sys

app = Flask(__name__)


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


@app.route('/users')
def usersHandlers():
    return jsonify({'users': users})


if(__name__ == '__main__'):
    app.run(host="0.0.0.0", port="4000", debug=True)
