import os

from flask import Flask, request
import telebot
import main
from main import bot

TOKEN = main.bot_token
server = Flask(__name__)


@server.route('/' + TOKEN, methods=['POST', 'GET'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=<heroku app url> + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
