# ── SSL-патч для Windows (первая строка) ────────────────────────────────
import ssl as _ssl
_ssl._create_default_https_context = _ssl._create_unverified_context
# ─────────────────────────────────────────────────────────────────────────

import os, json, asyncio, sqlite3, re, random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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

# ── ВСЕ ПРЕМИУМ ЭМОДЗИ ──
EMOJI = {
    # Основные
    'OK': '5870633910337015697', 'ERR': '5870657884844462243', 'EYE': '6037397706505195857',
    'BOT': '6030400221232501136', 'DEL': '6039522349517115015', 'STATS': '5870921681735781843',
    'INFO': '6028435952299413210', 'GEAR': '6032742198179532882', 'MSG': '5778208881301787450',
    'SEND': '5963103826075456248', 'BL': '5870675217193048938', 'CMD': '6032949275732742941',
    
    # Стрелки
    'ARROW_RIGHT': '6037622221625626773', 'ARROW_LEFT': '6039519841256214245',
    'ARROW_UP': '6028205772117118673', 'ARROW_DOWN': '6037157012242960559',
    'ARROW_UP_SEND': '6039573425268201570', 'ARROW_DOWN_IN': '5963087934696459905',
    
    # Замки
    'LOCK_OPEN': '6037496202990194718', 'LOCK_CLOSED': '6037249452824072506',
    'LOCK_CLOSED_2': '5778570255555105942',
    
    # Люди
    'USER': '6032994772321309200', 'USERS': '6033125983572201397',
    'SPEAKING': '6032653721853234759', 'WAVE': '6041921818896372382',
    'THUMB_UP': '6041720006973067267', 'THUMB_DOWN': '6041716699848249286',
    'CLAP': '5994417835630137549', 'POINT_UP': '5884106131822875141',
    
    # Эмодзи реакций
    'SMILE': '6039587087559168309', 'THINK': '6043960760130868895',
    'ANGRY': '6044118213631938928', 'SAD': '6042029429301973188',
    'HEART': '6037533152593842454', 'STAR': '6030425896546996257',
    
    # Медиа
    'PHOTO': '5767117162619605573', 'VIDEO': '6039391078136681499',
    'DOCUMENT': '6034969813032374911', 'FOLDER': '6037475557082403885',
    'CLIP': '5776138384942567185', 'PICTURE': '6030466823290360017',
    
    # Инструменты
    'WRENCH': '5962952497197748583', 'HAMMER': '6039729023343400390',
    'SCISSORS': '5771880672192893347', 'PENCIL': '6039779802741739617',
    'KEYBOARD': '6039404727542747508', 'MAGNIFY': '6032850693348399258',
    
    # Разное
    'BELL': '6039486778597970865', 'BELL_OFF': '6039569594157371705',
    'SPEAKER': '6039381989985882045', 'MUTE': '6039505337151655702',
    'CALENDAR': '5890937706803894250', 'CLOCK': '6037268453759389862',
    'GIFT': '6037175527846975726', 'BOMB': '5920515922505765329',
    'CROSS': '6030757850274336631', 'CHECK': '6030839471832829491',
    'PLUS': '6032924188828767321', 'QUESTION': '6030848053177486888',
    'EXCLAMATION': '6030563507299160824', 'INFO_SQUARE': '6028435952299413210',
    
    # Компьютер/Телефон
    'TV': '6044356915029348425', 'PHONE': '6039605143601680423',
    'COMPUTER': '5942734685976138521', 'KEYBOARD_2': '5767262289564536912',
    
    # Книги/Документы
    'BOOK': '6037286673010660132', 'NOTE': '5778299625370817409',
    'NEWSPAPER': '5895519358871932592', 'CHART': '5938539885907415367',
    
    # Погода/Природа
    'SUN': '5938525265838739643', 'MOON': '5769143090103193926',
    'CLOUD': '6028115612163641653', 'CYCLONE': '6050588788021793070',
    'DROP': '6050632433479455053',
    
    # Еда
    'BURGER': '6041874690220233085', 'APPLE': '5775870512127283512',
    'CAKE': '5922305158636639117', 'COIN': '5778613750688911681',
    'MONEY': '5904359114531675993', 'DIAMOND': '6037083366438737901',
    
    # Игры/Развлечения
    'GAME': '5938413566624272793', 'FILM': '5944777041709633960',
    'MICROPHONE': '6030722571412967168', 'MUSIC': '6037364759811068375',
    'MASK': '6032625495328165724', 'MAGIC': '6021792097454002931',
    
    # Транспорт
    'AIRPLANE': '6028346797368283073', 'HOUSE': '6042137469204303531',
    'DOOR': '6035130900075777681',
    
    # Спорт
    'SOCCER': '6042069608721027027', 'MEDAL': '6037428784888549034',
    
    # Медицина
    'PILL': '6050677620830376838', 'BRAIN': '5864019342873598613',
    
    # Разное 2
    'WIFI': '6048723247501938454', 'INFINITY': '6048407885233263063',
    'SPONGE': '5811966564039135541', 'BRUSH': '6050679691004612757',
    'LABEL': '6039565797406282001', 'PIN': '6042011682497106307',
}

