# ── SSL-патч для Windows (первая строка, до всех импортов) ───────────────
import ssl as _ssl
_ssl._create_default_https_context = _ssl._create_unverified_context
# ─────────────────────────────────────────────────────────────────────────

import os
import json
import asyncio
import sqlite3
import re
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
import aiohttp

try:
    import speech_recognition as sr
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "SpeechRecognition"], check=False)
    import speech_recognition as sr

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN    = "8738745683:AAGZF174_5exSVt55Ou4pVS54W8J1NpCL04"
GROQ_API_KEY = "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"
ADMIN_ID     = 5883796026
ADMIN_ID_2   = 1989613788
DB_PATH      = "business_bot.db"
CONN_FILE    = "biz_connections.json"
# ====================================================

def is_admin(uid: int) -> bool:
    return uid in (ADMIN_ID, ADMIN_ID_2)

bot     = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp      = Dispatcher(storage=storage)

business_connections: dict = {}

# ==================== ПРЕМИУМ ЭМОДЗИ ====================
def tge(eid, fb=''):
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

EM_GEAR   = tge('5870982283724328568', '⚙️')
EM_OK     = tge('5870633910337015697', '✅')
EM_ERR    = tge('5870657884844462243', '❌')
EM_EYE    = tge('6037397706505195857', '👁')
EM_BOT    = tge('6030400221232501136', '🤖')
EM_PERSON = tge('5870994129244131212', '👤')
EM_MSG    = tge('5778208881301787450', '💬')
EM_DEL    = tge('5870875489362513438', '🗑')
EM_STATS  = tge('5870921681735781843', '📊')
EM_KEY    = tge('5870676941614354370', '🔑')
EM_BELL   = tge('6039486778597970865', '🔔')
EM_LOCK   = tge('6037249452824072506', '🔒')
EM_SHIELD = tge('6030537007350944596', '🛡')
EM_CLOCK  = tge('5983150113483134607', '⏰')
EM_MONEY  = tge('5904462880941545555', '🪙')
EM_FIRE   = tge('5199457120428249992', '🔥')
EM_INFO   = tge('6028435952299413210', 'ℹ️')
EM_BACK   = tge('5893057118545646106', '◁')
EM_LIST   = tge('5870528606328852614', '📁')
EM_PENCIL = tge('5870676941614354370', '✏️')


# ==================== FSM ====================
class AIConfig(StatesGroup):
    waiting_prompt = State()

class BlacklistState(StatesGroup):
    waiting_id = State()

class AutoReplyState(StatesGroup):
    waiting_text = State()


# ==================== БАЗА ДАННЫХ ====================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    # Настройки бота
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    # Сохранённые (удалённые) сообщения
    c.execute('''CREATE TABLE IF NOT EXISTS message_cache (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id     INTEGER,
        msg_id      INTEGER,
        user_id     INTEGER,
        username    TEXT,
        first_name  TEXT,
        text        TEXT,
        file_id     TEXT,
        file_type   TEXT,
        caption     TEXT,
        timestamp   TEXT,
        UNIQUE(chat_id, msg_id)
    )''')

    # Статистика по пользователям
    c.execute('''CREATE TABLE IF NOT EXISTS user_stats (
        user_id    INTEGER PRIMARY KEY,
        username   TEXT,
        first_name TEXT,
        msg_count  INTEGER DEFAULT 0,
        last_seen  TEXT
    )''')

    # Чёрный список (не отвечаем ИИ)
    c.execute('''CREATE TABLE IF NOT EXISTS blacklist (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        added_at TEXT
    )''')

    # История диалогов ИИ
    c.execute('''CREATE TABLE IF NOT EXISTS ai_memory (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER,
        role       TEXT,
        content    TEXT,
        timestamp  TEXT
    )''')

    # Дефолтные настройки
    defaults = {
        'ai_enabled':      '0',
        'spy_enabled':     '1',   # слежка за удалёнными
        'ai_prompt':       'Ты - профессиональный помощник бизнес-аккаунта. Отвечай вежливо, по делу.',
        'ai_model':        'llama-3.3-70b-versatile',
        'auto_reply':      '',    # авто-ответ на первое сообщение
        'reply_chance':    '30',  # % шанс reply
        'typing_speed':    '1',   # множитель скорости печати
        'notify_deleted':  '1',   # уведомлять об удалённых
        'log_all_msgs':    '1',   # логировать все сообщения
    }
    for k, v in defaults.items():
        c.execute('INSERT OR IGNORE INTO settings VALUES (?, ?)', (k, v))

    conn.commit()
    conn.close()


