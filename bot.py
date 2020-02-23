import re
import time
import telebot
from telebot import types

authorized_users = []

userState = {}  # so they won't reset every time the bot restarts

bot = telebot.TeleBot("zzz")

hideBoard = types.ReplyKeyboardRemove()  # if sent as reply_markup, will hide the keyboard

commands = {  # command description used in the "help" command
    'start': 'Начать работу',
    'help': 'Показывает информацию о доступных командах',
    'promo': 'Запускает акции на заранее установленную группу товаров',
    'presence': 'Установить наличие товара по указанному артикулу',
    'price': 'Устанавливает новую цену для указанного артикула',
    'orders': 'Показывает пришедшие заказы за сегодня',
    'bossapp': 'Синхронизировать Prom по прайсу из Boss-app',
    'good': 'Я умею делать хорошо'
}


def dump(obj):
    for attr in dir(obj):
        print("obj.%s = %r" % (attr, getattr(obj, attr)))


def get_user_step(message):
    cid = message.chat.id
    user_id = message.json['from']['id']
    user_hash = str(cid) + str(user_id)

    if user_hash in userState:
        return userState[user_hash]['action'], userState[user_hash]['step']
    else:
        reset_user_state(user_hash)
        print("New user detected, who hasn't used \"/start\" yet: " + user_hash)
        return 'None', 0


def authorize_user_action(cid, user_id, action):
    if user_id not in authorized_users:
        bot.send_message(cid, "Ты кто такой?")
        return False

    user_hash = str(cid) + str(user_id)

    if user_hash not in userState:
        reset_user_state(user_hash)
    elif action != userState[user_hash]['action']:
        reset_user_state(user_hash)
        # userState[user_hash]['action'] = action

    return True


def reset_user_state(user_hash):
    userState[user_hash] = {}
    userState[user_hash] = {
        'action': 'None',
        'step': 0,
        'user_input': 'None'
    }


# only used for console output now
def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)


def get_product_code(text):
    product_code = text.upper()

    # [TODO] validate

    return product_code


# handle the "/start" command
@bot.message_handler(commands=['start'])
def command_start(message):
    cid = message.chat.id
    user_id = message.json['from']['id']
    if not authorize_user_action(cid, user_id, 'start'):
        return

    command_help(message)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    itembtn1 = types.KeyboardButton('/Запустить_акции')
    itembtn2 = types.KeyboardButton('/Изменить_наличие')
    itembtn3 = types.KeyboardButton('/Установить_цену')
    itembtn4 = types.KeyboardButton('/BOSS_app_прайс')
    itembtn5 = types.KeyboardButton('/Показать_заказы_за_сегодня')
    itembtn6 = types.KeyboardButton('/Сделай_мне_хорошо')
    markup.row(itembtn1, itembtn2)
    markup.row(itembtn3, itembtn4)
    markup.row(itembtn5, itembtn6)
    bot.send_message(cid, "Что мне сделать для тебя:", reply_markup=markup)


# help page
@bot.message_handler(commands=['help'])
def command_help(message):
    cid = message.chat.id
    bot.send_chat_action(cid, 'typing')
    help_text = "Я могу: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)  # send the generated help page


@bot.message_handler(commands=['Запустить_акции', 'promo'])
def command_start_promo(message):
    cid = message.chat.id
    user_id = message.json['from']['id']
    user_hash = str(cid) + str(user_id)
    if not authorize_user_action(cid, user_id, 'promo'):
        return

    bot.send_chat_action(cid, 'typing')
    bot.send_message(cid, "_Я запущу акции на заранее установленную группу товаров_", parse_mode='MarkdownV2')
    userState[user_hash]['action'] = 'promo'
    userState[user_hash]['step'] = 1


@bot.message_handler(commands=['Изменить_наличие', 'presence'])
def command_set_presence(message):
    cid = message.chat.id
    user_id = message.json['from']['id']
    user_hash = str(cid) + str(user_id)
    if not authorize_user_action(cid, user_id, 'presence'):
        return
    bot.send_chat_action(cid, 'typing')

    one_time_kb = types.ReplyKeyboardMarkup(one_time_keyboard=True)  # create the image selection keyboard
    one_time_kb.add('Гарантированное_наличие')
    one_time_kb.add('В_наличии')
    one_time_kb.add('Нет_в_наличии')
    one_time_kb.add('Ожидается')

    bot.send_message(cid, "_Я установлю наличие товара по артикулу_",
                     reply_markup=one_time_kb, parse_mode='MarkdownV2')  # show the keyboard
    userState[user_hash]['action'] = 'presence'
    userState[user_hash]['step'] = 1


@bot.message_handler(func=lambda message: get_user_step(message) == ('presence', 1))
def get_presence_action(message):
    cid = message.chat.id
    user_id = message.json['from']['id']
    user_hash = str(cid) + str(user_id)
    if not authorize_user_action(cid, user_id, 'presence'):
        return

    text = message.text
    bot.send_chat_action(cid, 'typing')

    # markup = types.ForceReply(selective=False)
    # bot.send_message(message.chat.id, "Укажи артикул:", reply_markup=markup)

    if text == 'Гарантированное_наличие':
        userState[user_hash]['user_input'] = ('available', 'true')
        userState[user_hash]['step'] = 2
    elif text == 'В_наличии':
        userState[user_hash]['user_input'] = ('available', 'false')
        userState[user_hash]['step'] = 2
    elif text == 'Нет_в_наличии':
        userState[user_hash]['user_input'] = ('not_available', 'false')
        userState[user_hash]['step'] = 2
    elif text == 'Ожидается':
        userState[user_hash]['user_input'] = ('waiting', 'false')
        userState[user_hash]['step'] = 2
    else:
        bot.send_message(cid, "*Я не понимаю! Либо 'Снять', либо 'Вернуть'*", parse_mode='MarkdownV2')
        # bot.send_message(cid, "Попробуй еще раз.")
        reset_user_state(user_hash)
        markup = types.ReplyKeyboardMarkup()
        itembtn_go = types.KeyboardButton('/start')
        markup.row(itembtn_go)
        bot.send_message(cid, "Попробуй еще раз.", reply_markup=markup)
        return

    bot.send_message(message.chat.id, "Укажи *артикул*:", reply_markup=hideBoard, parse_mode='MarkdownV2')