def tge(eid, fb=''): return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

# Создаем переменные для удобного использования
EM_OK    = tge(EMOJI['CHECK'], '✅')
EM_ERR   = tge(EMOJI['CROSS'], '❌')
EM_EYE   = tge(EMOJI['EYE'], '👁')
EM_BOT   = tge(EMOJI['BOT'], '🤖')
EM_DEL   = tge(EMOJI['DEL'], '🗑')
EM_STATS = tge(EMOJI['STATS'], '📊')
EM_INFO  = tge(EMOJI['INFO'], 'ℹ️')
EM_GEAR  = tge(EMOJI['GEAR'], '⚙️')
EM_MSG   = tge(EMOJI['MSG'], '💬')
EM_SEND  = tge(EMOJI['ARROW_UP_SEND'], '📤')
EM_BL    = tge(EMOJI['BL'], '⛔')
EM_CMD   = tge(EMOJI['CMD'], '🎯')
EM_USERS = tge(EMOJI['USERS'], '👥')
EM_USER  = tge(EMOJI['USER'], '👤')
EM_LOCK  = tge(EMOJI['LOCK_CLOSED'], '🔒')
EM_UNLOCK = tge(EMOJI['LOCK_OPEN'], '🔓')
EM_STAR  = tge(EMOJI['STAR'], '⭐️')
EM_HEART = tge(EMOJI['HEART'], '❤️')
EM_BELL  = tge(EMOJI['BELL'], '🔔')
EM_CLOCK = tge(EMOJI['CLOCK'], '⏲️')
EM_CALENDAR = tge(EMOJI['CALENDAR'], '📅')
EM_PHOTO = tge(EMOJI['PHOTO'], '📷')
EM_VIDEO = tge(EMOJI['VIDEO'], '📺')
EM_FILE  = tge(EMOJI['DOCUMENT'], '📄')
EM_FOLDER = tge(EMOJI['FOLDER'], '📁')
EM_PLUS  = tge(EMOJI['PLUS'], '➕')
EM_QUESTION = tge(EMOJI['QUESTION'], '❓')
EM_EXCLAMATION = tge(EMOJI['EXCLAMATION'], '❗️')
EM_ARROW_RIGHT = tge(EMOJI['ARROW_RIGHT'], '➡️')
EM_ARROW_LEFT = tge(EMOJI['ARROW_LEFT'], '⬅️')
EM_ARROW_UP = tge(EMOJI['ARROW_UP'], '⬆️')
EM_ARROW_DOWN = tge(EMOJI['ARROW_DOWN'], '⬇️')
EM_CHECK = tge(EMOJI['CHECK'], '✅')
EM_CROSS = tge(EMOJI['CROSS'], '❌')

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
            'ai_enabled':'0','spy_enabled':'1','notify_deleted':'1',
            'log_msgs':'1','ai_prompt':'Ты — профессиональный помощник бизнес-аккаунта. Отвечай вежливо и по делу.',
            'ai_model':'llama-3.3-70b-versatile','reply_chance':'30',
            'typing_speed':'1.0','auto_reply':'',
        }.items():
            c.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',(k,v))

