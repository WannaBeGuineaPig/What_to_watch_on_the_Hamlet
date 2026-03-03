import asyncio
import os
import random
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен из переменных окружения
TOKEN = os.getenv('BOT_TOKEN')

# Проверяем, что токен загружен
if not TOKEN:
    raise ValueError("Токен не найден! Создай файл .env с BOT_TOKEN=твой_токен")

# Создаем экземпляры бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# База фактов о кино
MOVIE_FACTS = [
    "🎬 Самый первый фильм в истории кино длился всего 2 секунды и назывался «Прибытие поезда»",
    "🍿 За время просмотра всех фильмов вселенной Marvel вы потратите более 50 часов",
    "🎭 Самый титулованный актер всех времен — Кэтрин Хепберн, получившая 4 «Оскара»",
    "📽️ Самый дорогой фильм в истории — «Пираты Карибского моря: На странных берегах» (378 млн $)",
    "🎪 Самый кассовый фильм в истории — «Аватар» (2.8 миллиарда долларов)",
    "🎨 Первый цветной фильм — «Бекки Шарп» вышел в 1935 году",
    "🎬 Самый длинный фильм в мире длится 87 часов и называется «Список фильма»",
    "🍿 В среднем человек проводит около 3 месяцев жизни за просмотром фильмов",
    "🎭 Самый молодой обладатель «Оскара» — Татум О’Нил (10 лет)",
    "📽️ Самый короткий фильм в истории длится всего 1 секунду",
    "🎪 Фильм «Титаник» держал рекорд по кассовым сборам 12 лет",
    "🎨 В фильме «Безумный Макс: Дорога ярости» было использовано 1500 настоящих трюков",
    "🎬 Самый прибыльный фильм — «Ведьма из Блэр» (снят за 60 000$, собрал 248 млн $)",
    "🍿 Более 80% фильмов, выходящих в прокат, не окупаются в кинотеатрах",
    "🎭 Актеры озвучки «Симпсонов» зарабатывают по 300 000$ за серию",
]

# Функция для получения случайного факта
def get_random_movie_fact():
    return random.choice(MOVIE_FACTS)

# Определяем состояния для FSM (Finite State Machine)
class UserState(StatesGroup):
    waiting_for_gender = State()
    waiting_for_movie = State()

