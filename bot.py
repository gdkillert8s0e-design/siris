# ── SSL-патч для Windows (первая строка) ────────────────────────────────
import ssl as _ssl
_ssl._create_default_https_context = _ssl._create_unverified_context
# ─────────────────────────────────────────────────────────────────────────

import os, json, asyncio, sqlite3, re, random, string
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
import aiohttp

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8738745683:AAGZF174_5exSVt55Ou4pVS54W8J1NpCL04"
DB_PATH = "biz_bot.db"
CONN_FILE = "biz_conn.json"
# ====================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
biz_con = {}  # bc_id -> owner_user_id

# ── ID ПРЕМИУМ ЭМОДЗИ ──
EMOJI_ID = {
    'SETTINGS': '5870982283724328568',
    'USERS': '5870772616305839506',
    'STATS': '5870921681735781843',
    'CHECK': '5870633910337015697',
    'CROSS': '5870657884844462243',
    'TRASH': '5870875489362513438',
    'INFO': '6028435952299413210',
    'BOT': '6030400221232501136',
    'EYE': '6037397706505195857',
    'SEND': '5963103826075456248',
    'BELL': '6039486778597970865',
    'CLOCK': '5983150113483134607',
    'BACK': '6039519841256214245',
    'STAR': '6030425896546996257',
    'SPEECH': '5778208881301787450',
    'BLOCK': '5870675217193048938',
    'MEGAPHONE': '6039422865189638057',
    'PENCIL': '5870676941614354370',
    'GIFT': '6032644646587338669',
    'WAVE': '6041921818896372382',
    'THUMB_UP': '6041720006973067267',
    'QUESTION': '6030848053177486888',
    'HEART': '6037533152593842454',
    'FIRE': '5920515922505765329',
    'MONEY': '5904462880941545555',
    'CALENDAR': '5890937706803894250',
    'TIME': '5983150113483134607',
    'LINK': '5769289093221454192',
    'DOCUMENT': '5870528606328852614',
    'FOLDER': '5870528606328852614',
    'PHOTO': '6035128606563241721',
    'VIDEO': '6039391078136681499',
    'MUSIC': '6037364759811068375',
    'GAME': '5938413566624272793',
    'CODE': '5940433880585605708',
    'LOADING': '5345906554510012647',
}

def tge(eid, fb=''): 
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

# Переменные для текста с премиум эмодзи
EM_OK = tge(EMOJI_ID['CHECK'], '')
EM_ERR = tge(EMOJI_ID['CROSS'], '')
EM_EYE = tge(EMOJI_ID['EYE'], '')
EM_BOT = tge(EMOJI_ID['BOT'], '')
EM_DEL = tge(EMOJI_ID['TRASH'], '')
EM_STATS = tge(EMOJI_ID['STATS'], '')
EM_INFO = tge(EMOJI_ID['INFO'], '')
EM_GEAR = tge(EMOJI_ID['SETTINGS'], '')
EM_MSG = tge(EMOJI_ID['SPEECH'], '')
EM_SEND = tge(EMOJI_ID['SEND'], '')
EM_BL = tge(EMOJI_ID['BLOCK'], '')
EM_STAR = tge(EMOJI_ID['STAR'], '')
EM_BELL = tge(EMOJI_ID['BELL'], '')
EM_CLOCK = tge(EMOJI_ID['CLOCK'], '')
EM_ARROW = tge(EMOJI_ID['BACK'], '')
EM_WAVE = tge(EMOJI_ID['WAVE'], '')
EM_THUMB = tge(EMOJI_ID['THUMB_UP'], '')
EM_QUESTION = tge(EMOJI_ID['QUESTION'], '')
EM_HEART = tge(EMOJI_ID['HEART'], '')
EM_FIRE = tge(EMOJI_ID['FIRE'], '')
EM_MONEY = tge(EMOJI_ID['MONEY'], '')
EM_CALENDAR = tge(EMOJI_ID['CALENDAR'], '')
EM_TIME = tge(EMOJI_ID['TIME'], '')
EM_LINK = tge(EMOJI_ID['LINK'], '')
EM_FILE = tge(EMOJI_ID['DOCUMENT'], '')
EM_PHOTO = tge(EMOJI_ID['PHOTO'], '')
EM_VIDEO = tge(EMOJI_ID['VIDEO'], '')
EM_MUSIC = tge(EMOJI_ID['MUSIC'], '')
EM_GAME = tge(EMOJI_ID['GAME'], '')
EM_CODE = tge(EMOJI_ID['CODE'], '')
EM_LOADING = tge(EMOJI_ID['LOADING'], '')

# ==================== FSM ====================
class AddToBlacklist(StatesGroup):
    waiting = State()
class RemoveFromBlacklist(StatesGroup):
    waiting = State()
class BroadcastState(StatesGroup):
    waiting = State()
class SetAutoReply(StatesGroup):
    waiting = State()
class SetWelcomeMessage(StatesGroup):
    waiting = State()
class SetSpyMode(StatesGroup):
    waiting = State()
class SetTypingSpeed(StatesGroup):
    waiting = State()