def gs(key):  # get setting
    with db() as c:
        r = c.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
        return r['value'] if r else ''

def ss(key, val):  # set setting
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
        # держим последние 40
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
                    if prompt_override is None:  # сохраняем только для обычных диалогов
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

# ==================== КОМАНДНЫЙ ИИ (meta-AI) ====================
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
    result = await ask(uid, text, prompt_override=COMMANDER_PROMPT, history_override=[])
    if not result:
        await message.answer(f'{EM_ERR} ИИ не ответил. Проверьте GROQ_API_KEY.', parse_mode=ParseMode.HTML)
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
            f'{EM_USERS} Пользователей: <b>{u}</b>\n'
            f'{EM_MSG} Сообщений в кеше: <b>{m}</b>\n'
            f'{EM_BL} В чёрном списке: <b>{bl}</b>\n'
            f'{EM_STAR} Всего сообщений: <b>{tm}</b>\n\n'
            f'<b>Топ-5:</b>\n{top or "нет данных"}',
            reply_markup=back_kb(), parse_mode=ParseMode.HTML)

    elif action == 'users':
        rows = get_all_users()
        if not rows:
            await message.answer(f'{EM_INFO} Пользователей пока нет.', parse_mode=ParseMode.HTML)
            return
        lines = [f"• {EM_USER} <code>{r['user_id']}</code> {'@'+r['username'] if r['username'] else r['first_name'] or '?'} — {r['msg_count']} сообщ."
                 for r in rows[:20]]
        await message.answer(
            f'{EM_USERS} <b>Пользователи ({len(rows)})</b>\n\n'+'\n'.join(lines),
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
        for r in rows:
            chat_id = r['chat_id']
            if not chat_id or chat_id in sent_chats: continue
            sent_chats.add(chat_id)
            bc_id = next(iter(biz_con), None)
            if not bc_id: continue
            try:
                await bot.send_message(chat_id=chat_id, text=btext, business_connection_id=bc_id)
                ok+=1; await asyncio.sleep(0.1)
            except Exception as e:
                fail+=1; print(f"broadcast err {chat_id}: {e}")
        await status.edit_text(
            f'{EM_OK} <b>Рассылка завершена!</b>\n\n{EM_CHECK} Отправлено: {ok}\n{EM_CROSS} Ошибок: {fail}',
            parse_mode=ParseMode.HTML)

    elif action == 'ai_on':
        ss('ai_enabled','1')
        await message.answer(f'{EM_OK} ИИ-ответы <b>включены</b>.', reply_markup=main_kb(), parse_mode=ParseMode.HTML)

    elif action == 'ai_off':
        ss('ai_enabled','0')
        await message.answer(f'{EM_ERR} ИИ-ответы <b>выключены</b>.', reply_markup=main_kb(), parse_mode=ParseMode.HTML)

    elif action == 'spy_on':
        ss('spy_enabled','1')
        await message.answer(f'{EM_EYE} Слежка за удалёнными <b>включена</b>.', reply_markup=main_kb(), parse_mode=ParseMode.HTML)

    elif action == 'spy_off':
        ss('spy_enabled','0')
        await message.answer(f'{EM_EYE} Слежка за удалёнными <b>выключена</b>.', reply_markup=main_kb(), parse_mode=ParseMode.HTML)

    elif action == 'blacklist_add':
        try:
            bid = int(cmd['user_id'])
            with db() as conn:
                conn.execute('INSERT OR IGNORE INTO blacklist VALUES(?,?,?)',(bid,'',datetime.now().isoformat()))
            await message.answer(f'{EM_OK} ID <code>{bid}</code> добавлен в чёрный список.', parse_mode=ParseMode.HTML)
        except Exception as e:
            await message.answer(f'{EM_ERR} Ошибка: {e}', parse_mode=ParseMode.HTML)

    elif action == 'blacklist_remove':
        try:
            bid = int(cmd['user_id'])
            with db() as conn:
                conn.execute('DELETE FROM blacklist WHERE user_id=?',(bid,))
            await message.answer(f'{EM_OK} ID <code>{bid}</code> удалён из чёрного списка.', parse_mode=ParseMode.HTML)
        except Exception as e:
            await message.answer(f'{EM_ERR} Ошибка: {e}', parse_mode=ParseMode.HTML)

    elif action == 'blacklist_show':
        with db() as conn:
            bl = conn.execute('SELECT * FROM blacklist').fetchall()
        if not bl:
            await message.answer(f'{EM_BL} Чёрный список пуст.', parse_mode=ParseMode.HTML)
        else:
            lines = [f"• {EM_USER} <code>{r['user_id']}</code> {'@'+r['username'] if r['username'] else ''}" for r in bl]
            await message.answer(f'{EM_BL} <b>Чёрный список:</b>\n\n'+'\n'.join(lines), parse_mode=ParseMode.HTML)

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
            f'{EM_GEAR} <b>Business Monitor Bot</b>\n\n'
            f'{EM_BOT} ИИ-ответы: <b>{"🟢 Вкл" if gs("ai_enabled")=="1" else "🔴 Выкл"}</b>\n'
            f'{EM_EYE} Слежка: <b>{"🟢 Вкл" if gs("spy_enabled")=="1" else "🔴 Выкл"}</b>',
            reply_markup=main_kb(), parse_mode=ParseMode.HTML)

    else:
        chat_text = cmd.get('text', text)
        reply = await ask(uid, chat_text)
        if reply:
            await message.answer(reply, parse_mode=ParseMode.HTML)

