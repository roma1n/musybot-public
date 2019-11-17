import telebot
import deezer_handler
import list_builder
import traceback
import deezer


with open('telebot_token.txt', 'r') as f:
    bot_token = f.read()

bot = telebot.TeleBot(bot_token)

ds = deezer_handler.Session()

users_in_process = {}


@bot.message_handler(commands=['start', 'help'], content_types=['text'])
def send_welcome(message):
    bot.send_message(message.from_user.id,
                     "Hello. Use /chart to get list of charts. Use /search to execute search on deezer")


tracks_in_message = {}
user_context = {}


# chart
@bot.message_handler(commands=['chart'], content_types=['text'])
def chart(message):
    try:
        user_id = message.from_user.id
        lb = list_builder.ListBuilder(list_builder.to_list_of_lists(ds.charts()))
        k = lb.get_keyboard()
        bot.send_message(user_id, 'Select chart', reply_markup=k)
        user_context[user_id] = ds.chart_id
    except Exception:
        print(traceback.format_exc())


# search
@bot.message_handler(commands=['search'], content_types=['text'])
def search(message):
    try:
        user_id = message.from_user.id
        m = bot.send_message(user_id, 'Enter your query')
        bot.register_next_step_handler(m, searcher)
    except Exception:
        print(traceback.format_exc())


def searcher(message):
    user_id = message.from_user.id
    tracks = ds.exec_search(message.text)
    send_tracks(user_id, tracks)


# send_[object]_info
def send_track_info(message, ids=None, names=None):
    try:
        if names is None:
            names = list()
        if ids is None:
            ids = list()
        i = 0
        for counter in range(len(names)):
            if names[counter] == [message.text]:
                i = counter
                break
        else:
            return None
        send_object_info(message.from_user.id, ds.track_info[ids[i]])
    except Exception:
        print(traceback.format_exc())


def send_object_info(user_id, obj):
    if type(obj) == list:
        send_tracks(user_id, obj)
    else:
        user_context[user_id] = obj
        lb = list_builder.ListBuilder([ds.get_options(obj)])
        params = ds.get_parameter_list(obj)
        ans = []
        for p in params:
            ans.append(ds.get_parameter(obj, p))
        bot.send_message(user_id,
                         'no info' if len(ans) == 0 else '\n'.join(ans),
                         reply_markup=lb.get_keyboard())


# send_[object]_parameter
@bot.message_handler(content_types=['text'])
def send_parameter(message):
    user_id = message.from_user.id
    if user_context[user_id] == ds.chart_id:
        tracks = ds.chart_tracks(region=message.text)
        send_tracks(user_id, tracks)
    elif message.text == 'download':
        if type(user_context[user_id]) == deezer.Track:
            fname = ds.download(user_context[user_id].id)
            with open(fname, 'rb') as file:
                bot.send_audio(user_id, file)
    else:
        res = ds.exec_option(user_context[user_id], message.text)
        if type(res['context']) == type(user_context[user_id]) and res['context'].id == user_context[user_id].id:
            bot.send_message(user_id, res['text'])
        else:
            send_object_info(user_id, res['context'])


def send_tracks(user_id, tracks):
    try:
        names = ds.track_name(tracks)
        lb = list_builder.ListBuilder(names)
        cb = list_builder.ListBuilder(['more information about track in this list...'])
        cbq = cb.get_inline_list(callbacks=['inf on tracks'])
        message = bot.send_message(user_id, lb.get_numerated(), reply_markup=cbq)
        tracks_in_message[message.message_id] = []
        for i in range(len(tracks)):
            ds.track_info[tracks[i].id] = tracks[i]
            tracks_in_message[message.message_id].append(tracks[i].id)
    except Exception:
        print(traceback.format_exc())


@bot.callback_query_handler(func=lambda cbq: 'inf on tracks' in cbq.data)
def callback(cbq):
    ids = tracks_in_message[cbq.message.message_id]
    names = []
    for i in ids:
        names.append([ds.track_name(ds.track_info[i])[0]])
    lb = list_builder.ListBuilder(names)
    message = bot.send_message(cbq.from_user.id, 'Select track', reply_markup=lb.get_keyboard())
    bot.register_next_step_handler(message, send_track_info, ids=ids, names=names)


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=1)
