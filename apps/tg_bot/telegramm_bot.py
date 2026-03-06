import asyncio
import os
import random
import aiohttp
from finished_model.request_to_model import RequestModel
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import requests

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токены из переменных окружения
TOKEN = os.getenv('BOT_TOKEN')
KINOPOISK_API_KEY = os.getenv('KINOPOISK_API_KEY')  # Новый ключ

# Проверяем, что токены загружены
if not TOKEN:
    raise ValueError("Токен бота не найден! Создай файл .env с BOT_TOKEN=твой_токен")
if not KINOPOISK_API_KEY:
    raise ValueError("API ключ Кинопоиска не найден! Добавь KINOPOISK_API_KEY в .env файл")

# API конфигурация для Kinopoisk API Unofficial
API_TRANSFORMER_URL = "http://127.0.0.1:8000/predict-type-message?message="

API_URL = "https://kinopoiskapiunofficial.tech/api/v2.2/films"
HEADERS = {
    "X-API-KEY": KINOPOISK_API_KEY,
    "Content-Type": "application/json"
}

# Создаем экземпляры бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


model = RequestModel()

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
    "🎬 Самый кассовый фильм 2023 года — «Барби» (1.4 миллиарда $)",
    "📽️ Фильм «Аватар: Путь воды» снимали 13 лет",
    "🎭 Леонардо ДиКаприо получил свой первый «Оскар» только через 22 года после начала карьеры",
    "🍿 Самый дорогой эпизод в истории ТВ стоит 15 млн $ — финал «Игры престолов»",
]

# Функция для получения случайного факта
def get_random_movie_fact():
    return random.choice(MOVIE_FACTS)

