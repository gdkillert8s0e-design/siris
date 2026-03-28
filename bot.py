# ── SSL-патч для Windows (первая строка) ────────────────────────────────
import ssl as _ssl
_ssl._create_default_https_context = _ssl._create_unverified_context
# ─────────────────────────────────────────────────────────────────────────

import os, json, asyncio, sqlite3, re, random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
import aiohttp

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN    = "8738745683:AAGZF174_5exSVt55Ou4pVS54W8J1NpCL04"
GROQ_API_KEY = "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"
ADMIN_ID     = 5883796026
ADMIN_ID_2   = 1989613788
DB_PATH      = "biz_bot.db"
CONN_FILE    = "biz_conn.json"
# ====================================================

def is_admin(uid): return uid in (ADMIN_ID, ADMIN_ID_2)

bot     = Bot(token=BOT_TOKEN)
dp      = Dispatcher(storage=MemoryStorage())
biz_con = {}  # bc_id -> owner_user_id

# ── ID ПРЕМИУМ ЭМОДЗИ ──
EMOJI_ID = {
    'SETTINGS': '5870982283724328568',
    'PROFILE': '5870994129244131212',
    'USERS': '5870772616305839506',
    'FILE': '5870528606328852614',
    'STATS': '5870921681735781843',
    'HOME': '5873147866364514353',
    'LOCK': '6037249452824072506',
    'UNLOCK': '6037496202990194718',
    'MEGAPHONE': '6039422865189638057',
    'CHECK': '5870633910337015697',
    'CROSS': '5870657884844462243',
    'PENCIL': '5870676941614354370',
    'TRASH': '5870875489362513438',
    'INFO': '6028435952299413210',
    'BOT': '6030400221232501136',
    'EYE': '6037397706505195857',
    'EYE_HIDDEN': '6037243349675544634',
    'SEND': '5963103826075456248',
    'BELL': '6039486778597970865',
    'CLOCK': '5983150113483134607',
    'BACK': '6039519841256214245',
    'STAR': '6030425896546996257',
    'SPEECH': '5778208881301787450',
    'BLOCK': '5870675217193048938',
    'CHANNEL': '6039391078136681499',
    'ROBOT': '6030400221232501136',
    'MESSAGE': '5778208881301787450',
    'SMILE': '5870764288364252592',
    'WAVE': '6041921818896372382',
    'THUMB_UP': '6041720006973067267',
}

def tge(eid, fb=''): 
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

# Переменные для текстовых сообщений с премиум эмодзи
EM_OK    = tge(EMOJI_ID['CHECK'], '')
EM_ERR   = tge(EMOJI_ID['CROSS'], '')
EM_EYE   = tge(EMOJI_ID['EYE'], '')
EM_BOT   = tge(EMOJI_ID['BOT'], '')
EM_DEL   = tge(EMOJI_ID['TRASH'], '')
EM_STATS = tge(EMOJI_ID['STATS'], '')
EM_INFO  = tge(EMOJI_ID['INFO'], '')
EM_GEAR  = tge(EMOJI_ID['SETTINGS'], '')
EM_MSG   = tge(EMOJI_ID['SPEECH'], '')
EM_SEND  = tge(EMOJI_ID['SEND'], '')
EM_BL    = tge(EMOJI_ID['BLOCK'], '')
EM_CMD   = tge(EMOJI_ID['STAR'], '')
EM_USERS = tge(EMOJI_ID['USERS'], '')
EM_USER  = tge(EMOJI_ID['PROFILE'], '')
EM_LOCK  = tge(EMOJI_ID['LOCK'], '')
EM_UNLOCK = tge(EMOJI_ID['UNLOCK'], '')
EM_STAR  = tge(EMOJI_ID['STAR'], '')
EM_BELL  = tge(EMOJI_ID['BELL'], '')
EM_CLOCK = tge(EMOJI_ID['CLOCK'], '')
EM_CHECK = tge(EMOJI_ID['CHECK'], '')
EM_CROSS = tge(EMOJI_ID['CROSS'], '')
EM_PENCIL = tge(EMOJI_ID['PENCIL'], '')
EM_ARROW_LEFT = tge(EMOJI_ID['BACK'], '')
EM_ARROW_RIGHT = tge(EMOJI_ID['SEND'], '')
EM_WAVE = tge(EMOJI_ID['WAVE'], '')
EM_THUMB_UP = tge(EMOJI_ID['THUMB_UP'], '')

# ==================== КЛАВИАТУРЫ ====================

def main_kb():
    """Главная клавиатура с премиум эмодзи"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Настройки",
                callback_data='s_settings',
                icon_custom_emoji_id=EMOJI_ID['SETTINGS']
            ),
            InlineKeyboardButton(
                text="Слежка",
                callback_data='s_spy',
                icon_custom_emoji_id=EMOJI_ID['EYE']
            )
        ],
        [
            InlineKeyboardButton(
                text="Рассылка",
                callback_data='s_broadcast',
                icon_custom_emoji_id=EMOJI_ID['MEGAPHONE']
            ),
            InlineKeyboardButton(
                text="Чёрный список",
                callback_data='s_bl',
                icon_custom_emoji_id=EMOJI_ID['BLOCK']
            )
        ],
        [
            InlineKeyboardButton(
                text="Авто-ответ",
                callback_data='s_auto',
                icon_custom_emoji_id=EMOJI_ID['SPEECH']
            ),
            InlineKeyboardButton(
                text="Очистить память",
                callback_data='s_clearmem',
                icon_custom_emoji_id=EMOJI_ID['TRASH']
            )
        ],
    ])

def admin_kb():
    """Админская клавиатура с дополнительными функциями"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data='s_stats',
                icon_custom_emoji_id=EMOJI_ID['STATS']
            ),
            InlineKeyboardButton(
                text="👥 Пользователи",
                callback_data='s_users',
                icon_custom_emoji_id=EMOJI_ID['USERS']
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Главное меню",
                callback_data='back'
            )
        ]
    ])

