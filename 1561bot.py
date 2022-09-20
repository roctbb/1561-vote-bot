from telebot import TeleBot, types
from config import token, default_balance, projects_count
import json

bot = TeleBot(token=token)

state = {}

try:
    with open('state.json') as f:
        state = json.load(f)
except:
    state = {
        "projects": {
            str(i): {
                "count": 0,
                "reviews": [],
                "users": []
            } for i in range(1, projects_count + 1)
        },
        "users": {}
    }


def safe_send(to, m, keyboard=None):
    try:
        bot.send_message(to, m, reply_markup=keyboard)
    except Exception as e:
        print("Message error:", e)


def save():
    try:
        with open('state.json', 'w') as f:
            f.write(json.dumps(state))
    except Exception as e:
        print("save error", e)


def init_user(message):
    if str(message.chat.id) not in state["users"]:
        state["users"][str(message.from_user.id)] = {
            "balance": default_balance,
            "user_id": message.from_user.id,
            "state": "project"
        }

        try:
            state["users"][str(message.from_user.id)]["username"] = message.from_user.username
        except:
            pass

        try:
            state["users"][str(message.from_user.id)]["first_name"] = message.from_user.first_name
            state["users"][str(message.from_user.id)]["last_name"] = message.from_user.last_name
        except:
            pass


def make_projects_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for i in range(1, projects_count + 1):
        button = types.KeyboardButton(text="🗒 " + str(i))
        keyboard.add(button)

    return keyboard


def make_money_keyboard(money_count):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("Назад")
    for i in range(1, money_count + 1):
        button = types.KeyboardButton(text="💸 " + str(i))
        keyboard.add(button)

    return keyboard


def make_voting(message):
    if state["users"][str(message.from_user.id)]["balance"] > 0:
        state["users"][str(message.from_user.id)]["state"] = "project"
        safe_send(message.chat.id, "Укажи номер фотографии, за которую хочешь проголосовать 👀.", None)
    else:
        state["users"][str(message.from_user.id)]["state"] = "finished"
        safe_send(message.chat.id, "Спасибо за участие в голосовании! Ты вложил все свои монеты! 🙌")



@bot.message_handler(commands=['start', 'help'])
def start(message):
    init_user(message)

    safe_send(message.chat.id, f"""Привет! Этот бот поможет тебе проголосовать за летнюю фотографию от учеников нашей школы 🤓. 
    
Сейчас у тебя 💸 {state["users"][str(message.from_user.id)]["balance"]} монет. Ты можешь выбрать любимую фотографию и вложить сразу все монеты или распределить свой капитал между несколькими.""")

    make_voting(message)
    save()

@bot.message_handler(commands=['alive'])
def alive(message):
    safe_send(message.chat.id, "yep.")

@bot.message_handler(content_types=['text'])
def process_message(message):
    init_user(message)

    answer = str(message.text)
    money_count = state["users"][str(message.from_user.id)]["balance"]


    if state["users"][str(message.from_user.id)]["state"] == "project":
        answer = answer.lstrip("🗒 ")
        if answer.isnumeric() and int(answer) in range(1, projects_count + 1):
            if money_count > 0:
                state["users"][str(message.from_user.id)]["state"] = "money"
                state["users"][str(message.from_user.id)]["chosen"] = answer
                safe_send(message.chat.id, f'Сейчас у тебя 💸 {money_count} монет. Сколько хочешь отдать фотографии {answer}?', make_money_keyboard(money_count))
            else:
                safe_send(message.chat.id, "Монеты закончились.")
        else:
            safe_send(message.chat.id, "Выбери номер фотографии...", None)

    elif state["users"][str(message.from_user.id)]["state"] == "money":
        answer = answer.lstrip("💸 ")
        if answer.isnumeric() and int(answer) in range(1, money_count + 1):
            state["users"][str(message.from_user.id)]["state"] = "review"

            chosen_project = state["users"][str(message.from_user.id)]["chosen"]
            state["projects"][chosen_project]["count"] += int(answer)
            state["projects"][chosen_project]["users"].append((str(message.from_user.id), int(answer)))

            state["users"][str(message.from_user.id)]["balance"] -= int(answer)

            safe_send(message.chat.id, "Расскажи, чем тебе понравилась эта фотография? Что хотелось бы передать авторам? Ответ напиши одним сообщением... 🖌", types.ReplyKeyboardRemove())
        else:
            make_voting(message)

    elif state["users"][str(message.from_user.id)]["state"] == "review":

        chosen_project = state["users"][str(message.from_user.id)]["chosen"]
        state["projects"][chosen_project]["reviews"].append((str(message.from_user.id), answer))

        safe_send(message.chat.id, "Большое спасибо, твой голос сохранен! 👍")
        make_voting(message)
    else:
        make_voting(message)

    save()

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print("General exception:", e)