# ==================== КЛАВИАТУРЫ ====================
def main_kb():
    ai  = '🟢' if gs('ai_enabled')=='1' else '🔴'
    spy = '🟢' if gs('spy_enabled')=='1' else '🔴'
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'{ai} ИИ-ответы',         callback_data='s_ai'),
         InlineKeyboardButton(text=f'{spy} Слежка',           callback_data='s_spy')],
        [InlineKeyboardButton(text=f'{EM_STATS} Статистика',   callback_data='s_stats'),
         InlineKeyboardButton(text=f'{EM_USERS} Пользователи', callback_data='s_users')],
        [InlineKeyboardButton(text=f'{EM_BL} Чёрный список',   callback_data='s_bl'),
         InlineKeyboardButton(text=f'{EM_SEND} Рассылка',      callback_data='s_broadcast')],
        [InlineKeyboardButton(text=f'{EM_MSG} Авто-ответ',     callback_data='s_auto'),
         InlineKeyboardButton(text=f'{EM_DEL} Очист. AI память', callback_data='s_clearmem')],
    ])

def back_kb(cb='back'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'{EM_ARROW_LEFT} Назад', callback_data=cb)]
    ])

def ai_kb():
    on = gs('ai_enabled')=='1'
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'{EM_CHECK if on else EM_CROSS} {"Включено" if on else "Выключено"}', callback_data='t_ai')],
        [InlineKeyboardButton(text=f'{EM_PENCIL} Изменить промпт', callback_data='t_prompt')],
        [InlineKeyboardButton(text=f'{EM_BOT} Модель: '+gs('ai_model').split('-')[0], callback_data='t_model')],
        [InlineKeyboardButton(text=f'{EM_MSG} Reply-шанс: {gs("reply_chance")}%', callback_data='t_chance')],
        [InlineKeyboardButton(text=f'{EM_CLOCK} Скорость печати: x{gs("typing_speed")}', callback_data='t_speed')],
        [InlineKeyboardButton(text=f'{EM_ARROW_LEFT} Назад', callback_data='back')],
    ])

def spy_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f'{EM_EYE} {"Вкл" if gs("spy_enabled")=="1" else "Выкл"} Слежка',
            callback_data='t_spy')],
        [InlineKeyboardButton(
            text=f'{EM_BELL} {"Вкл" if gs("notify_deleted")=="1" else "Выкл"} Уведомления',
            callback_data='t_notify')],
        [InlineKeyboardButton(
            text=f'{EM_FILE} {"Вкл" if gs("log_msgs")=="1" else "Выкл"} Логирование',
            callback_data='t_log')],
        [InlineKeyboardButton(text=f'{EM_ARROW_LEFT} Назад', callback_data='back')],
    ])

