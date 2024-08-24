import uuid
from flask import Blueprint, Flask, make_response, render_template, request
from flask_socketio import SocketIO, emit

socketio = SocketIO()
app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = "SECRET"
main = Blueprint("main", __name__)

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/player")
def player() :
    return render_template("player.html")
app.register_blueprint(main)
socketio.init_app(app)
# Dictionary to store session info
session_user = {}
player1_message = None
player2_message = None

@socketio.on('connect')
def handle_connect():
    session_id = request.sid
    # Check for a user ID in cookies
    user_id = request.cookies.get('user_id')
    if user_id is None:
        # Generate a new user ID and set it in the response cookies
        user_id = str(uuid.uuid4())
        response = make_response()
        response.set_cookie('user_id', user_id)
        emit('message', {'type': 'status', 'content': 'user_id_set', 'cookie': user_id}, room=session_id)
    else:
        emit('message', {'type': 'status', 'content': 'user_id_exists', 'cookie': user_id}, room=session_id)

@socketio.on('message')
def handle_message(data):
    global player1_message, player2_message

    msg_type, content = data['type'], data['content']
    session_id = request.sid
    user_id = request.cookies.get('user_id')

    if msg_type == 'init':
        player_found = False
        for player, info in session_user.items():
            if info['user_id'] == user_id:
                player_found = True
                emit('message', {'type': 'status', 'content': f'{player}'})
                break

        if not player_found:
            if 'player1' not in session_user:
                session_user['player1'] = {'session_id': session_id, 'user_id': user_id}
                emit('message', {'type': 'status', 'content': 'player1'})
            elif 'player2' not in session_user:
                session_user['player2'] = {'session_id': session_id, 'user_id': user_id}
                emit('message', {'type': 'status', 'content': 'player2'})
            else:
                emit('message', {'type': 'status', 'content': 'Game is full'})
    elif 'player' in msg_type or 'admin' in msg_type:
        add_players(msg_type, session_id, content)
    elif 'advisor' in msg_type:
        add_keyword_by_advisor(content)
    elif 'message' in msg_type:
        store_player_message(session_id, content)

        # Check if both players sent their messages
        if player1_message is not None and player2_message is not None:
            # Compare messages and declare winner
            if player1_message == player2_message:
                send_winner_notification()

            # Notify admin with both player messages
            notify_admin_with_messages()

            # Reset messages
            player1_message = None
            player2_message = None

def add_players(player_type, session_id, player_name):
    # if player_type in session_user:
    #     emit('message', {'type': 'status', 'content': f"{player_type} already exists"}, to=session_id)
    #     return
    user_id = request.cookies.get('user_id')
    session_user[player_type] = {'player_name': player_name, 'session_id': session_id, 'user_id': user_id}
    emit('message', {'type': 'status', 'content': f"{player_type} added"}, to=session_id)

    # Start game when player2 is added
    if player_type == 'player2':
        player1 = session_user.get('player1')
        admin = session_user.get('admin')

        if player1:
            emit('message', {'type': 'status', 'content': 'starting game ...'}, to=player1['session_id'])
            emit('message', {'type': 'status', 'content': 'starting game ...'}, to=session_id)
            if admin:
                emit('message', {'type': 'status', 'content': f"player 1 : {player1['player_name']}, player 2 : {player_name}"}, to=admin['session_id'])

def add_keyword_by_advisor(keywords):
    player1_keyword, player2_keyword = keywords.split(',')
    admin = session_user.get('admin')

    if admin:
        emit('message', {'type': 'status', 'content': f"player one : {player1_keyword}, player two : {player2_keyword}"}, to=admin['session_id'])

def store_player_message(session_id, message):
    global player1_message, player2_message

    for player, info in session_user.items():
        if info['session_id'] == session_id:
            if player == 'player1':
                player1_message = message
            elif player == 'player2':
                player2_message = message
            break

def send_winner_notification():
    admin = session_user.get('admin')
    if admin:
        emit('message', {'type': 'status', 'content': 'We have a winner!'}, to=admin['session_id'])

def notify_admin_with_messages():
    admin = session_user.get('admin')
    if admin:
        emit('message', {'type': 'status', 'content': f"player 1 : {player1_message}, player 2 : {player2_message}"}, to=admin['session_id'])



socketio.run(app)