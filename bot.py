# ── SSL-патч для Windows ─────────────────────────────────────────────────
import ssl as _ssl
_ssl._create_default_https_context = _ssl._create_unverified_context
# ─────────────────────────────────────────────────────────────────────────

import asyncio, json, os, random, re, sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    BufferedInputFile,
)

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "ВАШ_BOT_TOKEN"  # вставь токен
OWNER_ID  = 5883796026        # только этот человек может пользоваться ботом
DB_PATH   = "fake_post.db"
# ====================================================

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())

# ── Премиум эмодзи ──────────────────────────────────────────────────────
def tge(eid, fb=""): return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

EM_GEAR   = tge("5870982283724328568", "⚙")
EM_OK     = tge("5870633910337015697", "✅")
EM_ERR    = tge("5870657884844462243", "❌")
EM_PENCIL = tge("5870676941614354370", "✏")
EM_TRASH  = tge("5870875489362513438", "🗑")
EM_INFO   = tge("6028435952299413210", "ℹ")
EM_GIFT   = tge("6032644646587338669", "🎁")
EM_PARTY  = tge("6041731551845159060", "🎉")
EM_CLOCK  = tge("5983150113483134607", "⏰")
EM_LINK   = tge("5769289093221454192", "🔗")
EM_PHOTO  = tge("6035128606563241721", "🖼")
EM_FILE   = tge("5870528606328852614", "📁")
EM_STAT   = tge("5870921681735781843", "📊")
EM_PERSON = tge("5870994129244131212", "👤")
EM_LIST   = tge("5870772616305839506", "👥")
EM_WRITE  = tge("5870753782874246579", "✍")
EM_SEND   = tge("5963103826075456248", "📤")
EM_TAG    = tge("5886285355279193209", "🏷")
EM_PRIZE  = tge("5884479287171485878", "🎯")
EM_LOCK   = tge("6037249452824072506", "🔒")
EM_RAND   = tge("5345906554510012647", "🔀")
EM_DICE   = tge("6041731551845159060", "🎲")
EM_TIMER  = tge("5890937706803894250", "📅")
EM_BACK   = tge("5893057118545646106", "◁")

# ── ID иконок для инлайн кнопок ─────────────────────────────────────────
IK_OK     = "5870633910337015697"
IK_ERR    = "5870657884844462243"
IK_PENCIL = "5870676941614354370"
IK_TRASH  = "5870875489362513438"
IK_SEND   = "5963103826075456248"
IK_GEAR   = "5870982283724328568"
IK_PHOTO  = "6035128606563241721"
IK_FILE   = "5870528606328852614"
IK_LINK   = "5769289093221454192"
IK_GIFT   = "6032644646587338669"
IK_PARTY  = "6041731551845159060"
IK_PRIZE  = "5884479287171485878"
IK_LIST   = "5870772616305839506"
IK_STAT   = "5870921681735781843"
IK_RAND   = "5345906554510012647"
IK_CLOCK  = "5983150113483134607"
IK_BACK   = "5893057118545646106"
IK_TAG    = "5886285355279193209"
IK_WRITE  = "5870753782874246579"
IK_PERSON = "5870994129244131212"