def model_kb():
    models=[('llama-3.3-70b-versatile','Llama 3.3 70B'),('llama-3.1-8b-instant','Llama 3.1 8B'),
            ('mixtral-8x7b-32768','Mixtral 8x7B'),('gemma2-9b-it','Gemma2 9B')]
    cur = gs('ai_model')
    rows=[[InlineKeyboardButton(text=('✅ ' if v==cur else '')+l, callback_data=f'm_{v}')] for v,l in models]
    rows.append([InlineKeyboardButton(text=f'{EM_ARROW_LEFT} Назад', callback_data='s_ai')])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def bl_kb():
    with db() as c:
        bl = c.execute('SELECT * FROM blacklist').fetchall()
    rows=[]
    for r in bl:
        n = f"@{r['username']}" if r['username'] else str(r['user_id'])
        rows.append([InlineKeyboardButton(text=f'{EM_CROSS} {n}', callback_data=f'bl_rm_{r["user_id"]}')])
    rows.append([InlineKeyboardButton(text=f'{EM_ARROW_LEFT} Назад', callback_data='back')])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ==================== HANDLERS — ADMIN BOT ====================

@dp.message(Command('start'))
async def cmd_start(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    ai  = '🟢 Вкл' if gs('ai_enabled')=='1' else '🔴 Выкл'
    spy = '🟢 Вкл' if gs('spy_enabled')=='1' else '🔴 Выкл'
    await msg.answer(
        f'{EM_GEAR} <b>Business Monitor Bot</b>\n\n'
        f'{EM_BOT} ИИ-ответы: <b>{ai}</b>\n'
        f'{EM_EYE} Слежка за удалёнными: <b>{spy}</b>\n\n'
        f'{EM_CMD} <b>Умный ввод команд:</b>\n'
        f'Просто напишите мне что хотите сделать:\n'
        f'<i>«включи ии», «сделай рассылку: текст», «покажи статистику», «добавь в чс 123»</i>\n\n'
        f'{EM_INFO} Или используйте кнопки ниже:',
        reply_markup=main_kb(), parse_mode=ParseMode.HTML)

@dp.message(Command('clear'))
async def cmd_clear(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    clear_ai_mem(msg.from_user.id)
    await msg.answer(f'{EM_OK} AI-память очищена.', parse_mode=ParseMode.HTML)

@dp.callback_query(F.data=='back')
async def cb_back(cb: types.CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return await cb.answer()
    await state.clear()
    try:
        await cb.message.edit_text(
            f'{EM_GEAR} <b>Business Monitor Bot</b>\n\n'
            f'{EM_BOT} ИИ-ответы: <b>{"🟢 Вкл" if gs("ai_enabled")=="1" else "🔴 Выкл"}</b>\n'
            f'{EM_EYE} Слежка: <b>{"🟢 Вкл" if gs("spy_enabled")=="1" else "🔴 Выкл"}</b>',
            reply_markup=main_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data=='s_ai')
async def cb_ai(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer()
    on = gs('ai_enabled')=='1'
    try:
        await cb.message.edit_text(
            f'{EM_BOT} <b>Настройки ИИ-ответов</b>\n\n'
            f'Статус: <b>{"🟢 Включено" if on else "🔴 Выключено"}</b>\n'
            f'Модель: <code>{gs("ai_model")}</code>\n'
            f'Reply-шанс: <b>{gs("reply_chance")}%</b>\n'
            f'Скорость: <b>x{gs("typing_speed")}</b>',
            reply_markup=ai_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data=='t_ai')
async def cb_t_ai(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer()
    new = toggle('ai_enabled')
    await cb.answer(f'ИИ {"включён" if new=="1" else "выключен"}')
    await cb_ai(cb)

@dp.callback_query(F.data=='t_prompt')
async def cb_t_prompt(cb: types.CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return await cb.answer()
    cur = gs('ai_prompt')
    try:
        await cb.message.edit_text(
            f'{EM_PENCIL} <b>Изменение промпта</b>\n\n<b>Текущий:</b>\n<blockquote>{cur[:300]}</blockquote>\n\nОтправьте новый:',
            reply_markup=back_kb('s_ai'), parse_mode=ParseMode.HTML)
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
    if not is_admin(cb.from_user.id): return await cb.answer()
    try:
        await cb.message.edit_text(f'{EM_BOT} <b>Выберите модель:</b>', reply_markup=model_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data.startswith('m_'))
async def cb_set_model(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer()
    ss('ai_model', cb.data[2:])
    await cb.answer(f'Модель: {cb.data[2:].split("-")[0]}')
    await cb_t_model(cb)

@dp.callback_query(F.data=='t_chance')
async def cb_chance(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer()
    steps=[0,10,20,30,50,70,100]; cur=int(gs('reply_chance') or 30)
    idx=steps.index(cur) if cur in steps else 3
    new=steps[(idx+1)%len(steps)]; ss('reply_chance',str(new))
    await cb.answer(f'Reply-шанс: {new}%')
    await cb_ai(cb)

@dp.callback_query(F.data=='t_speed')
async def cb_speed(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer()
    steps=[0.5,1.0,1.5,2.0,3.0]
    try: idx=steps.index(float(gs('typing_speed') or 1))
    except: idx=1
    new=steps[(idx+1)%len(steps)]; ss('typing_speed',str(new))
    await cb.answer(f'Скорость x{new}')
    await cb_ai(cb)

@dp.callback_query(F.data=='s_spy')
async def cb_spy(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer()
    try:
        await cb.message.edit_text(
            f'{EM_EYE} <b>Слежка за удалёнными сообщениями</b>\n\n'
            f'Когда кто-то удаляет сообщение в диалоге — бот пришлёт его содержимое, ID и юзернейм.',
            reply_markup=spy_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data=='t_spy')
async def cb_t_spy(cb):
    if not is_admin(cb.from_user.id): return await cb.answer()
    new=toggle('spy_enabled'); await cb.answer(f'Слежка {"вкл" if new=="1" else "выкл"}')
    await cb_spy(cb)

@dp.callback_query(F.data=='t_notify')
async def cb_t_notify(cb):
    if not is_admin(cb.from_user.id): return await cb.answer()
    new=toggle('notify_deleted'); await cb.answer(f'Уведомления {"вкл" if new=="1" else "выкл"}')
    await cb_spy(cb)

@dp.callback_query(F.data=='t_log')
async def cb_t_log(cb):
    if not is_admin(cb.from_user.id): return await cb.answer()
    new=toggle('log_msgs'); await cb.answer(f'Логирование {"вкл" if new=="1" else "выкл"}')
    await cb_spy(cb)

@dp.callback_query(F.data=='s_stats')
async def cb_stats_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer()
    u,m,bl,tm = get_stats()
    rows = get_all_users()[:5]
    top = '\n'.join(f"  {i+1}. {'@'+r['username'] if r['username'] else r['first_name'] or str(r['user_id'])} — {r['msg_count']}"
                    for i,r in enumerate(rows))
    try:
        await cb.message.edit_text(
            f'{EM_STATS} <b>Статистика</b>\n\n'
            f'{EM_USERS} Пользователей: <b>{u}</b>\n{EM_FILE} Кеш: <b>{m}</b>\n'
            f'{EM_BL} ЧС: <b>{bl}</b>\n{EM_STAR} Всего: <b>{tm}</b>\n\n'
            f'<b>Топ-5:</b>\n{top or "нет данных"}',
            reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data=='s_users')
async def cb_users_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer()
    rows = get_all_users()
    lines=[f"• {EM_USER} <code>{r['user_id']}</code> {'@'+r['username'] if r['username'] else r['first_name'] or '?'} — {r['msg_count']}"
           for r in rows[:20]]
    try:
        await cb.message.edit_text(
            f'{EM_USERS} <b>Пользователи ({len(rows)})</b>\n\n'+(('\n'.join(lines)) if lines else 'Нет данных'),
            reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data=='s_bl')
async def cb_bl(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer()
    with db() as c:
        bl=c.execute('SELECT COUNT(*) FROM blacklist').fetchone()[0]
    try:
        await cb.message.edit_text(
            f'{EM_BL} <b>Чёрный список</b>\nВсего: <b>{bl}</b>\n\nНажмите на пользователя чтобы удалить.',
            reply_markup=bl_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data.startswith('bl_rm_'))
async def cb_bl_rm(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer()
    uid=int(cb.data.replace('bl_rm_',''))
    with db() as c: c.execute('DELETE FROM blacklist WHERE user_id=?',(uid,))
    await cb.answer(f'Удалён: {uid}')
    await cb_bl(cb)

@dp.callback_query(F.data=='s_broadcast')
async def cb_broadcast_start(cb: types.CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return await cb.answer()
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
            # ИСПРАВЛЕНО: проверяем наличие файла перед отправкой
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
        f'{EM_OK} <b>Рассылка завершена!</b>\n{EM_CHECK} Отправлено: {ok}\n{EM_CROSS} Ошибок: {fail}',
        reply_markup=main_kb(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data=='s_auto')
async def cb_auto(cb: types.CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return await cb.answer()
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

@dp.callback_query(F.data=='s_clearmem')
async def cb_clearmem(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer()
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
    try:
        if bc.is_enabled:
            biz_con[bc.id] = bc.user.id
            save_connections(biz_con)
            print(f"Бизнес-подключение: {bc.id} -> {bc.user.id}")
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
    if gs('spy_enabled') != '1': return
    if gs('notify_deleted') != '1': return
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
                    f'{EM_USER} <b>Кто:</b> {u_name}\n'
                    f'🆔 <b>User ID:</b> <code>{u_id}</code>\n'
                    f'{EM_MSG} <b>Чат:</b> <code>{event.chat.id}</code>\n'
                    f'{EM_CLOCK} <b>Время отправки:</b> {ts}\n'
                )
                if content:
                    text += f'\n<b>Текст:</b>\n<blockquote>{content[:800]}</blockquote>'
            else:
                text = (
                    f'{EM_DEL} <b>Удалено сообщение!</b>\n\n'
                    f'{EM_MSG} Чат: <code>{event.chat.id}</code>\n'
                    f'🆔 Msg ID: <code>{msg_id}</code>\n\n'
                    f'⚠️ Сообщение не закешировано (логирование было выключено)'
                )
                cached = None; fid = None; ftype = ''

            for aid in (ADMIN_ID, ADMIN_ID_2):
                try:
                    await bot.send_message(aid, text, parse_mode=ParseMode.HTML)
                    if cached and fid and ftype:
                        cap = f'{EM_FILE} Удалённый {ftype}'
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
    try:
        bc_id = msg.business_connection_id
        if not bc_id: return
        if bc_id not in biz_con:
            biz_con[bc_id] = ADMIN_ID
            save_connections(biz_con)
        owner_id = biz_con[bc_id]

        cache_msg(msg)

        if msg.from_user and msg.from_user.id == owner_id:
            return

        uid  = msg.from_user.id if msg.from_user else 0
        text = msg.text or msg.caption or ''

        auto = gs('auto_reply')
        if auto and uid:
            with db() as c:
                cnt=c.execute('SELECT COUNT(*) FROM msg_cache WHERE user_id=? AND chat_id=?',
                              (uid, msg.chat.id)).fetchone()[0]
            if cnt == 1:
                await asyncio.sleep(random.uniform(1, 3))
                try:
                    await bot.send_message(chat_id=msg.chat.id, text=auto,
                                           business_connection_id=bc_id,
                                           reply_to_message_id=msg.message_id)
                except Exception as e:
                    print(f"auto_reply err: {e}")
                return

        if gs('ai_enabled') != '1': return
        if not text: return
        if uid and is_blacklisted(uid):
            print(f"User {uid} blacklisted, skip"); return

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
