import os
import json
import asyncio
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import aiohttp
import random
import re

# Установка зависимостей для голоса
try:
    import speech_recognition as sr
except ImportError:
    print("📦 Устанавливаю SpeechRecognition...")
    import subprocess
    subprocess.run(["pip", "install", "SpeechRecognition"], check=False)
    import speech_recognition as sr

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Инициализация бота БЕЗ DefaultBotProperties (это важно для business!)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Хранилище бизнес-подключений
business_connections = {}
BUSINESS_CONNECTIONS_FILE = 'business_connections.json'


# Состояния FSM
class ConfigStates(StatesGroup):
    waiting_for_config = State()


# ==================== РАБОТА С БИЗНЕС-ПОДКЛЮЧЕНИЯМИ ====================
def load_business_connections():
    """Загрузить бизнес-подключения из файла"""
    if os.path.exists(BUSINESS_CONNECTIONS_FILE):
        try:
            with open(BUSINESS_CONNECTIONS_FILE, 'r', encoding='utf-8') as f:
                connections = json.load(f)
                print(f"✔️ Загружено {len(connections)} бизнес-подключений")
                return connections
        except Exception as e:
            print(f"✖️ Ошибка загрузки подключений: {e}")
            return {}
    return {}


def save_business_connections(connections):
    """Сохранить бизнес-подключения в файл"""
    try:
        with open(BUSINESS_CONNECTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(connections, f, ensure_ascii=False, indent=2)
        print(f"💾 Сохранено {len(connections)} бизнес-подключений")
    except Exception as e:
        print(f"✖️ Ошибка сохранения подключений: {e}")


# ==================== ИНИЦИАЛИЗАЦИЯ БД ====================
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()

    # Таблица конфигурации
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_prompt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # Таблица памяти для каждого пользователя
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Добавляем дефолтный конфиг если его нет
    cursor.execute('SELECT COUNT(*) FROM ai_config WHERE is_active = 1')
    if cursor.fetchone()[0] == 0:
        default_prompt = "Ты - профессиональный помощник бизнес-аккаунта. Отвечай вежливо, по делу и профессионально."
        cursor.execute('INSERT INTO ai_config (system_prompt, is_active) VALUES (?, 1)', (default_prompt,))

    conn.commit()
    conn.close()


# Получение активного конфига
def get_active_config():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT system_prompt FROM ai_config WHERE is_active = 1 ORDER BY id DESC LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Ты - помощник."


# Сохранение конфига
def save_config(system_prompt):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE ai_config SET is_active = 0')
    cursor.execute('INSERT INTO ai_config (system_prompt, is_active) VALUES (?, 1)', (system_prompt,))
    conn.commit()
    conn.close()


# Удаление конфига (возврат к дефолтному)
def delete_config():
    default_prompt = "Ты - профессиональный помощник бизнес-аккаунта. Отвечай вежливо, по делу и профессионально."
    save_config(default_prompt)


# Получение истории диалога для пользователя
def get_conversation_history(user_id, limit=10):
    """Получить последние N сообщений из памяти"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content FROM conversation_memory 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (user_id, limit))
    messages = cursor.fetchall()
    conn.close()
    # Возвращаем в правильном порядке (от старых к новым)
    return [{"role": role, "content": content} for role, content in reversed(messages)]


# Сохранение сообщения в память
def save_to_memory(user_id, role, content):
    """Сохранить сообщение в память"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversation_memory (user_id, role, content) 
        VALUES (?, ?, ?)
    ''', (user_id, role, content))
    conn.commit()
    conn.close()


# Очистка памяти пользователя
def clear_memory(user_id):
    """Очистить всю память пользователя"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM conversation_memory WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


# Клавиатуры
def get_thinking_inline_keyboard():
    """Inline клавиатура для меню мышления"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Текущий конфиг", callback_data="show_config")],
            [InlineKeyboardButton(text="⚙️ Изменить конфиг", callback_data="change_config")],
            [InlineKeyboardButton(text="🗑 Удалить конфиг", callback_data="delete_config")]
        ]
    )
    return keyboard


def get_config_view_keyboard():
    """Клавиатура для просмотра конфига"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_thinking")]
        ]
    )
    return keyboard


def get_change_config_keyboard():
    """Клавиатура для изменения конфига"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_thinking")]
        ]
    )
    return keyboard


def get_delete_confirm_keyboard():
    """Клавиатура подтверждения удаления"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✔️ Да", callback_data="confirm_delete")],
            [InlineKeyboardButton(text="✖️ Нет", callback_data="back_to_thinking")]
        ]
    )
    return keyboard


# Установка команд бота
async def set_bot_commands():
    commands = [
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="clear", description="Очистить память диалога")
    ]
    await bot.set_my_commands(commands)


def json_config_to_prompt(config_data):
    """Преобразует JSON конфиг в четкий system prompt"""
    try:
        if isinstance(config_data, str):
            config_data = json.loads(config_data)

        # НОВЫЙ ФОРМАТ: если есть 'system_prompt' - используем его напрямую
        if 'system_prompt' in config_data and isinstance(config_data['system_prompt'], str):
            return config_data['system_prompt']

        # Если это конфиг с полем "personality" (старый формат)
        if 'personality' in config_data:
            name = config_data.get('name', 'Ассистент')
            personality = config_data['personality']

            prompt_parts = [
                f"=== ЛИЧНОСТЬ: {name} ===\n"
            ]

            # Базовая информация
            if 'base_info' in personality:
                info = personality['base_info']
                prompt_parts.append("ОСНОВНАЯ ИНФОРМАЦИЯ:")
                for key, value in info.items():
                    prompt_parts.append(f"  {key}: {value}")
                prompt_parts.append("")

            # Стиль общения
            if 'communication_style' in personality:
                comm = personality['communication_style']
                prompt_parts.append("СТИЛЬ ОБЩЕНИЯ:")

                if 'writing_style' in comm:
                    ws = comm['writing_style']
                    prompt_parts.append("  Написание:")
                    prompt_parts.append(f"    - Регистр: {ws.get('case', 'lowercase_only')}")
                    prompt_parts.append(f"    - Макс слов: {ws.get('max_words_per_message', 15)}")

                    if 'punctuation' in ws:
                        p = ws['punctuation']
                        prompt_parts.append("    - Пунктуация:")
                        if not p.get('exclamation_marks', False):
                            prompt_parts.append("      × НЕТ восклицательных знаков")
                        if not p.get('dashes', False):
                            prompt_parts.append("      × НЕТ длинных тире")
                        if p.get('closing_parenthesis_as_smile', False):
                            prompt_parts.append("      ✓ Используй ) как смайлик")

                if 'vocabulary' in comm:
                    vocab = comm['vocabulary']
                    if 'common_words' in vocab:
                        prompt_parts.append(f"  Частые слова: {', '.join(vocab['common_words'][:10])}")

                prompt_parts.append("")

            # Паттерны сообщений
            if 'message_patterns' in personality:
                patterns = personality['message_patterns']
                prompt_parts.append("ПРИМЕРЫ ФРАЗ:")
                for pattern in patterns[:8]:
                    prompt_parts.append(f"  - {pattern}")
                prompt_parts.append("")

            # Поведение ответов
            if 'response_behavior' in personality:
                rb = personality['response_behavior']
                prompt_parts.append("ПРАВИЛА ОТВЕТОВ:")
                prompt_parts.append(f"  - Длина: {rb.get('response_length', 'very_short')}")
                prompt_parts.append(f"  - Избегай заглавных: {rb.get('avoid_capitals', True)}")

                if 'emoji_usage' in rb:
                    eu = rb['emoji_usage']
                    prompt_parts.append(f"  - Эмодзи: {eu.get('frequency', 'rare')}")
                    if 'preferred_emoji' in eu:
                        prompt_parts.append(f"    Используй: {', '.join(eu['preferred_emoji'])}")

                prompt_parts.append("")

            # Шаблоны ответов
            if 'response_templates' in personality:
                templates = personality['response_templates']
                prompt_parts.append("ШАБЛОНЫ ОТВЕТОВ:")
                for key, value in list(templates.items())[:6]:
                    prompt_parts.append(f"  {key}: {value}")
                prompt_parts.append("")

            # Ограничения
            if 'constraints' in personality:
                const = personality['constraints']
                if 'never_use' in const:
                    prompt_parts.append("СТРОГО ЗАПРЕЩЕНО:")
                    for item in const['never_use']:
                        prompt_parts.append(f"  × {item}")

                if 'always_use' in const:
                    prompt_parts.append("\nВСЕГДА ИСПОЛЬЗУЙ:")
                    for item in const['always_use']:
                        prompt_parts.append(f"  ✓ {item}")

                prompt_parts.append("")

            # Примеры сообщений
            if 'example_messages' in personality:
                examples = personality['example_messages']
                prompt_parts.append("ПРИМЕРЫ ТВОИХ СООБЩЕНИЙ:")
                for ex in examples[:10]:
                    prompt_parts.append(f"  → {ex}")

            return '\n'.join(prompt_parts)

        # УНИВЕРСАЛЬНЫЙ ПАРСЕР для любой другой JSON структуры
        prompt_parts = []

        def parse_dict(data, indent=0):
            """Рекурсивно парсит словарь в читаемый промпт"""
            for key, value in data.items():
                prefix = "  " * indent

                if isinstance(value, dict):
                    prompt_parts.append(f"{prefix}## {key.upper().replace('_', ' ')}:")
                    parse_dict(value, indent + 1)
                elif isinstance(value, list):
                    prompt_parts.append(f"{prefix}## {key.upper().replace('_', ' ')}:")
                    for item in value:
                        if isinstance(item, dict):
                            parse_dict(item, indent + 1)
                        else:
                            prompt_parts.append(f"{prefix}  - {item}")
                elif isinstance(value, (str, int, float, bool)):
                    prompt_parts.append(f"{prefix}{key.replace('_', ' ')}: {value}")

        # Если есть имя - добавляем заголовок
        if 'name' in config_data:
            prompt_parts.append(f"=== ПЕРСОНАЖ: {config_data['name']} ===\n")

        parse_dict(config_data)

        return '\n'.join(prompt_parts)

    except Exception as e:
        print(f"Ошибка парсинга конфига: {e}")
        return str(config_data)


def clean_ai_formatting(text):
    """Удаляет все форматирование из ответа ИИ"""
    import re

    # Удаляем блоки кода
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)

    # Удаляем жирный текст
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)

    # Удаляем курсив
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # Удаляем оставшиеся звездочки и подчеркивания
    text = text.replace('*', '').replace('_', '')

    # Удаляем зачеркнутый текст
    text = re.sub(r'~~([^~]+)~~', r'\1', text)

    return text.strip()


def calculate_typing_time(text):
    """Рассчитывает время печатания на основе длины текста"""
    # Средняя скорость печати: 2-4 символов в секунду (медленнее для коротких)
    char_count = len(text)

    # Для коротких сообщений (до 20 символов) - быстрее
    if char_count <= 20:
        base_time = char_count * random.uniform(0.15, 0.25)
    else:
        base_time = char_count * random.uniform(0.25, 0.4)

    # Ограничиваем максимальное время
    max_time = 12  # максимум 12 секунд печатания
    typing_time = min(base_time, max_time)

    # Минимум 1.5 секунды
    typing_time = max(typing_time, 1.5)

    return typing_time


async def handle_rate_limit_error(chat_id, business_connection_id=None):
    """Обработка ошибки rate limit - ждем и отвечаем"""
    print("⚠️ Rate limit достигнут, ждем 5 секунд...")
    await asyncio.sleep(5)

    fallback_message = "ща"

    if business_connection_id:
        await bot.send_message(
            chat_id=chat_id,
            text=fallback_message,
            business_connection_id=business_connection_id
        )
    else:
        await bot.send_message(chat_id=chat_id, text=fallback_message)

    print("✔️ Отправлено fallback сообщение")


async def transcribe_voice(voice_file_path):
    """Транскрибация голосового сообщения через Google Speech Recognition"""
    try:
        import speech_recognition as sr

        # Конвертируем OGG в WAV
        wav_path = voice_file_path.replace('.ogg', '.wav')

        process = await asyncio.create_subprocess_exec(
            'ffmpeg', '-i', voice_file_path, '-acodec', 'pcm_s16le',
            '-ar', '16000', '-ac', '1', wav_path, '-y',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        # Распознаем
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='ru-RU')

        # Удаляем временные файлы
        try:
            os.remove(wav_path)
            os.remove(voice_file_path)
        except:
            pass

        return text

    except Exception as e:
        print(f"✖️ Ошибка распознавания: {e}")
        return None


def split_message_naturally(text):
    """Разбивает сообщение на несколько частей естественным образом"""
    # Если в тексте есть переносы строк - ВСЕГДА используем их
    if '\n' in text:
        parts = [p.strip() for p in text.split('\n') if p.strip()]

        # Если частей 1-2, группируем рандомно
        if len(parts) <= 2:
            # 70% шанс разбить на отдельные сообщения
            if random.random() < 0.7 and len(parts) > 1:
                return [p for p in parts if p.strip()]  # Фильтруем пустые
            else:
                return [text.strip()] if text.strip() else ["ок"]

        # Если частей 3+, всегда разбиваем, но иногда группируем по 2
        messages = []
        i = 0
        while i < len(parts):
            # 40% шанс объединить 2 строки в одно сообщение
            if random.random() < 0.4 and i < len(parts) - 1:
                combined = (parts[i] + '\n' + parts[i + 1]).strip()
                if combined:
                    messages.append(combined)
                i += 2
            else:
                if parts[i].strip():
                    messages.append(parts[i].strip())
                i += 1

        return messages if messages else ["ок"]

    # Подсчет слов
    words = text.split()
    word_count = len(words)

    # Если меньше 8 слов - 60% шанс разбить на 2 сообщения
    if word_count < 8:
        if random.random() < 0.6 and word_count >= 4:
            # Разбиваем пополам по словам
            mid = word_count // 2
            part1 = ' '.join(words[:mid]).strip()
            part2 = ' '.join(words[mid:]).strip()
            if part1 and part2:
                return [part1, part2]
        return [text.strip()] if text.strip() else ["ок"]

    # Если 8-15 слов - ВСЕГДА разбиваем на 2-3 сообщения
    if word_count < 15:
        import re
        sentences = re.split(r'(?<=[.!?,])\s+', text)

        if len(sentences) <= 1:
            # Режем по запятым
            parts = [p.strip() for p in text.split(',') if p.strip()]
            if len(parts) >= 2:
                mid = len(parts) // 2
                part1 = ', '.join(parts[:mid]).strip()
                part2 = ', '.join(parts[mid:]).strip()
                result = []
                if part1:
                    result.append(part1)
                if part2:
                    result.append(part2)
                return result if result else [text.strip()]

            # Режем по словам
            if word_count >= 6:
                third = word_count // 3
                part1 = ' '.join(words[:third]).strip()
                part2 = ' '.join(words[third:third * 2]).strip()
                part3 = ' '.join(words[third * 2:]).strip()
                result = []
                if part1:
                    result.append(part1)
                if part2:
                    result.append(part2)
                if part3:
                    result.append(part3)
                return result if result else [text.strip()]

        # Делим предложения на 2-3 части
        if len(sentences) == 2:
            return [s.strip() for s in sentences if s.strip()]
        else:
            mid = len(sentences) // 2
            part1 = ' '.join(sentences[:mid]).strip()
            part2 = ' '.join(sentences[mid:]).strip()
            result = []
            if part1:
                result.append(part1)
            if part2:
                result.append(part2)
            return result if result else [text.strip()]

    # Если 15+ слов - ОБЯЗАТЕЛЬНО разбиваем на 2-4 части
    import re
    sentences = re.split(r'(?<=[.!?,])\s+', text)

    if len(sentences) <= 1:
        # Если одно длинное предложение - режем по запятым
        parts = [p.strip() for p in text.split(',') if p.strip()]
        if len(parts) > 2:
            num_messages = random.randint(2, min(4, len(parts)))
            chunk_size = max(1, len(parts) // num_messages)
            messages = []
            for i in range(num_messages):
                start = i * chunk_size
                if i == num_messages - 1:
                    end = len(parts)
                else:
                    end = start + chunk_size
                msg = ', '.join(parts[start:end]).strip()
                if msg:
                    messages.append(msg)
            return messages if messages else [text.strip()]

        # Режем по словам
        num_messages = random.randint(2, min(4, word_count // 3))
        chunk_size = max(1, word_count // num_messages)
        messages = []
        for i in range(num_messages):
            start = i * chunk_size
            if i == num_messages - 1:
                end = word_count
            else:
                end = start + chunk_size
            msg = ' '.join(words[start:end]).strip()
            if msg:
                messages.append(msg)
        return messages if messages else [text.strip()]

    # Группируем предложения в 2-4 сообщения
    num_messages = random.randint(2, min(4, len(sentences)))
    chunk_size = max(1, len(sentences) // num_messages)

    messages = []
    for i in range(num_messages):
        start = i * chunk_size
        if i == num_messages - 1:
            end = len(sentences)
        else:
            end = start + chunk_size

        chunk = ' '.join(sentences[start:end]).strip()
        if chunk:
            messages.append(chunk)

    return messages if messages else [text.strip() if text.strip() else ["ок"]]


async def get_ai_response(user_id, message_text, system_prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Получаем историю диалога
    history = get_conversation_history(user_id, limit=10)

    # Если конфиг в JSON формате, конвертируем в промпт
    try:
        json.loads(system_prompt)
        system_prompt = json_config_to_prompt(system_prompt)
    except:
        pass

    # Формируем сообщения
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message_text})

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }

    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    ai_response = result['choices'][0]['message']['content']
                    ai_response = clean_ai_formatting(ai_response)

                    save_to_memory(user_id, "user", message_text)
                    save_to_memory(user_id, "assistant", ai_response)

                    return ai_response
                elif response.status == 429:
                    # Rate limit - возвращаем None как сигнал
                    print("⚠️ Rate limit 429 получен")
                    return None
                else:
                    error_text = await response.text()
                    print(f"✖️ API ошибка {response.status}: {error_text}")
                    return None
    except Exception as e:
        print(f"✖️ Исключение: {str(e)}")
        return None


# ==================== КОМАНДЫ ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    config = get_active_config()

    # Форматируем конфиг для отображения
    try:
        config_json = json.loads(config)
        config_preview = json.dumps(config_json, ensure_ascii=False, indent=2)
        if len(config_preview) > 200:
            config_preview = config_preview[:200] + "..."
    except:
        config_preview = config[:200] + "..." if len(config) > 200 else config

    await message.answer(
        f"🧠 <b>Настройка мышления ИИ</b>\n\n"
        f"📄 <b>Текущий конфиг:</b>\n"
        f"<blockquote>{config_preview}</blockquote>",
        reply_markup=get_thinking_inline_keyboard(),
        parse_mode="HTML"
    )


@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    """Очистка памяти диалога"""
    user_id = message.from_user.id
    clear_memory(user_id)

    await message.answer(
        "✔️ <b>Память диалога очищена!</b>\n\n"
        "История переписки удалена, начинаем с чистого листа.",
        parse_mode="HTML"
    )


# ==================== CALLBACK HANDLERS ====================
@dp.callback_query(F.data == "back_to_thinking")
async def callback_back_to_thinking(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к меню настроек мышления"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("✖️ Доступ запрещён", show_alert=True)
        return

    # Сбрасываем состояние FSM
    await state.clear()

    config = get_active_config()

    # Форматируем конфиг для отображения
    try:
        config_json = json.loads(config)
        config_preview = json.dumps(config_json, ensure_ascii=False, indent=2)
        if len(config_preview) > 200:
            config_preview = config_preview[:200] + "..."
    except:
        config_preview = config[:200] + "..." if len(config) > 200 else config

    try:
        await callback.message.edit_text(
            f"🧠 <b>Настройка мышления ИИ</b>\n\n"
            f"📄 <b>Текущий конфиг:</b>\n"
            f"<blockquote>{config_preview}</blockquote>",
            reply_markup=get_thinking_inline_keyboard(),
            parse_mode="HTML"
        )
    except:
        pass

    await callback.answer()


@dp.callback_query(F.data == "show_config")
async def callback_show_config(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("✖️ Доступ запрещён", show_alert=True)
        return

    config = get_active_config()

    # Форматируем конфиг
    try:
        config_json = json.loads(config)
        config_text = json.dumps(config_json, ensure_ascii=False, indent=2)
    except:
        config_text = config

    # Если конфиг слишком длинный, отправляем файлом
    if len(config_text) > 3000:
        await callback.message.answer_document(
            types.BufferedInputFile(config_text.encode('utf-8'), filename="config.json"),
            caption="<b>📝 Текущая конфигурация ИИ</b>",
            parse_mode="HTML"
        )
        await callback.answer("Конфиг отправлен файлом")
    else:
        try:
            await callback.message.edit_text(
                f"📝 <b>Текущая конфигурация ИИ:</b>\n\n"
                f"<blockquote>{config_text}</blockquote>",
                reply_markup=get_config_view_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer()
        except Exception as e:
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)


@dp.callback_query(F.data == "change_config")
async def callback_change_config(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("✖️ Доступ запрещён", show_alert=True)
        return

    await state.set_state(ConfigStates.waiting_for_config)

    example_config = '''{
  "name": "никита",
  "personality": {
    "base_info": {
      "age": 22,
      "occupation": ["кодер", "ютубер"]
    },
    "communication_style": {
      "writing_style": {
        "case": "lowercase_only",
        "max_words_per_message": 15,
        "punctuation": {
          "exclamation_marks": false,
          "dashes": false,
          "closing_parenthesis_as_smile": true
        }
      },
      "vocabulary": {
        "common_words": ["норм", "окей", "го", "агась", "че"]
      }
    },
    "message_patterns": [
      "как дела?)",
      "норм)",
      "понял)"
    ],
    "response_behavior": {
      "response_length": "very_short",
      "avoid_capitals": true,
      "emoji_usage": {
        "frequency": "rare",
        "preferred_emoji": [")", "?)"]
      }
    },
    "response_templates": {
      "help": "че нужно?)",
      "success": "готово)",
      "error": "баг)"
    },
    "constraints": {
      "never_use": [
        "восклицательные знаки",
        "заглавные буквы",
        "длинные тире"
      ],
      "always_use": [
        "строчные буквы",
        "короткие фразы",
        "смайлик )"
      ]
    },
    "example_messages": [
      "привет) че как?)",
      "норм) кодю)",
      "го сделаем?)",
      "окей) щас"
    ]
  }
}'''

    try:
        await callback.message.edit_text(
            "⚙️ <b>изменение конфига</b>\n\n"
            "<b>📄 отправь новый конфиг:</b>\n"
            "• простой текст для system prompt\n"
            "• json файл с детальной конфигурацией\n\n"
            "<b>📋 структура json пример:</b>\n\n"
            "<blockquote expandable>"
            f"<pre>{example_config}</pre>"
            "</blockquote>\n\n"
            "<b>основные поля:</b>\n"
            "• <code>name</code> - имя персонажа\n"
            "• <code>personality.communication_style</code> - стиль общения\n"
            "• <code>personality.message_patterns</code> - примеры фраз\n"
            "• <code>personality.constraints</code> - ограничения\n"
            "• <code>personality.example_messages</code> - примеры сообщений",
            reply_markup=get_change_config_keyboard(),
            parse_mode="HTML"
        )
    except:
        pass

    await callback.answer("отправь новый конфиг")


@dp.callback_query(F.data == "delete_config")
async def callback_delete_config(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("✖️ Доступ запрещён", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            "🗑 <b>Удаление конфигурации</b>\n\n"
            "Вы уверены, что хотите сбросить конфигурацию?\n"
            "Будет установлен стандартный system prompt.",
            reply_markup=get_delete_confirm_keyboard(),
            parse_mode="HTML"
        )
    except:
        pass

    await callback.answer()


@dp.callback_query(F.data == "confirm_delete")
async def callback_confirm_delete(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("✖️ Доступ запрещён", show_alert=True)
        return

    delete_config()

    config = get_active_config()
    config_preview = config[:200] + "..." if len(config) > 200 else config

    try:
        await callback.message.edit_text(
            f"✔️ <b>Конфигурация сброшена!</b>\n\n"
            f"📄 <b>Текущий конфиг:</b>\n"
            f"<blockquote>{config_preview}</blockquote>",
            reply_markup=get_thinking_inline_keyboard(),
            parse_mode="HTML"
        )
    except:
        pass

    await callback.answer("Конфиг удалён")


@dp.message(ConfigStates.waiting_for_config)
async def process_new_config(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    new_config = None

    # Если отправлен файл
    if message.document:
        if message.document.mime_type == 'application/json':
            file = await bot.get_file(message.document.file_id)
            file_content = await bot.download_file(file.file_path)
            try:
                # Читаем JSON и сохраняем как строку
                json_data = json.loads(file_content.read().decode('utf-8'))
                new_config = json.dumps(json_data, ensure_ascii=False, indent=2)
                print(f"✔️ JSON конфиг загружен из файла")
            except Exception as e:
                await message.answer(f"✖️ ошибка чтения json: {e}", parse_mode="HTML")
                return
        else:
            await message.answer("✖️ поддерживаются только json файлы", parse_mode="HTML")
            return
    # Если отправлен текст
    elif message.text:
        try:
            # Проверяем, является ли текст JSON
            json_data = json.loads(message.text)
            new_config = json.dumps(json_data, ensure_ascii=False, indent=2)
            print(f"✔️ JSON конфиг загружен из текста")
        except:
            # Если не JSON, сохраняем как обычный текст
            new_config = message.text
            print(f"✔️ Текстовый конфиг загружен")

    if new_config:
        save_config(new_config)
        await state.clear()

        # Тестируем конвертацию
        test_prompt = json_config_to_prompt(new_config)
        print(f"📝 Сгенерированный промпт ({len(test_prompt)} символов):")
        print(f"{test_prompt[:500]}..." if len(test_prompt) > 500 else test_prompt)

        # Форматируем превью
        try:
            config_json = json.loads(new_config)

            # Определяем тип конфига
            if 'system_prompt' in config_json:
                config_type = "system_prompt (готовый промпт)"
                name = config_json.get('name', 'не указано')
            elif 'personality' in config_json:
                config_type = "personality structure"
                name = config_json.get('name', 'ассистент')
            else:
                config_type = "универсальная структура"
                name = config_json.get('name', config_json.get('basic_info', {}).get('name', 'не указано'))

            config_preview = f"имя: {name}\n"
            config_preview += f"тип: {config_type}\n"
            config_preview += f"полей: {len(config_json)}"

        except:
            config_preview = new_config[:200] + "..." if len(new_config) > 200 else new_config

        await message.answer(
            f"✔️ <b>конфиг обновлен)</b>\n\n"
            f"📄 <b>новый конфиг:</b>\n<blockquote>{config_preview}</blockquote>",
            reply_markup=get_thinking_inline_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer("✖️ не удалось получить конфиг", parse_mode="HTML")


# ==================== BUSINESS HANDLERS ====================
@dp.business_connection()
async def handle_business_connection(business_connection: types.BusinessConnection):
    """Обработка подключения/отключения бизнес-аккаунта"""
    try:
        user_id = business_connection.user.id
        connection_id = business_connection.id
        is_enabled = business_connection.is_enabled

        if is_enabled:
            business_connections[connection_id] = user_id
            save_business_connections(business_connections)
            print(f"✔️ Бизнес-подключение установлено: {connection_id} -> User {user_id}")
        else:
            if connection_id in business_connections:
                del business_connections[connection_id]
                save_business_connections(business_connections)
            print(f"✖️ Бизнес-подключение отключено: {connection_id}")

        print(f"📊 Всего подключений: {len(business_connections)}")

    except Exception as e:
        print(f"✖️ Ошибка сохранения подключения: {e}")


@dp.business_message(F.text)
async def handle_business_text_message(message: types.Message):
    """Обработка текстовых сообщений из бизнес-чатов"""
    try:
        business_connection_id = message.business_connection_id

        if not business_connection_id:
            return

        if business_connection_id not in business_connections:
            business_connections[business_connection_id] = ADMIN_ID
            save_business_connections(business_connections)
            print(f"✔️ Автосохранение: {business_connection_id} -> {ADMIN_ID}")

        bot_owner_id = business_connections[business_connection_id]

        if message.from_user and message.from_user.id == bot_owner_id:
            print(f"⏭️ Сообщение от владельца - пропускаем")
            return

        user_message = message.text
        user_id = message.from_user.id
        print(f"📨 Сообщение от клиента {user_id}: {user_message}")

        # Рандомный шанс ответить с reply (30%)
        should_reply = random.random() < 0.3
        reply_to_id = message.message_id if should_reply else None

        if should_reply:
            print(f"💬 Будем отвечать с reply")

        # Задержка перед началом
        initial_delay = random.uniform(1, 5)
        print(f"⏳ Ждем {initial_delay:.1f} сек перед началом печатания...")
        await asyncio.sleep(initial_delay)

        # Показываем что печатаем
        await bot.send_chat_action(
            chat_id=message.chat.id,
            action="typing",
            business_connection_id=business_connection_id
        )

        # Получаем ответ от ИИ
        system_prompt = get_active_config()
        ai_response = await get_ai_response(user_id, user_message, system_prompt)

        # Если rate limit - обрабатываем
        if ai_response is None:
            await handle_rate_limit_error(message.chat.id, business_connection_id)
            return

        # Разбиваем ответ на части
        message_parts = split_message_naturally(ai_response)
        print(f"📝 Ответ разбит на {len(message_parts)} сообщений")

        # Отправляем каждое сообщение
        for idx, part in enumerate(message_parts):
            typing_time = calculate_typing_time(part)
            print(
                f"⌨️ Сообщение {idx + 1}/{len(message_parts)}: печатаем {len(part)} символов ({typing_time:.1f} сек)...")

            typing_intervals = max(int(typing_time / 4), 1)
            interval_time = typing_time / typing_intervals

            for i in range(typing_intervals):
                await asyncio.sleep(interval_time)
                await bot.send_chat_action(
                    chat_id=message.chat.id,
                    action="typing",
                    business_connection_id=business_connection_id
                )

            # Первое сообщение с reply (если выпал шанс)
            if idx == 0 and reply_to_id:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=part,
                    reply_to_message_id=reply_to_id,
                    business_connection_id=business_connection_id
                )
            else:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=part,
                    business_connection_id=business_connection_id
                )

            print(f"✔️ Сообщение {idx + 1}/{len(message_parts)} отправлено")

            if idx < len(message_parts) - 1:
                # Короткая пауза для коротких сообщений, длиннее для больших
                if len(part) < 20:
                    between_delay = random.uniform(0.5, 1.5)
                else:
                    between_delay = random.uniform(1, 2.5)
                print(f"⏳ Пауза {between_delay:.1f} сек перед следующим сообщением...")
                await asyncio.sleep(between_delay)

                await bot.send_chat_action(
                    chat_id=message.chat.id,
                    action="typing",
                    business_connection_id=business_connection_id
                )

        print(f"✅ Все сообщения отправлены!")

    except Exception as e:
        print(f"✖️ Ошибка бизнес-сообщения: {e}")
        import traceback
        traceback.print_exc()


@dp.business_message(F.voice)
async def handle_business_voice_message(message: types.Message):
    """Обработка голосовых сообщений из бизнес-чатов"""
    try:
        business_connection_id = message.business_connection_id

        if not business_connection_id:
            return

        if business_connection_id not in business_connections:
            business_connections[business_connection_id] = ADMIN_ID
            save_business_connections(business_connections)
            print(f"✔️ Автосохранение: {business_connection_id} -> {ADMIN_ID}")

        bot_owner_id = business_connections[business_connection_id]

        if message.from_user and message.from_user.id == bot_owner_id:
            print(f"⏭️ Голосовое от владельца - пропускаем")
            return

        user_id = message.from_user.id
        voice_duration = message.voice.duration
        print(f"🎤 Голосовое сообщение от клиента {user_id} ({voice_duration} сек)")

        # Рандомный шанс ответить с reply (30%)
        should_reply = random.random() < 0.3
        reply_to_id = message.message_id if should_reply else None

        if should_reply:
            print(f"💬 Будем отвечать с reply на голосовое")

        # Имитируем прослушивание
        listen_time = min(voice_duration, 20)
        intervals = max(1, int(listen_time / 4))
        interval_duration = listen_time / intervals

        print(f"👂 Имитируем прослушивание {listen_time:.1f} сек...")

        for i in range(intervals):
            await bot.send_chat_action(
                chat_id=message.chat.id,
                action="typing",
                business_connection_id=business_connection_id
            )
            await asyncio.sleep(interval_duration)

        # Скачиваем и распознаем
        voice = message.voice
        file = await bot.get_file(voice.file_id)
        voice_path = f"/tmp/business_voice_{user_id}_{voice.file_id}.ogg"
        await bot.download_file(file.file_path, voice_path)

        transcribed_text = await transcribe_voice(voice_path)

        if not transcribed_text:
            await bot.send_message(
                chat_id=message.chat.id,
                text="не расслышал, повтори",
                reply_to_message_id=reply_to_id,
                business_connection_id=business_connection_id
            )
            return

        print(f"📝 Распознано: {transcribed_text}")

        # Получаем ответ от ИИ
        system_prompt = get_active_config()
        ai_response = await get_ai_response(user_id, transcribed_text, system_prompt)

        if ai_response is None:
            await handle_rate_limit_error(message.chat.id, business_connection_id)
            return

        # Разбиваем на части
        message_parts = split_message_naturally(ai_response)
        print(f"📝 Ответ разбит на {len(message_parts)} сообщений")

        for idx, part in enumerate(message_parts):
            typing_time = calculate_typing_time(part)
            print(
                f"⌨️ Сообщение {idx + 1}/{len(message_parts)}: печатаем {len(part)} символов ({typing_time:.1f} сек)...")

            typing_intervals = max(int(typing_time / 4), 1)
            interval_time = typing_time / typing_intervals

            for i in range(typing_intervals):
                await asyncio.sleep(interval_time)
                await bot.send_chat_action(
                    chat_id=message.chat.id,
                    action="typing",
                    business_connection_id=business_connection_id
                )

            # Первое сообщение с reply (если выпал шанс)
            if idx == 0 and reply_to_id:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=part,
                    reply_to_message_id=reply_to_id,
                    business_connection_id=business_connection_id
                )
            else:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=part,
                    business_connection_id=business_connection_id
                )

            print(f"✔️ Сообщение {idx + 1}/{len(message_parts)} отправлено")

            if idx < len(message_parts) - 1:
                between_delay = random.uniform(1, 3)
                print(f"⏳ Пауза {between_delay:.1f} сек...")
                await asyncio.sleep(between_delay)

                await bot.send_chat_action(
                    chat_id=message.chat.id,
                    action="typing",
                    business_connection_id=business_connection_id
                )

        print(f"✅ Голосовое обработано!")

    except Exception as e:
        print(f"✖️ Ошибка бизнес-голоса: {e}")
        import traceback
        traceback.print_exc()

# Обработка обычных сообщений (только для админа)
@dp.message()
async def handle_message(message: types.Message):
    if hasattr(message, 'business_connection_id') and message.business_connection_id:
        return

    if message.from_user.id != ADMIN_ID:
        return

    if message.text and message.text.startswith('/'):
        return

    user_message = message.text or message.caption or ""

    if not user_message:
        return

    # Получаем ответ от ИИ
    system_prompt = get_active_config()
    ai_response = await get_ai_response(message.from_user.id, user_message, system_prompt)

    # Если rate limit - обрабатываем
    if ai_response is None:
        await handle_rate_limit_error(message.chat.id)
        return

    await message.answer(ai_response, parse_mode="HTML")

@dp.message(F.voice)
async def handle_admin_voice(message: types.Message):
    """Обработка голосовых сообщений от админа"""
    if message.from_user.id != ADMIN_ID:
        return

    await bot.send_chat_action(message.chat.id, "typing")

    try:
        voice = message.voice
        file = await bot.get_file(voice.file_id)
        voice_path = f"/tmp/admin_voice_{voice.file_id}.ogg"
        await bot.download_file(file.file_path, voice_path)

        transcribed_text = await transcribe_voice(voice_path)

        if not transcribed_text:
            await message.answer("✖️ Не удалось распознать")
            return

        system_prompt = get_active_config()
        ai_response = await get_ai_response(message.from_user.id, transcribed_text, system_prompt)

        if ai_response is None:
            await handle_rate_limit_error(message.chat.id)
            return

        await message.answer(ai_response, parse_mode="HTML")

    except Exception as e:
        print(f"✖️ Ошибка голоса: {e}")
        await message.answer("✖️ Ошибка обработки")

# Запуск бота
async def main():
    global business_connections

    # Загружаем подключения
    business_connections = load_business_connections()

    # Инициализируем БД
    init_db()

    # Устанавливаем команды
    await set_bot_commands()

    print("🤖 Бот запущен!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