# ==================== БД ====================
def db_conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with db_conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS visitors(
            user_id    INTEGER PRIMARY KEY,
            username   TEXT,
            first_name TEXT,
            last_name  TEXT,
            first_seen TEXT,
            last_seen  TEXT,
            visits     INTEGER DEFAULT 1
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS posts(
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT,
            text        TEXT,
            photo_id    TEXT,
            file_id     TEXT,
            file_name   TEXT,
            btn_text    TEXT,
            btn_url     TEXT,
            btn2_text   TEXT,
            btn2_url    TEXT,
            created_at  TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS giveaways(
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT,
            prize       TEXT,
            winners_cnt INTEGER DEFAULT 1,
            end_date    TEXT,
            condition   TEXT,
            participants TEXT DEFAULT '[]',
            winners      TEXT DEFAULT '[]',
            status       TEXT DEFAULT 'active',
            created_at   TEXT
        )""")

def log_visitor(user: types.User):
    now = datetime.now().isoformat()
    with db_conn() as c:
        existing = c.execute("SELECT * FROM visitors WHERE user_id=?", (user.id,)).fetchone()
        if existing:
            c.execute("""UPDATE visitors SET last_seen=?, visits=visits+1,
                username=?, first_name=?, last_name=? WHERE user_id=?""",
                (now, user.username or "", user.first_name or "", user.last_name or "", user.id))
        else:
            c.execute("""INSERT INTO visitors VALUES(?,?,?,?,?,?,1)""",
                (user.id, user.username or "", user.first_name or "",
                 user.last_name or "", now, now))

def get_visitors():
    with db_conn() as c:
        return c.execute("SELECT * FROM visitors ORDER BY last_seen DESC").fetchall()

def save_post(data: dict) -> int:
    with db_conn() as c:
        c.execute("""INSERT INTO posts(title,text,photo_id,file_id,file_name,
            btn_text,btn_url,btn2_text,btn2_url,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (data.get("title",""), data.get("text",""), data.get("photo_id",""),
             data.get("file_id",""), data.get("file_name",""),
             data.get("btn_text",""), data.get("btn_url",""),
             data.get("btn2_text",""), data.get("btn2_url",""),
             datetime.now().isoformat()))
        return c.lastrowid

def get_posts():
    with db_conn() as c:
        return c.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()

def get_post(pid: int):
    with db_conn() as c:
        return c.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone()

def delete_post(pid: int):
    with db_conn() as c:
        c.execute("DELETE FROM posts WHERE id=?", (pid,))

def save_giveaway(data: dict) -> int:
    with db_conn() as c:
        c.execute("""INSERT INTO giveaways(title,prize,winners_cnt,end_date,condition,created_at)
            VALUES(?,?,?,?,?,?)""",
            (data.get("title",""), data.get("prize",""), data.get("winners",1),
             data.get("end_date",""), data.get("condition",""),
             datetime.now().isoformat()))
        return c.lastrowid

def get_giveaways():
    with db_conn() as c:
        return c.execute("SELECT * FROM giveaways ORDER BY id DESC").fetchall()

def get_giveaway(gid: int):
    with db_conn() as c:
        return c.execute("SELECT * FROM giveaways WHERE id=?", (gid,)).fetchone()

def pick_winners(gid: int):
    gw = get_giveaway(gid)
    if not gw: return []
    parts = json.loads(gw["participants"] or "[]")
    cnt   = min(gw["winners_cnt"], len(parts))
    if cnt == 0: return []
    winners = random.sample(parts, cnt)
    with db_conn() as c:
        c.execute("UPDATE giveaways SET winners=?, status='finished' WHERE id=?",
                  (json.dumps(winners), gid))
    return winners

# ==================== FSM ====================
class PostBuilder(StatesGroup):
    title     = State()
    text      = State()
    photo     = State()
    file      = State()
    btn1_text = State()
    btn1_url  = State()
    btn2_text = State()
    btn2_url  = State()
    preview   = State()

class GiveawayBuilder(StatesGroup):
    title     = State()
    prize     = State()
    winners   = State()
    end_date  = State()
    condition = State()
    preview   = State()

# ==================== HELPER ====================
def is_owner(uid: int) -> bool:
    return uid == OWNER_ID

PRIVATE_MSG = (
    f"{EM_LOCK} <b>Доступ ограничен</b>\n\n"
    f"Этот бот является частным инструментом для ограниченного круга пользователей.\n\n"
    f"<i>Для получения доступа обратитесь к администратору.</i>"
)

def post_keyboard(post: dict) -> InlineKeyboardMarkup | None:
    rows = []
    if post.get("btn_text") and post.get("btn_url"):
        rows.append([InlineKeyboardButton(
            text=post["btn_text"], url=post["btn_url"],
            icon_custom_emoji_id=IK_LINK)])
    if post.get("btn2_text") and post.get("btn2_url"):
        rows.append([InlineKeyboardButton(
            text=post["btn2_text"], url=post["btn2_url"],
            icon_custom_emoji_id=IK_LINK)])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

async def send_post_preview(chat_id: int, post: dict, extra_text: str = ""):
    """Отправляет предпросмотр поста."""
    kb  = post_keyboard(post)
    txt = (post.get("text") or "") + (f"\n\n{extra_text}" if extra_text else "")
    if post.get("photo_id"):
        await bot.send_photo(chat_id, post["photo_id"], caption=txt or None,
                             parse_mode=ParseMode.HTML, reply_markup=kb)
    elif post.get("file_id"):
        await bot.send_document(chat_id, post["file_id"],
                                caption=txt or None, parse_mode=ParseMode.HTML,
                                reply_markup=kb)
    elif txt:
        await bot.send_message(chat_id, txt, parse_mode=ParseMode.HTML, reply_markup=kb)

# ==================== КЛАВИАТУРЫ ====================
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать пост",      callback_data="new_post",    icon_custom_emoji_id=IK_PENCIL),
         InlineKeyboardButton(text="Мои посты",         callback_data="my_posts",    icon_custom_emoji_id=IK_LIST)],
        [InlineKeyboardButton(text="Розыгрыш",          callback_data="new_giv",     icon_custom_emoji_id=IK_GIFT),
         InlineKeyboardButton(text="Мои розыгрыши",     callback_data="my_givs",     icon_custom_emoji_id=IK_PARTY)],
        [InlineKeyboardButton(text="Случайный победитель", callback_data="rng_winner",icon_custom_emoji_id=IK_RAND),
         InlineKeyboardButton(text="Кто нажимал /start",  callback_data="visitors",  icon_custom_emoji_id=IK_PERSON)],
        [InlineKeyboardButton(text="Статистика",        callback_data="stats",       icon_custom_emoji_id=IK_STAT)],
    ])

def back_kb(cb="main"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data=cb, icon_custom_emoji_id=IK_BACK)]
    ])

def post_builder_kb(step: str):
    """Клавиатура для каждого шага создания поста."""
    skip = [InlineKeyboardButton(text="Пропустить", callback_data=f"skip_{step}", icon_custom_emoji_id=IK_OK)]
    back = [InlineKeyboardButton(text="Отмена",     callback_data="cancel_build",  icon_custom_emoji_id=IK_ERR)]
    return InlineKeyboardMarkup(inline_keyboard=[skip, back])

def post_confirm_kb(tmp_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сохранить пост",      callback_data=f"save_post_{tmp_id}",   icon_custom_emoji_id=IK_OK)],
        [InlineKeyboardButton(text="Скачать как HTML",    callback_data=f"dl_html_{tmp_id}",     icon_custom_emoji_id=IK_FILE)],
        [InlineKeyboardButton(text="Пересоздать",         callback_data="new_post",              icon_custom_emoji_id=IK_PENCIL)],
        [InlineKeyboardButton(text="Отмена",              callback_data="main",                  icon_custom_emoji_id=IK_BACK)],
    ])