@bot.message_handler(func=lambda message: get_user_step(message) == ('presence', 2))
def get_presence_code(message):
    cid = message.chat.id
    user_id = message.json['from']['id']
    user_hash = str(cid) + str(user_id)
    if not authorize_user_action(cid, user_id, 'presence'):
        return

    bot.send_chat_action(cid, 'typing')
    product_code = get_product_code(message.text)
    print('Call Prom functionality for the code ' + product_code)

    bot.send_message(cid, 'Артикул "' + product_code + '" принят. Значение: ' + str(userState[user_hash]['user_input']))
    bot.send_message(cid, 'Но я пока хз что с ним делать 🤪')

    reset_user_state(user_hash)


@bot.message_handler(commands=['Установить_цену', 'price'])
def command_set_new_price(message):
    cid = message.chat.id
    user_id = message.json['from']['id']
    user_hash = str(cid) + str(user_id)
    if not authorize_user_action(cid, user_id, 'price'):
        return

    bot.send_chat_action(cid, 'typing')
    bot.send_message(cid, "_Я установлю новую цену по артикулу_", parse_mode='MarkdownV2')

    markup = types.ForceReply(selective=False)
    bot.send_message(message.chat.id, 'Укажи новую *цену* \(одно целое число\)\.',
                     reply_markup=markup, parse_mode='MarkdownV2')
    userState[user_hash]['action'] = 'price'
    userState[user_hash]['step'] = 1


@bot.message_handler(func=lambda message: get_user_step(message) == ('price', 1))
def get_new_price_action(message):
    cid = message.chat.id
    user_id = message.json['from']['id']
    user_hash = str(cid) + str(user_id)
    if not authorize_user_action(cid, user_id, 'price'):
        return

    text = message.text
    bot.send_chat_action(cid, 'typing')

    pattern = re.compile(r"^\d{2,4}$")

    if pattern.match(text):
        userState[user_hash]['user_input'] = text
        userState[user_hash]['step'] = 2
    else:
        bot.send_message(cid, "*Это не похоже на цену\.*", parse_mode='MarkdownV2')
        # bot.send_message(cid, "Попробуй еще раз.")
        reset_user_state(user_hash)

        markup = types.ReplyKeyboardMarkup()
        itembtn_go = types.KeyboardButton('/start')
        markup.row(itembtn_go)
        bot.send_message(cid, "Попробуй еще раз.", reply_markup=markup)
        return

    bot.send_message(message.chat.id, "Укажи *артикул*:", reply_markup=hideBoard, parse_mode='MarkdownV2')


@bot.message_handler(func=lambda message: get_user_step(message) == ('price', 2))
def get_new_price_code(message):
    cid = message.chat.id
    user_id = message.json['from']['id']
    user_hash = str(cid) + str(user_id)
    if not authorize_user_action(cid, user_id, 'price'):
        return

    bot.send_chat_action(cid, 'typing')
    product_code = get_product_code(message.text)
    print('Call Prom functionality ' + product_code)

    bot.send_message(cid, 'Артикул "' + product_code + '" принят. Новая цена: ' + userState[user_hash]['user_input'])
    bot.send_message(cid, 'Но я пока хз что с этим делать 🤪')

    reset_user_state(user_hash)


@bot.message_handler(commands=['Показать_заказы_за_сегодня', 'orders'])
def command_show_todays_orders(message):
    cid = message.chat.id
    user_id = message.json['from']['id']
    user_hash = str(cid) + str(user_id)
    if not authorize_user_action(cid, user_id, 'orders'):
        return

    bot.send_chat_action(cid, 'typing')
    time.sleep(2)
    bot.reply_to(message, "Это слишком круто для меня!")


@bot.message_handler(commands=['BOSS_app_прайс', 'bossapp'])
def command_sync_bossapp(message):
    cid = message.chat.id
    user_id = message.json['from']['id']
    user_hash = str(cid) + str(user_id)
    if not authorize_user_action(cid, user_id, 'bossapp'):
        return

    bot.send_chat_action(cid, 'typing')
    time.sleep(2)
    bot.reply_to(message, "Это слишком круто для меня!")
    bot.send_message(message.chat.id, "_Может быть, я буду уметь проверять наличие в Prom, по брошенному мне PDF "
                                      "прайсу из Boss\-app_", parse_mode='MarkdownV2')


@bot.message_handler(commands=['Сделай_мне_хорошо', 'good'])
def command_make_me_good(message):
    cid = message.chat.id
    bot.send_message(cid, "Я умею делать хорошо...")
    bot.send_chat_action(cid, 'typing')  # show the bot "typing" (max. 5 secs)
    time.sleep(4)
    bot.send_message(cid, "...но только не тебе! 😂🤣😝")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    cid = message.chat.id

    markup = types.ReplyKeyboardMarkup()
    itembtn_go = types.KeyboardButton('/start')
    markup.row(itembtn_go)
    bot.send_message(cid, "Что делаем?", reply_markup=markup)


bot.set_update_listener(listener)  # register listener

bot.polling()
