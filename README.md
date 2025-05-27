import telebot
import json
import os
from datetime import datetime
from config import BOT_TOKEN, ADMIN_ID
from telebot import types

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для хранения состояний пользователей
user_states = {}
user_data = {}

# Состояния для FSM
class States:
    MAIN_MENU = "main_menu"
    CATALOG = "catalog"
    FRAGRANCE_DETAILS = "fragrance_details"
    QUESTIONNAIRE_STYLE = "questionnaire_style"
    QUESTIONNAIRE_OCCASION = "questionnaire_occasion"
    QUESTIONNAIRE_RECIPIENT = "questionnaire_recipient"
    ORDER_NAME = "order_name"
    ORDER_CITY = "order_city"
    ORDER_PHONE = "order_phone"
    ORDER_DELIVERY = "order_delivery"

def load_catalog():
    """Загрузка каталога из JSON файла"""
    try:
        with open('catalog.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_order(order_data):
    """Сохранение заказа в JSON файл"""
    try:
        with open('orders.json', 'r', encoding='utf-8') as f:
            orders = json.load(f)
    except FileNotFoundError:
        orders = []
    
    order_data['timestamp'] = datetime.now().isoformat()
    orders.append(order_data)
    
    with open('orders.json', 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def get_user_cart(user_id):
    """Получить корзину пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {'cart': []}
    return user_data[user_id]['cart']

def add_to_cart(user_id, item):
    """Добавить товар в корзину"""
    cart = get_user_cart(user_id)
    cart.append(item)

def get_fragrance_recommendations(questionnaire):
    """Подбор ароматов на основе анкеты"""
    catalog = load_catalog()
    style = questionnaire['style']
    occasion = questionnaire['occasion']
    recipient = questionnaire['recipient']
    
    # Определяем пол для фильтрации
    gender_filter = None
    if recipient == 'boyfriend':
        gender_filter = ['male', 'unisex']
    elif recipient == 'girlfriend':
        gender_filter = ['female', 'unisex']
    else:  # self
        gender_filter = ['unisex']
    
    # Фильтруем ароматы по критериям
    recommendations = []
    for fragrance in catalog:
        # Проверяем соответствие стилю
        if fragrance.get('style') == style:
            # Проверяем соответствие случаю
            if fragrance.get('occasion') == occasion or fragrance.get('occasion') == 'daily':
                # Проверяем соответствие полу
                if fragrance.get('gender') in gender_filter:
                    recommendations.append(fragrance)
    
    # Если строгих совпадений мало, добавляем похожие
    if len(recommendations) < 3:
        for fragrance in catalog:
            if fragrance not in recommendations:
                if fragrance.get('style') == style and fragrance.get('gender') in gender_filter:
                    recommendations.append(fragrance)
                if len(recommendations) >= 5:
                    break
    
    # Возвращаем топ-3 рекомендации
    return recommendations[:3]

def create_main_menu_keyboard():
    """Создание главного меню"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🌸 Каталог ароматов", callback_data="catalog"),
        types.InlineKeyboardButton("🧪 Подбор аромата", callback_data="questionnaire"),
        types.InlineKeyboardButton("🛒 Оформить заказ", callback_data="order")
    )
    return markup

