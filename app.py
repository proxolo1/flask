from flask import Flask, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

@socketio.on('message')
def handle_message(data):
    print(f'Received message: {data}')
    emit('response', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)