# ==================== БД ====================
def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with db() as c:
        # Настройки владельцев
        c.execute('''CREATE TABLE IF NOT EXISTS settings(
            owner_id INTEGER PRIMARY KEY,
            spy_enabled INTEGER DEFAULT 1,
            log_msgs INTEGER DEFAULT 1,
            auto_reply TEXT DEFAULT '',
            welcome_message TEXT DEFAULT '',
            typing_speed REAL DEFAULT 1.0,
            reply_chance INTEGER DEFAULT 30
        )''')
        
        # Кэш сообщений
        c.execute('''CREATE TABLE IF NOT EXISTS msg_cache(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            chat_id INTEGER, msg_id INTEGER, user_id INTEGER,
            username TEXT, first_name TEXT, text TEXT,
            file_id TEXT, file_type TEXT, caption TEXT, ts TEXT,
            UNIQUE(owner_id, chat_id, msg_id))''')
        
        # Статистика пользователей
        c.execute('''CREATE TABLE IF NOT EXISTS user_stats(
            owner_id INTEGER,
            user_id INTEGER,
            username TEXT, first_name TEXT,
            chat_id INTEGER, msg_count INTEGER DEFAULT 0,
            first_seen TEXT, last_seen TEXT,
            PRIMARY KEY(owner_id, user_id))''')
        
        # Чёрный список
        c.execute('''CREATE TABLE IF NOT EXISTS blacklist(
            owner_id INTEGER,
            user_id INTEGER,
            username TEXT,
            reason TEXT,
            ts TEXT,
            PRIMARY KEY(owner_id, user_id))''')
        
        # Белый список (доверенные пользователи)
        c.execute('''CREATE TABLE IF NOT EXISTS whitelist(
            owner_id INTEGER,
            user_id INTEGER,
            username TEXT,
            note TEXT,
            ts TEXT,
            PRIMARY KEY(owner_id, user_id))''')
        
        # Заметки о пользователях
        c.execute('''CREATE TABLE IF NOT EXISTS user_notes(
            owner_id INTEGER,
            user_id INTEGER,
            note TEXT,
            ts TEXT,
            PRIMARY KEY(owner_id, user_id))''')
        
        # Статистика по дням
        c.execute('''CREATE TABLE IF NOT EXISTS daily_stats(
            owner_id INTEGER,
            date TEXT,
            messages INTEGER DEFAULT 0,
            users INTEGER DEFAULT 0,
            PRIMARY KEY(owner_id, date))''')
        
        # Логи действий
        c.execute('''CREATE TABLE IF NOT EXISTS action_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            action TEXT,
            user_id INTEGER,
            details TEXT,
            ts TEXT)''')

def get_setting(owner_id, key):
    with db() as c:
        r = c.execute(f'SELECT {key} FROM settings WHERE owner_id=?', (owner_id,)).fetchone()
        if r:
            return r[0]
        # Дефолтные значения
        defaults = {
            'spy_enabled': 1,
            'log_msgs': 1,
            'auto_reply': '',
            'welcome_message': '',
            'typing_speed': 1.0,
            'reply_chance': 30,
        }
        return defaults.get(key, '')

def update_setting(owner_id, key, value):
    with db() as c:
        c.execute(f'''INSERT INTO settings(owner_id, {key}) 
                    VALUES(?, ?) 
                    ON CONFLICT(owner_id) DO UPDATE SET {key}=excluded.{key}''',
                  (owner_id, value))

def log_action(owner_id, action, user_id=None, details=''):
    with db() as c:
        c.execute('INSERT INTO action_log(owner_id, action, user_id, details, ts) VALUES(?,?,?,?,?)',
                  (owner_id, action, user_id, details, datetime.now().isoformat()))