def create_catalog_keyboard():
    """Создание клавиатуры каталога с категориями"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Создаем категории по брендам
    markup.add(
        types.InlineKeyboardButton("🏆 Премиум бренды", callback_data="category_premium"),
        types.InlineKeyboardButton("💎 Селективная парфюмерия", callback_data="category_selective")
    )
    markup.add(
        types.InlineKeyboardButton("🌸 Популярные ароматы", callback_data="category_popular"),
        types.InlineKeyboardButton("🎯 По стилю", callback_data="category_style")
    )
    markup.add(
        types.InlineKeyboardButton("📋 Все ароматы", callback_data="category_all"),
        types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="main_menu")
    )
    
    return markup

def create_category_keyboard(category):
    """Создание клавиатуры для конкретной категории"""
    catalog = load_catalog()
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if category == "premium":
        # Премиум бренды: Tom Ford, Creed, MFK
        brands = ["Tom Ford", "Creed", "MFK"]
        fragrances = [f for f in catalog if f['brand'] in brands]
    elif category == "selective":
        # Селективная парфюмерия: Initio, By Kilian, Parfums de Marly
        brands = ["Initio", "By Kilian", "Parfums de Marly"]
        fragrances = [f for f in catalog if f['brand'] in brands]
    elif category == "popular":
        # Популярные: Byredo, YSL, Chanel, Dior
        brands = ["Byredo", "YSL", "Chanel", "Dior", "Giorgio Armani"]
        fragrances = [f for f in catalog if f['brand'] in brands]
    elif category == "style":
        # По стилю - создаем подменю стилей
        markup.add(
            types.InlineKeyboardButton("🌿 Свежие ароматы", callback_data="style_fresh"),
            types.InlineKeyboardButton("🌳 Древесные ароматы", callback_data="style_woody"),
            types.InlineKeyboardButton("🌸 Восточные ароматы", callback_data="style_oriental"),
            types.InlineKeyboardButton("🍰 Гурманские ароматы", callback_data="style_gourmand")
        )
        markup.add(types.InlineKeyboardButton("⬅️ Назад к каталогу", callback_data="catalog"))
        return markup
    else:  # category == "all"
        fragrances = catalog
    
    # Добавляем ароматы выбранной категории
    for fragrance in fragrances:
        button_text = f"{fragrance['brand']} | {fragrance['name']}"
        callback_data = f"fragrance_{catalog.index(fragrance)}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
    markup.add(types.InlineKeyboardButton("⬅️ Назад к каталогу", callback_data="catalog"))
    return markup

def create_style_keyboard(style):
    """Создание клавиатуры для ароматов по стилю"""
    catalog = load_catalog()
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Фильтруем ароматы по стилю
    fragrances = [f for f in catalog if f.get('style') == style]
    
    for fragrance in fragrances:
        button_text = f"{fragrance['brand']} | {fragrance['name']}"
        callback_data = f"fragrance_{catalog.index(fragrance)}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
    markup.add(types.InlineKeyboardButton("⬅️ Назад к стилям", callback_data="category_style"))
    return markup

def create_volume_keyboard(fragrance_index):
    """Создание клавиатуры выбора объема"""
    catalog = load_catalog()
    fragrance = catalog[fragrance_index]
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    volume_buttons = []
    for volume, price in fragrance['prices'].items():
        button_text = f"{volume} мл"
        callback_data = f"volume_{fragrance_index}_{volume}"
        volume_buttons.append(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
    # Добавляем кнопки по 2 в ряд
    for i in range(0, len(volume_buttons), 2):
        if i + 1 < len(volume_buttons):
            markup.add(volume_buttons[i], volume_buttons[i + 1])
        else:
            markup.add(volume_buttons[i])
    
    markup.add(types.InlineKeyboardButton("⬅️ Назад к каталогу", callback_data="catalog"))
    return markup

def create_questionnaire_style_keyboard():
    """Создание клавиатуры выбора стиля"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🌿 Свежий", callback_data="style_fresh"),
        types.InlineKeyboardButton("🌳 Древесный", callback_data="style_woody"),
        types.InlineKeyboardButton("🌸 Восточный", callback_data="style_oriental"),
        types.InlineKeyboardButton("🍰 Гурманский", callback_data="style_gourmand")
    )
    markup.add(types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="main_menu"))
    return markup

def create_questionnaire_occasion_keyboard():
    """Создание клавиатуры выбора случая"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("☀️ На каждый день", callback_data="occasion_daily"),
        types.InlineKeyboardButton("💕 Для свидания", callback_data="occasion_date"),
        types.InlineKeyboardButton("💼 Для офиса", callback_data="occasion_office"),
        types.InlineKeyboardButton("🎁 В подарок", callback_data="occasion_gift")
    )
    return markup

def create_questionnaire_recipient_keyboard():
    """Создание клавиатуры выбора получателя"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👤 Себе", callback_data="recipient_self"),
        types.InlineKeyboardButton("👨 Парню", callback_data="recipient_boyfriend"),
        types.InlineKeyboardButton("👩 Девушке", callback_data="recipient_girlfriend")
    )
    return markup