def back_kb(cb='back'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=cb,
                icon_custom_emoji_id=EMOJI_ID['BACK']
            )
        ]
    ])

def settings_kb():
    ai_status = gs('ai_enabled') == '1'
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{'✅' if ai_status else '❌'} ИИ-ответы",
                callback_data='t_ai',
                icon_custom_emoji_id=EMOJI_ID['BOT']
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Изменить промпт",
                callback_data='t_prompt',
                icon_custom_emoji_id=EMOJI_ID['PENCIL']
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🤖 Модель: {gs('ai_model').split('-')[0]}",
                callback_data='t_model',
                icon_custom_emoji_id=EMOJI_ID['BOT']
            )
        ],
        [
            InlineKeyboardButton(
                text=f"💬 Reply-шанс: {gs('reply_chance')}%",
                callback_data='t_chance',
                icon_custom_emoji_id=EMOJI_ID['SPEECH']
            )
        ],
        [
            InlineKeyboardButton(
                text=f"⚡ Скорость: x{gs('typing_speed')}",
                callback_data='t_speed',
                icon_custom_emoji_id=EMOJI_ID['CLOCK']
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data='back',
                icon_custom_emoji_id=EMOJI_ID['BACK']
            )
        ]
    ])

def spy_kb():
    spy_on = gs('spy_enabled') == '1'
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{'👁️' if spy_on else '👁️‍🗨️'} Слежка за удалёнными",
                callback_data='t_spy',
                icon_custom_emoji_id=EMOJI_ID['EYE'] if spy_on else EMOJI_ID['EYE_HIDDEN']
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data='back',
                icon_custom_emoji_id=EMOJI_ID['BACK']
            )
        ]
    ])