def cache_msg(owner_id, msg: types.Message):
    if not get_setting(owner_id, 'log_msgs'):
        return
    u = msg.from_user
    fid = ftype = None
    if msg.photo: fid, ftype = msg.photo[-1].file_id, 'photo'
    elif msg.video: fid, ftype = msg.video.file_id, 'video'
    elif msg.document: fid, ftype = msg.document.file_id, 'document'
    elif msg.voice: fid, ftype = msg.voice.file_id, 'voice'
    elif msg.sticker: fid, ftype = msg.sticker.file_id, 'sticker'
    
    with db() as c:
        c.execute('''INSERT OR IGNORE INTO msg_cache
            (owner_id, chat_id, msg_id, user_id, username, first_name, text, file_id, file_type, caption, ts)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
            (owner_id, msg.chat.id, msg.message_id,
             u.id if u else 0, u.username if u else '', u.first_name if u else '',
             msg.text or '', fid, ftype, msg.caption or '', datetime.now().isoformat()))
        
        if u:
            now = datetime.now().isoformat()
            c.execute('''INSERT INTO user_stats(owner_id, user_id, username, first_name, chat_id, msg_count, first_seen, last_seen)
                VALUES(?,?,?,?,?,1,?,?) ON CONFLICT(owner_id, user_id) DO UPDATE SET
                msg_count=msg_count+1, last_seen=excluded.last_seen,
                username=excluded.username, first_name=excluded.first_name,
                chat_id=excluded.chat_id''',
                (owner_id, u.id, u.username or '', u.first_name or '', msg.chat.id, now, now))
            
            # Обновляем дневную статистику
            today = datetime.now().strftime('%Y-%m-%d')
            c.execute('''INSERT INTO daily_stats(owner_id, date, messages, users)
                VALUES(?,?,1,1) ON CONFLICT(owner_id, date) DO UPDATE SET
                messages=messages+1, users=users+1''',
                (owner_id, today))

def get_cached(owner_id, chat_id, msg_id):
    with db() as c:
        return c.execute('SELECT * FROM msg_cache WHERE owner_id=? AND chat_id=? AND msg_id=?',
                        (owner_id, chat_id, msg_id)).fetchone()

def is_blacklisted(owner_id, uid):
    with db() as c:
        return c.execute('SELECT 1 FROM blacklist WHERE owner_id=? AND user_id=?', (owner_id, uid)).fetchone() is not None

def is_whitelisted(owner_id, uid):
    with db() as c:
        return c.execute('SELECT 1 FROM whitelist WHERE owner_id=? AND user_id=?', (owner_id, uid)).fetchone() is not None

def get_all_users(owner_id):
    with db() as c:
        return c.execute('SELECT user_id, username, first_name, chat_id, msg_count, first_seen, last_seen FROM user_stats WHERE owner_id=? ORDER BY msg_count DESC', (owner_id,)).fetchall()

def get_stats(owner_id):
    with db() as c:
        u = c.execute('SELECT COUNT(*) FROM user_stats WHERE owner_id=?', (owner_id,)).fetchone()[0]
        m = c.execute('SELECT COUNT(*) FROM msg_cache WHERE owner_id=?', (owner_id,)).fetchone()[0]
        bl = c.execute('SELECT COUNT(*) FROM blacklist WHERE owner_id=?', (owner_id,)).fetchone()[0]
        wl = c.execute('SELECT COUNT(*) FROM whitelist WHERE owner_id=?', (owner_id,)).fetchone()[0]
        tm = c.execute('SELECT SUM(msg_count) FROM user_stats WHERE owner_id=?', (owner_id,)).fetchone()[0] or 0
    return u, m, bl, wl, tm

def get_today_stats(owner_id):
    today = datetime.now().strftime('%Y-%m-%d')
    with db() as c:
        r = c.execute('SELECT messages, users FROM daily_stats WHERE owner_id=? AND date=?', (owner_id, today)).fetchone()
        if r:
            return r['messages'], r['users']
    return 0, 0

def add_to_blacklist(owner_id, user_id, username, reason=''):
    with db() as c:
        c.execute('INSERT OR REPLACE INTO blacklist(owner_id, user_id, username, reason, ts) VALUES(?,?,?,?,?)',
                  (owner_id, user_id, username, reason, datetime.now().isoformat()))
    log_action(owner_id, 'blacklist_add', user_id, reason)

def remove_from_blacklist(owner_id, user_id):
    with db() as c:
        c.execute('DELETE FROM blacklist WHERE owner_id=? AND user_id=?', (owner_id, user_id))
    log_action(owner_id, 'blacklist_remove', user_id)

def add_to_whitelist(owner_id, user_id, username, note=''):
    with db() as c:
        c.execute('INSERT OR REPLACE INTO whitelist(owner_id, user_id, username, note, ts) VALUES(?,?,?,?,?)',
                  (owner_id, user_id, username, note, datetime.now().isoformat()))
    log_action(owner_id, 'whitelist_add', user_id, note)

def remove_from_whitelist(owner_id, user_id):
    with db() as c:
        c.execute('DELETE FROM whitelist WHERE owner_id=? AND user_id=?', (owner_id, user_id))
    log_action(owner_id, 'whitelist_remove', user_id)

def add_user_note(owner_id, user_id, note):
    with db() as c:
        c.execute('INSERT OR REPLACE INTO user_notes(owner_id, user_id, note, ts) VALUES(?,?,?,?)',
                  (owner_id, user_id, note, datetime.now().isoformat()))
    log_action(owner_id, 'add_note', user_id, note)

def get_user_note(owner_id, user_id):
    with db() as c:
        r = c.execute('SELECT note FROM user_notes WHERE owner_id=? AND user_id=?', (owner_id, user_id)).fetchone()
        return r['note'] if r else ''

def get_blacklist(owner_id):
    with db() as c:
        return c.execute('SELECT user_id, username, reason, ts FROM blacklist WHERE owner_id=? ORDER BY ts DESC', (owner_id,)).fetchall()

def get_whitelist(owner_id):
    with db() as c:
        return c.execute('SELECT user_id, username, note, ts FROM whitelist WHERE owner_id=? ORDER BY ts DESC', (owner_id,)).fetchall()

def get_top_users(owner_id, limit=10):
    with db() as c:
        return c.execute('SELECT user_id, username, first_name, msg_count FROM user_stats WHERE owner_id=? ORDER BY msg_count DESC LIMIT ?', (owner_id, limit)).fetchall()

def get_recent_users(owner_id, limit=10):
    with db() as c:
        return c.execute('SELECT user_id, username, first_name, last_seen FROM user_stats WHERE owner_id=? ORDER BY last_seen DESC LIMIT ?', (owner_id, limit)).fetchall()

# ==================== КЛАВИАТУРЫ ====================

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data='stats'),
            InlineKeyboardButton(text="👥 Пользователи", callback_data='users')
        ],
        [
            InlineKeyboardButton(text="⛔ Чёрный список", callback_data='blacklist'),
            InlineKeyboardButton(text="✅ Белый список", callback_data='whitelist')
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data='settings'),
            InlineKeyboardButton(text="📢 Рассылка", callback_data='broadcast')
        ],
        [
            InlineKeyboardButton(text="📝 Заметки о пользователях", callback_data='notes'),
            InlineKeyboardButton(text="📈 Активность", callback_data='activity')
        ],
        [
            InlineKeyboardButton(text="🔍 Поиск пользователя", callback_data='search'),
            InlineKeyboardButton(text="🗑 Очистить кэш", callback_data='clear_cache')
        ],
        [
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data='help')
        ]
    ])

def back_kb(cb='back'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=cb, icon_custom_emoji_id=EMOJI_ID['BACK'])]
    ])

def settings_kb(owner_id):
    spy = "✅" if get_setting(owner_id, 'spy_enabled') else "❌"
    log = "✅" if get_setting(owner_id, 'log_msgs') else "❌"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{spy} Слежка", callback_data='toggle_spy')],
        [InlineKeyboardButton(text=f"{log} Логирование", callback_data='toggle_log')],
        [InlineKeyboardButton(text="💬 Авто-ответ", callback_data='set_auto_reply')],
        [InlineKeyboardButton(text="👋 Приветствие", callback_data='set_welcome')],
        [InlineKeyboardButton(text=f"⚡ Скорость печати: x{get_setting(owner_id, 'typing_speed')}", callback_data='set_speed')],
        [InlineKeyboardButton(text="◀️ Назад", callback_data='back')]
    ])

def user_menu_kb(user_id, username):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Добавить заметку", callback_data=f'note_add_{user_id}'),
            InlineKeyboardButton(text="⛔ В ЧС", callback_data=f'bl_add_{user_id}')
        ],
        [
            InlineKeyboardButton(text="✅ В белый список", callback_data=f'wl_add_{user_id}'),
            InlineKeyboardButton(text="📊 Статистика", callback_data=f'user_stats_{user_id}')
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data='users')]
    ])

# ==================== HANDLERS ====================

@dp.message(Command('start'))
async def cmd_start(msg: types.Message):
    welcome_text = (
        f"{EM_BOT} <b>Business Monitor Bot</b>\n\n"
        f"{EM_WAVE} <b>Привет! Я бот для мониторинга бизнес-аккаунта Telegram</b>\n\n"
        f"{EM_STAR} <b>Мои возможности:</b>\n"
        f"• {EM_EYE} <b>Слежка</b> — перехват удалённых сообщений\n"
        f"• {EM_BL} <b>Чёрный список</b> — блокировка по ID или username\n"
        f"• {EM_HEART} <b>Белый список</b> — доверенные пользователи\n"
        f"• {EM_MSG} <b>Авто-ответ</b> — приветствие для новых\n"
        f"• {EM_STATS} <b>Статистика</b> — аналитика активности\n"
        f"• {EM_PHOTO} <b>Заметки</b> — пометки о пользователях\n"
        f"• {EM_MUSIC} <b>Активность</b> — графики и отчёты\n\n"
        f"{EM_THUMB} <i>Используйте кнопки ниже для управления</i>"
    )
    await msg.answer(welcome_text, reply_markup=main_kb(), parse_mode=ParseMode.HTML)

# ==================== ОСНОВНЫЕ ФУНКЦИИ ====================

@dp.callback_query(F.data == 'stats')
async def show_stats(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    u, m, bl, wl, tm = get_stats(owner_id)
    today_msgs, today_users = get_today_stats(owner_id)
    top = get_top_users(owner_id, 5)
    
    top_text = '\n'.join([f"{i+1}. {r['username'] or r['first_name'] or r['user_id']} — {r['msg_count']} сообщ."
                          for i, r in enumerate(top)]) or "нет данных"
    
    await cb.message.edit_text(
        f"{EM_STATS} <b>Статистика</b>\n\n"
        f"{EM_USERS} Всего пользователей: <b>{u}</b>\n"
        f"{EM_MSG} Всего сообщений: <b>{m}</b>\n"
        f"{EM_BL} В чёрном списке: <b>{bl}</b>\n"
        f"{EM_HEART} В белом списке: <b>{wl}</b>\n"
        f"{EM_STAR} Всего сообщений: <b>{tm}</b>\n\n"
        f"{EM_CALENDAR} <b>Сегодня:</b>\n"
        f"• Сообщений: {today_msgs}\n"
        f"• Новых пользователей: {today_users}\n\n"
        f"{EM_FIRE} <b>Топ-5 активных:</b>\n{top_text}",
        reply_markup=back_kb(),
        parse_mode=ParseMode.HTML
    )
    await cb.answer()

@dp.callback_query(F.data == 'users')
async def show_users(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    users = get_all_users(owner_id)
    
    if not users:
        await cb.message.edit_text(
            f"{EM_INFO} Пользователей пока нет.",
            reply_markup=back_kb(),
            parse_mode=ParseMode.HTML
        )
        await cb.answer()
        return
    
    lines = []
    for u in users[:15]:
        name = u['username'] or u['first_name'] or str(u['user_id'])
        lines.append(f"• <code>{u['user_id']}</code> {name} — {u['msg_count']} сообщ.")
    
    text = f"{EM_USERS} <b>Пользователи ({len(users)})</b>\n\n" + '\n'.join(lines)
    if len(users) > 15:
        text += f"\n\n<i>и ещё {len(users) - 15} пользователей...</i>"
    
    # Добавляем кнопки для поиска
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск по ID/username", callback_data='search_user')],
        [InlineKeyboardButton(text="◀️ Назад", callback_data='back')]
    ])
    
    await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await cb.answer()

@dp.callback_query(F.data == 'search_user')
async def search_user_start(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.edit_text(
        f"{EM_QUESTION} <b>Поиск пользователя</b>\n\n"
        f"Введите ID или username пользователя для поиска:",
        reply_markup=back_kb(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(AddToBlacklist.waiting)
    await cb.answer()

@dp.message(AddToBlacklist.waiting)
async def search_user_result(msg: types.Message, state: FSMContext):
    owner_id = msg.from_user.id
    query = msg.text.strip()
    
    # Пробуем найти пользователя
    with db() as c:
        if query.isdigit():
            user = c.execute('SELECT * FROM user_stats WHERE owner_id=? AND user_id=?', (owner_id, int(query))).fetchone()
        else:
            user = c.execute('SELECT * FROM user_stats WHERE owner_id=? AND username=?', (owner_id, query.replace('@', ''))).fetchone()
    
    if user:
        note = get_user_note(owner_id, user['user_id'])
        await msg.answer(
            f"{EM_USER} <b>Пользователь найден</b>\n\n"
            f"🆔 ID: <code>{user['user_id']}</code>\n"
            f"👤 Имя: {user['first_name'] or '?'}\n"
            f"🔖 Username: @{user['username'] or 'нет'}\n"
            f"💬 Сообщений: {user['msg_count']}\n"
            f"📅 Первое появление: {user['first_seen'][:16] if user['first_seen'] else '?'}\n"
            f"🕐 Последний раз: {user['last_seen'][:16] if user['last_seen'] else '?'}\n\n"
            f"📝 Заметка: {note or 'нет'}",
            reply_markup=user_menu_kb(user['user_id'], user['username']),
            parse_mode=ParseMode.HTML
        )
    else:
        await msg.answer(
            f"{EM_ERR} Пользователь не найден в базе.",
            reply_markup=back_kb(),
            parse_mode=ParseMode.HTML
        )
    
    await state.clear()

@dp.callback_query(F.data == 'blacklist')
async def show_blacklist(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    bl = get_blacklist(owner_id)
    
    if not bl:
        await cb.message.edit_text(
            f"{EM_BL} <b>Чёрный список пуст</b>\n\n"
            f"Добавить пользователя можно командой:\n"
            f"<code>/block @username</code> или <code>/block 123456789</code>",
            reply_markup=back_kb(),
            parse_mode=ParseMode.HTML
        )
    else:
        lines = []
        for r in bl:
            name = r['username'] or str(r['user_id'])
            reason = f" — {r['reason']}" if r['reason'] else ""
            lines.append(f"• <code>{r['user_id']}</code> {name}{reason}")
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить в ЧС", callback_data='add_to_bl')],
            [InlineKeyboardButton(text="◀️ Назад", callback_data='back')]
        ])
        
        await cb.message.edit_text(
            f"{EM_BL} <b>Чёрный список ({len(bl)})</b>\n\n" + '\n'.join(lines[:20]),
            reply_markup=kb,
            parse_mode=ParseMode.HTML
        )
    await cb.answer()

@dp.callback_query(F.data == 'add_to_bl')
async def add_to_bl_start(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.edit_text(
        f"{EM_BL} <b>Добавление в чёрный список</b>\n\n"
        f"Введите ID или @username пользователя:\n"
        f"<i>Можно добавить причину через пробел</i>\n\n"
        f"Пример: <code>@username спам</code>\n"
        f"Пример: <code>123456789 оскорбления</code>",
        reply_markup=back_kb(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(AddToBlacklist.waiting)
    await cb.answer()

@dp.message(AddToBlacklist.waiting)
async def add_to_bl_process(msg: types.Message, state: FSMContext):
    owner_id = msg.from_user.id
    text = msg.text.strip()
    
    # Парсим ID и причину
    parts = text.split(' ', 1)
    user_input = parts[0]
    reason = parts[1] if len(parts) > 1 else ''
    
    # Извлекаем user_id
    user_id = None
    username = None
    if user_input.isdigit():
        user_id = int(user_input)
    elif user_input.startswith('@'):
        username = user_input[1:]
    
    if user_id:
        # Проверяем, есть ли пользователь в базе
        with db() as c:
            user = c.execute('SELECT username FROM user_stats WHERE owner_id=? AND user_id=?', (owner_id, user_id)).fetchone()
            if user:
                username = user['username']
        
        add_to_blacklist(owner_id, user_id, username or str(user_id), reason)
        await msg.answer(
            f"{EM_OK} Пользователь <code>{user_id}</code> добавлен в чёрный список.\n"
            f"Причина: {reason or 'не указана'}",
            reply_markup=back_kb(),
            parse_mode=ParseMode.HTML
        )
    elif username:
        # Ищем пользователя по username
        with db() as c:
            user = c.execute('SELECT user_id FROM user_stats WHERE owner_id=? AND username=?', (owner_id, username)).fetchone()
            if user:
                user_id = user['user_id']
                add_to_blacklist(owner_id, user_id, username, reason)
                await msg.answer(
                    f"{EM_OK} Пользователь @{username} добавлен в чёрный список.\n"
                    f"Причина: {reason or 'не указана'}",
                    reply_markup=back_kb(),
                    parse_mode=ParseMode.HTML
                )
            else:
                await msg.answer(
                    f"{EM_ERR} Пользователь @{username} не найден в базе.\n"
                    f"Он должен написать хотя бы одно сообщение.",
                    reply_markup=back_kb(),
                    parse_mode=ParseMode.HTML
                )
    else:
        await msg.answer(
            f"{EM_ERR} Неверный формат. Используйте ID или @username.",
            reply_markup=back_kb(),
            parse_mode=ParseMode.HTML
        )
    
    await state.clear()

@dp.callback_query(F.data == 'whitelist')
async def show_whitelist(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    wl = get_whitelist(owner_id)
    
    if not wl:
        await cb.message.edit_text(
            f"{EM_HEART} <b>Белый список пуст</b>\n\n"
            f"Доверенные пользователи не блокируются и получают приоритет.",
            reply_markup=back_kb(),
            parse_mode=ParseMode.HTML
        )
    else:
        lines = []
        for r in wl:
            name = r['username'] or str(r['user_id'])
            note = f" — {r['note']}" if r['note'] else ""
            lines.append(f"• <code>{r['user_id']}</code> {name}{note}")
        
        await cb.message.edit_text(
            f"{EM_HEART} <b>Белый список ({len(wl)})</b>\n\n" + '\n'.join(lines[:20]),
            reply_markup=back_kb(),
            parse_mode=ParseMode.HTML
        )
    await cb.answer()

@dp.callback_query(F.data == 'notes')
async def show_notes_menu(cb: types.CallbackQuery):
    await cb.message.edit_text(
        f"{EM_FILE} <b>Заметки о пользователях</b>\n\n"
        f"Выберите действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Добавить/изменить заметку", callback_data='add_note')],
            [InlineKeyboardButton(text="🔍 Поиск по заметкам", callback_data='search_notes')],
            [InlineKeyboardButton(text="◀️ Назад", callback_data='back')]
        ]),
        parse_mode=ParseMode.HTML
    )
    await cb.answer()

@dp.callback_query(F.data == 'activity')
async def show_activity(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    recent = get_recent_users(owner_id, 10)
    top = get_top_users(owner_id, 10)
    
    recent_text = '\n'.join([f"• {r['username'] or r['first_name'] or r['user_id']} — {r['last_seen'][:16] if r['last_seen'] else '?'}"
                              for r in recent]) or "нет данных"
    
    top_text = '\n'.join([f"• {r['username'] or r['first_name'] or r['user_id']} — {r['msg_count']} сообщ."
                          for r in top]) or "нет данных"
    
    await cb.message.edit_text(
        f"{EM_FIRE} <b>Активность пользователей</b>\n\n"
        f"{EM_TIME} <b>Последние активные:</b>\n{recent_text}\n\n"
        f"{EM_STAR} <b>Топ по сообщениям:</b>\n{top_text}",
        reply_markup=back_kb(),
        parse_mode=ParseMode.HTML
    )
    await cb.answer()

@dp.callback_query(F.data == 'settings')
async def show_settings(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    await cb.message.edit_text(
        f"{EM_GEAR} <b>Настройки бота</b>\n\n"
        f"Выберите параметр для настройки:",
        reply_markup=settings_kb(owner_id),
        parse_mode=ParseMode.HTML
    )
    await cb.answer()

@dp.callback_query(F.data == 'toggle_spy')
async def toggle_spy(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    current = get_setting(owner_id, 'spy_enabled')
    new = 0 if current else 1
    update_setting(owner_id, 'spy_enabled', new)
    await cb.answer(f"Слежка {'включена' if new else 'выключена'}")
    await show_settings(cb)

@dp.callback_query(F.data == 'toggle_log')
async def toggle_log(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    current = get_setting(owner_id, 'log_msgs')
    new = 0 if current else 1
    update_setting(owner_id, 'log_msgs', new)
    await cb.answer(f"Логирование {'включено' if new else 'выключено'}")
    await show_settings(cb)

@dp.callback_query(F.data == 'set_auto_reply')
async def set_auto_reply_start(cb: types.CallbackQuery, state: FSMContext):
    owner_id = cb.from_user.id
    current = get_setting(owner_id, 'auto_reply')
    
    await cb.message.edit_text(
        f"{EM_MSG} <b>Авто-ответ</b>\n\n"
        f"Текущий авто-ответ:\n<blockquote>{current or 'не задан'}</blockquote>\n\n"
        f"Отправьте новый текст (или <code>-</code> чтобы выключить):",
        reply_markup=back_kb(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(SetAutoReply.waiting)
    await cb.answer()

@dp.message(SetAutoReply.waiting)
async def process_auto_reply(msg: types.Message, state: FSMContext):
    owner_id = msg.from_user.id
    text = msg.text.strip()
    new_value = '' if text == '-' else text
    update_setting(owner_id, 'auto_reply', new_value)
    await state.clear()
    await msg.answer(
        f"{EM_OK} Авто-ответ {'выключен' if text=='-' else 'установлен'}.",
        reply_markup=main_kb(),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(F.data == 'set_welcome')
async def set_welcome_start(cb: types.CallbackQuery, state: FSMContext):
    owner_id = cb.from_user.id
    current = get_setting(owner_id, 'welcome_message')
    
    await cb.message.edit_text(
        f"{EM_WAVE} <b>Приветственное сообщение</b>\n\n"
        f"Текущее приветствие:\n<blockquote>{current or 'не задано'}</blockquote>\n\n"
        f"Отправьте новый текст (или <code>-</code> чтобы выключить):",
        reply_markup=back_kb(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(SetWelcomeMessage.waiting)
    await cb.answer()

@dp.message(SetWelcomeMessage.waiting)
async def process_welcome(msg: types.Message, state: FSMContext):
    owner_id = msg.from_user.id
    text = msg.text.strip()
    new_value = '' if text == '-' else text
    update_setting(owner_id, 'welcome_message', new_value)
    await state.clear()
    await msg.answer(
        f"{EM_OK} Приветствие {'выключено' if text=='-' else 'установлено'}.",
        reply_markup=main_kb(),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(F.data == 'set_speed')
async def set_speed_start(cb: types.CallbackQuery, state: FSMContext):
    owner_id = cb.from_user.id
    current = get_setting(owner_id, 'typing_speed')
    
    await cb.message.edit_text(
        f"{EM_CLOCK} <b>Скорость печати</b>\n\n"
        f"Текущая скорость: <b>x{current}</b>\n\n"
        f"Выберите скорость:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🐢 Медленно (x0.5)", callback_data='speed_0.5')],
            [InlineKeyboardButton(text="👌 Нормально (x1.0)", callback_data='speed_1.0')],
            [InlineKeyboardButton(text="⚡ Быстро (x1.5)", callback_data='speed_1.5')],
            [InlineKeyboardButton(text="🚀 Очень быстро (x2.0)", callback_data='speed_2.0')],
            [InlineKeyboardButton(text="💨 Максимум (x3.0)", callback_data='speed_3.0')],
            [InlineKeyboardButton(text="◀️ Назад", callback_data='settings')]
        ]),
        parse_mode=ParseMode.HTML
    )
    await cb.answer()

@dp.callback_query(F.data.startswith('speed_'))
async def set_speed(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    speed = float(cb.data.split('_')[1])
    update_setting(owner_id, 'typing_speed', speed)
    await cb.answer(f"Скорость x{speed}")
    await show_settings(cb)

@dp.callback_query(F.data == 'broadcast')
async def broadcast_start(cb: types.CallbackQuery, state: FSMContext):
    owner_id = cb.from_user.id
    users = get_all_users(owner_id)
    
    await cb.message.edit_text(
        f"{EM_SEND} <b>Рассылка</b>\n\n"
        f"Пользователей: <b>{len(users)}</b>\n\n"
        f"Отправьте текст для рассылки (можно с фото/видео):",
        reply_markup=back_kb(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(BroadcastState.waiting)
    await cb.answer()

@dp.message(BroadcastState.waiting)
async def process_broadcast(msg: types.Message, state: FSMContext):
    owner_id = msg.from_user.id
    text = msg.text or msg.caption or ''
    if not text and not msg.photo and not msg.video and not msg.document:
        return
    
    await state.clear()
    users = get_all_users(owner_id)
    status = await msg.answer(f"{EM_SEND} Рассылаю {len(users)} пользователям...")
    
    ok = fail = 0
    sent = set()
    bc_id = next(iter(biz_con), None)
    
    if not bc_id:
        await status.edit_text(f"{EM_ERR} Нет активного бизнес-подключения!")
        return
    
    for u in users:
        chat_id = u['chat_id']
        if not chat_id or chat_id in sent:
            continue
        sent.add(chat_id)
        try:
            if msg.photo:
                await bot.send_photo(chat_id, msg.photo[-1].file_id, caption=text, business_connection_id=bc_id)
            elif msg.video:
                await bot.send_video(chat_id, msg.video.file_id, caption=text, business_connection_id=bc_id)
            elif msg.document:
                await bot.send_document(chat_id, msg.document.file_id, caption=text, business_connection_id=bc_id)
            else:
                await bot.send_message(chat_id=chat_id, text=text, business_connection_id=bc_id)
            ok += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            fail += 1
            print(f"broadcast err {chat_id}: {e}")
    
    await status.edit_text(
        f"{EM_OK} <b>Рассылка завершена!</b>\n✅ Отправлено: {ok}\n❌ Ошибок: {fail}",
        reply_markup=main_kb(),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(F.data == 'clear_cache')
async def clear_cache(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    with db() as c:
        c.execute('DELETE FROM msg_cache WHERE owner_id=?', (owner_id,))
        c.execute('DELETE FROM user_stats WHERE owner_id=?', (owner_id,))
    
    await cb.message.edit_text(
        f"{EM_OK} <b>Кэш очищен!</b>\n\n"
        f"Все сохранённые сообщения и статистика удалены.",
        reply_markup=back_kb(),
        parse_mode=ParseMode.HTML
    )
    await cb.answer()

@dp.callback_query(F.data == 'help')
async def show_help(cb: types.CallbackQuery):
    help_text = (
        f"{EM_INFO} <b>Помощь по боту</b>\n\n"
        f"<b>📊 Статистика</b> — общая статистика активности\n"
        f"<b>👥 Пользователи</b> — список всех пользователей\n"
        f"<b>⛔ Чёрный список</b> — блокировка нежелательных\n"
        f"<b>✅ Белый список</b> — доверенные пользователи\n"
        f"<b>📝 Заметки</b> — пометки о пользователях\n"
        f"<b>📈 Активность</b> — последние активные и топ\n"
        f"<b>⚙️ Настройки</b> — настройка бота\n"
        f"<b>📢 Рассылка</b> — массовая отправка\n\n"
        f"<b>🔍 Поиск пользователя</b> — по ID или username\n"
        f"<b>🗑 Очистить кэш</b> — удалить историю\n\n"
        f"<b>Команды:</b>\n"
        f"/start — Главное меню\n"
        f"/block @username [причина] — Добавить в ЧС\n"
        f"/unblock @username — Удалить из ЧС\n"
        f"/stats — Показать статистику"
    )
    
    await cb.message.edit_text(help_text, reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    await cb.answer()

@dp.callback_query(F.data == 'back')
async def back_to_main(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    welcome_text = (
        f"{EM_BOT} <b>Business Monitor Bot</b>\n\n"
        f"{EM_WAVE} <b>Главное меню</b>\n\n"
        f"Выберите действие:"
    )
    await cb.message.edit_text(welcome_text, reply_markup=main_kb(), parse_mode=ParseMode.HTML)
    await cb.answer()

# ==================== BUSINESS HANDLERS ====================

@dp.business_connection()
async def on_biz_conn(bc: types.BusinessConnection):
    try:
        if bc.is_enabled:
            biz_con[bc.id] = bc.user.id
            save_connections(biz_con)
            print(f"Бизнес-подключение: {bc.id} -> {bc.user.id}")
            await bot.send_message(bc.user.id, 
                f"{EM_OK} <b>Бизнес аккаунт подключён!</b>\n\n"
                f"Бот готов к работе. Используйте /start для настройки.",
                parse_mode=ParseMode.HTML)
        else:
            biz_con.pop(bc.id, None)
            save_connections(biz_con)
    except Exception as e:
        print(f"biz_conn err: {e}")

@dp.deleted_business_messages()
async def on_deleted(event: types.BusinessMessagesDeleted):
    for bc_id, owner_id in biz_con.items():
        if not get_setting(owner_id, 'spy_enabled'):
            continue
        
        for msg_id in event.message_ids:
            cached = get_cached(owner_id, event.chat.id, msg_id)
            if cached:
                u_name = f"@{cached['username']}" if cached['username'] else (cached['first_name'] or '?')
                content = cached['text'] or cached['caption'] or ''
                
                text = (
                    f"{EM_DEL} <b>Удалено сообщение!</b>\n\n"
                    f"👤 <b>Кто:</b> {u_name}\n"
                    f"🆔 <b>ID:</b> <code>{cached['user_id']}</code>\n"
                    f"💬 <b>Чат:</b> <code>{event.chat.id}</code>\n"
                    f"⏰ <b>Время:</b> {cached['ts'][:16] if cached['ts'] else '?'}\n"
                )
                if content:
                    text += f"\n<b>Текст:</b>\n<blockquote>{content[:500]}</blockquote>"
                
                try:
                    await bot.send_message(owner_id, text, parse_mode=ParseMode.HTML)
                except Exception as e:
                    print(f"notify err: {e}")

@dp.business_message()
async def on_biz_msg(msg: types.Message):
    try:
        bc_id = msg.business_connection_id
        if not bc_id or bc_id not in biz_con:
            return
        
        owner_id = biz_con[bc_id]
        
        # Кешируем сообщение
        cache_msg(owner_id, msg)
        
        # Пропускаем сообщения от владельца
        if msg.from_user and msg.from_user.id == owner_id:
            return
        
        uid = msg.from_user.id if msg.from_user else 0
        
        # Проверяем чёрный список
        if is_blacklisted(owner_id, uid):
            print(f"User {uid} в чёрном списке")
            return
        
        text = msg.text or msg.caption or ''
        
        # Приветствие для нового пользователя
        with db() as c:
            cnt = c.execute('SELECT COUNT(*) FROM msg_cache WHERE owner_id=? AND user_id=?', (owner_id, uid)).fetchone()[0]
        
        if cnt == 1:
            welcome = get_setting(owner_id, 'welcome_message')
            if welcome:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                try:
                    await bot.send_message(chat_id=msg.chat.id, text=welcome,
                                           business_connection_id=bc_id,
                                           reply_to_message_id=msg.message_id)
                except Exception as e:
                    print(f"welcome err: {e}")
                return
        
        # Авто-ответ
        auto_reply = get_setting(owner_id, 'auto_reply')
        if auto_reply and cnt == 1:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            try:
                await bot.send_message(chat_id=msg.chat.id, text=auto_reply,
                                       business_connection_id=bc_id,
                                       reply_to_message_id=msg.message_id)
            except Exception as e:
                print(f"auto_reply err: {e}")
        
    except Exception as e:
        print(f"on_biz_msg err: {e}")

@dp.message(Command('block'))
async def block_user(msg: types.Message):
    owner_id = msg.from_user.id
    if owner_id not in biz_con.values():
        await msg.answer("❌ Бот не подключён к бизнес-аккаунту")
        return
    
    args = msg.text.split(' ', 1)
    if len(args) < 2:
        await msg.answer("❌ Использование: /block @username [причина]")
        return
    
    user_input = args[0].replace('/block', '').strip()
    reason = args[1] if len(args) > 1 else ''
    
    if user_input.isdigit():
        user_id = int(user_input)
        add_to_blacklist(owner_id, user_id, str(user_id), reason)
        await msg.answer(f"✅ Пользователь {user_id} добавлен в ЧС")
    elif user_input.startswith('@'):
        username = user_input[1:]
        with db() as c:
            user = c.execute('SELECT user_id FROM user_stats WHERE owner_id=? AND username=?', (owner_id, username)).fetchone()
            if user:
                add_to_blacklist(owner_id, user['user_id'], username, reason)
                await msg.answer(f"✅ Пользователь @{username} добавлен в ЧС")
            else:
                await msg.answer(f"❌ Пользователь @{username} не найден")
    else:
        await msg.answer("❌ Неверный формат. Используйте ID или @username")

@dp.message(Command('unblock'))
async def unblock_user(msg: types.Message):
    owner_id = msg.from_user.id
    if owner_id not in biz_con.values():
        await msg.answer("❌ Бот не подключён к бизнес-аккаунту")
        return
    
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("❌ Использование: /unblock @username")
        return
    
    user_input = args[1]
    
    if user_input.isdigit():
        user_id = int(user_input)
        remove_from_blacklist(owner_id, user_id)
        await msg.answer(f"✅ Пользователь {user_id} удалён из ЧС")
    elif user_input.startswith('@'):
        username = user_input[1:]
        with db() as c:
            user = c.execute('SELECT user_id FROM blacklist WHERE owner_id=? AND username=?', (owner_id, username)).fetchone()
            if user:
                remove_from_blacklist(owner_id, user['user_id'])
                await msg.answer(f"✅ Пользователь @{username} удалён из ЧС")
            else:
                await msg.answer(f"❌ Пользователь @{username} не в ЧС")
    else:
        await msg.answer("❌ Неверный формат")

# ==================== ЗАПУСК ====================
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

async def main():
    global biz_con
    biz_con = load_connections()
    init_db()
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Главное меню"),
        types.BotCommand(command="block", description="Добавить в чёрный список"),
        types.BotCommand(command="unblock", description="Удалить из чёрного списка"),
    ])
    print(f"🤖 Business Bot запущен! Подключений: {len(biz_con)}")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