def posts_list_kb(posts):
    rows = [[InlineKeyboardButton(
                text=f"#{p['id']} {p['title'] or p['text'][:30] or '—'}",
                callback_data=f"view_post_{p['id']}", icon_custom_emoji_id=IK_TAG)]
             for p in posts]
    rows.append([InlineKeyboardButton(text="Назад", callback_data="main", icon_custom_emoji_id=IK_BACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def post_actions_kb(pid: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Предпросмотр",     callback_data=f"preview_post_{pid}", icon_custom_emoji_id=IK_SEND)],
        [InlineKeyboardButton(text="Скачать HTML",     callback_data=f"dl_html_saved_{pid}",icon_custom_emoji_id=IK_FILE)],
        [InlineKeyboardButton(text="Удалить пост",     callback_data=f"del_post_{pid}",     icon_custom_emoji_id=IK_TRASH)],
        [InlineKeyboardButton(text="Назад к списку",   callback_data="my_posts",            icon_custom_emoji_id=IK_BACK)],
    ])

def giveaway_actions_kb(gid: int, status: str):
    rows = [
        [InlineKeyboardButton(text="Выбрать победителей", callback_data=f"pick_{gid}", icon_custom_emoji_id=IK_RAND)],
        [InlineKeyboardButton(text="Показать участников",  callback_data=f"parts_{gid}",icon_custom_emoji_id=IK_LIST)],
        [InlineKeyboardButton(text="Удалить",             callback_data=f"del_giv_{gid}",icon_custom_emoji_id=IK_TRASH)],
        [InlineKeyboardButton(text="Назад",               callback_data="my_givs",      icon_custom_emoji_id=IK_BACK)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# Временное хранилище данных при создании
_tmp: dict = {}

def make_tmp_id(uid: int) -> str:
    return f"{uid}_{int(datetime.now().timestamp())}"

# ==================== /start ====================
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    log_visitor(msg.from_user)
    if not is_owner(msg.from_user.id):
        await msg.answer(PRIVATE_MSG, parse_mode=ParseMode.HTML)
        return
    await msg.answer(
        f"{EM_GIFT} <b>FakePost Builder</b>\n\n"
        f"{EM_WRITE} Создавай убедительные посты для розыгрышей\n"
        f"{EM_PARTY} Управляй розыгрышами и выбирай победителей\n"
        f"{EM_RAND} Случайный выбор победителя из списка\n"
        f"{EM_PERSON} Просмотр всех кто когда-либо открывал бота\n\n"
        f"{EM_INFO} Выбери действие:",
        reply_markup=main_kb(), parse_mode=ParseMode.HTML
    )

@dp.callback_query(F.data == "main")
async def cb_main(cb: types.CallbackQuery, state: FSMContext):
    if not is_owner(cb.from_user.id): return await cb.answer()
    await state.clear()
    try:
        await cb.message.edit_text(
            f"{EM_GIFT} <b>FakePost Builder</b>\n\n{EM_INFO} Выбери действие:",
            reply_markup=main_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

# ==================== СОЗДАНИЕ ПОСТА ====================
@dp.callback_query(F.data == "new_post")
async def cb_new_post(cb: types.CallbackQuery, state: FSMContext):
    if not is_owner(cb.from_user.id): return await cb.answer()
    await state.clear()
    tid = make_tmp_id(cb.from_user.id)
    _tmp[tid] = {}
    await state.update_data(tid=tid)
    try:
        await cb.message.edit_text(
            f"{EM_TAG} <b>Шаг 1/7 — Заголовок поста</b>\n\n"
            f"Введи заголовок (только для твоей навигации, не попадёт в пост):",
            reply_markup=post_builder_kb("title"), parse_mode=ParseMode.HTML)
    except:
        await cb.message.answer(
            f"{EM_TAG} <b>Шаг 1/7 — Заголовок поста</b>\n\n"
            f"Введи заголовок (только для навигации):",
            reply_markup=post_builder_kb("title"), parse_mode=ParseMode.HTML)
    await state.set_state(PostBuilder.title)
    await cb.answer()

@dp.callback_query(F.data == "cancel_build")
async def cb_cancel(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await cb.message.edit_text(
            f"{EM_ERR} Создание отменено.\n\n{EM_INFO} Выбери действие:",
            reply_markup=main_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

# Шаг 1 — заголовок
@dp.message(PostBuilder.title)
async def pb_title(msg: types.Message, state: FSMContext):
    if not is_owner(msg.from_user.id): return
    d = await state.get_data(); tid = d["tid"]
    _tmp[tid]["title"] = msg.text or ""
    await state.set_state(PostBuilder.text)
    await msg.answer(
        f"{EM_WRITE} <b>Шаг 2/7 — Текст поста</b>\n\n"
        f"Введи основной текст. Поддерживается HTML:\n"
        f"<code>&lt;b&gt;жирный&lt;/b&gt;</code> <code>&lt;i&gt;курсив&lt;/i&gt;</code> <code>&lt;a href='url'&gt;ссылка&lt;/a&gt;</code>",
        reply_markup=post_builder_kb("text"), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "skip_title", PostBuilder.title)
async def pb_skip_title(cb: types.CallbackQuery, state: FSMContext):
    d = await state.get_data(); _tmp[d["tid"]]["title"] = ""
    await state.set_state(PostBuilder.text)
    await cb.message.edit_text(
        f"{EM_WRITE} <b>Шаг 2/7 — Текст поста</b>\n\nВведи основной текст:",
        reply_markup=post_builder_kb("text"), parse_mode=ParseMode.HTML)
    await cb.answer()

# Шаг 2 — текст
@dp.message(PostBuilder.text)
async def pb_text(msg: types.Message, state: FSMContext):
    if not is_owner(msg.from_user.id): return
    d = await state.get_data(); tid = d["tid"]
    _tmp[tid]["text"] = msg.text or msg.caption or ""
    await state.set_state(PostBuilder.photo)
    await msg.answer(
        f"{EM_PHOTO} <b>Шаг 3/7 — Фото</b>\n\nОтправь фото (или нажми Пропустить):",
        reply_markup=post_builder_kb("photo"), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "skip_text", PostBuilder.text)
async def pb_skip_text(cb: types.CallbackQuery, state: FSMContext):
    d = await state.get_data(); _tmp[d["tid"]]["text"] = ""
    await state.set_state(PostBuilder.photo)
    await cb.message.edit_text(
        f"{EM_PHOTO} <b>Шаг 3/7 — Фото</b>\n\nОтправь фото (или нажми Пропустить):",
        reply_markup=post_builder_kb("photo"), parse_mode=ParseMode.HTML)
    await cb.answer()

# Шаг 3 — фото
@dp.message(PostBuilder.photo, F.photo)
async def pb_photo(msg: types.Message, state: FSMContext):
    if not is_owner(msg.from_user.id): return
    d = await state.get_data(); tid = d["tid"]
    _tmp[tid]["photo_id"] = msg.photo[-1].file_id
    await state.set_state(PostBuilder.file)
    await msg.answer(
        f"{EM_FILE} <b>Шаг 4/7 — Файл</b>\n\nОтправь файл/документ (или нажми Пропустить):",
        reply_markup=post_builder_kb("file"), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "skip_photo", PostBuilder.photo)
async def pb_skip_photo(cb: types.CallbackQuery, state: FSMContext):
    d = await state.get_data(); _tmp[d["tid"]]["photo_id"] = ""
    await state.set_state(PostBuilder.file)
    await cb.message.edit_text(
        f"{EM_FILE} <b>Шаг 4/7 — Файл</b>\n\nОтправь файл (или нажми Пропустить):",
        reply_markup=post_builder_kb("file"), parse_mode=ParseMode.HTML)
    await cb.answer()

@dp.message(PostBuilder.photo)  # если прислал не фото
async def pb_photo_wrong(msg: types.Message, state: FSMContext):
    await msg.answer(f"{EM_ERR} Отправь именно фото, или нажми Пропустить.",
                     reply_markup=post_builder_kb("photo"), parse_mode=ParseMode.HTML)

# Шаг 4 — файл
@dp.message(PostBuilder.file, F.document)
async def pb_file(msg: types.Message, state: FSMContext):
    if not is_owner(msg.from_user.id): return
    d = await state.get_data(); tid = d["tid"]
    _tmp[tid]["file_id"]   = msg.document.file_id
    _tmp[tid]["file_name"] = msg.document.file_name or "file"
    await state.set_state(PostBuilder.btn1_text)
    await msg.answer(
        f"{EM_LINK} <b>Шаг 5/7 — Кнопка 1 (текст)</b>\n\nВведи текст кнопки (например: «Участвовать») или нажми Пропустить:",
        reply_markup=post_builder_kb("btn1_text"), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "skip_file", PostBuilder.file)
async def pb_skip_file(cb: types.CallbackQuery, state: FSMContext):
    d = await state.get_data(); _tmp[d["tid"]]["file_id"] = ""; _tmp[d["tid"]]["file_name"] = ""
    await state.set_state(PostBuilder.btn1_text)
    await cb.message.edit_text(
        f"{EM_LINK} <b>Шаг 5/7 — Кнопка 1 (текст)</b>\n\nВведи текст кнопки или нажми Пропустить:",
        reply_markup=post_builder_kb("btn1_text"), parse_mode=ParseMode.HTML)
    await cb.answer()

@dp.message(PostBuilder.file)
async def pb_file_wrong(msg: types.Message):
    await msg.answer(f"{EM_ERR} Отправь файл/документ, или нажми Пропустить.",
                     reply_markup=post_builder_kb("file"), parse_mode=ParseMode.HTML)

# Шаг 5 — кнопка 1 текст
@dp.message(PostBuilder.btn1_text)
async def pb_btn1_text(msg: types.Message, state: FSMContext):
    if not is_owner(msg.from_user.id): return
    d = await state.get_data(); tid = d["tid"]
    _tmp[tid]["btn_text"] = msg.text or ""
    await state.set_state(PostBuilder.btn1_url)
    await msg.answer(
        f"{EM_LINK} <b>Шаг 5b/7 — Кнопка 1 (ссылка)</b>\n\nВведи ссылку для кнопки «{_tmp[tid]['btn_text']}»:",
        reply_markup=post_builder_kb("btn1_url"), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "skip_btn1_text", PostBuilder.btn1_text)
async def pb_skip_btn1(cb: types.CallbackQuery, state: FSMContext):
    d = await state.get_data(); _tmp[d["tid"]]["btn_text"] = ""; _tmp[d["tid"]]["btn_url"] = ""
    await state.set_state(PostBuilder.btn2_text)
    await cb.message.edit_text(
        f"{EM_LINK} <b>Шаг 6/7 — Кнопка 2 (текст)</b>\n\nВведи текст второй кнопки или нажми Пропустить:",
        reply_markup=post_builder_kb("btn2_text"), parse_mode=ParseMode.HTML)
    await cb.answer()

# Шаг 5b — кнопка 1 url
@dp.message(PostBuilder.btn1_url)
async def pb_btn1_url(msg: types.Message, state: FSMContext):
    if not is_owner(msg.from_user.id): return
    d = await state.get_data(); tid = d["tid"]
    url = msg.text or ""
    if url and not url.startswith("http"):
        url = "https://" + url
    _tmp[tid]["btn_url"] = url
    await state.set_state(PostBuilder.btn2_text)
    await msg.answer(
        f"{EM_LINK} <b>Шаг 6/7 — Кнопка 2 (текст)</b>\n\nВведи текст второй кнопки (или нажми Пропустить):",
        reply_markup=post_builder_kb("btn2_text"), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "skip_btn1_url", PostBuilder.btn1_url)
async def pb_skip_btn1_url(cb: types.CallbackQuery, state: FSMContext):
    d = await state.get_data(); _tmp[d["tid"]]["btn_url"] = ""
    await state.set_state(PostBuilder.btn2_text)
    await cb.message.edit_text(
        f"{EM_LINK} <b>Шаг 6/7 — Кнопка 2 (текст)</b>\n\nВведи текст второй кнопки (или Пропустить):",
        reply_markup=post_builder_kb("btn2_text"), parse_mode=ParseMode.HTML)
    await cb.answer()

# Шаг 6 — кнопка 2 текст
@dp.message(PostBuilder.btn2_text)
async def pb_btn2_text(msg: types.Message, state: FSMContext):
    if not is_owner(msg.from_user.id): return
    d = await state.get_data(); tid = d["tid"]
    _tmp[tid]["btn2_text"] = msg.text or ""
    await state.set_state(PostBuilder.btn2_url)
    await msg.answer(
        f"{EM_LINK} <b>Шаг 6b/7 — Кнопка 2 (ссылка)</b>\n\nВведи ссылку для второй кнопки:",
        reply_markup=post_builder_kb("btn2_url"), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "skip_btn2_text", PostBuilder.btn2_text)
async def pb_skip_btn2(cb: types.CallbackQuery, state: FSMContext):
    d = await state.get_data(); _tmp[d["tid"]]["btn2_text"] = ""; _tmp[d["tid"]]["btn2_url"] = ""
    await state.set_state(PostBuilder.preview)
    await _show_preview(cb.message, d["tid"], cb.from_user.id)
    await cb.answer()

# Шаг 6b — кнопка 2 url
@dp.message(PostBuilder.btn2_url)
async def pb_btn2_url(msg: types.Message, state: FSMContext):
    if not is_owner(msg.from_user.id): return
    d = await state.get_data(); tid = d["tid"]
    url = msg.text or ""
    if url and not url.startswith("http"): url = "https://" + url
    _tmp[tid]["btn2_url"] = url
    await state.set_state(PostBuilder.preview)
    await _show_preview(msg, tid, msg.from_user.id)

@dp.callback_query(F.data == "skip_btn2_url", PostBuilder.btn2_url)
async def pb_skip_btn2_url(cb: types.CallbackQuery, state: FSMContext):
    d = await state.get_data(); _tmp[d["tid"]]["btn2_url"] = ""
    await state.set_state(PostBuilder.preview)
    await _show_preview(cb.message, d["tid"], cb.from_user.id)
    await cb.answer()

async def _show_preview(msg_or_obj, tid: str, uid: int):
    post = _tmp.get(tid, {})
    await msg_or_obj.answer(
        f"{EM_SEND} <b>Шаг 7/7 — Предпросмотр</b>\n\n"
        f"Вот как будет выглядеть пост:",
        parse_mode=ParseMode.HTML)
    await send_post_preview(uid, post)
    await msg_or_obj.answer(
        f"{EM_INFO} Что сделать с постом?",
        reply_markup=post_confirm_kb(tid), parse_mode=ParseMode.HTML)

# Сохранить пост
@dp.callback_query(F.data.startswith("save_post_"))
async def cb_save_post(cb: types.CallbackQuery, state: FSMContext):
    if not is_owner(cb.from_user.id): return await cb.answer()
    tid  = cb.data.replace("save_post_", "")
    post = _tmp.get(tid, {})
    if not post:
        await cb.answer("Данные устарели, создайте пост заново.", show_alert=True); return
    pid = save_post(post)
    _tmp.pop(tid, None)
    await state.clear()
    try:
        await cb.message.edit_text(
            f"{EM_OK} <b>Пост #{pid} сохранён!</b>\n\nНайди его в разделе «Мои посты».",
            reply_markup=main_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

# Скачать HTML (временный)
@dp.callback_query(F.data.startswith("dl_html_"))
async def cb_dl_html(cb: types.CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer()
    raw = cb.data.replace("dl_html_", "")
    if raw.startswith("saved_"):
        pid  = int(raw.replace("saved_", ""))
        row  = get_post(pid)
        post = dict(row) if row else {}
    else:
        post = _tmp.get(raw, {})
    if not post:
        await cb.answer("Данные не найдены.", show_alert=True); return

    # Генерируем HTML
    btns_html = ""
    if post.get("btn_text") and post.get("btn_url"):
        btns_html += f'<a href="{post["btn_url"]}" class="btn">{post["btn_text"]}</a>\n'
    if post.get("btn2_text") and post.get("btn2_url"):
        btns_html += f'<a href="{post["btn2_url"]}" class="btn">{post["btn2_text"]}</a>\n'

    html = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{post.get('title','Post')}</title>
<style>
  body{{font-family:system-ui,sans-serif;max-width:600px;margin:40px auto;padding:20px;background:#0e1117;color:#e8ecf7}}
  .card{{background:#161b27;border:1px solid #2a3450;border-radius:16px;padding:24px}}
  h2{{color:#6384ff;margin-top:0}}
  .text{{line-height:1.6;margin:16px 0;white-space:pre-wrap}}
  .btn{{display:inline-block;margin:8px 4px 0;padding:10px 20px;background:#6384ff;
        color:#fff;border-radius:10px;text-decoration:none;font-weight:600}}
  .btn:hover{{background:#4a6de0}}
</style></head><body>
<div class="card">
  <h2>{post.get('title','') or 'Пост'}</h2>
  <div class="text">{post.get('text','')}</div>
  {btns_html}
</div></body></html>"""

    data = html.encode("utf-8")
    fname = f"post_{int(datetime.now().timestamp())}.html"
    await bot.send_document(cb.from_user.id,
        BufferedInputFile(data, filename=fname),
        caption=f"{EM_FILE} Пост в HTML формате",
        parse_mode=ParseMode.HTML)
    await cb.answer("HTML отправлен!")

# ==================== МОИ ПОСТЫ ====================
@dp.callback_query(F.data == "my_posts")
async def cb_my_posts(cb: types.CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer()
    posts = get_posts()
    if not posts:
        try:
            await cb.message.edit_text(
                f"{EM_INFO} У тебя пока нет сохранённых постов.",
                reply_markup=back_kb(), parse_mode=ParseMode.HTML)
        except: pass
        return await cb.answer()
    try:
        await cb.message.edit_text(
            f"{EM_LIST} <b>Мои посты ({len(posts)})</b>\n\nВыбери пост:",
            reply_markup=posts_list_kb(posts), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data.startswith("view_post_"))
async def cb_view_post(cb: types.CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer()
    pid  = int(cb.data.replace("view_post_", ""))
    post = get_post(pid)
    if not post:
        await cb.answer("Пост не найден.", show_alert=True); return
    info = (
        f"{EM_TAG} <b>Пост #{pid}</b>\n\n"
        f"<b>Заголовок:</b> {post['title'] or '—'}\n"
        f"<b>Текст:</b> {(post['text'] or '')[:100]}{'...' if len(post['text'] or '')>100 else ''}\n"
        f"<b>Фото:</b> {'Да' if post['photo_id'] else 'Нет'}\n"
        f"<b>Файл:</b> {post['file_name'] or 'Нет'}\n"
        f"<b>Кнопок:</b> {(1 if post['btn_text'] else 0)+(1 if post['btn2_text'] else 0)}\n"
        f"<b>Создан:</b> {post['created_at'][:16]}"
    )
    try:
        await cb.message.edit_text(info, reply_markup=post_actions_kb(pid), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data.startswith("preview_post_"))
async def cb_preview_post(cb: types.CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer()
    pid  = int(cb.data.replace("preview_post_", ""))
    post = get_post(pid)
    if not post: return await cb.answer("Пост не найден.", show_alert=True)
    await send_post_preview(cb.from_user.id, dict(post))
    await cb.answer("Предпросмотр отправлен!")

@dp.callback_query(F.data.startswith("del_post_"))
async def cb_del_post(cb: types.CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer()
    pid = int(cb.data.replace("del_post_", ""))
    delete_post(pid)
    await cb.answer(f"Пост #{pid} удалён")
    await cb_my_posts(cb)

# ==================== РОЗЫГРЫШИ ====================
@dp.callback_query(F.data == "new_giv")
async def cb_new_giv(cb: types.CallbackQuery, state: FSMContext):
    if not is_owner(cb.from_user.id): return await cb.answer()
    await state.clear()
    tid = make_tmp_id(cb.from_user.id)
    _tmp[tid] = {}
    await state.update_data(tid=tid)
    try:
        await cb.message.edit_text(
            f"{EM_GIFT} <b>Новый розыгрыш — Шаг 1/5</b>\n\nВведи название розыгрыша:",
            reply_markup=back_kb("main"), parse_mode=ParseMode.HTML)
    except: pass
    await state.set_state(GiveawayBuilder.title)
    await cb.answer()

@dp.message(GiveawayBuilder.title)
async def giv_title(msg: types.Message, state: FSMContext):
    if not is_owner(msg.from_user.id): return
    d = await state.get_data(); _tmp[d["tid"]]["title"] = msg.text or ""
    await state.set_state(GiveawayBuilder.prize)
    await msg.answer(
        f"{EM_PRIZE} <b>Шаг 2/5 — Приз</b>\n\nЧто разыгрываем? Опиши приз:",
        reply_markup=back_kb("main"), parse_mode=ParseMode.HTML)

@dp.message(GiveawayBuilder.prize)
async def giv_prize(msg: types.Message, state: FSMContext):
    if not is_owner(msg.from_user.id): return
    d = await state.get_data(); _tmp[d["tid"]]["prize"] = msg.text or ""
    await state.set_state(GiveawayBuilder.winners)
    await msg.answer(
        f"{EM_RAND} <b>Шаг 3/5 — Количество победителей</b>\n\nСколько победителей? (число):",
        reply_markup=back_kb("main"), parse_mode=ParseMode.HTML)

@dp.message(GiveawayBuilder.winners)
async def giv_winners(msg: types.Message, state: FSMContext):
    if not is_owner(msg.from_user.id): return
    try: n = int(msg.text or "1")
    except: n = 1
    d = await state.get_data(); _tmp[d["tid"]]["winners"] = max(1, n)
    await state.set_state(GiveawayBuilder.end_date)
    await msg.answer(
        f"{EM_CLOCK} <b>Шаг 4/5 — Дата окончания</b>\n\nВведи дату окончания (например: 31.12.2025) или нажми Пропустить:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="skip_end_date", icon_custom_emoji_id=IK_OK)],
        ]), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "skip_end_date", GiveawayBuilder.end_date)
async def giv_skip_date(cb: types.CallbackQuery, state: FSMContext):
    d = await state.get_data(); _tmp[d["tid"]]["end_date"] = ""
    await state.set_state(GiveawayBuilder.condition)
    await cb.message.edit_text(
        f"{EM_WRITE} <b>Шаг 5/5 — Условие участия</b>\n\nОпиши условие (или нажми Пропустить):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="skip_condition", icon_custom_emoji_id=IK_OK)],
        ]), parse_mode=ParseMode.HTML)
    await cb.answer()

@dp.message(GiveawayBuilder.end_date)
async def giv_date(msg: types.Message, state: FSMContext):
    if not is_owner(msg.from_user.id): return
    d = await state.get_data(); _tmp[d["tid"]]["end_date"] = msg.text or ""
    await state.set_state(GiveawayBuilder.condition)
    await msg.answer(
        f"{EM_WRITE} <b>Шаг 5/5 — Условие участия</b>\n\nОпиши условие (или нажми Пропустить):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="skip_condition", icon_custom_emoji_id=IK_OK)],
        ]), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "skip_condition", GiveawayBuilder.condition)
async def giv_skip_cond(cb: types.CallbackQuery, state: FSMContext):
    d = await state.get_data(); _tmp[d["tid"]]["condition"] = ""
    await _save_giveaway(cb.message, d["tid"], state)
    await cb.answer()

@dp.message(GiveawayBuilder.condition)
async def giv_condition(msg: types.Message, state: FSMContext):
    if not is_owner(msg.from_user.id): return
    d = await state.get_data(); _tmp[d["tid"]]["condition"] = msg.text or ""
    await _save_giveaway(msg, d["tid"], state)

async def _save_giveaway(msg_obj, tid: str, state: FSMContext):
    data = _tmp.get(tid, {})
    gid  = save_giveaway(data)
    _tmp.pop(tid, None); await state.clear()
    gw = get_giveaway(gid)
    await msg_obj.answer(
        f"{EM_PARTY} <b>Розыгрыш #{gid} создан!</b>\n\n"
        f"{EM_TAG} Название: <b>{gw['title']}</b>\n"
        f"{EM_PRIZE} Приз: <b>{gw['prize']}</b>\n"
        f"{EM_RAND} Победителей: <b>{gw['winners_cnt']}</b>\n"
        f"{EM_CLOCK} Дата окончания: <b>{gw['end_date'] or 'Не указана'}</b>\n"
        f"{EM_WRITE} Условие: <b>{gw['condition'] or 'Не указано'}</b>\n\n"
        f"{EM_INFO} Участники добавляются через «Мои розыгрыши».",
        reply_markup=main_kb(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "my_givs")
async def cb_my_givs(cb: types.CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer()
    givs = get_giveaways()
    if not givs:
        try: await cb.message.edit_text(f"{EM_INFO} Розыгрышей пока нет.",
                                         reply_markup=back_kb(), parse_mode=ParseMode.HTML)
        except: pass
        return await cb.answer()
    rows = []
    for g in givs:
        icon = "🟢" if g["status"]=="active" else "🔴"
        rows.append([InlineKeyboardButton(
            text=f"{icon} #{g['id']} {g['title'][:25]}",
            callback_data=f"view_giv_{g['id']}", icon_custom_emoji_id=IK_GIFT)])
    rows.append([InlineKeyboardButton(text="Назад", callback_data="main", icon_custom_emoji_id=IK_BACK)])
    try:
        await cb.message.edit_text(
            f"{EM_PARTY} <b>Мои розыгрыши ({len(givs)})</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data.startswith("view_giv_"))
async def cb_view_giv(cb: types.CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer()
    gid = int(cb.data.replace("view_giv_", ""))
    gw  = get_giveaway(gid)
    if not gw: return await cb.answer("Не найден", show_alert=True)
    parts  = json.loads(gw["participants"] or "[]")
    winners= json.loads(gw["winners"] or "[]")
    text = (
        f"{EM_PARTY} <b>Розыгрыш #{gid}</b>\n\n"
        f"{EM_TAG} <b>Название:</b> {gw['title']}\n"
        f"{EM_PRIZE} <b>Приз:</b> {gw['prize']}\n"
        f"{EM_RAND} <b>Победителей:</b> {gw['winners_cnt']}\n"
        f"{EM_CLOCK} <b>Дата:</b> {gw['end_date'] or '—'}\n"
        f"{EM_WRITE} <b>Условие:</b> {gw['condition'] or '—'}\n"
        f"{EM_LIST} <b>Участников:</b> {len(parts)}\n"
        f"<b>Статус:</b> {'🟢 Активен' if gw['status']=='active' else '🔴 Завершён'}\n"
    )
    if winners:
        text += f"\n🏆 <b>Победители:</b> " + ", ".join([f"<code>{w}</code>" for w in winners])
    try:
        await cb.message.edit_text(text, reply_markup=giveaway_actions_kb(gid, gw["status"]),
                                   parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data.startswith("pick_"))
async def cb_pick_winners(cb: types.CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer()
    gid = int(cb.data.replace("pick_", ""))
    gw  = get_giveaway(gid)
    parts = json.loads(gw["participants"] or "[]")
    if not parts:
        await cb.answer("Участников нет! Добавьте участников.", show_alert=True); return
    winners = pick_winners(gid)
    w_text  = "\n".join([f"🏆 <code>{w}</code>" for w in winners])
    await cb.message.answer(
        f"{EM_PARTY} <b>Победители розыгрыша #{gid}!</b>\n\n{w_text}",
        parse_mode=ParseMode.HTML)
    await cb.answer("Победители выбраны!")
    await cb_view_giv(cb)

@dp.callback_query(F.data.startswith("parts_"))
async def cb_show_parts(cb: types.CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer()
    gid   = int(cb.data.replace("parts_", ""))
    gw    = get_giveaway(gid)
    parts = json.loads(gw["participants"] or "[]")
    text  = f"{EM_LIST} <b>Участники розыгрыша #{gid}</b>\n\n"
    if parts:
        text += "\n".join([f"• <code>{p}</code>" for p in parts])
    else:
        text += "Участников пока нет.\n\nДобавить участника — отправь команду:\n<code>/addpart {gid} ИМЯ_ИЛИ_ID</code>"
    await cb.message.answer(text, parse_mode=ParseMode.HTML)
    await cb.answer()

@dp.callback_query(F.data.startswith("del_giv_"))
async def cb_del_giv(cb: types.CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer()
    gid = int(cb.data.replace("del_giv_", ""))
    with db_conn() as c: c.execute("DELETE FROM giveaways WHERE id=?", (gid,))
    await cb.answer(f"Розыгрыш #{gid} удалён")
    await cb_my_givs(cb)

# Добавить участника
@dp.message(Command("addpart"))
async def cmd_addpart(msg: types.Message):
    if not is_owner(msg.from_user.id): return
    parts_cmd = (msg.text or "").split(maxsplit=2)
    if len(parts_cmd) < 3:
        await msg.answer(f"{EM_ERR} Формат: /addpart [ID розыгрыша] [имя или ID участника]",
                         parse_mode=ParseMode.HTML); return
    try: gid = int(parts_cmd[1])
    except:
        await msg.answer(f"{EM_ERR} ID розыгрыша должен быть числом.", parse_mode=ParseMode.HTML); return
    participant = parts_cmd[2].strip()
    gw = get_giveaway(gid)
    if not gw: await msg.answer(f"{EM_ERR} Розыгрыш #{gid} не найден.", parse_mode=ParseMode.HTML); return
    parts = json.loads(gw["participants"] or "[]")
    if participant in parts:
        await msg.answer(f"{EM_ERR} <code>{participant}</code> уже в списке участников.", parse_mode=ParseMode.HTML); return
    parts.append(participant)
    with db_conn() as c: c.execute("UPDATE giveaways SET participants=? WHERE id=?", (json.dumps(parts, ensure_ascii=False), gid))
    await msg.answer(f"{EM_OK} <code>{participant}</code> добавлен в розыгрыш #{gid}. Всего участников: {len(parts)}",
                     parse_mode=ParseMode.HTML)

# ==================== СЛУЧАЙНЫЙ ПОБЕДИТЕЛЬ ====================
@dp.callback_query(F.data == "rng_winner")
async def cb_rng(cb: types.CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer()
    try:
        await cb.message.edit_text(
            f"{EM_RAND} <b>Случайный победитель</b>\n\n"
            f"Отправь список участников (каждый с новой строки) командой:\n\n"
            f"<code>/pick\nИмя1\nИмя2\nИмя3</code>\n\n"
            f"Или через пробел: <code>/pick Имя1 Имя2 Имя3</code>",
            reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.message(Command("pick"))
async def cmd_pick(msg: types.Message):
    if not is_owner(msg.from_user.id): return
    text = (msg.text or "").replace("/pick", "", 1).strip()
    if not text:
        await msg.answer(f"{EM_ERR} Укажи участников после /pick", parse_mode=ParseMode.HTML); return
    parts = [p.strip() for p in re.split(r'[\n,]+', text) if p.strip()]
    if len(parts) < 2:
        parts = text.split()
    if not parts:
        await msg.answer(f"{EM_ERR} Нет участников.", parse_mode=ParseMode.HTML); return
    winner = random.choice(parts)
    await msg.answer(
        f"{EM_PARTY} <b>Победитель выбран!</b>\n\n"
        f"Участников: <b>{len(parts)}</b>\n\n"
        f"🏆 <b>Победитель: <code>{winner}</code></b>\n\n"
        f"<i>Поздравляем!</i>",
        parse_mode=ParseMode.HTML)

# ==================== ПОСЕТИТЕЛИ ====================
@dp.callback_query(F.data == "visitors")
async def cb_visitors(cb: types.CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer()
    rows = get_visitors()
    if not rows:
        try: await cb.message.edit_text(f"{EM_INFO} Пока никто не открывал бота.",
                                         reply_markup=back_kb(), parse_mode=ParseMode.HTML)
        except: pass
        return await cb.answer()
    lines = []
    for r in rows[:30]:
        name = f"@{r['username']}" if r['username'] else f"{r['first_name']} {r['last_name'] or ''}".strip()
        lines.append(
            f"• <code>{r['user_id']}</code> {name}\n"
            f"  Заходов: <b>{r['visits']}</b> | Последний: <b>{str(r['last_seen'])[:16]}</b>")
    text = f"{EM_LIST} <b>Все кто открывал бота ({len(rows)})</b>\n\n" + "\n".join(lines)
    try:
        await cb.message.edit_text(text, reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    except:
        await cb.message.answer(text, reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    await cb.answer()

# ==================== СТАТИСТИКА ====================
@dp.callback_query(F.data == "stats")
async def cb_stats(cb: types.CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer()
    visitors = get_visitors()
    posts    = get_posts()
    givs     = get_giveaways()
    active   = sum(1 for g in givs if g["status"]=="active")
    total_vis= sum(r["visits"] for r in visitors)
    try:
        await cb.message.edit_text(
            f"{EM_STAT} <b>Статистика</b>\n\n"
            f"{EM_PERSON} Уникальных посетителей: <b>{len(visitors)}</b>\n"
            f"{EM_LIST} Всего заходов: <b>{total_vis}</b>\n"
            f"{EM_TAG} Сохранённых постов: <b>{len(posts)}</b>\n"
            f"{EM_GIFT} Всего розыгрышей: <b>{len(givs)}</b>\n"
            f"{EM_PARTY} Активных розыгрышей: <b>{active}</b>",
            reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

# ==================== ЗАПУСК ====================
async def main():
    init_db()
    await bot.set_my_commands([
        types.BotCommand(command="start",   description="Главное меню"),
        types.BotCommand(command="pick",    description="Выбрать победителя из списка"),
        types.BotCommand(command="addpart", description="Добавить участника в розыгрыш"),
    ])
    print("🎁 FakePost Bot запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
