from telebot import types


class ListBuilder:
    def __init__(self, l):
        self.list = l

    def get_inline_list(self, callbacks=[], **kwargs):
        res = types.InlineKeyboardMarkup(**kwargs)
        callbacks += ['None' for i in range(len(self.list) - len(callbacks))]
        res.add(*[types.InlineKeyboardButton(name, callback_data=cb) for name, cb in zip(self.list, callbacks)])
        return res

    def get_keyboard(self, *args, **kwargs):
        res = types.ReplyKeyboardMarkup(*args, **kwargs)
        for line in self.list:
            res.add(*[types.KeyboardButton(col) for col in line])
        return res

    def get_numerated(self, joiner='\n'):
        return joiner.join(['{}. {}'.format(number + 1, element) for number, element in enumerate(self.list)])

    def get(self, joiner='\n'):
        return joiner.join(['{}'.format(i) for i in self.list])


def to_list_of_lists(l):
    return [[i] for i in l]
