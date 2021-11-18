import os
from flask import Flask, request
import telegram
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

load_dotenv()

URL = os.getenv("bot_url")
TOKEN = os.getenv("bot_token")
db_name = os.getenv("db_name")
db_user = os.getenv("db_user")
db_user_password = os.getenv("db_user_password")


bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_user_password}@localhost/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# model class


class UsersTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50))

    def __init__(self, user_name):
        self.user_name = user_name

    def __repr__(self):
        return f"<User {self.user_name}>"


messages = []


@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():

    update = telegram.Update.de_json(request.get_json(force=True), bot)
    user = update.effective_user
    user_id = user.id
    user_name = f'{user.last_name} {user.first_name} (@{user.username})'
    chat_id = update.message.chat.id
    msg_id = update.message.message_id
    messages.append(msg_id)
    photo = bot.get_user_profile_photos(user.id).to_dict()

    text_msg = update.message.text.encode('utf-8').decode()

    if text_msg == "/start":
        all_users_db = UsersTable.query.all()
        results = [user.user_name for user in all_users_db]
        if user_name not in results:
            new_user = UsersTable(user_name=user_name)
            db.session.add(new_user)
            db.session.commit()

    elif text_msg == "/me":
        s = bot.send_photo(user_id, photo['photos'][0][0]['file_id'])
        messages.append(s.message_id)
        sends = [user_name, user_id]

        for send in sends:
            s = bot.send_message(user_id, send)
            messages.append(s.message_id)

    elif text_msg == "/clear":
        for ms_id in messages:
            try:
                bot.deleteMessage(chat_id, ms_id)
            except:
                pass

    return 'ok'


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():

    s = bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=TOKEN))
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


@app.route('/')
def index():
    return '<h1>app Flask</h1>'


if __name__ == '__main__':
    app.run(threaded=True)
