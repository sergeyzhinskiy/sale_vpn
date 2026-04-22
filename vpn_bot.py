import asyncio
import random
import string
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
import configparser
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

#считываем учетные данные
#config=configparser.ConfigParser()
#config.read("config.ini")
config = configparser.ConfigParser()
with open('config.ini') as fh:
    config.read_file(fh)
# or:
config.read('config.ini')
# Bot settings
API_ID = config['Telegram']['API_ID']
API_HASH = config['Telegram']['api_hash']
BOT_TOKEN = config['Telegram']['BOT_TOKEN']
ADMIN_IDS = [int(id) for id in config['Telegram']['admin_ids'].split(',')]
PRICES = {
    '1week': 100,  # in rubles or other currency
    '1month': 300,
    '3months': 800,
}
VPN_SERVERS = {
    'EU': 'europe.example.com',
    'US': 'usa.example.com',
    'ASIA': 'asia.example.com',
}

# In-memory "database" (replace with real DB in production)
users_db = {}
keys_db = {}
payments_db = {}

# Initialize Telegram client
client = TelegramClient('vpn_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def generate_vpn_key(server, duration):
    """Generate a random VPN key (simulate)"""
    prefix = {
        'EU': 'EU',
        'US': 'US',
        'ASIA': 'AS'
    }.get(server, 'GL')
    
    key = f"{prefix}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}"
    expiry_date = datetime.now() + timedelta(days=duration)
    return key, expiry_date

async def send_key_to_user(user_id, key_info):
    """Send VPN key to user"""
    server, key, expiry = key_info
    message = (
        "✅ Ваш VPN ключ активирован!\n\n"
        f"🌍 Сервер: {server}\n"
        f"🔑 Ключ: `{key}`\n"
        f"📅 Срок действия: {expiry.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Адрес сервера: {VPN_SERVERS[server]}\n\n"
        "Инструкция по настройке:\n"
        "1. Скачайте приложение OpenVPN\n"
        "2. Добавьте новый профиль\n"
        "3. Введите данные сервера и ключ\n"
        "4. Подключитесь и пользуйтесь!"
    )
    
    try:
        await client.send_message(user_id, message, parse_mode='md')
        return True
    except Exception as e:
        logger.error(f"Failed to send key to user {user_id}: {e}")
        return False

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle /start command"""
    user_id = event.sender_id
    if user_id not in users_db:
        users_db[user_id] = {
            'registered': datetime.now(),
            'purchases': 0,
            'balance': 0
        }
    
    buttons = [
        [Button.inline("🛒 Купить VPN", b"buy_vpn")],
        [Button.inline("ℹ️ Информация", b"info")],
        [Button.inline("📞 Поддержка", b"support")]
    ]
    
    if user_id in ADMIN_IDS:
        buttons.append([Button.inline("👑 Админ панель", b"admin_panel")])
    
    await event.respond(
        "🔒 Добро пожаловать в VPN сервис!\n\n"
        "Здесь вы можете приобрести доступ к быстрым и безопасным VPN серверам по всему миру.",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b"buy_vpn"))
async def buy_vpn_handler(event):
    """Handle VPN purchase menu"""
    buttons = [
        [Button.inline("🇪🇺 Европа", b"server_EU")],
        [Button.inline("🇺🇸 США", b"server_US")],
        [Button.inline("🇨🇳 Азия", b"server_ASIA")],
        [Button.inline("🔙 Назад", b"main_menu")]
    ]
    await event.edit(
        "🌍 Выберите регион VPN сервера:",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b"info"))
async def info_handler(event):
    """Show info about service"""
    await event.edit(
        "ℹ️ Информация о VPN сервисе:\n\n"
        "🔒 Безопасность: 256-bit шифрование\n"
        "🚀 Скорость: до 1 Гбит/с\n"
        "🌍 Сервера в 15+ странах\n"
        "📱 Поддержка всех устройств\n\n"
        "Наши преимущества:\n"
        "- Без логов\n"
        "- Поддержка 24/7\n"
        "- Быстрая настройка",
        buttons=[[Button.inline("🔙 Назад", b"main_menu")]]
    )

@client.on(events.CallbackQuery(data=b"support"))
async def support_handler(event):
    """Show support info"""
    await event.edit(
        "📞 Поддержка\n\n"
        "По всем вопросам обращайтесь к @vpn_support\n"
        "или на email: support@vpnservice.example\n\n"
        "Мы онлайн 24/7!",
        buttons=[[Button.inline("🔙 Назад", b"main_menu")]]
    )

@client.on(events.CallbackQuery(data=b"main_menu"))
async def main_menu_handler(event):
    """Return to main menu"""
    await start_handler(event)

@client.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel_handler(event):
    """Show admin panel"""
    if event.sender_id not in ADMIN_IDS:
        await event.answer("Доступ запрещен!")
        return
    
    total_users = len(users_db)
    active_keys = sum(1 for k in keys_db.values() if k['expiry'] > datetime.now())
    total_sales = sum(u['purchases'] for u in users_db.values())
    
    buttons = [
        [Button.inline("📊 Статистика", b"admin_stats")],
        [Button.inline("🔑 Сгенерировать ключи", b"admin_gen_keys")],
        [Button.inline("📩 Рассылка", b"admin_broadcast")],
        [Button.inline("🔙 Назад", b"main_menu")]
    ]
    
    await event.edit(
        f"👑 Админ панель\n\n"
        f"👥 Пользователей: {total_users}\n"
        f"🔑 Активных ключей: {active_keys}\n"
        f"💰 Всего продаж: {total_sales}",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b"admin_stats"))
async def admin_stats_handler(event):
    """Show detailed stats"""
    if event.sender_id not in ADMIN_IDS:
        await event.answer("Доступ запрещен!")
        return
    
    today = datetime.now().date()
    new_today = sum(1 for u in users_db.values() if u['registered'].date() == today)
    sales_today = sum(1 for p in payments_db.values() if p['date'].date() == today)
    
    await event.edit(
        f"📊 Детальная статистика\n\n"
        f"👥 Новых сегодня: {new_today}\n"
        f"💰 Продаж сегодня: {sales_today}\n"
        f"💳 Общий доход: {sum(p['amount'] for p in payments_db.values())} руб.",
        buttons=[[Button.inline("🔙 В админку", b"admin_panel")]]
    )

@client.on(events.CallbackQuery())
async def callback_handler(event):
    """Handle all other callbacks"""
    data = event.data.decode('utf-8')
    
    if data.startswith("server_"):
        server = data.split("_")[1]
        buttons = [
            [Button.inline("1 неделя - 100 руб.", f"duration_{server}_7")],
            [Button.inline("1 месяц - 300 руб.", f"duration_{server}_30")],
            [Button.inline("3 месяца - 800 руб.", f"duration_{server}_90")],
            [Button.inline("🔙 Назад", b"buy_vpn")]
        ]
        await event.edit(
            f"Вы выбрали сервер: {server}\n\n"
            "Выберите срок действия:",
            buttons=buttons
        )
    
    elif data.startswith("duration_"):
        _, server, days = data.split("_")
        days = int(days)
        
        # Generate payment ID
        payment_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        payments_db[payment_id] = {
            'user_id': event.sender_id,
            'server': server,
            'duration': days,
            'amount': PRICES[f"{days//7}week"] if days != 90 else PRICES["3months"],
            'date': datetime.now(),
            'completed': False
        }
        
        buttons = [
            [Button.url("💳 Оплатить", f"https://example.com/pay/{payment_id}")],
            [Button.inline("✅ Я оплатил", f"check_payment_{payment_id}")],
            [Button.inline("🔙 Назад", f"server_{server}")]
        ]
        
        await event.edit(
            f"💳 Оплата доступа к VPN\n\n"
            f"🌍 Сервер: {server}\n"
            f"⏳ Срок: {days} дней\n"
            f"💰 Сумма: {payments_db[payment_id]['amount']} руб.\n\n"
            "После оплаты нажмите кнопку 'Я оплатил'",
            buttons=buttons
        )
    
    elif data.startswith("check_payment_"):
        payment_id = data.split("_")[2]
        payment = payments_db.get(payment_id)
        
        if not payment:
            await event.answer("Платеж не найден!", alert=True)
            return
        
        if payment['completed']:
            await event.answer("Этот платеж уже обработан!", alert=True)
            return
        
        # In a real bot, you would check payment status with your payment provider
        # Here we'll simulate successful payment 80% of the time
        if random.random() < 0.8:
            payment['completed'] = True
            key, expiry = generate_vpn_key(payment['server'], payment['duration'])
            
            keys_db[key] = {
                'user_id': payment['user_id'],
                'server': payment['server'],
                'expiry': expiry,
                'generated': datetime.now()
            }
            
            users_db[payment['user_id']]['purchases'] += 1
            
            await send_key_to_user(payment['user_id'], 
                                 (payment['server'], key, expiry))
            await event.answer("✅ Платеж подтвержден! Ключ отправлен вам в личные сообщения.", alert=True)
            await event.delete()
        else:
            await event.answer("❌ Платеж еще не поступил. Попробуйте позже.", alert=True)

async def main():
    """Main function"""
    logger.info("Starting VPN Bot...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    # Create config.ini if not exists
    try:
        with open('config.ini', 'x') as f:
            f.write("""[Telegram]
api_id = YOUR_API_ID
api_hash = YOUR_API_HASH
bot_token = YOUR_BOT_TOKEN
admin_ids = YOUR_USER_ID
""")
        print("Created config.ini. Please fill it with your credentials.")
        exit()
    except FileExistsError:
        pass
    
    client.loop.run_until_complete(main())