# Функция для поиска фильмов через Kinopoisk API Unofficial
async def search_movies(query: str, limit: int = 5):
    """
    Поиск фильмов по названию через Kinopoisk API Unofficial
    """
    try:
        async with aiohttp.ClientSession() as session:
            # Параметры запроса
            params = {
                "keyword": query,  # Поиск по ключевому слову
                "page": 1,
                "order": "RATING",  # Сортировка по рейтингу
                "type": "FILM"  # Ищем только фильмы (не сериалы)
            }
            
            async with session.get(API_URL, headers=HEADERS, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("items", [])[:limit]
                else:
                    print(f"Ошибка API: {response.status}")
                    if response.status == 401:
                        print("Проверь API ключ - он может быть недействительным")
                    elif response.status == 429:
                        print("Слишком много запросов. Лимит 20 запросов в секунду")
                    return []
    except Exception as e:
        print(f"Ошибка при запросе к API: {e}")
        return []

# Функция для форматирования информации о фильме (адаптирована под Kinopoisk API)
def format_movie_info(movie, gender: str, fact: str = None):
    """
    Форматирует информацию о фильме для отправки пользователю
    """
    # Основная информация из Kinopoisk API
    name_ru = movie.get('nameRu', 'Название неизвестно')
    name_en = movie.get('nameEn', '')
    name_original = movie.get('nameOriginal', '')
    year = movie.get('year', 'Год неизвестен')
    rating = movie.get('ratingKinopoisk', 'Нет рейтинга')
    description = movie.get('description', 'Описание отсутствует')
    film_length = movie.get('filmLength', 'Неизвестно')
    kinopoisk_id = movie.get('kinopoiskId', '')
    
    # Формируем полное название
    if name_en and name_en != name_ru:
        full_name = f"{name_ru} / {name_en}"
    elif name_original and name_original != name_ru:
        full_name = f"{name_ru} / {name_original}"
    else:
        full_name = name_ru
    
    # Жанры
    genres = [g.get('genre') for g in movie.get('genres', [])[:3]]
    genres_str = ', '.join(genres) if genres else 'Не указаны'
    
    # Страны
    countries = [c.get('country') for c in movie.get('countries', [])[:2]]
    countries_str = ', '.join(countries) if countries else 'Не указаны'
    
    # Формируем сообщение в зависимости от пола
    if gender == "male":
        header = f"🎯 Ара, нашёл для тебя!\n\n"
    else:
        header = f"🎯 Джан, нашла для тебя!\n\n"
    
    # Основной блок информации
    movie_info = (
        f"📽️ **{full_name}**\n"
        f"📅 **Год:** {year}\n"
        f"⭐ **Рейтинг КП:** {rating}\n"
        f"🌍 **Страна:** {countries_str}\n"
        f"🎭 **Жанры:** {genres_str}\n"
        f"⏱️ **Длительность:** {film_length} мин.\n"
        f"🔗 **Ссылка:** https://www.kinopoisk.ru/film/{kinopoisk_id}/\n\n"
        f"📝 **Описание:**\n{description[:300]}{'...' if len(description) > 300 else ''}\n\n"
    )
    
    # Добавляем случайный факт если есть
    if fact:
        movie_info += f"⚡ **Кстати:** {fact}\n\n"
    
    # Инструкция для последнего фильма
    movie_info += "Можешь попробовать найти другой фильм или узнать ещё факт!"
    
    return header + movie_info

# Определяем состояния для FSM (Finite State Machine)
class UserState(StatesGroup):
    waiting_for_gender = State()
    waiting_for_movie = State()
    waiting_for_find_movie = State()
    waiting_for_type_message = State()

# Главное меню
def get_main_menu_keyboard():
    buttons = [
        [KeyboardButton(text="🎬 Найти фильм"), KeyboardButton(text="Подбор фильма")],
        [KeyboardButton(text="🎲 Случайный факт"), KeyboardButton(text="❓ Помощь"), KeyboardButton(text="Определение тональности")],
        [KeyboardButton(text="🚪 Выход")],
        # [KeyboardButton(text="Подборка фильма")]
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
        [KeyboardButton(text="🎬 Новый поиск"), KeyboardButton(text="Подбор фильма")],
        [KeyboardButton(text="🎲 Ещё факт"), KeyboardButton(text="❓ Помощь"), KeyboardButton(text="Определение тональности")],
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

# Обработчик главного меню
@dp.message(lambda message: message.text == "Подбор фильма")
async def find_movie_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Введити текст для побора фильма по предпочтениям:",
        reply_markup=get_main_menu_keyboard()
    )
    await state.set_state(UserState.waiting_for_find_movie)

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
        f"📽️ В базе {len(MOVIE_FACTS)} интересных фактов о кино!\n\n"
        "🎬 **Поиск фильмов:**\n"
        "Бот ищет фильмы через Kinopoisk API Unofficial и показывает:\n"
        "- Название (русское и оригинальное)\n"
        "- Год выпуска\n"
        "- Рейтинг Кинопоиска\n"
        "- Страна производства\n"
        "- Жанры\n"
        "- Длительность\n"
        "- Описание\n"
        "- Постер (если есть)\n"
        "- Ссылку на Кинопоиск"
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

@dp.message(UserState.waiting_for_type_message)
async def process_type_message(message: types.Message, state: FSMContext):
    if message.text in ["🎬 Новый поиск", "Подбор фильма", "🚪 Выход", "❓ Помощь", "🎲 Ещё факт", 'Определение тональности']:
        if message.text == "🎬 Новый поиск":
            await message.answer(
                "Выбери свой пол:",
                reply_markup=get_gender_keyboard()
            )
            await state.set_state(UserState.waiting_for_gender)
        elif message.text == "🚪 Выход":
            await exit_bot(message, state)
        elif message.text == "❓ Помощь":
            await help_handler(message, state)
        elif message.text == "🎲 Ещё факт":
            await more_fact_handler(message, state)
        elif message.text == "Определение тональности":
            await message.answer(
                "Введите сообщение:",
                reply_markup=get_main_menu_keyboard()
            )
            await state.set_state(UserState.waiting_for_type_message)
        return
    
    result = send_request_type_message(message.text)
    await message.answer(
        f"Тип комментария: {result['russian_type_message']}\n Точность: {result['accuracy']}",
        reply_markup=get_movie_search_keyboard(),
    )

def send_request_type_message(input_text: str):
    return requests.get(API_TRANSFORMER_URL + input_text).json()

@dp.message(UserState.waiting_for_find_movie)
async def process_movie_find(message: types.Message, state: FSMContext):
    if message.text in ["🎬 Найти фильм", "🚪 Выход", "❓ Помощь", "🎲 Ещё факт", 'Определение тональности']:
        if message.text == "🎬 Найти фильм":
            await message.answer(
                "Выбери свой пол:",
                reply_markup=get_gender_keyboard()
            )
            await state.set_state(UserState.waiting_for_gender)

        elif message.text == "🚪 Выход":
            await exit_bot(message, state)
        elif message.text == "❓ Помощь":
            await help_handler(message, state)
        elif message.text == "🎲 Ещё факт":
            await more_fact_handler(message, state)
        elif message.text == "Определение тональности":
            await message.answer(
                "Введите сообщение:",
            )
            await state.set_state(UserState.waiting_for_type_message)
        return
    
    result = model.request_model(message.text)

    await asyncio.sleep(1)
    await message.answer(result, reply_markup=get_movie_search_keyboard(), parse_mode="Markdown")

# Обработчик поиска фильма
@dp.message(UserState.waiting_for_movie)
async def process_movie_search(message: types.Message, state: FSMContext):
    # Обработка кнопок во время поиска
    if message.text in ["🎬 Новый поиск", 'Подбор фильма', "🚪 Выход", "❓ Помощь", "🎲 Ещё факт", 'Определение тональности']:
        if message.text == "🎬 Новый поиск":
            await message.answer(
                "Выбери свой пол:",
                reply_markup=get_gender_keyboard()
            )
            await state.set_state(UserState.waiting_for_gender)
        elif message.text == "🎬 Новый поиск":
            await message.answer(
                "Введити текст для побора фильма по предпочтениям: ",
                reply_markup=get_main_menu_keyboard()
            )
            await state.set_state(UserState.waiting_for_find_movie)
        elif message.text == "🚪 Выход":
            await exit_bot(message, state)
        elif message.text == "❓ Помощь":
            await help_handler(message, state)
        elif message.text == "🎲 Ещё факт":
            await more_fact_handler(message, state)
        elif message.text == "Определение тональности":
            await message.answer(
                "Введите сообщение:",
            )
            await state.set_state(UserState.waiting_for_type_message)
        return
    
    query = message.text
    if (send_request_type_message(query)['russian_type_message'] == 'Негативный'):
        await message.answer('Ара, нельзя так!!!', reply_markup=get_movie_search_keyboard(), parse_mode="Markdown")
        return
    
    # Получаем данные пользователя
    user_data = await state.get_data()
    gender = user_data.get("gender", "unknown")
    
    # Отправляем сообщение о начале поиска
    searching_msg = await message.answer(
        "🔍 Ищу фильмы на Кинопоиске... Это может занять несколько секунд.",
        reply_markup=get_movie_search_keyboard()
    )
    
    # Поиск фильмов через API
    movies = await search_movies(query)
    
    # Удаляем сообщение о поиске
    await searching_msg.delete()
    
    if not movies:
        # Получаем случайный факт
        random_fact = get_random_movie_fact()
        
        # Если ничего не нашли
        if gender == "male":
            response = (
                f"😕 Ара, по запросу \"{query}\" ничего не нашлось на Кинопоиске.\n\n"
                f"Попробуй изменить запрос или поищи что-то другое!\n\n"
                f"⚡ А пока лови факт:\n**{random_fact}**"
            )
        else:
            response = (
                f"😕 Джан, по запросу \"{query}\" ничего не нашлось на Кинопоиске.\n\n"
                f"Попробуй изменить запрос или поищи что-то другое!\n\n"
                f"⚡ А пока лови факт:\n**{random_fact}**"
            )
        
        await message.answer(response, reply_markup=get_movie_search_keyboard(), parse_mode="Markdown")
        return
    
    # Отправляем результаты (до 3 фильмов)
    for i, movie in enumerate(movies[:3]):
        # Получаем случайный факт только для первого фильма
        random_fact = get_random_movie_fact() if i == 0 else None
        
        formatted_info = format_movie_info(movie, gender, random_fact)
        
        # Отправляем фото, если есть
        poster = movie.get('posterUrl')
        if poster:
            await message.answer_photo(
                photo=poster,
                caption=formatted_info,
                reply_markup=get_movie_search_keyboard() if i == len(movies[:3]) - 1 else ReplyKeyboardRemove(),
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                formatted_info,
                reply_markup=get_movie_search_keyboard() if i == len(movies[:3]) - 1 else ReplyKeyboardRemove(),
                parse_mode="Markdown"
            )
        
        # Небольшая задержка между сообщениями
        await asyncio.sleep(0.5)

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
        await help_handler(message, state)
    elif message.text == "Определение тональности":
        await message.answer(
            "Введите сообщение: ",
            reply_markup=get_main_menu_keyboard()
        )
        await state.set_state(UserState.waiting_for_type_message)
    else:
        await message.answer(
            "Используй меню для навигации или нажми /start",
            reply_markup=get_main_menu_keyboard()
        )

# Запуск бота
async def main():
    print("🎬 КиноBот запущен...")
    print(f"📽️ В базе {len(MOVIE_FACTS)} фактов о кино")
    print(f"🔑 Kinopoisk API Unofficial подключен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())