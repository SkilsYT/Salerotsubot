
import asyncio
import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command

API_TOKEN = "7505755437:AAEDECktNxLBMepXHqUZ2iqkTnuY6jKvdKw"
ADMIN_ID = 789110539  # твой Telegram ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Простая in-memory база
users = {}
rewards = {
    "Футболка": 1500,
    "Кепка": 1000,
}

def generate_promo():
    return str(uuid.uuid4())[:8]

# --- Команды пользователя ---

@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users:
        promo = generate_promo()
        users[user_id] = {"promo": promo, "bonus": 0, "referrals": []}
        await message.answer(f"Привет! Твой промокод: {promo}")
    else:
        await message.answer(f"Ты уже зарегистрирован. Твой промокод: {users[user_id]['promo']}")

@dp.message(Command("баланс"))
async def balance(message: types.Message):
    user_id = message.from_user.id
    bonus = users.get(user_id, {}).get("bonus", 0)
    await message.answer(f"У тебя {bonus} бонусов.")

@dp.message(Command("заказ"))
async def order(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Пример: /заказ 3500 [промокод (необязательно)]")
        return

    user_id = message.from_user.id
    try:
        amount = int(args[1])
    except ValueError:
        await message.answer("Сумма должна быть числом.")
        return

    bonus = 0
    if amount >= 5000:
        bonus = 200
    elif amount >= 3000:
        bonus = 150

    users[user_id]["bonus"] += bonus
    await message.answer(f"Заказ на {amount} принят. Тебе начислено {bonus} бонусов.")

    if len(args) == 3:
        ref_promo = args[2]
        for uid, data in users.items():
            if data["promo"] == ref_promo and uid != user_id:
                data["bonus"] += 100
                data["referrals"].append(user_id)
                await bot.send_message(uid, f"Твой промокод использован! +100 бонусов.")

@dp.message(Command("обмен"))
async def redeem(message: types.Message):
    user_id = message.from_user.id
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for item in rewards:
        markup.add(KeyboardButton(item))
    await message.answer("Выбери вещь для обмена:", reply_markup=markup)

@dp.message()
async def handle_item(message: types.Message):
    user_id = message.from_user.id
    item = message.text
    if item in rewards:
        cost = rewards[item]
        if users[user_id]["bonus"] >= cost:
            users[user_id]["bonus"] -= cost
            await message.answer(f"Ты обменял бонусы на «{item}». Мы скоро свяжемся с тобой!")
        else:
            await message.answer(f"Недостаточно бонусов. Нужно {cost}, у тебя {users[user_id]['bonus']}.")

# --- Админ-панель ---

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У тебя нет доступа.")
        return

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="Товары", callback_data="admin_items")],
        [InlineKeyboardButton(text="Рассылка", callback_data="admin_broadcast")]
    ])
    await message.answer("Админ-панель:", reply_markup=markup)

@dp.callback_query(lambda c: c.data.startswith("admin_"))
async def handle_admin_callbacks(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    if callback.data == "admin_users":
        text = "Пользователи:
"
        for uid, data in users.items():
            text += f"ID: {uid} | Бонусов: {data['bonus']} | Рефералы: {len(data['referrals'])}
"
        await callback.message.answer(text or "Нет данных.")

    elif callback.data == "admin_items":
        text = "Товары:
"
        for item, cost in rewards.items():
            text += f"{item}: {cost} бонусов
"
        await callback.message.answer(text)

    elif callback.data == "admin_broadcast":
        await callback.message.answer("Введи текст рассылки:")
        dp.message.register(waiting_broadcast)

async def waiting_broadcast(message: types.Message):
    for uid in users:
        try:
            await bot.send_message(uid, f"Сообщение от администрации:

{message.text}")
        except:
            pass
    await message.answer("Рассылка завершена.")
    dp.message.unregister(waiting_broadcast)

# --- Запуск ---

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