def get_setting(key: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key=?', (key,))
    row  = c.fetchone()
    conn.close()
    return row[0] if row else ''

def set_setting(key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (key, value))
    conn.commit()
    conn.close()

def toggle_setting(key: str) -> str:
    cur = get_setting(key)
    new = '0' if cur == '1' else '1'
    set_setting(key, new)
    return new

def cache_message(msg: types.Message):
    if get_setting('log_all_msgs') != '1':
        return
    try:
        u        = msg.from_user
        file_id  = None
        file_type= None
        if msg.photo:
            file_id   = msg.photo[-1].file_id
            file_type = 'photo'
        elif msg.video:
            file_id   = msg.video.file_id
            file_type = 'video'
        elif msg.document:
            file_id   = msg.document.file_id
            file_type = 'document'
        elif msg.voice:
            file_id   = msg.voice.file_id
            file_type = 'voice'
        elif msg.sticker:
            file_id   = msg.sticker.file_id
            file_type = 'sticker'
        elif msg.video_note:
            file_id   = msg.video_note.file_id
            file_type = 'video_note'

        conn = sqlite3.connect(DB_PATH)
        c    = conn.cursor()
        c.execute('''INSERT OR IGNORE INTO message_cache
            (chat_id, msg_id, user_id, username, first_name, text, file_id, file_type, caption, timestamp)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (msg.chat.id, msg.message_id,
             u.id if u else 0,
             u.username if u else '',
             u.first_name if u else '',
             msg.text or '',
             file_id, file_type,
             msg.caption or '',
             datetime.now().isoformat()))
        conn.commit()
        conn.close()

        # Обновляем статистику
        if u:
            conn = sqlite3.connect(DB_PATH)
            c    = conn.cursor()
            c.execute('''INSERT INTO user_stats (user_id, username, first_name, msg_count, last_seen)
                VALUES (?,?,?,1,?)
                ON CONFLICT(user_id) DO UPDATE SET
                    msg_count = msg_count+1,
                    last_seen = excluded.last_seen,
                    username  = excluded.username,
                    first_name= excluded.first_name''',
                (u.id, u.username or '', u.first_name or '', datetime.now().isoformat()))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"cache_message error: {e}")

def get_cached_message(chat_id: int, msg_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c    = conn.cursor()
    c.execute('SELECT * FROM message_cache WHERE chat_id=? AND msg_id=?', (chat_id, msg_id))
    row  = c.fetchone()
    conn.close()
    return row

def is_blacklisted(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute('SELECT 1 FROM blacklist WHERE user_id=?', (user_id,))
    r    = c.fetchone()
    conn.close()
    return r is not None

def add_blacklist(user_id: int, username: str = ''):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute('INSERT OR IGNORE INTO blacklist VALUES (?,?,?)',
              (user_id, username, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def remove_blacklist(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute('DELETE FROM blacklist WHERE user_id=?', (user_id,))
    conn.commit()
    conn.close()

def get_blacklist():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c    = conn.cursor()
    c.execute('SELECT * FROM blacklist')
    r    = c.fetchall()
    conn.close()
    return r

def get_ai_history(user_id: int, limit=10):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute('''SELECT role, content FROM ai_memory
        WHERE user_id=? ORDER BY timestamp DESC LIMIT ?''', (user_id, limit))
    msgs = c.fetchall()
    conn.close()
    return [{"role": r, "content": cont} for r, cont in reversed(msgs)]

def save_ai_memory(user_id: int, role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute('INSERT INTO ai_memory (user_id,role,content,timestamp) VALUES (?,?,?,?)',
              (user_id, role, content, datetime.now().isoformat()))
    # Чистим старые — оставляем 30
    c.execute('''DELETE FROM ai_memory WHERE id NOT IN (
        SELECT id FROM ai_memory WHERE user_id=? ORDER BY timestamp DESC LIMIT 30
    ) AND user_id=?''', (user_id, user_id))
    conn.commit()
    conn.close()

def clear_ai_memory(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute('DELETE FROM ai_memory WHERE user_id=?', (user_id,))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute('SELECT COUNT(*) FROM user_stats')
    users = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM message_cache')
    msgs  = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM blacklist')
    bl    = c.fetchone()[0]
    c.execute('SELECT SUM(msg_count) FROM user_stats')
    total = c.fetchone()[0] or 0
    conn.close()
    return users, msgs, bl, total

def get_top_users(limit=5):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c    = conn.cursor()
    c.execute('SELECT * FROM user_stats ORDER BY msg_count DESC LIMIT ?', (limit,))
    r    = c.fetchall()
    conn.close()
    return r


# ==================== БИЗ-ПОДКЛЮЧЕНИЯ ====================
def load_connections():
    if os.path.exists(CONN_FILE):
        try:
            with open(CONN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_connections(d):
    with open(CONN_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


# ==================== GROQ AI ====================
def clean_formatting(text: str) -> str:
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    return re.sub(r'~~([^~]+)~~', r'\1', text).replace('*','').replace('_','').strip()

async def ask_groq(user_id: int, text: str) -> str | None:
    prompt = get_setting('ai_prompt')
    model  = get_setting('ai_model') or 'llama-3.3-70b-versatile'
    history = get_ai_history(user_id)

    messages = [{"role": "system", "content": prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": text})

    try:
        conn = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=conn) as s:
            async with s.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 1024},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as r:
                if r.status == 200:
                    data    = await r.json()
                    reply   = clean_formatting(data['choices'][0]['message']['content'])
                    save_ai_memory(user_id, "user",      text)
                    save_ai_memory(user_id, "assistant", reply)
                    return reply
                elif r.status == 429:
                    print("Groq rate limit")
                    return None
                else:
                    err = await r.text()
                    print(f"Groq error {r.status}: {err[:200]}")
                    return None
    except Exception as e:
        print(f"Groq exception: {e}")
        return None

def typing_time(text: str) -> float:
    n = len(text)
    t = n * random.uniform(0.15, 0.25) if n <= 20 else n * random.uniform(0.25, 0.4)
    spd = float(get_setting('typing_speed') or '1')
    return max(min(t / max(spd, 0.1), 12), 1.0)

def split_naturally(text: str) -> list[str]:
    if '\n' in text:
        parts = [p.strip() for p in text.split('\n') if p.strip()]
        if len(parts) <= 2:
            return parts if random.random() < 0.7 else [text.strip()]
        msgs, i = [], 0
        while i < len(parts):
            if random.random() < 0.4 and i < len(parts)-1:
                msgs.append((parts[i]+'\n'+parts[i+1]).strip()); i += 2
            else:
                msgs.append(parts[i]); i += 1
        return msgs or [text]
    words = text.split()
    wc    = len(words)
    if wc < 8:
        if random.random() < 0.5 and wc >= 4:
            m = wc // 2
            return [' '.join(words[:m]), ' '.join(words[m:])]
        return [text]
    sents = re.split(r'(?<=[.!?])\s+', text)
    n     = random.randint(2, min(4, max(2, len(sents))))
    cs    = max(1, len(sents) // n)
    return [' '.join(sents[i*cs:(i+1)*cs if i<n-1 else None]).strip() for i in range(n) if ' '.join(sents[i*cs:(i+1)*cs if i<n-1 else None]).strip()]

async def send_ai_reply(chat_id, user_id, text, bc_id, reply_to=None):
    response = await ask_groq(user_id, text)
    if not response:
        return

    parts        = split_naturally(response)
    use_reply    = reply_to and random.randint(1, 100) <= int(get_setting('reply_chance') or '30')
    first_reply  = reply_to if use_reply else None

    for idx, part in enumerate(parts):
        tt       = typing_time(part)
        intervals = max(int(tt / 4), 1)
        for _ in range(intervals):
            await asyncio.sleep(tt / intervals)
            try:
                await bot.send_chat_action(chat_id=chat_id, action="typing", business_connection_id=bc_id)
            except:
                pass
        try:
            kwargs = {"chat_id": chat_id, "text": part, "business_connection_id": bc_id}
            if idx == 0 and first_reply:
                kwargs["reply_to_message_id"] = first_reply
            await bot.send_message(**kwargs)
        except Exception as e:
            print(f"send_ai_reply error: {e}")

        if idx < len(parts)-1:
            await asyncio.sleep(random.uniform(0.5, 2.0))


# ==================== КЛАВИАТУРЫ ====================
def main_kb():
    ai  = '🟢' if get_setting('ai_enabled') == '1' else '🔴'
    spy = '🟢' if get_setting('spy_enabled') == '1' else '🔴'
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{ai} ИИ-ответы",        callback_data="menu_ai"),
         InlineKeyboardButton(text=f"{spy} Слежка за удал.", callback_data="menu_spy")],
        [InlineKeyboardButton(text="📊 Статистика",           callback_data="menu_stats"),
         InlineKeyboardButton(text="👥 Пользователи",         callback_data="menu_users")],
        [InlineKeyboardButton(text="⛔ Чёрный список",        callback_data="menu_blacklist"),
         InlineKeyboardButton(text="🔔 Уведомления",         callback_data="menu_notify")],
        [InlineKeyboardButton(text="⚙️ Прочие настройки",    callback_data="menu_misc")],
    ])

def ai_kb():
    enabled = get_setting('ai_enabled') == '1'
    btn_lbl = f"{'🟢 Включено' if enabled else '🔴 Выключено'}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_lbl,               callback_data="ai_toggle")],
        [InlineKeyboardButton(text="✏️ Изменить промпт",  callback_data="ai_prompt")],
        [InlineKeyboardButton(text="🧠 Модель: " + get_setting('ai_model').split('-')[0], callback_data="ai_model")],
        [InlineKeyboardButton(text="💬 Шанс reply: " + get_setting('reply_chance') + "%", callback_data="ai_reply_chance")],
        [InlineKeyboardButton(text="⚡ Скорость печати x" + get_setting('typing_speed'), callback_data="ai_speed")],
        [InlineKeyboardButton(text="🗑 Очистить всю AI-память", callback_data="ai_clear_all")],
        [InlineKeyboardButton(text="◁ Назад",             callback_data="back_main")],
    ])

def spy_kb():
    enabled = get_setting('spy_enabled') == '1'
    notif   = get_setting('notify_deleted') == '1'
    log     = get_setting('log_all_msgs') == '1'
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'🟢' if enabled else '🔴'} Слежка за удалёнными", callback_data="spy_toggle")],
        [InlineKeyboardButton(text=f"{'🟢' if notif else '🔴'} Уведомлять меня",       callback_data="spy_notify_toggle")],
        [InlineKeyboardButton(text=f"{'🟢' if log else '🔴'} Логировать все сообщ.",   callback_data="spy_log_toggle")],
        [InlineKeyboardButton(text="◁ Назад", callback_data="back_main")],
    ])

def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◁ Назад", callback_data="back_main")]
    ])

def blacklist_kb():
    bl = get_blacklist()
    rows = []
    for row in bl:
        name = f"@{row['username']}" if row['username'] else str(row['user_id'])
        rows.append([InlineKeyboardButton(text=f"❌ {name}", callback_data=f"bl_remove_{row['user_id']}")])
    rows.append([InlineKeyboardButton(text="➕ Добавить по ID", callback_data="bl_add")])
    rows.append([InlineKeyboardButton(text="◁ Назад",           callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def model_kb():
    models = [
        ("llama-3.3-70b-versatile", "Llama 3.3 70B"),
        ("llama-3.1-8b-instant",    "Llama 3.1 8B"),
        ("mixtral-8x7b-32768",      "Mixtral 8x7B"),
        ("gemma2-9b-it",            "Gemma2 9B"),
    ]
    cur = get_setting('ai_model')
    rows = []
    for val, label in models:
        tick = "✅ " if val == cur else ""
        rows.append([InlineKeyboardButton(text=tick+label, callback_data=f"set_model_{val}")])
    rows.append([InlineKeyboardButton(text="◁ Назад", callback_data="menu_ai")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def misc_kb():
    auto = get_setting('auto_reply')
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{'🟢' if auto else '🔴'} Авто-ответ на первое сообщение",
            callback_data="misc_autoreply")],
        [InlineKeyboardButton(text="◁ Назад", callback_data="back_main")],
    ])


# ==================== HANDLERS ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    ai  = '🟢 Вкл' if get_setting('ai_enabled') == '1' else '🔴 Выкл'
    spy = '🟢 Вкл' if get_setting('spy_enabled') == '1' else '🔴 Выкл'
    await message.answer(
        f'{EM_SHIELD} <b>Business Monitor Bot</b>\n\n'
        f'{EM_BOT} ИИ-ответы: <b>{ai}</b>\n'
        f'{EM_EYE} Слежка за удалёнными: <b>{spy}</b>\n\n'
        f'{EM_INFO} Выберите раздел настроек:',
        reply_markup=main_kb(), parse_mode=ParseMode.HTML
    )

@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    if not is_admin(message.from_user.id): return
    clear_ai_memory(message.from_user.id)
    await message.answer(f'{EM_OK} Память ИИ очищена.', parse_mode=ParseMode.HTML)

# ── Главное меню ──────────────────────────────────
@dp.callback_query(F.data == "back_main")
async def cb_back(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return await callback.answer()
    await state.clear()
    ai  = '🟢 Вкл' if get_setting('ai_enabled') == '1' else '🔴 Выкл'
    spy = '🟢 Вкл' if get_setting('spy_enabled') == '1' else '🔴 Выкл'
    try:
        await callback.message.edit_text(
            f'{EM_SHIELD} <b>Business Monitor Bot</b>\n\n'
            f'{EM_BOT} ИИ-ответы: <b>{ai}</b>\n'
            f'{EM_EYE} Слежка за удалёнными: <b>{spy}</b>\n\n'
            f'{EM_INFO} Выберите раздел настроек:',
            reply_markup=main_kb(), parse_mode=ParseMode.HTML
        )
    except: pass
    await callback.answer()

# ── ИИ меню ───────────────────────────────────────
@dp.callback_query(F.data == "menu_ai")
async def cb_ai_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    enabled = get_setting('ai_enabled') == '1'
    try:
        await callback.message.edit_text(
            f'{EM_BOT} <b>Настройки ИИ-ответов</b>\n\n'
            f'Статус: <b>{"🟢 Включено" if enabled else "🔴 Выключено"}</b>\n'
            f'Модель: <code>{get_setting("ai_model")}</code>\n'
            f'Шанс reply: <b>{get_setting("reply_chance")}%</b>\n'
            f'Скорость печати: <b>x{get_setting("typing_speed")}</b>',
            reply_markup=ai_kb(), parse_mode=ParseMode.HTML
        )
    except: pass
    await callback.answer()

@dp.callback_query(F.data == "ai_toggle")
async def cb_ai_toggle(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    new = toggle_setting('ai_enabled')
    await callback.answer(f"ИИ-ответы {'включены' if new=='1' else 'выключены'}")
    await cb_ai_menu(callback)

@dp.callback_query(F.data == "ai_prompt")
async def cb_ai_prompt(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return await callback.answer()
    cur = get_setting('ai_prompt')
    try:
        await callback.message.edit_text(
            f'{EM_PENCIL} <b>Изменение промпта</b>\n\n'
            f'<b>Текущий:</b>\n<blockquote>{cur[:300]}</blockquote>\n\n'
            f'Отправьте новый промпт:',
            reply_markup=back_kb(), parse_mode=ParseMode.HTML
        )
    except: pass
    await state.set_state(AIConfig.waiting_prompt)
    await callback.answer()

@dp.message(AIConfig.waiting_prompt)
async def process_ai_prompt(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    if message.text:
        set_setting('ai_prompt', message.text.strip())
        await state.clear()
        await message.answer(f'{EM_OK} Промпт обновлён!', reply_markup=back_kb(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "ai_model")
async def cb_ai_model(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    try:
        await callback.message.edit_text(
            f'{EM_GEAR} <b>Выберите модель ИИ:</b>',
            reply_markup=model_kb(), parse_mode=ParseMode.HTML
        )
    except: pass
    await callback.answer()

@dp.callback_query(F.data.startswith("set_model_"))
async def cb_set_model(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    model = callback.data.replace("set_model_", "")
    set_setting('ai_model', model)
    await callback.answer(f"Модель: {model}")
    await cb_ai_model(callback)

@dp.callback_query(F.data == "ai_reply_chance")
async def cb_reply_chance(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    cur    = int(get_setting('reply_chance') or '30')
    # Циклично переключаем: 0 → 10 → 20 → 30 → 50 → 70 → 100 → 0
    steps  = [0, 10, 20, 30, 50, 70, 100]
    idx    = steps.index(cur) if cur in steps else 2
    new    = steps[(idx + 1) % len(steps)]
    set_setting('reply_chance', str(new))
    await callback.answer(f"Шанс reply: {new}%")
    await cb_ai_menu(callback)

@dp.callback_query(F.data == "ai_speed")
async def cb_ai_speed(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    cur   = float(get_setting('typing_speed') or '1')
    steps = [0.5, 1.0, 1.5, 2.0, 3.0]
    try:
        idx = steps.index(cur)
    except:
        idx = 1
    new = steps[(idx + 1) % len(steps)]
    set_setting('typing_speed', str(new))
    await callback.answer(f"Скорость x{new}")
    await cb_ai_menu(callback)

@dp.callback_query(F.data == "ai_clear_all")
async def cb_clear_all_memory(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    conn = sqlite3.connect(DB_PATH)
    conn.execute('DELETE FROM ai_memory')
    conn.commit()
    conn.close()
    await callback.answer("Вся AI-память очищена!")
    await cb_ai_menu(callback)

# ── Слежка ────────────────────────────────────────
@dp.callback_query(F.data == "menu_spy")
async def cb_spy_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    enabled = get_setting('spy_enabled') == '1'
    notif   = get_setting('notify_deleted') == '1'
    log     = get_setting('log_all_msgs') == '1'
    try:
        await callback.message.edit_text(
            f'{EM_EYE} <b>Слежка за удалёнными сообщениями</b>\n\n'
            f'Статус: <b>{"🟢 Включено" if enabled else "🔴 Выключено"}</b>\n'
            f'Уведомления: <b>{"🟢 Да" if notif else "🔴 Нет"}</b>\n'
            f'Логировать все: <b>{"🟢 Да" if log else "🔴 Нет"}</b>\n\n'
            f'{EM_INFO} Когда кто-то удаляет сообщение — бот пришлёт '
            f'содержимое + ID + юзернейм удалившего.',
            reply_markup=spy_kb(), parse_mode=ParseMode.HTML
        )
    except: pass
    await callback.answer()

@dp.callback_query(F.data == "spy_toggle")
async def cb_spy_toggle(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    new = toggle_setting('spy_enabled')
    await callback.answer(f"Слежка {'включена' if new=='1' else 'выключена'}")
    await cb_spy_menu(callback)

@dp.callback_query(F.data == "spy_notify_toggle")
async def cb_spy_notify(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    new = toggle_setting('notify_deleted')
    await callback.answer(f"Уведомления {'вкл' if new=='1' else 'выкл'}")
    await cb_spy_menu(callback)

@dp.callback_query(F.data == "spy_log_toggle")
async def cb_spy_log(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    new = toggle_setting('log_all_msgs')
    await callback.answer(f"Логирование {'вкл' if new=='1' else 'выкл'}")
    await cb_spy_menu(callback)

# ── Статистика ────────────────────────────────────
@dp.callback_query(F.data == "menu_stats")
async def cb_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    users, msgs, bl, total = get_stats()
    top = get_top_users(5)
    top_text = ''
    for i, row in enumerate(top, 1):
        name = f"@{row['username']}" if row['username'] else row['first_name'] or str(row['user_id'])
        top_text += f"  {i}. {name} — {row['msg_count']} сообщ.\n"

    try:
        await callback.message.edit_text(
            f'{EM_STATS} <b>Статистика</b>\n\n'
            f'👥 Уникальных пользователей: <b>{users}</b>\n'
            f'💬 Сообщений в кеше: <b>{msgs}</b>\n'
            f'⛔ В чёрном списке: <b>{bl}</b>\n'
            f'📨 Всего сообщений: <b>{total}</b>\n\n'
            f'<b>🏆 Топ-5 активных:</b>\n{top_text or "  Нет данных"}',
            reply_markup=back_kb(), parse_mode=ParseMode.HTML
        )
    except: pass
    await callback.answer()

# ── Пользователи ──────────────────────────────────
@dp.callback_query(F.data == "menu_users")
async def cb_users(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    top = get_top_users(10)
    if not top:
        text = f'{EM_PERSON} <b>Пользователи</b>\n\nПока нет данных.'
    else:
        lines = []
        for row in top:
            name = f"@{row['username']}" if row['username'] else (row['first_name'] or '?')
            lines.append(f"• <code>{row['user_id']}</code> {name} — {row['msg_count']} сообщ. | {str(row['last_seen'])[:10]}")
        text = f'{EM_PERSON} <b>Пользователи (топ 10)</b>\n\n' + '\n'.join(lines)
    try:
        await callback.message.edit_text(text, reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await callback.answer()

# ── Чёрный список ─────────────────────────────────
@dp.callback_query(F.data == "menu_blacklist")
async def cb_blacklist(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    bl = get_blacklist()
    try:
        await callback.message.edit_text(
            f'⛔ <b>Чёрный список</b>\n\n'
            f'{EM_INFO} Пользователям в чёрном списке ИИ не отвечает.\n'
            f'Всего: <b>{len(bl)}</b>',
            reply_markup=blacklist_kb(), parse_mode=ParseMode.HTML
        )
    except: pass
    await callback.answer()

@dp.callback_query(F.data == "bl_add")
async def cb_bl_add(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return await callback.answer()
    try:
        await callback.message.edit_text(
            f'⛔ <b>Добавить в чёрный список</b>\n\nОтправьте Telegram ID пользователя:',
            reply_markup=back_kb(), parse_mode=ParseMode.HTML
        )
    except: pass
    await state.set_state(BlacklistState.waiting_id)
    await callback.answer()

@dp.message(BlacklistState.waiting_id)
async def process_bl_add(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        uid = int(message.text.strip())
        add_blacklist(uid)
        await state.clear()
        await message.answer(f'{EM_OK} ID <code>{uid}</code> добавлен в чёрный список.',
                             reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    except:
        await message.answer(f'{EM_ERR} Введите числовой ID.')

@dp.callback_query(F.data.startswith("bl_remove_"))
async def cb_bl_remove(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    uid = int(callback.data.replace("bl_remove_", ""))
    remove_blacklist(uid)
    await callback.answer(f"Удалён из ЧС: {uid}")
    await cb_blacklist(callback)

# ── Уведомления ───────────────────────────────────
@dp.callback_query(F.data == "menu_notify")
async def cb_notify(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    notif = get_setting('notify_deleted') == '1'
    try:
        await callback.message.edit_text(
            f'{EM_BELL} <b>Уведомления</b>\n\n'
            f'Уведомления об удалённых: <b>{"🟢 Вкл" if notif else "🔴 Выкл"}</b>',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"{'🟢 Включено' if notif else '🔴 Выключено'}",
                    callback_data="spy_notify_toggle2")],
                [InlineKeyboardButton(text="◁ Назад", callback_data="back_main")],
            ]), parse_mode=ParseMode.HTML
        )
    except: pass
    await callback.answer()

@dp.callback_query(F.data == "spy_notify_toggle2")
async def cb_notify_toggle2(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    new = toggle_setting('notify_deleted')
    await callback.answer(f"Уведомления {'вкл' if new=='1' else 'выкл'}")
    await cb_notify(callback)

# ── Прочие настройки ──────────────────────────────
@dp.callback_query(F.data == "menu_misc")
async def cb_misc(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer()
    auto = get_setting('auto_reply')
    try:
        await callback.message.edit_text(
            f'{EM_GEAR} <b>Прочие настройки</b>\n\n'
            f'Авто-ответ на первое сообщение:\n'
            f'<blockquote>{"Не задан" if not auto else auto[:200]}</blockquote>',
            reply_markup=misc_kb(), parse_mode=ParseMode.HTML
        )
    except: pass
    await callback.answer()

@dp.callback_query(F.data == "misc_autoreply")
async def cb_misc_autoreply(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return await callback.answer()
    auto = get_setting('auto_reply')
    try:
        await callback.message.edit_text(
            f'💬 <b>Авто-ответ на первое сообщение</b>\n\n'
            f'{"Текущий: <blockquote>" + auto + "</blockquote>" if auto else "Не задан"}\n\n'
            f'Отправьте текст авто-ответа (или <code>-</code> чтобы отключить):',
            reply_markup=back_kb(), parse_mode=ParseMode.HTML
        )
    except: pass
    await state.set_state(AutoReplyState.waiting_text)
    await callback.answer()

@dp.message(AutoReplyState.waiting_text)
async def process_autoreply(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    text = message.text.strip() if message.text else ''
    if text == '-':
        set_setting('auto_reply', '')
        await message.answer(f'{EM_OK} Авто-ответ отключён.', reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    else:
        set_setting('auto_reply', text)
        await message.answer(f'{EM_OK} Авто-ответ установлен.', reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    await state.clear()


# ==================== BUSINESS HANDLERS ====================

@dp.business_connection()
async def on_biz_connection(bc: types.BusinessConnection):
    try:
        if bc.is_enabled:
            business_connections[bc.id] = bc.user.id
            save_connections(business_connections)
            print(f"Бизнес-подключение: {bc.id} -> {bc.user.id}")
            # Уведомляем всех админов
            for aid in (ADMIN_ID, ADMIN_ID_2):
                try:
                    await bot.send_message(aid,
                        f'{EM_OK} <b>Бизнес-аккаунт подключён!</b>\n'
                        f'ID подключения: <code>{bc.id}</code>\n'
                        f'Пользователь: <code>{bc.user.id}</code>',
                        parse_mode=ParseMode.HTML)
                except: pass
        else:
            business_connections.pop(bc.id, None)
            save_connections(business_connections)
            print(f"Бизнес-подключение отключено: {bc.id}")
    except Exception as e:
        print(f"biz_connection error: {e}")


@dp.deleted_business_messages()
async def on_deleted_biz_msgs(event: types.BusinessMessagesDeleted):
    """Срабатывает когда сообщения удалены в бизнес-чате."""
    if get_setting('spy_enabled') != '1':
        return
    if get_setting('notify_deleted') != '1':
        return

    try:
        chat_id = event.chat.id
        for msg_id in event.message_ids:
            cached = get_cached_message(chat_id, msg_id)

            # Формируем текст уведомления
            if cached:
                u_id   = cached['user_id']
                u_name = f"@{cached['username']}" if cached['username'] else cached['first_name'] or '?'
                content= cached['text'] or cached['caption'] or ''
                ftype  = cached['file_type'] or ''
                fid    = cached['file_id']
                ts     = str(cached['timestamp'])[:16]

                header = (
                    f'{EM_DEL} <b>Удалено сообщение!</b>\n\n'
                    f'{EM_PERSON} <b>Кто:</b> {u_name}\n'
                    f'🆔 <b>ID:</b> <code>{u_id}</code>\n'
                    f'💬 <b>Чат:</b> <code>{chat_id}</code>\n'
                    f'🕓 <b>Когда написал:</b> {ts}\n\n'
                )

                if content:
                    header += f'<b>Текст:</b>\n<blockquote>{content[:500]}</blockquote>'

            else:
                header = (
                    f'{EM_DEL} <b>Удалено сообщение!</b>\n\n'
                    f'💬 <b>Чат:</b> <code>{chat_id}</code>\n'
                    f'🆔 <b>ID сообщения:</b> <code>{msg_id}</code>\n\n'
                    f'⚠️ Сообщение не было закешировано (логирование было выкл.)'
                )

            # Отправляем уведомление всем админам
            for aid in (ADMIN_ID, ADMIN_ID_2):
                try:
                    await bot.send_message(aid, header, parse_mode=ParseMode.HTML)
                    # Если есть медиа — пересылаем
                    if cached and fid and ftype:
                        cap = f'📎 Удалённый файл ({ftype})'
                        if ftype == 'photo':
                            await bot.send_photo(aid, fid, caption=cap)
                        elif ftype == 'video':
                            await bot.send_video(aid, fid, caption=cap)
                        elif ftype == 'document':
                            await bot.send_document(aid, fid, caption=cap)
                        elif ftype == 'voice':
                            await bot.send_voice(aid, fid, caption=cap)
                        elif ftype == 'sticker':
                            await bot.send_sticker(aid, fid)
                        elif ftype == 'video_note':
                            await bot.send_video_note(aid, fid)
                except Exception as e:
                    print(f"notify admin error: {e}")

    except Exception as e:
        print(f"on_deleted_biz_msgs error: {e}")
        import traceback; traceback.print_exc()


@dp.business_message()
async def on_biz_message(message: types.Message):
    """Все входящие бизнес-сообщения."""
    try:
        bc_id = message.business_connection_id
        if not bc_id:
            return

        if bc_id not in business_connections:
            business_connections[bc_id] = ADMIN_ID
            save_connections(business_connections)

        owner_id = business_connections[bc_id]

        # Кешируем сообщение (до проверки владельца)
        cache_message(message)

        # Если это сообщение от владельца — не отвечаем ИИ
        if message.from_user and message.from_user.id == owner_id:
            return

        user_id = message.from_user.id if message.from_user else 0

        # Авто-ответ на первое сообщение
        auto_reply = get_setting('auto_reply')
        if auto_reply:
            conn = sqlite3.connect(DB_PATH)
            c    = conn.cursor()
            c.execute('SELECT COUNT(*) FROM message_cache WHERE user_id=? AND chat_id=?',
                      (user_id, message.chat.id))
            count = c.fetchone()[0]
            conn.close()
            if count == 1:  # первое сообщение от этого юзера в этом чате
                await asyncio.sleep(random.uniform(1, 3))
                try:
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=auto_reply,
                        business_connection_id=bc_id,
                        reply_to_message_id=message.message_id
                    )
                except Exception as e:
                    print(f"auto_reply error: {e}")
                return

        # ИИ ответы
        if get_setting('ai_enabled') != '1':
            return
        if is_blacklisted(user_id):
            print(f"User {user_id} in blacklist, skip AI")
            return

        text = message.text or message.caption
        if not text:
            return

        await asyncio.sleep(random.uniform(1, 4))
        await send_ai_reply(message.chat.id, user_id, text, bc_id, message.message_id)

    except Exception as e:
        print(f"on_biz_message error: {e}")
        import traceback; traceback.print_exc()


# ── Обычные сообщения от админа ───────────────────
@dp.message()
async def on_admin_message(message: types.Message):
    if hasattr(message, 'business_connection_id') and message.business_connection_id:
        return
    if not is_admin(message.from_user.id):
        return
    if message.text and message.text.startswith('/'):
        return

    text = message.text or ''
    if not text:
        return

    response = await ask_groq(message.from_user.id, text)
    if response:
        await message.answer(response, parse_mode=ParseMode.HTML)


# ==================== ЗАПУСК ====================
async def main():
    global business_connections
    business_connections = load_connections()
    init_db()

    await bot.set_my_commands([
        types.BotCommand(command="start", description="Главное меню"),
        types.BotCommand(command="clear", description="Очистить AI память"),
    ])

    print("🤖 Business Monitor Bot запущен!")
    print(f"   Подключений загружено: {len(business_connections)}")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
