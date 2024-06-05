import telebot
import requests
from bs4 import BeautifulSoup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class FoodParserBotApp:

    def __init__(self, api_token, target_channel_id, users):
        self.api_token = api_token
        self.target_channel_id = target_channel_id
        self.users = users
        self.message_text = ""

        self.bot = telebot.TeleBot(self.api_token)

        self.bot.message_handler(commands=['start'])(self.send_welcome)
        self.bot.message_handler(content_types=['text'])(self.handle_text)
        self.bot.callback_query_handler(func=lambda call: True)(self.handle_query)

    # Открывает ссылку, достает из нее title и description
    # Возвращает строку формата Название: title, Описание: description, Ссылка: URL
    def get_preview_text(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()

            result = ""

            soup = BeautifulSoup(response.content, 'html.parser')
            # Попробуем получить мета-описание
            title = soup.find('meta', attrs={'name': 'title'})
            description = soup.find('meta', attrs={'name': 'description'})
            if title and title.get('content'):
                result += f"Название: {title['content']}\n"
                if description and description.get('content'):
                    result += f"Описание: {description['content']}\n"
                result += f"Ссылка: {url}"
                return result

            return "Не удалось извлечь предварительный просмотр."
        except requests.RequestException as e:
            return f"Произошла ошибка при попытке получить данные: {e}"

    def send_welcome(self, message):
        sender_id = message.from_user.id
        if sender_id not in self.users:
            self.bot.reply_to(message, "Извини, у тебя нет доступа, чтобы работать со мной")
            return
        self.bot.reply_to(message, "Привет!\n"
                              "Пришли мне ссылку на рецепт🤗")
        return

    def handle_text(self, message):
        sender_id = message.from_user.id
        if sender_id not in self.users:
            self.bot.reply_to(message, "Извини, у тебя нет доступа, чтобы работать со мной")
            return

        self.bot.reply_to(message, "🔍 Сканирую ссылку...")

        url = message.text
        preview_text = self.get_preview_text(url)
        self.message_text = preview_text

        markup = InlineKeyboardMarkup()
        yes_button = InlineKeyboardButton('✅Да', callback_data='yes')
        no_button = InlineKeyboardButton('❌Нет', callback_data='no')
        markup.add(yes_button, no_button)

        self.bot.reply_to(message, text=self.message_text)
        self.bot.send_message(message.chat.id, "Хочешь, чтобы я опубликовал это сообщение в канале?", reply_markup=markup)

    def handle_query(self, call):
        if call.data == 'yes':
            self.bot.send_message(chat_id=self.target_channel_id, text=self.message_text)
            self.bot.send_message(call.message.chat.id, '✅Готово! Сообщение опубликовано в канале Рецепты 🥘🍝🍲')
            self.bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        elif call.data == 'no':
            self.bot.send_message(call.message.chat.id, 'Хорошо. Если передумаешь, нажми на "Да".')

    def start(self):
        self.bot.polling()

if __name__ == "__main__":
    API_TOKEN = "token"
    TARGET_CHANNEL_ID = -1 # channel where bot posts the messages
    USERS = {11111111111, # first allowed user id
             22222222222} # second allowed user id
    telegram_bot = FoodParserBotApp(API_TOKEN, TARGET_CHANNEL_ID, USERS)
    telegram_bot.start()

