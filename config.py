import os

# Telegram Bot Token
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token_here")

# Пути к JSON-файлам (каталог ароматов и заказы)
CATALOG_FILE = "catalog.json"
ORDERS_FILE = "orders.json"

# Настройки сервера (для Render.com)
PORT = int(os.environ.get("PORT", 5000))
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
WEBHOOK_URL = f"https://{RENDER_EXTERNAL_HOSTNAME}/{BOT_TOKEN}" if RENDER_EXTERNAL_HOSTNAME else None
