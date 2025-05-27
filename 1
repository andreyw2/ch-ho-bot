import telebot
from telebot import types
from flask import Flask, request
import json
import os

# Токен из переменной окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Flask-приложение
app = Flask(__name__)

# Загрузка товаров
with open('catalog.json', encoding='utf-8') as f:
    catalog = json.load(f)

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    for category in catalog:
        markup.add(types.InlineKeyboardButton(category, callback_data=f"category_{category}"))
    bot.send_message(message.chat.id, "Выберите категорию аромата:", reply_markup=markup)

# Обработка нажатий
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("category_"):
        category = call.data.replace("category_", "")
        products = catalog[category]
        markup = types.InlineKeyboardMarkup()
        for product in products:
            markup.add(types.InlineKeyboardButton(product['name'], callback_data=f"product_{product['name']}"))
        bot.send_message(call.message.chat.id, f"Ароматы в категории {category}:", reply_markup=markup)

    elif call.data.startswith("product_"):
        name = call.data.replace("product_", "")
        for products in catalog.values():
            for product in products:
                if product['name'] == name:
                    description = f"**{product['name']}**\nЦена: {product['price']}₽\nНапиши, если хочешь заказать!"
                    bot.send_message(call.message.chat.id, description, parse_mode="Markdown")
                    return

# Webhook endpoint
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return 'ok', 200

# Для Render.com — запуск Flask-приложения
@app.route('/')
def index():
    return "Бот работает"

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f'https://{os.environ.get("RENDER_EXTERNAL_HOSTNAME")}/{BOT_TOKEN}')
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