def create_delivery_keyboard():
    """Создание клавиатуры выбора доставки"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📦 СДЭК", callback_data="delivery_cdek"),
        types.InlineKeyboardButton("📮 Почта России", callback_data="delivery_post"),
        types.InlineKeyboardButton("📋 Boxberry", callback_data="delivery_boxberry")
    )
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик команды /start"""
    user_states[message.from_user.id] = States.MAIN_MENU
    
    welcome_text = """🌸 Добро пожаловать в Ch & Ho — Original Fragrances!

Выберите действие:"""
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=create_main_menu_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Обработчик всех callback запросов"""
    user_id = call.from_user.id
    data = call.data
    
    try:
        if data == "main_menu":
            handle_main_menu(call)
        elif data == "catalog":
            handle_catalog(call)
        elif data.startswith("category_"):
            handle_category_selection(call)
        elif data.startswith("style_") and not data.startswith("style_fresh") and not data.startswith("style_woody") and not data.startswith("style_oriental") and not data.startswith("style_gourmand"):
            handle_style_selection(call)
        elif data in ["style_fresh", "style_woody", "style_oriental", "style_gourmand"]:
            handle_style_fragrance_list(call)
        elif data.startswith("fragrance_"):
            handle_fragrance_details(call)
        elif data.startswith("volume_"):
            handle_volume_selection(call)
        elif data == "questionnaire":
            handle_questionnaire_start(call)
        elif data.startswith("style_"):
            handle_style_selection(call)
        elif data.startswith("occasion_"):
            handle_occasion_selection(call)
        elif data.startswith("recipient_"):
            handle_recipient_selection(call)
        elif data == "order":
            handle_order_start(call)
        elif data.startswith("delivery_"):
            handle_delivery_selection(call)
        
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.answer_callback_query(call.id, "Произошла ошибка. Попробуйте еще раз.")
        print(f"Error in callback_handler: {e}")

def handle_main_menu(call):
    """Обработка главного меню"""
    user_states[call.from_user.id] = States.MAIN_MENU
    
    welcome_text = """🌸 Добро пожаловать в Ch & Ho — Original Fragrances!