# Главное меню
def get_main_menu_keyboard():
    buttons = [
        [KeyboardButton(text="🎬 Найти фильм")],
        [KeyboardButton(text="🎲 Случайный факт"), KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="🚪 Выход")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard

# Клавиатура для выбора пола
def get_gender_keyboard():
    buttons = [
        [KeyboardButton(text="Я парень 👨")],
        [KeyboardButton(text="Я девушка 👩")],
        [KeyboardButton(text="🔙 Назад в меню")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard

# Клавиатура во время поиска фильмов
def get_movie_search_keyboard():
    buttons = [
        [KeyboardButton(text="🎬 Новый поиск")],
        [KeyboardButton(text="🎲 Ещё факт"), KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="🚪 Выход")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard

# Клавиатура после выхода
def get_exit_keyboard():
    buttons = [
        [KeyboardButton(text="✨ Начать общение")],
        [KeyboardButton(text="🎲 Случайный факт"), KeyboardButton(text="❓ Помощь")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🌟 Добро пожаловать в КиноBот!\n\n"
        "Я помогу тебе найти лучшие фильмы и сериалы, а также расскажу интересные факты о кино!\n"
        "Выбери действие в меню ниже:",
        reply_markup=get_main_menu_keyboard()
    )

# Обработчик главного меню
@dp.message(lambda message: message.text == "🎬 Найти фильм")
async def find_movie_start(message: types.Message, state: FSMContext):
    await message.answer(
        "🌟 Давай познакомимся!\n\nВыбери свой пол:",
        reply_markup=get_gender_keyboard()
    )
    await state.set_state(UserState.waiting_for_gender)

# Обработчик случайного факта
@dp.message(lambda message: message.text == "🎲 Случайный факт")
async def random_fact_handler(message: types.Message, state: FSMContext):
    fact = get_random_movie_fact()
    
    # Определяем текущее меню
    current_state = await state.get_state()
    if current_state == UserState.waiting_for_movie:
        reply_markup = get_movie_search_keyboard()
    elif current_state is None:
        reply_markup = get_main_menu_keyboard()
    else:
        reply_markup = get_exit_keyboard()
    
    await message.answer(
        f"🎯 **Случайный факт о кино:**\n\n{fact}\n\n"
        f"Хочешь узнать ещё факт или найти фильм?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# Обработчик кнопки "Ещё факт" во время поиска
@dp.message(lambda message: message.text == "🎲 Ещё факт")
async def more_fact_handler(message: types.Message, state: FSMContext):
    fact = get_random_movie_fact()
    await message.answer(
        f"🎯 **Ещё один факт:**\n\n{fact}",
        reply_markup=get_movie_search_keyboard(),
        parse_mode="Markdown"
    )

# Обработчик помощи
@dp.message(lambda message: message.text == "❓ Помощь")
async def help_handler(message: types.Message, state: FSMContext):
    help_text = (
        "📚 **Как пользоваться ботом:**\n\n"
        "1️⃣ Нажми '🎬 Найти фильм' для поиска\n"
        "2️⃣ Выбери свой пол\n"
        "3️⃣ Введи название или описание фильма/сериала\n"
        "4️⃣ Получи рекомендации со случайным фактом\n\n"
        "🎲 **Случайные факты:**\n"
        "- Нажми '🎲 Случайный факт' в любом меню\n"
        "- Во время поиска доступна кнопка '🎲 Ещё факт'\n\n"
        "🔹 **Команды:**\n"
        "/start - Главное меню\n"
        "/exit - Выход из диалога\n\n"
        "📽️ В базе {} интересных фактов о кино!".format(len(MOVIE_FACTS))
    )
    
    # Проверяем текущее состояние для правильного меню
    current_state = await state.get_state()
    
    if current_state == UserState.waiting_for_movie:
        reply_markup = get_movie_search_keyboard()
    else:
        reply_markup = get_main_menu_keyboard()
    
    await message.answer(help_text, reply_markup=reply_markup, parse_mode="Markdown")

# Обработчик выбора пола
@dp.message(UserState.waiting_for_gender)
async def process_gender(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в меню":
        await state.clear()
        await message.answer(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    gender = message.text
    
    # Сохраняем пол в состояние
    if gender == "Я парень 👨":
        await state.update_data(gender="male")
        await message.answer(
            "Ара, джан! 👋\n\n"
            "Дорогой, я помогу тебе найти лучшие фильмы на просторах кино! 🎬\n"
            "Напиши название или описание фильма/сериала, который хочешь посмотреть:",
            reply_markup=get_movie_search_keyboard()
        )
    elif gender == "Я девушка 👩":
        await state.update_data(gender="female")
        await message.answer(
            "Джан, сирун! 💫\n\n"
            "Дорогая, я помогу тебе найти лучшие фильмы на просторах кино! 🎬\n"
            "Напиши название или описание фильма/сериала, который хочешь посмотреть:",
            reply_markup=get_movie_search_keyboard()
        )
    else:
        await message.answer(
            "Пожалуйста, выбери пол, используя кнопки ниже:",
            reply_markup=get_gender_keyboard()
        )
        return
    
    await state.set_state(UserState.waiting_for_movie)

# Обработчик поиска фильма
@dp.message(UserState.waiting_for_movie)
async def process_movie_search(message: types.Message, state: FSMContext):
    # Обработка кнопок во время поиска
    if message.text == "🎬 Новый поиск":
        await message.answer(
            "Выбери свой пол:",
            reply_markup=get_gender_keyboard()
        )
        await state.set_state(UserState.waiting_for_gender)
        return
    elif message.text == "🚪 Выход":
        await exit_bot(message, state)
        return
    elif message.text == "❓ Помощь":
        await help_handler(message, state)
        return
    elif message.text == "🎲 Ещё факт":
        await more_fact_handler(message, state)
        return
    
    # Получаем данные пользователя
    user_data = await state.get_data()
    gender = user_data.get("gender", "unknown")
    
    # Получаем случайный факт
    random_fact = get_random_movie_fact()
    
    # Заглушка для поиска фильмов (пока без API)
    movie_name = message.text
    
    # Разные ответы в зависимости от пола
    if gender == "male":
        response = (
            f"🎯 Ара, отличный выбор!\n\n"
            f"Ты ищешь: \"{movie_name}\"\n"
            f"Джан, я уже ищу этот фильм для тебя... 🔍\n\n"
            f"⚡ Пока ищу, лови интересный факт:\n"
            f"**{random_fact}**\n\n"
            f"Можешь попробовать найти другой фильм или узнать ещё факт!"
        )
    else:
        response = (
            f"🎯 Джан, прекрасный выбор!\n\n"
            f"Ты ищешь: \"{movie_name}\"\n"
            f"Сирун, я уже ищу этот фильм для тебя... 🔍\n\n"
            f"⚡ Пока ищу, лови интересный факт:\n"
            f"**{random_fact}**\n\n"
            f"Можешь попробовать найти другой фильм или узнать ещё факт!"
        )
    
    await message.answer(response, reply_markup=get_movie_search_keyboard(), parse_mode="Markdown")

# Обработчик команды /exit
@dp.message(Command("exit"))
async def exit_bot(message: types.Message, state: FSMContext):
    # Получаем данные пользователя для персонализированного прощания
    user_data = await state.get_data()
    gender = user_data.get("gender", "unknown")
    
    if gender == "male":
        farewell = "Ара, джан! Было приятно пообщаться! 👋\n\n"
    elif gender == "female":
        farewell = "Джан, сирун! Было приятно пообщаться! 👋\n\n"
    else:
        farewell = "Было приятно пообщаться! 👋\n\n"
    
    # Добавляем случайный факт на прощание
    random_fact = get_random_movie_fact()
    
    await message.answer(
        farewell + f"🎬 Напоследок интересный факт:\n{random_fact}\n\n"
        "Если захочешь продолжить, нажми кнопку ниже:",
        reply_markup=get_exit_keyboard(),
        parse_mode="Markdown"
    )
    
    # Очищаем состояние пользователя
    await state.clear()

# Обработчик кнопки "✨ Начать общение" после выхода
@dp.message(lambda message: message.text == "✨ Начать общение")
async def start_new_chat(message: types.Message, state: FSMContext):
    await cmd_start(message, state)

# Обработчик текстовых сообщений вне состояний
@dp.message()
async def handle_other_messages(message: types.Message, state: FSMContext):
    if message.text == "🚪 Выход":
        await exit_bot(message, state)
    elif message.text == "✨ Начать общение":
        await cmd_start(message, state)
    elif message.text == "❓ Помощь":
        await help_handler(message, state)
    elif message.text == "🎲 Случайный факт":
        await random_fact_handler(message, state)
    else:
        await message.answer(
            "Используй меню для навигации или нажми /start",
            reply_markup=get_main_menu_keyboard()
        )

# Запуск бота
async def main():
    print("🎬 КиноBот запущен...")
    print(f"📽️ В базе {len(MOVIE_FACTS)} фактов о кино")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())