def model_kb():
    models = [
        ('llama-3.3-70b-versatile', 'Llama 3.3 70B'),
        ('llama-3.1-8b-instant', 'Llama 3.1 8B'),
        ('mixtral-8x7b-32768', 'Mixtral 8x7B'),
        ('gemma2-9b-it', 'Gemma2 9B')
    ]
    cur = gs('ai_model')
    rows = []
    for v, l in models:
        rows.append([
            InlineKeyboardButton(
                text=f"{'✅ ' if v == cur else ''}{l}",
                callback_data=f'm_{v}',
                icon_custom_emoji_id=EMOJI_ID['BOT']
            )
        ])
    rows.append([
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data='s_settings',
            icon_custom_emoji_id=EMOJI_ID['BACK']
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def bl_kb():
    with db() as c:
        bl = c.execute('SELECT * FROM blacklist').fetchall()
    rows = []
    for r in bl:
        n = f"@{r['username']}" if r['username'] else str(r['user_id'])
        rows.append([
            InlineKeyboardButton(
                text=f"❌ {n}",
                callback_data=f'bl_rm_{r["user_id"]}',
                icon_custom_emoji_id=EMOJI_ID['CROSS']
            )
        ])
    rows.append([
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data='back',
            icon_custom_emoji_id=EMOJI_ID['BACK']
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ==================== FSM ====================
class SetPrompt(StatesGroup):
    waiting = State()
class SetAutoReply(StatesGroup):
    waiting = State()
class BroadcastState(StatesGroup):
    waiting = State()

# ==================== БД ====================
def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with db() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS msg_cache(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER, msg_id INTEGER, user_id INTEGER,
            username TEXT, first_name TEXT, text TEXT,
            file_id TEXT, file_type TEXT, caption TEXT, ts TEXT,
            UNIQUE(chat_id, msg_id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_stats(
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
            chat_id INTEGER, msg_count INTEGER DEFAULT 0, last_seen TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS blacklist(
            user_id INTEGER PRIMARY KEY, username TEXT, ts TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS ai_memory(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, role TEXT, content TEXT, ts TEXT)''')
        for k,v in {
            'ai_enabled':'1','spy_enabled':'1','notify_deleted':'1',
            'log_msgs':'1','ai_prompt':'Ты — профессиональный помощник бизнес-аккаунта. Отвечай вежливо и по делу.',
            'ai_model':'llama-3.3-70b-versatile','reply_chance':'30',
            'typing_speed':'1.0','auto_reply':'',
        }.items():
            c.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',(k,v))

def gs(key):
    with db() as c:
        r = c.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
        return r['value'] if r else ''

def ss(key, val):
    with db() as c:
        c.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',(key,val))

def toggle(key):
    cur = gs(key); new = '0' if cur=='1' else '1'
    ss(key, new); return new

def cache_msg(msg: types.Message):
    if gs('log_msgs') != '1': return
    u = msg.from_user
    fid=ftype=None
    if msg.photo:       fid,ftype = msg.photo[-1].file_id,'photo'
    elif msg.video:     fid,ftype = msg.video.file_id,'video'
    elif msg.document:  fid,ftype = msg.document.file_id,'document'
    elif msg.voice:     fid,ftype = msg.voice.file_id,'voice'
    elif msg.sticker:   fid,ftype = msg.sticker.file_id,'sticker'
    elif msg.video_note:fid,ftype = msg.video_note.file_id,'video_note'
    with db() as c:
        c.execute('''INSERT OR IGNORE INTO msg_cache
            (chat_id,msg_id,user_id,username,first_name,text,file_id,file_type,caption,ts)
            VALUES(?,?,?,?,?,?,?,?,?,?)''',
            (msg.chat.id, msg.message_id,
             u.id if u else 0, u.username if u else '', u.first_name if u else '',
             msg.text or '', fid, ftype, msg.caption or '', datetime.now().isoformat()))
        if u:
            c.execute('''INSERT INTO user_stats(user_id,username,first_name,chat_id,msg_count,last_seen)
                VALUES(?,?,?,?,1,?) ON CONFLICT(user_id) DO UPDATE SET
                msg_count=msg_count+1, last_seen=excluded.last_seen,
                username=excluded.username, first_name=excluded.first_name,
                chat_id=excluded.chat_id''',
                (u.id, u.username or '', u.first_name or '', msg.chat.id, datetime.now().isoformat()))

def get_cached(chat_id, msg_id):
    with db() as c:
        return c.execute('SELECT * FROM msg_cache WHERE chat_id=? AND msg_id=?',(chat_id,msg_id)).fetchone()

def is_blacklisted(uid):
    with db() as c:
        return c.execute('SELECT 1 FROM blacklist WHERE user_id=?',(uid,)).fetchone() is not None

def get_all_users():
    with db() as c:
        return c.execute('SELECT user_id,username,first_name,chat_id,msg_count FROM user_stats ORDER BY msg_count DESC').fetchall()

def get_stats():
    with db() as c:
        u  = c.execute('SELECT COUNT(*) FROM user_stats').fetchone()[0]
        m  = c.execute('SELECT COUNT(*) FROM msg_cache').fetchone()[0]
        bl = c.execute('SELECT COUNT(*) FROM blacklist').fetchone()[0]
        tm = c.execute('SELECT SUM(msg_count) FROM user_stats').fetchone()[0] or 0
    return u,m,bl,tm

def get_ai_history(uid, limit=10):
    with db() as c:
        rows = c.execute('''SELECT role,content FROM ai_memory
            WHERE user_id=? ORDER BY ts DESC LIMIT ?''',(uid,limit)).fetchall()
    return [{"role":r['role'],"content":r['content']} for r in reversed(rows)]

def save_ai_mem(uid, role, content):
    with db() as c:
        c.execute('INSERT INTO ai_memory(user_id,role,content,ts) VALUES(?,?,?,?)',
                  (uid,role,content,datetime.now().isoformat()))
        c.execute('''DELETE FROM ai_memory WHERE id NOT IN(
            SELECT id FROM ai_memory WHERE user_id=? ORDER BY ts DESC LIMIT 40
        ) AND user_id=?''',(uid,uid))

def clear_ai_mem_all():
    with db() as c:
        c.execute('DELETE FROM ai_memory')

def clear_ai_mem(uid):
    with db() as c:
        c.execute('DELETE FROM ai_memory WHERE user_id=?',(uid,))

# ==================== GROQ ====================
def clean(text):
    text = re.sub(r'```[\s\S]*?```','',text)
    text = re.sub(r'`[^`]+`','',text)
    for p,r in [(r'\*\*([^\*]+)\*\*',r'\1'),(r'__([^_]+)__',r'\1'),
                (r'\*([^\*]+)\*',r'\1'),(r'_([^_]+)_',r'\1'),(r'~~([^~]+)~~',r'\1')]:
        text = re.sub(p,r,text)
    return text.replace('*','').replace('_','').strip()

async def ask(uid, text, prompt_override=None, history_override=None):
    prompt  = prompt_override or gs('ai_prompt')
    model   = gs('ai_model') or 'llama-3.3-70b-versatile'
    history = history_override if history_override is not None else get_ai_history(uid)
    msgs    = [{"role":"system","content":prompt}] + history + [{"role":"user","content":text}]
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as s:
            async with s.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {GROQ_API_KEY}","Content-Type":"application/json"},
                json={"model":model,"messages":msgs,"temperature":0.7,"max_tokens":1024},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as r:
                if r.status == 200:
                    d     = await r.json()
                    reply = clean(d['choices'][0]['message']['content'])
                    if prompt_override is None:
                        save_ai_mem(uid,"user",text)
                        save_ai_mem(uid,"assistant",reply)
                    return reply
                else:
                    print(f"Groq {r.status}: {await r.text()}")
                    return None
    except Exception as e:
        print(f"Groq exception: {e}"); return None

def t_time(text):
    n = len(text)
    t = n*random.uniform(0.15,0.25) if n<=20 else n*random.uniform(0.25,0.4)
    return max(min(t/max(float(gs('typing_speed') or 1),0.1),12),1.0)

def split_msg(text):
    if '\n' in text:
        parts = [p.strip() for p in text.split('\n') if p.strip()]
        if len(parts) <= 2:
            return parts if random.random()<0.7 and len(parts)>1 else [text.strip()]
        out,i=[],0
        while i<len(parts):
            if random.random()<0.4 and i<len(parts)-1:
                out.append(parts[i]+'\n'+parts[i+1]); i+=2
            else:
                out.append(parts[i]); i+=1
        return out or [text]
    w=text.split(); wc=len(w)
    if wc<8:
        if random.random()<0.5 and wc>=4:
            m=wc//2; return [' '.join(w[:m]),' '.join(w[m:])]
        return [text]
    sents=re.split(r'(?<=[.!?])\s+',text)
    n=random.randint(2,min(4,max(2,len(sents)))); cs=max(1,len(sents)//n)
    return [' '.join(sents[i*cs:(i+1)*cs if i<n-1 else None]).strip() for i in range(n)
            if ' '.join(sents[i*cs:(i+1)*cs if i<n-1 else None]).strip()]

async def send_biz_reply(chat_id, user_id, text, bc_id, reply_to=None):
    response = await ask(user_id, text)
    if not response: return
    parts = split_msg(response)
    use_reply = reply_to and random.randint(1,100)<=int(gs('reply_chance') or 30)
    for idx,part in enumerate(parts):
        tt = t_time(part); iv = max(int(tt/4),1)
        for _ in range(iv):
            await asyncio.sleep(tt/iv)
            try: await bot.send_chat_action(chat_id=chat_id, action="typing", business_connection_id=bc_id)
            except: pass
        try:
            kw = {"chat_id":chat_id,"text":part,"business_connection_id":bc_id}
            if idx==0 and use_reply: kw["reply_to_message_id"]=reply_to
            await bot.send_message(**kw)
        except Exception as e: print(f"send_biz_reply err: {e}")
        if idx<len(parts)-1: await asyncio.sleep(random.uniform(0.5,2.0))

# ==================== КОМАНДНЫЙ ИИ ====================
COMMANDER_PROMPT = """Ты — командный ИИ для управления Telegram бизнес-ботом.
Пользователь пишет тебе команды на естественном языке. Твоя задача — понять что он хочет
и вернуть JSON с действием.

Доступные действия:
- {"action":"stats"} — показать статистику
- {"action":"users"} — список пользователей
- {"action":"broadcast","text":"..."} — разослать сообщение ВСЕМ пользователям из БД
- {"action":"ai_on"} — включить ИИ-ответы
- {"action":"ai_off"} — выключить ИИ-ответы
- {"action":"spy_on"} — включить слежку
- {"action":"spy_off"} — выключить слежку
- {"action":"blacklist_add","user_id":123} — добавить в чёрный список
- {"action":"blacklist_remove","user_id":123} — убрать из ЧС
- {"action":"blacklist_show"} — показать ЧС
- {"action":"set_prompt","text":"..."} — изменить промпт ИИ
- {"action":"clear_memory"} — очистить всю AI-память
- {"action":"menu"} — показать главное меню
- {"action":"chat","text":"..."} — просто поговорить / ответить на вопрос

Всегда возвращай ТОЛЬКО валидный JSON без пояснений и без markdown."""

async def execute_command(uid: int, text: str, message: types.Message):
    if not is_admin(uid):
        await message.answer(f"{EM_ERR} Доступ запрещён. Эта команда только для администраторов.", parse_mode=ParseMode.HTML)
        return
    
    result = await ask(uid, text, prompt_override=COMMANDER_PROMPT, history_override=[])
    if not result:
        await message.answer(f'{EM_ERR} ИИ не ответил.', parse_mode=ParseMode.HTML)
        return

    try:
        json_match = re.search(r'\{[\s\S]*\}', result)
        if not json_match:
            raise ValueError("no json")
        cmd = json.loads(json_match.group())
    except Exception:
        await message.answer(result, parse_mode=ParseMode.HTML)
        return

    action = cmd.get('action','chat')

    if action == 'stats':
        u,m,bl,tm = get_stats()
        rows = get_all_users()[:5]
        top = '\n'.join(f"  {i+1}. {'@'+r['username'] if r['username'] else r['first_name'] or str(r['user_id'])} — {r['msg_count']}"
                        for i,r in enumerate(rows))
        await message.answer(
            f'{EM_STATS} <b>Статистика</b>\n\n'
            f'👥 Пользователей: <b>{u}</b>\n'
            f'💬 Сообщений: <b>{m}</b>\n'
            f'⛔ В ЧС: <b>{bl}</b>\n'
            f'⭐️ Всего: <b>{tm}</b>\n\n'
            f'<b>Топ-5:</b>\n{top or "нет данных"}',
            reply_markup=back_kb(), parse_mode=ParseMode.HTML)

    elif action == 'users':
        rows = get_all_users()
        if not rows:
            await message.answer(f'{EM_INFO} Пользователей пока нет.', parse_mode=ParseMode.HTML)
            return
        lines = [f"• 👤 <code>{r['user_id']}</code> {'@'+r['username'] if r['username'] else r['first_name'] or '?'} — {r['msg_count']} сообщ."
                 for r in rows[:20]]
        await message.answer(
            f'👥 <b>Пользователи ({len(rows)})</b>\n\n'+'\n'.join(lines),
            reply_markup=back_kb(), parse_mode=ParseMode.HTML)

    elif action == 'broadcast':
        btext = cmd.get('text','')
        if not btext:
            await message.answer(f'{EM_ERR} Нет текста для рассылки.', parse_mode=ParseMode.HTML)
            return
        rows = get_all_users()
        if not rows:
            await message.answer(f'{EM_INFO} Нет пользователей для рассылки.', parse_mode=ParseMode.HTML)
            return
        status = await message.answer(f'{EM_SEND} Начинаю рассылку {len(rows)} пользователям...', parse_mode=ParseMode.HTML)
        ok=fail=0
        sent_chats = set()
        bc_id = next(iter(biz_con), None)
        for r in rows:
            chat_id = r['chat_id']
            if not chat_id or chat_id in sent_chats: continue
            sent_chats.add(chat_id)
            if not bc_id: continue
            try:
                await bot.send_message(chat_id=chat_id, text=btext, business_connection_id=bc_id)
                ok+=1; await asyncio.sleep(0.1)
            except Exception as e:
                fail+=1; print(f"broadcast err {chat_id}: {e}")
        await status.edit_text(
            f'{EM_OK} <b>Рассылка завершена!</b>\n\n✅ Отправлено: {ok}\n❌ Ошибок: {fail}',
            parse_mode=ParseMode.HTML)

    elif action == 'ai_on':
        ss('ai_enabled','1')
        await message.answer(f'{EM_OK} ИИ-ответы <b>включены</b>.', reply_markup=main_kb(), parse_mode=ParseMode.HTML)

    elif action == 'ai_off':
        ss('ai_enabled','0')
        await message.answer(f'{EM_ERR} ИИ-ответы <b>выключены</b>.', reply_markup=main_kb(), parse_mode=ParseMode.HTML)

    elif action == 'spy_on':
        ss('spy_enabled','1')
        await message.answer(f'{EM_EYE} Слежка <b>включена</b>.', reply_markup=main_kb(), parse_mode=ParseMode.HTML)

    elif action == 'spy_off':
        ss('spy_enabled','0')
        await message.answer(f'{EM_EYE} Слежка <b>выключена</b>.', reply_markup=main_kb(), parse_mode=ParseMode.HTML)

    elif action == 'blacklist_add':
        try:
            bid = int(cmd['user_id'])
            with db() as conn:
                conn.execute('INSERT OR IGNORE INTO blacklist VALUES(?,?,?)',(bid,'',datetime.now().isoformat()))
            await message.answer(f'{EM_OK} ID <code>{bid}</code> добавлен в ЧС.', parse_mode=ParseMode.HTML)
        except Exception as e:
            await message.answer(f'{EM_ERR} Ошибка: {e}', parse_mode=ParseMode.HTML)

    elif action == 'blacklist_remove':
        try:
            bid = int(cmd['user_id'])
            with db() as conn:
                conn.execute('DELETE FROM blacklist WHERE user_id=?',(bid,))
            await message.answer(f'{EM_OK} ID <code>{bid}</code> удалён из ЧС.', parse_mode=ParseMode.HTML)
        except Exception as e:
            await message.answer(f'{EM_ERR} Ошибка: {e}', parse_mode=ParseMode.HTML)

    elif action == 'blacklist_show':
        with db() as conn:
            bl = conn.execute('SELECT * FROM blacklist').fetchall()
        if not bl:
            await message.answer(f'{EM_BL} Чёрный список пуст.', parse_mode=ParseMode.HTML)
        else:
            lines = [f"• 👤 <code>{r['user_id']}</code> {'@'+r['username'] if r['username'] else ''}" for r in bl]
            await message.answer(f'⛔ <b>Чёрный список:</b>\n\n'+'\n'.join(lines), parse_mode=ParseMode.HTML)

    elif action == 'set_prompt':
        pt = cmd.get('text','')
        if pt:
            ss('ai_prompt', pt)
            await message.answer(f'{EM_OK} Промпт обновлён!\n\n<blockquote>{pt[:300]}</blockquote>', parse_mode=ParseMode.HTML)

    elif action == 'clear_memory':
        clear_ai_mem_all()
        await message.answer(f'{EM_OK} Вся AI-память очищена.', parse_mode=ParseMode.HTML)

    elif action == 'menu':
        await message.answer(
            f'⚙️ <b>Business Monitor Bot</b>\n\n'
            f'🤖 ИИ-ответы: <b>{"🟢 Вкл" if gs("ai_enabled")=="1" else "🔴 Выкл"}</b>\n'
            f'👁 Слежка: <b>{"🟢 Вкл" if gs("spy_enabled")=="1" else "🔴 Выкл"}</b>',
            reply_markup=main_kb(), parse_mode=ParseMode.HTML)

    else:
        chat_text = cmd.get('text', text)
        reply = await ask(uid, chat_text)
        if reply:
            await message.answer(reply, parse_mode=ParseMode.HTML)

# ==================== HANDLERS ====================

@dp.message(Command('start'))
async def cmd_start(msg: types.Message):
    """Приветственное сообщение с описанием бота (общедоступное)"""
    welcome_text = (
        f"{EM_BOT} <b>Business Monitor Bot</b>\n\n"
        f"{EM_WAVE} <b>Привет! Я бот для автоматизации бизнес-аккаунта Telegram.</b>\n\n"
        f"{EM_GEAR} <b>Мои возможности:</b>\n"
        f"• {EM_BOT} <b>ИИ-ответы</b> — автоматически отвечаю на сообщения клиентов с помощью ИИ\n"
        f"• {EM_EYE} <b>Слежка за удалёнными</b> — перехватываю и сохраняю удалённые сообщения\n"
        f"• {EM_SEND} <b>Рассылка</b> — массовая отправка сообщений всем пользователям\n"
        f"• {EM_BL} <b>Чёрный список</b> — блокировка нежелательных пользователей\n"
        f"• {EM_MSG} <b>Авто-ответ</b> — приветственное сообщение для новых клиентов\n"
        f"• {EM_TRASH} <b>AI-память</b> — сохранение контекста диалога для ИИ\n\n"
        f"{EM_INFO} <b>Как использовать:</b>\n"
        f"1️⃣ Подключите меня к бизнес-аккаунту Telegram\n"
        f"2️⃣ Настройте ИИ-ответы в разделе «Настройки»\n"
        f"3️⃣ Я буду автоматически отвечать на сообщения клиентов\n"
        f"4️⃣ Удалённые сообщения будут отправляться администраторам\n\n"
        f"{EM_THUMB_UP} <i>Используйте кнопки ниже для управления ботом</i>"
    )
    
    if is_admin(msg.from_user.id):
        await msg.answer(welcome_text, reply_markup=main_kb(), parse_mode=ParseMode.HTML)
    else:
        # Для обычных пользователей показываем только приветствие без кнопок админа
        await msg.answer(welcome_text, parse_mode=ParseMode.HTML)

@dp.message(Command('clear'))
async def cmd_clear(msg: types.Message):
    if not is_admin(msg.from_user.id):
        await msg.answer(f"{EM_ERR} Доступ запрещён. Эта команда только для администраторов.", parse_mode=ParseMode.HTML)
        return
    clear_ai_mem(msg.from_user.id)
    await msg.answer(f'{EM_OK} AI-память очищена.', parse_mode=ParseMode.HTML)

@dp.callback_query(F.data=='back')
async def cb_back(cb: types.CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    await state.clear()
    try:
        await cb.message.edit_text(
            f'⚙️ <b>Business Monitor Bot</b>\n\n'
            f'🤖 ИИ-ответы: <b>{"🟢 Вкл" if gs("ai_enabled")=="1" else "🔴 Выкл"}</b>\n'
            f'👁 Слежка: <b>{"🟢 Вкл" if gs("spy_enabled")=="1" else "🔴 Выкл"}</b>',
            reply_markup=main_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data=='s_settings')
async def cb_settings(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    try:
        await cb.message.edit_text(
            f'⚙️ <b>Настройки ИИ-ответов</b>\n\n'
            f'Статус: <b>{"🟢 Включено" if gs("ai_enabled")=="1" else "🔴 Выключено"}</b>\n'
            f'Модель: <code>{gs("ai_model")}</code>\n'
            f'Reply-шанс: <b>{gs("reply_chance")}%</b>\n'
            f'Скорость: <b>x{gs("typing_speed")}</b>',
            reply_markup=settings_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data=='s_stats')
async def cb_stats_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    u,m,bl,tm = get_stats()
    rows = get_all_users()[:5]
    top = '\n'.join(f"  {i+1}. {'@'+r['username'] if r['username'] else r['first_name'] or str(r['user_id'])} — {r['msg_count']}"
                    for i,r in enumerate(rows))
    try:
        await cb.message.edit_text(
            f'{EM_STATS} <b>Статистика</b>\n\n'
            f'👥 Пользователей: <b>{u}</b>\n'
            f'💬 Сообщений: <b>{m}</b>\n'
            f'⛔ В ЧС: <b>{bl}</b>\n'
            f'⭐️ Всего: <b>{tm}</b>\n\n'
            f'<b>Топ-5:</b>\n{top or "нет данных"}',
            reply_markup=admin_kb(), parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Stats error: {e}")
        await cb.message.answer(f'{EM_STATS} Статистика:\nПользователей: {u}\nСообщений: {m}\nЧС: {bl}\nВсего: {tm}')
    await cb.answer()

@dp.callback_query(F.data=='s_users')
async def cb_users_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    rows = get_all_users()
    lines = [f"• 👤 <code>{r['user_id']}</code> {'@'+r['username'] if r['username'] else r['first_name'] or '?'} — {r['msg_count']}"
             for r in rows[:20]]
    try:
        await cb.message.edit_text(
            f'👥 <b>Пользователи ({len(rows)})</b>\n\n' + ('\n'.join(lines) if lines else 'Нет данных'),
            reply_markup=admin_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data=='t_ai')
async def cb_t_ai(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    current = gs('ai_enabled')
    new = '0' if current == '1' else '1'
    ss('ai_enabled', new)
    
    if new == '1':
        await cb.answer('✅ ИИ-ответы включены!')
        await cb.message.answer(f'{EM_OK} <b>ИИ-ответы включены!</b>\nТеперь бот будет отвечать на сообщения собеседников.', parse_mode=ParseMode.HTML)
    else:
        await cb.answer('❌ ИИ-ответы выключены!')
        await cb.message.answer(f'{EM_ERR} <b>ИИ-ответы выключены!</b>\nБот больше не будет отвечать автоматически.', parse_mode=ParseMode.HTML)
    
    await cb_settings(cb)

@dp.callback_query(F.data=='t_prompt')
async def cb_t_prompt(cb: types.CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    cur = gs('ai_prompt')
    try:
        await cb.message.edit_text(
            f'✏️ <b>Изменение промпта</b>\n\n<b>Текущий:</b>\n<blockquote>{cur[:300]}</blockquote>\n\nОтправьте новый:',
            reply_markup=back_kb('s_settings'), parse_mode=ParseMode.HTML)
    except: pass
    await state.set_state(SetPrompt.waiting)
    await cb.answer()

@dp.message(SetPrompt.waiting)
async def proc_prompt(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    if msg.text:
        ss('ai_prompt', msg.text.strip())
        await state.clear()
        await msg.answer(f'{EM_OK} Промпт обновлён!', reply_markup=main_kb(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data=='t_model')
async def cb_t_model(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    try:
        await cb.message.edit_text(
            f'🤖 <b>Выберите модель:</b>',
            reply_markup=model_kb(),
            parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data.startswith('m_'))
async def cb_set_model(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    ss('ai_model', cb.data[2:])
    await cb.answer(f'Модель: {cb.data[2:].split("-")[0]}')
    await cb_settings(cb)

@dp.callback_query(F.data=='t_chance')
async def cb_chance(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    steps=[0,10,20,30,50,70,100]; cur=int(gs('reply_chance') or 30)
    idx=steps.index(cur) if cur in steps else 3
    new=steps[(idx+1)%len(steps)]; ss('reply_chance',str(new))
    await cb.answer(f'Reply-шанс: {new}%')
    await cb_settings(cb)

@dp.callback_query(F.data=='t_speed')
async def cb_speed(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    steps=[0.5,1.0,1.5,2.0,3.0]
    try: idx=steps.index(float(gs('typing_speed') or 1))
    except: idx=1
    new=steps[(idx+1)%len(steps)]; ss('typing_speed',str(new))
    await cb.answer(f'Скорость x{new}')
    await cb_settings(cb)

@dp.callback_query(F.data=='s_spy')
async def cb_spy(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    try:
        await cb.message.edit_text(
            f'{EM_EYE} <b>Слежка за удалёнными сообщениями</b>\n\n'
            f'Когда кто-то удаляет сообщение в диалоге — бот пришлёт его содержимое ТОЛЬКО администраторам.\n\n'
            f'Текущий статус: <b>{"🟢 Включена" if gs("spy_enabled")=="1" else "🔴 Выключена"}</b>',
            reply_markup=spy_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data=='t_spy')
async def cb_t_spy(cb):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    new = toggle('spy_enabled')
    status = "включена" if new == "1" else "выключена"
    await cb.answer(f'Слежка {status}')
    await cb_spy(cb)

@dp.callback_query(F.data=='s_broadcast')
async def cb_broadcast_start(cb: types.CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    rows=get_all_users()
    try:
        await cb.message.edit_text(
            f'{EM_SEND} <b>Рассылка</b>\n\nПользователей в базе: <b>{len(rows)}</b>\n\nОтправьте текст для рассылки:',
            reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await state.set_state(BroadcastState.waiting)
    await cb.answer()

@dp.message(BroadcastState.waiting)
async def proc_broadcast(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    text = msg.text or msg.caption or ''
    if not text: return
    await state.clear()
    rows=get_all_users()
    status=await msg.answer(f'{EM_SEND} Рассылаю {len(rows)} пользователям...', parse_mode=ParseMode.HTML)
    ok=fail=0; sent=set()
    bc_id = next(iter(biz_con), None)
    if not bc_id:
        await status.edit_text(f'{EM_ERR} Нет активного бизнес-подключения!', parse_mode=ParseMode.HTML)
        return
    
    for r in rows:
        chat_id=r['chat_id']
        if not chat_id or chat_id in sent: continue
        sent.add(chat_id)
        try:
            if msg.photo and msg.photo[-1].file_id:
                await bot.send_photo(chat_id, msg.photo[-1].file_id, caption=text, business_connection_id=bc_id)
            elif msg.video and msg.video.file_id:
                await bot.send_video(chat_id, msg.video.file_id, caption=text, business_connection_id=bc_id)
            elif msg.document and msg.document.file_id:
                await bot.send_document(chat_id, msg.document.file_id, caption=text, business_connection_id=bc_id)
            else:
                await bot.send_message(chat_id=chat_id, text=text, business_connection_id=bc_id)
            ok+=1; await asyncio.sleep(0.08)
        except Exception as e:
            fail+=1; print(f"broadcast {chat_id}: {e}")
    await status.edit_text(
        f'{EM_OK} <b>Рассылка завершена!</b>\n✅ Отправлено: {ok}\n❌ Ошибок: {fail}',
        reply_markup=main_kb(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data=='s_auto')
async def cb_auto(cb: types.CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    auto=gs('auto_reply')
    text_msg = f'{EM_MSG} <b>Авто-ответ на первое сообщение</b>\n\n'
    if auto:
        text_msg += f'Текущий:\n<blockquote>{auto}</blockquote>\n\n'
    else:
        text_msg += f'Не задан.\n\n'
    text_msg += f'Отправьте текст (или <code>-</code> чтобы выключить):'
    try:
        await cb.message.edit_text(
            text_msg,
            reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await state.set_state(SetAutoReply.waiting)
    await cb.answer()

@dp.message(SetAutoReply.waiting)
async def proc_auto(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    t=msg.text.strip() if msg.text else ''
    ss('auto_reply','' if t=='-' else t)
    await state.clear()
    await msg.answer(f'{EM_OK} {"Авто-ответ выключен" if t=="-" else "Авто-ответ установлен"}.', reply_markup=main_kb(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data=='s_bl')
async def cb_bl(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    with db() as c:
        bl=c.execute('SELECT COUNT(*) FROM blacklist').fetchone()[0]
    try:
        await cb.message.edit_text(
            f'⛔ <b>Чёрный список</b>\nВсего: <b>{bl}</b>\n\nНажмите на пользователя чтобы удалить.',
            reply_markup=bl_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data.startswith('bl_rm_'))
async def cb_bl_rm(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    uid=int(cb.data.replace('bl_rm_',''))
    with db() as c: c.execute('DELETE FROM blacklist WHERE user_id=?',(uid,))
    await cb.answer(f'Удалён: {uid}')
    await cb_bl(cb)

@dp.callback_query(F.data=='s_clearmem')
async def cb_clearmem(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Доступ запрещён", show_alert=True)
        return
    clear_ai_mem_all()
    await cb.answer('AI-память очищена!')
    try:
        await cb.message.edit_text(
            f'{EM_OK} <b>AI-память очищена!</b>',
            reply_markup=main_kb(), parse_mode=ParseMode.HTML)
    except: pass

@dp.message()
async def on_admin_msg(msg: types.Message, state: FSMContext):
    if hasattr(msg,'business_connection_id') and msg.business_connection_id: return
    if not is_admin(msg.from_user.id): return
    if msg.text and msg.text.startswith('/'): return
    current_state = await state.get_state()
    if current_state: return
    text = msg.text or ''
    if not text: return
    await execute_command(msg.from_user.id, text, msg)

# ==================== BUSINESS HANDLERS ====================

@dp.business_connection()
async def on_biz_conn(bc: types.BusinessConnection):
    """Обработка подключения бизнес-аккаунта"""
    try:
        if bc.is_enabled:
            biz_con[bc.id] = bc.user.id
            save_connections(biz_con)
            print(f"Бизнес-подключение: {bc.id} -> {bc.user.id}")
            # Уведомляем только администраторов
            for aid in (ADMIN_ID, ADMIN_ID_2):
                try:
                    await bot.send_message(aid,
                        f'{EM_OK} <b>Бизнес подключён!</b>\nID: <code>{bc.id}</code>',
                        parse_mode=ParseMode.HTML)
                except: pass
        else:
            biz_con.pop(bc.id, None)
            save_connections(biz_con)
    except Exception as e:
        print(f"biz_conn err: {e}")

@dp.deleted_business_messages()
async def on_deleted(event: types.BusinessMessagesDeleted):
    """Уведомление только администраторов о удалённых сообщениях"""
    if gs('spy_enabled') != '1': return
    try:
        for msg_id in event.message_ids:
            cached = get_cached(event.chat.id, msg_id)
            if cached:
                u_id   = cached['user_id']
                u_name = f"@{cached['username']}" if cached['username'] else (cached['first_name'] or '?')
                content= cached['text'] or cached['caption'] or ''
                ftype  = cached['file_type'] or ''
                fid    = cached['file_id']
                ts     = str(cached['ts'])[:16]
                text   = (
                    f'{EM_DEL} <b>Удалено сообщение!</b>\n\n'
                    f'👤 <b>Кто:</b> {u_name}\n'
                    f'🆔 <b>User ID:</b> <code>{u_id}</code>\n'
                    f'💬 <b>Чат:</b> <code>{event.chat.id}</code>\n'
                    f'⏰ <b>Время:</b> {ts}\n'
                )
                if content:
                    text += f'\n<b>Текст:</b>\n<blockquote>{content[:800]}</blockquote>'
            else:
                text = (
                    f'{EM_DEL} <b>Удалено сообщение!</b>\n\n'
                    f'💬 Чат: <code>{event.chat.id}</code>\n'
                    f'🆔 Msg ID: <code>{msg_id}</code>\n\n'
                    f'⚠️ Сообщение не закешировано'
                )
                cached = None; fid = None; ftype = ''

            # Отправляем уведомление ТОЛЬКО администраторам
            for aid in (ADMIN_ID, ADMIN_ID_2):
                try:
                    await bot.send_message(aid, text, parse_mode=ParseMode.HTML)
                    if cached and fid and ftype:
                        cap = f'📎 Удалённый {ftype}'
                        if ftype=='photo':      await bot.send_photo(aid,fid,caption=cap)
                        elif ftype=='video':    await bot.send_video(aid,fid,caption=cap)
                        elif ftype=='document': await bot.send_document(aid,fid,caption=cap)
                        elif ftype=='voice':    await bot.send_voice(aid,fid,caption=cap)
                        elif ftype=='sticker':  await bot.send_sticker(aid,fid)
                        elif ftype=='video_note': await bot.send_video_note(aid,fid)
                except Exception as e:
                    print(f"notify {aid} err: {e}")
    except Exception as e:
        print(f"on_deleted err: {e}")
        import traceback; traceback.print_exc()

@dp.business_message()
async def on_biz_msg(msg: types.Message):
    """Обработка бизнес-сообщений"""
    try:
        bc_id = msg.business_connection_id
        if not bc_id: return
        
        if bc_id not in biz_con:
            biz_con[bc_id] = ADMIN_ID
            save_connections(biz_con)
        owner_id = biz_con[bc_id]

        # Кешируем все сообщения
        cache_msg(msg)

        # НЕ ОТВЕЧАЕМ НА СВОИ СООБЩЕНИЯ
        if msg.from_user and msg.from_user.id == owner_id:
            print(f"Пропускаем сообщение от владельца: {owner_id}")
            return

        uid = msg.from_user.id if msg.from_user else 0
        text = msg.text or msg.caption or ''

        # Авто-ответ на первое сообщение
        auto = gs('auto_reply')
        if auto and uid:
            with db() as c:
                cnt = c.execute('SELECT COUNT(*) FROM msg_cache WHERE user_id=? AND chat_id=?',
                              (uid, msg.chat.id)).fetchone()[0]
            if cnt == 1:
                await asyncio.sleep(random.uniform(1, 3))
                try:
                    await bot.send_message(chat_id=msg.chat.id, text=auto,
                                           business_connection_id=bc_id,
                                           reply_to_message_id=msg.message_id)
                    print(f"Отправлен авто-ответ пользователю {uid}")
                except Exception as e:
                    print(f"auto_reply err: {e}")
                return

        # ИИ-ответы только если включены
        if gs('ai_enabled') != '1':
            print("ИИ-ответы выключены")
            return
            
        if not text:
            return
            
        if uid and is_blacklisted(uid):
            print(f"User {uid} в ЧС, пропускаем")
            return

        print(f"Отвечаем пользователю {uid}: {text[:50]}...")
        await asyncio.sleep(random.uniform(1, 4))
        await send_biz_reply(msg.chat.id, uid, text, bc_id, msg.message_id)

    except Exception as e:
        print(f"on_biz_msg err: {e}")
        import traceback; traceback.print_exc()

# ==================== ЗАПУСК ====================
def load_connections():
    if os.path.exists(CONN_FILE):
        try:
            with open(CONN_FILE,'r',encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def save_connections(d):
    with open(CONN_FILE,'w',encoding='utf-8') as f: json.dump(d,f,ensure_ascii=False,indent=2)

async def main():
    global biz_con
    biz_con = load_connections()
    init_db()
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Главное меню"),
        types.BotCommand(command="clear", description="Очистить AI-память"),
    ])
    print(f"🤖 Business Bot запущен! Подключений: {len(biz_con)}")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