Выберите действие:"""
    
    bot.edit_message_text(
        welcome_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_main_menu_keyboard()
    )

def handle_catalog(call):
    """Обработка каталога"""
    user_states[call.from_user.id] = States.CATALOG
    
    catalog_text = "🌸 Каталог ароматов\n\nВыберите категорию:"
    
    bot.edit_message_text(
        catalog_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_catalog_keyboard()
    )

def handle_category_selection(call):
    """Обработка выбора категории"""
    category = call.data.split("_")[1]
    
    category_names = {
        "premium": "🏆 Премиум бренды",
        "selective": "💎 Селективная парфюмерия", 
        "popular": "🌸 Популярные ароматы",
        "style": "🎯 По стилю",
        "all": "📋 Все ароматы"
    }
    
    text = f"{category_names.get(category, 'Ароматы')}\n\n"
    
    if category == "style":
        text += "Выберите стиль аромата:"
    else:
        text += "Выберите аромат:"
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_category_keyboard(category)
    )

def handle_style_fragrance_list(call):
    """Обработка списка ароматов по стилю"""
    style = call.data.split("_")[1]
    
    style_names = {
        "fresh": "🌿 Свежие ароматы",
        "woody": "🌳 Древесные ароматы",
        "oriental": "🌸 Восточные ароматы",
        "gourmand": "🍰 Гурманские ароматы"
    }
    
    text = f"{style_names.get(style, 'Ароматы')}\n\nВыберите аромат:"
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_style_keyboard(style)
    )

def handle_fragrance_details(call):
    """Обработка деталей аромата"""
    fragrance_index = int(call.data.split("_")[1])
    catalog = load_catalog()
    fragrance = catalog[fragrance_index]
    
    user_states[call.from_user.id] = States.FRAGRANCE_DETAILS
    
    details_text = f"🌸 {fragrance['brand']} — {fragrance['name']}\n\n"
    
    for volume, price in fragrance['prices'].items():
        details_text += f"{volume} мл — {price}₽\n"
    
    details_text += "\nВыберите объём:"
    
    bot.edit_message_text(
        details_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_volume_keyboard(fragrance_index)
    )

def handle_volume_selection(call):
    """Обработка выбора объема"""
    parts = call.data.split("_")
    fragrance_index = int(parts[1])
    volume = parts[2]
    
    catalog = load_catalog()
    fragrance = catalog[fragrance_index]
    price = fragrance['prices'][volume]
    
    # Добавляем в корзину
    item = {
        'brand': fragrance['brand'],
        'name': fragrance['name'],
        'volume': volume,
        'price': price
    }
    add_to_cart(call.from_user.id, item)
    
    success_text = f"✅ Добавлено в заказ: {fragrance['brand']} — {fragrance['name']} ({volume} мл)\n\nЦена: {price}₽"
    
    # Возвращаемся к каталогу
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🛒 Продолжить покупки", callback_data="catalog"),
        types.InlineKeyboardButton("📝 Оформить заказ", callback_data="order"),
        types.InlineKeyboardButton("⬅️ Главное меню", callback_data="main_menu")
    )
    
    bot.edit_message_text(
        success_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

def handle_questionnaire_start(call):
    """Начало анкеты подбора аромата"""
    user_states[call.from_user.id] = States.QUESTIONNAIRE_STYLE
    
    if call.from_user.id not in user_data:
        user_data[call.from_user.id] = {}
    user_data[call.from_user.id]['questionnaire'] = {}
    
    question_text = "🧪 Подбор аромата\n\nКакой стиль вам ближе?"
    
    bot.edit_message_text(
        question_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_questionnaire_style_keyboard()
    )

def handle_style_selection(call):
    """Обработка выбора стиля"""
    style = call.data.split("_")[1]
    user_data[call.from_user.id]['questionnaire']['style'] = style
    user_states[call.from_user.id] = States.QUESTIONNAIRE_OCCASION
    
    question_text = "Для какого случая аромат?"
    
    bot.edit_message_text(
        question_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_questionnaire_occasion_keyboard()
    )

def handle_occasion_selection(call):
    """Обработка выбора случая"""
    occasion = call.data.split("_")[1]
    user_data[call.from_user.id]['questionnaire']['occasion'] = occasion
    user_states[call.from_user.id] = States.QUESTIONNAIRE_RECIPIENT
    
    question_text = "Для кого подбираете?"
    
    bot.edit_message_text(
        question_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_questionnaire_recipient_keyboard()
    )

def handle_recipient_selection(call):
    """Обработка выбора получателя"""
    recipient = call.data.split("_")[1]
    user_data[call.from_user.id]['questionnaire']['recipient'] = recipient
    
    # Подбираем ароматы на основе анкеты
    recommendations = get_fragrance_recommendations(user_data[call.from_user.id]['questionnaire'])
    
    # Сохраняем результаты анкеты
    questionnaire_data = {
        'user_id': call.from_user.id,
        'username': call.from_user.username,
        'questionnaire': user_data[call.from_user.id]['questionnaire'],
        'recommendations': recommendations,
        'timestamp': datetime.now().isoformat()
    }
    
    # Сохраняем в файл анкет
    try:
        with open('questionnaires.json', 'r', encoding='utf-8') as f:
            questionnaires = json.load(f)
    except FileNotFoundError:
        questionnaires = []
    
    questionnaires.append(questionnaire_data)
    
    with open('questionnaires.json', 'w', encoding='utf-8') as f:
        json.dump(questionnaires, f, ensure_ascii=False, indent=2)
    
    # Отправляем уведомление администратору
    if ADMIN_ID:
        admin_text = f"📋 Новая анкета подбора аромата:\n\n"
        admin_text += f"Пользователь: @{call.from_user.username or call.from_user.first_name}\n"
        admin_text += f"Стиль: {questionnaire_data['questionnaire']['style']}\n"
        admin_text += f"Случай: {questionnaire_data['questionnaire']['occasion']}\n"
        admin_text += f"Получатель: {questionnaire_data['questionnaire']['recipient']}\n\n"
        admin_text += "Рекомендации:\n"
        for rec in recommendations:
            admin_text += f"• {rec['brand']} — {rec['name']}\n"
        
        try:
            bot.send_message(ADMIN_ID, admin_text)
        except:
            pass
    
    # Формируем текст с рекомендациями
    result_text = "✅ Отлично! На основе ваших ответов мы подобрали эти ароматы:\n\n"
    
    for i, rec in enumerate(recommendations, 1):
        result_text += f"{i}. {rec['brand']} — {rec['name']}\n"
        result_text += f"   Цены: 10мл — {rec['prices']['10']}₽, 15мл — {rec['prices']['15']}₽\n\n"
    
    result_text += "Хотите заказать один из них или вернуться в каталог?"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🌸 Каталог ароматов", callback_data="catalog"),
        types.InlineKeyboardButton("⬅️ Главное меню", callback_data="main_menu")
    )
    
    bot.edit_message_text(
        result_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

def handle_order_start(call):
    """Начало оформления заказа"""
    cart = get_user_cart(call.from_user.id)
    
    if not cart:
        no_items_text = "🛒 Ваша корзина пуста!\n\nДобавьте ароматы из каталога перед оформлением заказа."
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🌸 Каталог ароматов", callback_data="catalog"),
            types.InlineKeyboardButton("⬅️ Главное меню", callback_data="main_menu")
        )
        bot.edit_message_text(
            no_items_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        return
    
    user_states[call.from_user.id] = States.ORDER_NAME
    
    # Показываем содержимое корзины
    order_text = "🛒 Оформление заказа\n\nВаш заказ:\n"
    total = 0
    
    for item in cart:
        order_text += f"• {item['brand']} — {item['name']} ({item['volume']} мл) — {item['price']}₽\n"
        total += item['price']
    
    order_text += f"\nИтого: {total}₽\n\n"
    order_text += "Для оформления заказа введите ваше имя:"
    
    bot.edit_message_text(order_text, call.message.chat.id, call.message.message_id)

def handle_delivery_selection(call):
    """Обработка выбора доставки"""
    delivery = call.data.split("_")[1]
    user_data[call.from_user.id]['order']['delivery'] = delivery
    
    # Формируем финальный заказ
    order_data = user_data[call.from_user.id]['order']
    cart = get_user_cart(call.from_user.id)
    
    order_data['items'] = cart
    order_data['user_id'] = call.from_user.id
    order_data['username'] = call.from_user.username
    
    # Сохраняем заказ
    save_order(order_data)
    
    # Очищаем корзину
    if call.from_user.id in user_data:
        user_data[call.from_user.id]['cart'] = []
    
    # Отправляем уведомление администратору
    if ADMIN_ID:
        total = sum(item['price'] for item in cart)
        admin_text = f"🛒 Новый заказ!\n\n"
        admin_text += f"Клиент: {order_data['name']}\n"
        admin_text += f"Телефон: {order_data['phone']}\n"
        admin_text += f"Город: {order_data['city']}\n"
        admin_text += f"Доставка: {delivery}\n\n"
        admin_text += "Товары:\n"
        
        for item in cart:
            admin_text += f"• {item['brand']} — {item['name']} ({item['volume']} мл) — {item['price']}₽\n"
        
        admin_text += f"\nИтого: {total}₽"
        
        try:
            bot.send_message(ADMIN_ID, admin_text)
        except:
            pass
    
    success_text = "✅ Заказ оформлен! Мы свяжемся с вами для подтверждения."
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Главное меню", callback_data="main_menu"))
    
    bot.edit_message_text(
        success_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    """Обработчик текстовых сообщений"""
    user_id = message.from_user.id
    state = user_states.get(user_id)
    
    if state == States.ORDER_NAME:
        # Сохраняем имя
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['order'] = {'name': message.text}
        user_states[user_id] = States.ORDER_CITY
        
        bot.send_message(message.chat.id, "Введите ваш город:")
        
    elif state == States.ORDER_CITY:
        # Сохраняем город
        user_data[user_id]['order']['city'] = message.text
        user_states[user_id] = States.ORDER_PHONE
        
        bot.send_message(message.chat.id, "Введите ваш номер телефона:")
        
    elif state == States.ORDER_PHONE:
        # Сохраняем телефон
        user_data[user_id]['order']['phone'] = message.text
        user_states[user_id] = States.ORDER_DELIVERY
        
        bot.send_message(
            message.chat.id,
            "Выберите способ доставки:",
            reply_markup=create_delivery_keyboard()
        )
    else:
        # Неизвестная команда
        bot.send_message(
            message.chat.id,
            "Используйте кнопки для навигации или введите /start для возврата в главное меню."
        )

if __name__ == "__main__":
    print("Запуск бота Ch & Ho...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")