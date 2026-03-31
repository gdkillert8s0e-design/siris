# ── SSL-патч для Windows ─────────────────────────────────────────────────
import ssl as _ssl
_ssl._create_default_https_context = _ssl._create_unverified_context
# ─────────────────────────────────────────────────────────────────────────

import asyncio, json, logging, math, sqlite3, time
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery,
    BotCommand, BotCommandScopeChat, BotCommandScopeDefault,
    MessageEntity,
)
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

try:
    from aiocryptopay import AioCryptoPay, Networks
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ==================== НАСТРОЙКИ — ВСТАВЬ СВОИ ДАННЫЕ ====================
BOT_TOKEN    = "ВАШ_BOT_TOKEN"
ADMIN_IDS    = [5883796026, 1989613788]   # список ID администраторов
CHANNEL_ID   = -1001234567890             # ID приватного канала (отрицательное число)
CRYPTO_TOKEN = "ВАШ_CRYPTOBOT_TOKEN"     # токен от @CryptoBot (или "" чтобы отключить)
RUB_TO_USDT  = 90.0                       # курс: 1 USDT ≈ 90 рублей
STARS_RATE   = 1.5                        # 1 рубль = 1.5 звезды
# ========================================================================

# ── Премиум эмодзи ──────────────────────────────────────────────────────
def tge(eid, fb=""):
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

EM_GEAR    = tge("5870982283724328568", "⚙")
EM_PROFILE = tge("5870994129244131212", "👤")
EM_STATS   = tge("5870921681735781843", "📊")
EM_GROWTH  = tge("5870930636742595124", "📈")
EM_OK      = tge("5870633910337015697", "✅")
EM_ERR     = tge("5870657884844462243", "❌")
EM_PENCIL  = tge("5870676941614354370", "✏")
EM_TRASH   = tge("5870875489362513438", "🗑")
EM_BELL    = tge("6039486778597970865", "🔔")
EM_GIFT    = tge("6032644646587338669", "🎁")
EM_HORN    = tge("6039422865189638057", "📣")
EM_INFO    = tge("6028435952299413210", "ℹ")
EM_BOT     = tge("6030400221232501136", "🤖")
EM_WALLET  = tge("5769126056262898415", "👛")
EM_CLOCK   = tge("5775896410780079073", "🕓")
EM_PARTY   = tge("6041731551845159060", "🎉")
EM_LINK    = tge("5769289093221454192", "🔗")
EM_UP      = tge("5963103826075456248", "⬆")
EM_DOWN    = tge("6039802767931871481", "⬇")
EM_CAL     = tge("5890937706803894250", "📅")
EM_TAG     = tge("5886285355279193209", "🏷")
EM_MEDIA   = tge("6035128606563241721", "🖼")
EM_WRITE   = tge("5870753782874246579", "✍")
EM_RELOAD  = tge("5345906554510012647", "🔄")
EM_MONEY   = tge("5904462880941545555", "🪙")
EM_CRYPTO  = tge("5260752406890711732", "👾")
EM_FILE    = tge("5870528606328852614", "📁")

# ID для icon_custom_emoji_id в кнопках
IK_MONEY  = "5904462880941545555"
IK_CLOCK  = "5775896410780079073"
IK_STATS  = "5870921681735781843"
IK_PENCIL = "5870676941614354370"
IK_INFO   = "6028435952299413210"
IK_MEDIA  = "6035128606563241721"
IK_PRICE  = "5904462880941545555"
IK_DUR    = "5775896410780079073"
IK_HORN   = "6039422865189638057"
IK_OK     = "5870633910337015697"
IK_ERR    = "5870657884844462243"
IK_LINK   = "5769289093221454192"
IK_CRYPTO = "5260752406890711732"
IK_STARS  = "6032644646587338669"
IK_BACK   = "5893057118545646106"
IK_MEDIA2 = "5870528606328852614"
IK_PENCIL2= "5870676941614354370"

# ── БД ──────────────────────────────────────────────────────────────────
_db = sqlite3.connect("channel_bot.db", check_same_thread=False)
_db.row_factory = sqlite3.Row
_db.execute("PRAGMA journal_mode=WAL")

def init_db():
    _db.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            tg_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            joined_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS subscriptions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            started_at TEXT DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            warned INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount_rub REAL NOT NULL,
            method TEXT NOT NULL,
            invoice_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            paid_at TEXT
        );
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        );
    """)
    defs = {
        "price_rub":               "100",
        "duration_minutes":        "43200",
        "start_media_id":          "",
        "start_media_type":        "",
        "help_media_id":           "",
        "help_media_type":         "",
        "start_message_text":      f"👋 Добро пожаловать!\n\nПолучи доступ к нашему приватному каналу.",
        "start_message_entities":  "[]",
        "help_message_text":       "ℹ Помощь\n\n• /start — главное меню\n• /help — помощь\n\nДля покупки нажми Купить.",
        "help_message_entities":   "[]",
    }
    for k, v in defs.items():
        _db.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))
    _db.commit()

def gs(key): 
    r = _db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return r["value"] if r else ""

def ss(key, val):
    _db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, val))
    _db.commit()

def save_msg_data(key: str, message: Message):
    text = message.text or message.caption or ""
    ents = message.entities or message.caption_entities or []
    ss(key + "_text",     text)
    ss(key + "_entities", json.dumps([e.model_dump() for e in ents], ensure_ascii=False))

def load_msg_data(key: str) -> tuple[str, list]:
    text = gs(key + "_text")
    raw  = gs(key + "_entities")
    ents = []
    if raw:
        try:
            ents = [MessageEntity(**d) for d in json.loads(raw)]
        except: pass
    return text, ents

def upsert_user(tg_id, username, first_name):
    _db.execute("""
        INSERT INTO users(tg_id,username,first_name) VALUES(?,?,?)
        ON CONFLICT(tg_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name
    """, (tg_id, username or "", first_name or ""))
    _db.commit()

def get_active_sub(user_id):
    return _db.execute("""
        SELECT * FROM subscriptions WHERE user_id=? AND is_active=1 AND expires_at>datetime('now')
        ORDER BY expires_at DESC LIMIT 1
    """, (user_id,)).fetchone()

def add_subscription(user_id: int, dur_m: int) -> str:
    exp = (datetime.now(timezone.utc) + timedelta(minutes=dur_m)).isoformat()
    _db.execute("UPDATE subscriptions SET is_active=0 WHERE user_id=?", (user_id,))
    _db.execute("INSERT INTO subscriptions(user_id,expires_at) VALUES(?,?)", (user_id, exp))
    _db.commit()
    return exp

def add_payment(user_id, amount_rub, method, invoice_id=None):
    cur = _db.execute(
        "INSERT INTO payments(user_id,amount_rub,method,invoice_id) VALUES(?,?,?,?)",
        (user_id, amount_rub, method, invoice_id))
    _db.commit()
    return cur.lastrowid

def confirm_by_invoice(invoice_id: str):
    row = _db.execute(
        "SELECT * FROM payments WHERE invoice_id=? AND status='pending' LIMIT 1",
        (invoice_id,)).fetchone()
    if row:
        _db.execute("UPDATE payments SET status='paid',paid_at=datetime('now') WHERE id=?", (row["id"],))
        _db.commit()
    return row

def get_stats():
    def income(days):
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        r = _db.execute("SELECT COALESCE(SUM(amount_rub),0) s FROM payments WHERE status='paid' AND paid_at>=?", (since,)).fetchone()
        return r["s"] if r else 0.0
    return dict(
        total_users=_db.execute("SELECT COUNT(*) c FROM users").fetchone()["c"],
        active_subs=_db.execute("SELECT COUNT(*) c FROM subscriptions WHERE is_active=1 AND expires_at>datetime('now')").fetchone()["c"],
        income_day=income(1), income_week=income(7), income_month=income(30),
        income_year=income(365),
        income_all=_db.execute("SELECT COALESCE(SUM(amount_rub),0) s FROM payments WHERE status='paid'").fetchone()["s"],
    )

# ── Утилиты ──────────────────────────────────────────────────────────────
def fmt_rub(v): return f"{float(v):,.0f} ₽".replace(",", " ")

def fmt_dur(m):
    m = int(m)
    if m < 60:    return f"{m} мин."
    if m < 1440:  return f"{m//60} ч."
    if m < 10080: return f"{m//1440} дн."
    if m < 43200: return f"{m//10080} нед."
    return f"{m//43200} мес."

def fmt_left(expires_at: str) -> str:
    exp = datetime.fromisoformat(expires_at)
    if exp.tzinfo is None: exp = exp.replace(tzinfo=timezone.utc)
    delta = exp - datetime.now(timezone.utc)
    if delta.total_seconds() <= 0: return "истекла"
    s = int(delta.total_seconds())
    d, h, mi = s//86400, (s%86400)//3600, (s%3600)//60
    parts = []
    if d:  parts.append(f"{d} дн.")
    if h:  parts.append(f"{h} ч.")
    if mi: parts.append(f"{mi} мин.")
    return " ".join(parts) or "меньше минуты"

# ── FSM ──────────────────────────────────────────────────────────────────
class AdminSt(StatesGroup):
    edit_start   = State()
    edit_help    = State()
    media_choice = State()
    media_file   = State()
    edit_price   = State()
    dur_value    = State()
    dur_unit     = State()
    bc_message   = State()
    bc_btn_choice= State()
    bc_btn_text  = State()
    bc_btn_url   = State()

# ── Инициализация бота ────────────────────────────────────────────────────
bot    = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp     = Dispatcher(storage=MemoryStorage())
crypto = AioCryptoPay(token=CRYPTO_TOKEN, network=Networks.MAIN_NET) if (HAS_CRYPTO and CRYPTO_TOKEN and CRYPTO_TOKEN != "ВАШ_CRYPTOBOT_TOKEN") else None

# ── Клавиатуры ───────────────────────────────────────────────────────────
def kb_start(has_sub: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="Купить", callback_data="buy", icon_custom_emoji_id=IK_MONEY)]]
    if has_sub:
        rows.append([InlineKeyboardButton(text="Моя подписка", callback_data="my_stat", icon_custom_emoji_id=IK_CLOCK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Статистика",        callback_data="adm_stats",  icon_custom_emoji_id=IK_STATS),
         InlineKeyboardButton(text="Стартовое сообщ.",  callback_data="adm_start",  icon_custom_emoji_id=IK_PENCIL)],
        [InlineKeyboardButton(text="Help сообщение",    callback_data="adm_help",   icon_custom_emoji_id=IK_INFO),
         InlineKeyboardButton(text="Медиа",             callback_data="adm_media",  icon_custom_emoji_id=IK_MEDIA)],
        [InlineKeyboardButton(text="Цена подписки",     callback_data="adm_price",  icon_custom_emoji_id=IK_PRICE),
         InlineKeyboardButton(text="Срок подписки",     callback_data="adm_dur",    icon_custom_emoji_id=IK_DUR)],
        [InlineKeyboardButton(text="Рассылка",          callback_data="adm_bc",     icon_custom_emoji_id=IK_HORN)],
    ])

def kb_back_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Назад", callback_data="back_admin", icon_custom_emoji_id=IK_BACK)
    ]])

def kb_back_start() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Назад", callback_data="back_start", icon_custom_emoji_id=IK_BACK)
    ]])

def kb_pay() -> InlineKeyboardMarkup:
    rows = []
    if crypto:
        rows.append([InlineKeyboardButton(text="CryptoBot (USDT)", callback_data="pay_crypto", icon_custom_emoji_id=IK_CRYPTO)])
    rows.append([InlineKeyboardButton(text="Telegram Stars", callback_data="pay_stars", icon_custom_emoji_id=IK_STARS)])
    rows.append([InlineKeyboardButton(text="Назад", callback_data="back_start", icon_custom_emoji_id=IK_BACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_media_choice() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Для /start",  callback_data="media_for_start", icon_custom_emoji_id=IK_PENCIL2)],
        [InlineKeyboardButton(text="Для /help",   callback_data="media_for_help",  icon_custom_emoji_id=IK_INFO)],
        [InlineKeyboardButton(text="Назад",       callback_data="back_admin",      icon_custom_emoji_id=IK_BACK)],
    ])

DUR_MUL = {"dur_min":1,"dur_hour":60,"dur_day":1440,"dur_week":10080,"dur_month":43200}

def kb_dur_units() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Минуты",callback_data="dur_min"),
         InlineKeyboardButton(text="Часы",  callback_data="dur_hour")],
        [InlineKeyboardButton(text="Дни",   callback_data="dur_day"),
         InlineKeyboardButton(text="Недели",callback_data="dur_week")],
        [InlineKeyboardButton(text="Месяцы",callback_data="dur_month")],
        [InlineKeyboardButton(text="Назад", callback_data="back_admin", icon_custom_emoji_id=IK_BACK)],
    ])

def kb_bc_btn_choice() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да, добавить кнопку",   callback_data="bc_btn_yes", icon_custom_emoji_id=IK_OK)],
        [InlineKeyboardButton(text="Нет, отправить сразу",  callback_data="bc_btn_no",  icon_custom_emoji_id=IK_HORN)],
        [InlineKeyboardButton(text="Отмена",                callback_data="back_admin", icon_custom_emoji_id=IK_BACK)],
    ])

def success_kb(invite_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Вступить в канал", url=invite_url, icon_custom_emoji_id=IK_LINK)
    ]])

# ── Вспомогательные функции ──────────────────────────────────────────────
async def _del(msg: Message):
    try: await msg.delete()
    except: pass

async def send_start(target, edit=False):
    uid        = target.from_user.id
    kb         = kb_start(bool(get_active_sub(uid)))
    text, ents = load_msg_data("start_message")
    media_id   = gs("start_media_id")
    media_type = gs("start_media_type")
    msg: Message = target if isinstance(target, Message) else target.message

    if edit:
        await _del(msg)

    pm = None if ents else ParseMode.HTML
    chat_id = msg.chat.id

    if media_id:
        send = {"caption":text,"reply_markup":kb,
                "caption_entities":ents or None,"parse_mode":pm}
        if media_type == "photo":
            await bot.send_photo(chat_id, media_id, **send)
        elif media_type == "video":
            await bot.send_video(chat_id, media_id, **send)
        elif media_type == "animation":
            await bot.send_animation(chat_id, media_id, **send)
        else:
            await bot.send_message(chat_id, text, reply_markup=kb,
                                   entities=ents or None, parse_mode=pm)
    else:
        await bot.send_message(chat_id, text, reply_markup=kb,
                               entities=ents or None, parse_mode=pm)

async def send_admin_panel(target, edit=False):
    text = f'{EM_GEAR} <b>Панель администратора</b>\n\nВыберите раздел:'
    msg: Message = target if isinstance(target, Message) else target.message
    if edit:
        try: await msg.edit_text(text, reply_markup=kb_admin())
        except: await msg.answer(text, reply_markup=kb_admin())
    else:
        await msg.answer(text, reply_markup=kb_admin())

async def grant_access(user_id: int, dur_m: int) -> Optional[str]:
    try:
        expire_ts = int(time.time()) + (dur_m + 120) * 60
        link = await bot.create_chat_invite_link(CHANNEL_ID, member_limit=1, expire_date=expire_ts)
        return link.invite_link
    except Exception as ex:
        logger.error(f"create_chat_invite_link: {ex}")
        return None

async def notify_success(chat_id: int, dur_m: int):
    invite = await grant_access(chat_id, dur_m)
    text = (
        f'{EM_PARTY} <b>Оплата прошла успешно!</b>\n\n'
        f'{EM_OK} Подписка активирована на <b>{fmt_dur(dur_m)}</b>.\n\n'
        f'{EM_LINK} Одноразовая ссылка для вступления в канал:'
    )
    if invite:
        await bot.send_message(chat_id, text, reply_markup=success_kb(invite))
    else:
        await bot.send_message(chat_id, text + "\n\n<i>(Ошибка создания ссылки, обратитесь к администратору)</i>")

# ── Команды ──────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(msg: Message):
    upsert_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
    await send_start(msg)

@dp.message(Command("help"))
async def cmd_help(msg: Message):
    text, ents = load_msg_data("help_message")
    media_id   = gs("help_media_id")
    media_type = gs("help_media_type")
    pm = None if ents else ParseMode.HTML
    cap_ents = ents or None
    if media_id:
        send = {"caption":text,"caption_entities":cap_ents,"parse_mode":pm}
        if media_type == "photo":      await msg.answer_photo(media_id, **send)
        elif media_type == "video":    await msg.answer_video(media_id, **send)
        elif media_type == "animation":await msg.answer_animation(media_id, **send)
        else: await msg.answer(text, entities=cap_ents, parse_mode=pm)
    else:
        await msg.answer(text, entities=cap_ents, parse_mode=pm)

@dp.message(Command("admin"))
async def cmd_admin(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer(f'{EM_ERR} <b>Нет доступа.</b>')
        return
    await send_admin_panel(msg)

# ── Юзер-колбэки ─────────────────────────────────────────────────────────
@dp.callback_query(F.data == "back_start")
async def cb_back_start(cb: CallbackQuery):
    await send_start(cb, edit=True)
    await cb.answer()

@dp.callback_query(F.data == "buy")
async def cb_buy(cb: CallbackQuery):
    price = float(gs("price_rub"))
    dur_m = int(gs("duration_minutes"))
    stars = math.ceil(price * STARS_RATE)
    usdt  = round(price / RUB_TO_USDT, 2)
    await _del(cb.message)
    await bot.send_message(
        cb.from_user.id,
        f'{EM_WALLET} <b>Покупка подписки</b>\n\n'
        f'{EM_TAG} Срок: <b>{fmt_dur(dur_m)}</b>\n'
        f'{EM_MONEY} Цена: <b>{fmt_rub(price)}</b>\n'
        f'В звёздах: <b>{stars} ⭐</b>\n'
        f'В USDT: <b>{usdt}</b>\n\n'
        f'Выберите способ оплаты:',
        reply_markup=kb_pay()
    )
    await cb.answer()

@dp.callback_query(F.data == "my_stat")
async def cb_my_stat(cb: CallbackQuery):
    sub = get_active_sub(cb.from_user.id)
    if not sub:
        await cb.answer("У вас нет активной подписки.", show_alert=True); return
    remaining = fmt_left(sub["expires_at"])
    exp_fmt   = sub["expires_at"][:16].replace("T"," ")
    await _del(cb.message)
    await bot.send_message(
        cb.from_user.id,
        f'{EM_CLOCK} <b>Ваша подписка</b>\n\n'
        f'{EM_CAL} Истекает: <b>{exp_fmt} UTC</b>\n'
        f'{EM_OK} Осталось: <b>{remaining}</b>',
        reply_markup=kb_back_start()
    )
    await cb.answer()

# ── Оплата CryptoBot ─────────────────────────────────────────────────────
@dp.callback_query(F.data == "pay_crypto")
async def cb_pay_crypto(cb: CallbackQuery):
    if not crypto:
        await cb.answer("CryptoBot не настроен.", show_alert=True); return
    price_rub = float(gs("price_rub"))
    usdt      = round(price_rub / RUB_TO_USDT, 2)
    dur_m     = int(gs("duration_minutes"))
    try:
        invoice = await crypto.create_invoice(
            asset="USDT", amount=usdt,
            description=f"Подписка на канал ({fmt_dur(dur_m)})",
            payload=str(cb.from_user.id),
        )
        add_payment(cb.from_user.id, price_rub, "cryptobot", str(invoice.invoice_id))
        await cb.message.edit_text(
            f'{EM_CRYPTO} <b>Оплата через CryptoBot</b>\n\n'
            f'{EM_MONEY} Сумма: <b>{usdt} USDT</b>\n\n'
            f'Нажмите «Оплатить», затем вернитесь и нажмите «Проверить».\n'
            f'{EM_RELOAD} Бот также проверяет автоматически каждые 30 сек.',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Оплатить",        url=invoice.bot_invoice_url, icon_custom_emoji_id=IK_LINK)],
                [InlineKeyboardButton(text="Проверить оплату",callback_data=f"chk_{invoice.invoice_id}", icon_custom_emoji_id=IK_OK)],
                [InlineKeyboardButton(text="Назад",            callback_data="buy", icon_custom_emoji_id=IK_BACK)],
            ])
        )
    except Exception as ex:
        logger.error(f"CryptoBot invoice error: {ex}")
        await cb.answer("Ошибка при создании счёта.", show_alert=True)
    await cb.answer()

@dp.callback_query(F.data.startswith("chk_"))
async def cb_check_crypto(cb: CallbackQuery):
    if not crypto:
        await cb.answer("CryptoBot не настроен.", show_alert=True); return
    invoice_id = cb.data[4:]
    try:
        result = await crypto.get_invoices(invoice_ids=[int(invoice_id)])
        items  = result if isinstance(result, list) else (result.items if hasattr(result, "items") else [])
        if not items:
            await cb.answer("Счёт не найден.", show_alert=True); return
        inv = items[0]
        if inv.status == "paid":
            row = confirm_by_invoice(invoice_id)
            if row:
                dur_m = int(gs("duration_minutes"))
                add_subscription(row["user_id"], dur_m)
                invite = await grant_access(row["user_id"], dur_m)
                text = (f'{EM_PARTY} <b>Оплата подтверждена!</b>\n\n'
                        f'{EM_OK} Подписка на <b>{fmt_dur(dur_m)}</b>.\n\n'
                        f'{EM_LINK} Одноразовая ссылка:')
                if invite:
                    await cb.message.edit_text(text, reply_markup=success_kb(invite))
                else:
                    await cb.message.edit_text(text + "\n\n<i>(Обратитесь к администратору)</i>")
            else:
                await cb.answer("Уже обработано.", show_alert=True)
        else:
            await cb.answer(f"Ещё не оплачено (статус: {inv.status}).", show_alert=True)
    except Exception as ex:
        logger.error(f"chk_crypto error: {ex}")
        await cb.answer("Ошибка проверки.", show_alert=True)
    await cb.answer()

# ── Оплата Stars ─────────────────────────────────────────────────────────
@dp.callback_query(F.data == "pay_stars")
async def cb_pay_stars(cb: CallbackQuery):
    price_rub = float(gs("price_rub"))
    stars     = math.ceil(price_rub * STARS_RATE)
    dur_m     = int(gs("duration_minutes"))
    try: await cb.message.delete()
    except: pass
    await bot.send_invoice(
        chat_id=cb.from_user.id,
        title="Подписка на канал",
        description=f"Доступ к приватному каналу на {fmt_dur(dur_m)}",
        payload=f"stars_{cb.from_user.id}",
        currency="XTR",
        prices=[LabeledPrice(label="Подписка", amount=stars)],
    )
    await cb.answer()

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def on_payment(msg: Message):
    payload   = msg.successful_payment.invoice_payload
    user_id   = int(payload.split("_")[1])
    price_rub = float(gs("price_rub"))
    dur_m     = int(gs("duration_minutes"))
    inv_key   = f"stars_{msg.message_id}_{user_id}"
    add_payment(user_id, price_rub, "stars", inv_key)
    confirm_by_invoice(inv_key)
    add_subscription(user_id, dur_m)
    await notify_success(user_id, dur_m)

# ── Админ-колбэки ────────────────────────────────────────────────────────
@dp.callback_query(F.data == "back_admin")
async def cb_back_admin(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return await cb.answer()
    await state.clear()
    await send_admin_panel(cb, edit=True)
    await cb.answer()

@dp.callback_query(F.data == "adm_stats")
async def cb_adm_stats(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS: return await cb.answer()
    s = get_stats()
    await cb.message.edit_text(
        f'{EM_STATS} <b>Статистика бота</b>\n\n'
        f'{EM_BOT} Всего пользователей: <b>{s["total_users"]}</b>\n'
        f'{EM_OK} Активных подписок: <b>{s["active_subs"]}</b>\n\n'
        f'{EM_GROWTH} <b>Доходы:</b>\n'
        f'  За день:      <b>{fmt_rub(s["income_day"])}</b>\n'
        f'  За неделю:    <b>{fmt_rub(s["income_week"])}</b>\n'
        f'  За месяц:     <b>{fmt_rub(s["income_month"])}</b>\n'
        f'  За год:       <b>{fmt_rub(s["income_year"])}</b>\n'
        f'  За всё время: <b>{fmt_rub(s["income_all"])}</b>',
        reply_markup=kb_back_admin()
    )
    await cb.answer()

@dp.callback_query(F.data == "adm_start")
async def cb_adm_start(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return await cb.answer()
    cur = gs("start_message_text")
    await cb.message.edit_text(
        f'{EM_PENCIL} <b>Редактирование стартового сообщения</b>\n\n'
        f'<b>Текущий текст:</b>\n<blockquote>{cur[:300]}</blockquote>\n\n'
        f'{EM_INFO} Отправьте новый текст. Поддерживаются HTML и премиум эмодзи.',
        reply_markup=kb_back_admin()
    )
    await state.set_state(AdminSt.edit_start)
    await cb.answer()

@dp.message(AdminSt.edit_start)
async def msg_edit_start(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS: return
    save_msg_data("start_message", msg)
    await msg.answer(f'{EM_OK} <b>Стартовое сообщение обновлено!</b>', reply_markup=kb_back_admin())
    await state.clear()

@dp.callback_query(F.data == "adm_help")
async def cb_adm_help(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return await cb.answer()
    cur = gs("help_message_text")
    await cb.message.edit_text(
        f'{EM_INFO} <b>Редактирование Help-сообщения</b>\n\n'
        f'<b>Текущий текст:</b>\n<blockquote>{cur[:300]}</blockquote>\n\n'
        f'{EM_INFO} Отправьте новый текст. Поддерживаются HTML и премиум эмодзи.',
        reply_markup=kb_back_admin()
    )
    await state.set_state(AdminSt.edit_help)
    await cb.answer()

@dp.message(AdminSt.edit_help)
async def msg_edit_help(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS: return
    save_msg_data("help_message", msg)
    await msg.answer(f'{EM_OK} <b>Help-сообщение обновлено!</b>', reply_markup=kb_back_admin())
    await state.clear()

@dp.callback_query(F.data == "adm_media")
async def cb_adm_media(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return await cb.answer()
    st = gs("start_media_type") or "нет"
    ht = gs("help_media_type")  or "нет"
    await cb.message.edit_text(
        f'{EM_MEDIA} <b>Управление медиа</b>\n\n'
        f'Стартовое сообщение: <b>{st}</b>\n'
        f'Help-сообщение: <b>{ht}</b>\n\n'
        f'Для какого сообщения изменить медиа?',
        reply_markup=kb_media_choice()
    )
    await state.set_state(AdminSt.media_choice)
    await cb.answer()

@dp.callback_query(F.data.in_({"media_for_start","media_for_help"}))
async def cb_media_for(cb: CallbackQuery, state: FSMContext):
    which = "start" if cb.data == "media_for_start" else "help"
    await state.update_data(media_which=which)
    label = "стартового" if which == "start" else "help"
    await cb.message.edit_text(
        f'{EM_MEDIA} Отправьте <b>фото, видео или GIF</b> для {label} сообщения.\n\n'
        f'Или напишите <code>удалить</code> для удаления текущего медиа.',
        reply_markup=kb_back_admin()
    )
    await state.set_state(AdminSt.media_file)
    await cb.answer()

@dp.message(AdminSt.media_file)
async def msg_media_file(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS: return
    data  = await state.get_data()
    which = data.get("media_which", "start")
    if msg.text and msg.text.strip().lower() == "удалить":
        ss(f"{which}_media_id", ""); ss(f"{which}_media_type", "")
        await msg.answer(f'{EM_TRASH} Медиа удалено.', reply_markup=kb_back_admin())
    elif msg.photo:
        ss(f"{which}_media_id", msg.photo[-1].file_id); ss(f"{which}_media_type", "photo")
        await msg.answer(f'{EM_OK} Фото сохранено.', reply_markup=kb_back_admin())
    elif msg.video:
        ss(f"{which}_media_id", msg.video.file_id); ss(f"{which}_media_type", "video")
        await msg.answer(f'{EM_OK} Видео сохранено.', reply_markup=kb_back_admin())
    elif msg.animation:
        ss(f"{which}_media_id", msg.animation.file_id); ss(f"{which}_media_type", "animation")
        await msg.answer(f'{EM_OK} GIF сохранено.', reply_markup=kb_back_admin())
    else:
        await msg.answer(f'{EM_ERR} Отправьте фото, видео или GIF.'); return
    await state.clear()

@dp.callback_query(F.data == "adm_price")
async def cb_adm_price(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return await cb.answer()
    price = float(gs("price_rub"))
    stars = math.ceil(price * STARS_RATE)
    usdt  = round(price / RUB_TO_USDT, 2)
    await cb.message.edit_text(
        f'{EM_MONEY} <b>Управление ценой</b>\n\n'
        f'Текущая цена: <b>{fmt_rub(price)}</b>\n'
        f'В звёздах: <b>{stars} ⭐</b>\n'
        f'В USDT: <b>{usdt}</b>\n\n'
        f'{EM_WRITE} Введите новую цену в рублях:',
        reply_markup=kb_back_admin()
    )
    await state.set_state(AdminSt.edit_price)
    await cb.answer()

@dp.message(AdminSt.edit_price)
async def msg_edit_price(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS: return
    try:
        price = float(msg.text.strip().replace(",","."))
        if price <= 0: raise ValueError
        ss("price_rub", str(price))
        stars = math.ceil(price * STARS_RATE)
        usdt  = round(price / RUB_TO_USDT, 2)
        await msg.answer(
            f'{EM_OK} Цена обновлена:\n{EM_MONEY} <b>{fmt_rub(price)}</b> = <b>{stars} ⭐</b> = <b>{usdt} USDT</b>',
            reply_markup=kb_back_admin())
        await state.clear()
    except:
        await msg.answer(f'{EM_ERR} Введите корректное число, например: <code>150</code>')

@dp.callback_query(F.data == "adm_dur")
async def cb_adm_dur(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return await cb.answer()
    dur = int(gs("duration_minutes"))
    await cb.message.edit_text(
        f'{EM_CLOCK} <b>Управление сроком подписки</b>\n\n'
        f'Текущий срок: <b>{fmt_dur(dur)}</b> ({dur} мин.)\n\n'
        f'{EM_WRITE} Введите числовое значение (например: 30, 7, 1):',
        reply_markup=kb_back_admin()
    )
    await state.set_state(AdminSt.dur_value)
    await cb.answer()

@dp.message(AdminSt.dur_value)
async def msg_dur_value(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS: return
    try:
        val = int(msg.text.strip())
        if val <= 0: raise ValueError
        await state.update_data(dur_val=val)
        await msg.answer(
            f'{EM_CLOCK} Значение: <b>{val}</b>. Выберите единицу времени:',
            reply_markup=kb_dur_units())
        await state.set_state(AdminSt.dur_unit)
    except:
        await msg.answer(f'{EM_ERR} Введите целое положительное число, например: <code>30</code>')

@dp.callback_query(F.data.in_(set(DUR_MUL.keys())))
async def cb_dur_unit(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return await cb.answer()
    data    = await state.get_data()
    val     = data.get("dur_val", 1)
    minutes = val * DUR_MUL[cb.data]
    ss("duration_minutes", str(minutes))
    await cb.message.edit_text(
        f'{EM_OK} Срок подписки обновлён: <b>{fmt_dur(minutes)}</b> ({minutes} мин.)',
        reply_markup=kb_back_admin())
    await state.clear()
    await cb.answer()

# ── Рассылка ─────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "adm_bc")
async def cb_adm_bc(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return await cb.answer()
    await cb.message.edit_text(
        f'{EM_HORN} <b>Рассылка</b>\n\n'
        f'Отправьте сообщение для рассылки.\n'
        f'{EM_INFO} Поддерживаются: HTML, премиум эмодзи, фото, видео, GIF.',
        reply_markup=kb_back_admin())
    await state.set_state(AdminSt.bc_message)
    await cb.answer()

@dp.message(AdminSt.bc_message)
async def msg_bc_message(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS: return
    text = msg.text or msg.caption or ""
    ents = msg.entities or msg.caption_entities or []
    bc = {
        "text":     text,
        "entities": [e.model_dump() for e in ents],
        "photo_id": msg.photo[-1].file_id if msg.photo else None,
        "video_id": msg.video.file_id      if msg.video else None,
        "anim_id":  msg.animation.file_id  if msg.animation else None,
    }
    await state.update_data(bc=bc)
    await msg.answer(
        f'{EM_LINK} Хотите добавить кнопку-ссылку к рассылке?',
        reply_markup=kb_bc_btn_choice())
    await state.set_state(AdminSt.bc_btn_choice)

@dp.callback_query(F.data == "bc_btn_no")
async def cb_bc_no(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return await cb.answer()
    data = await state.get_data(); await state.clear()
    await cb.message.edit_text(f'{EM_RELOAD} <b>Запускаю рассылку...</b>')
    sent = await do_broadcast(data.get("bc",{}), None, None)
    await cb.message.edit_text(f'{EM_OK} <b>Рассылка завершена!</b> Отправлено: <b>{sent}</b>')
    await cb.answer()

@dp.callback_query(F.data == "bc_btn_yes")
async def cb_bc_yes(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return await cb.answer()
    await cb.message.edit_text(
        f'{EM_WRITE} Введите текст кнопки (поддерживаются премиум эмодзи):',
        reply_markup=kb_back_admin())
    await state.set_state(AdminSt.bc_btn_text)
    await cb.answer()

@dp.message(AdminSt.bc_btn_text)
async def msg_bc_btn_text(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS: return
    btn_emoji_id = None
    plain_text   = msg.text or "Ссылка"
    if msg.entities:
        for ent in msg.entities:
            if ent.type == "custom_emoji":
                btn_emoji_id = ent.custom_emoji_id
                plain_text = (plain_text[:ent.offset] + plain_text[ent.offset+ent.length:]).strip() or "Ссылка"
                break
    await state.update_data(btn_text=plain_text, btn_emoji_id=btn_emoji_id)
    await msg.answer(f'{EM_LINK} Введите URL для кнопки:', reply_markup=kb_back_admin())
    await state.set_state(AdminSt.bc_btn_url)

@dp.message(AdminSt.bc_btn_url)
async def msg_bc_btn_url(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS: return
    url = (msg.text or "").strip()
    if not url.startswith(("http://","https://","tg://")):
        await msg.answer(f'{EM_ERR} Введите корректный URL (начинается с https://).'); return
    data = await state.get_data(); await state.clear()
    await msg.answer(f'{EM_RELOAD} <b>Запускаю рассылку...</b>')
    sent = await do_broadcast(data.get("bc",{}), data.get("btn_text"), url, data.get("btn_emoji_id"))
    await msg.answer(f'{EM_OK} <b>Рассылка завершена!</b> Отправлено: <b>{sent}</b>')

async def do_broadcast(bc: dict, btn_text, btn_url, btn_emoji_id=None) -> int:
    kb = None
    if btn_text and btn_url:
        kw = {"text":btn_text,"url":btn_url}
        if btn_emoji_id: kw["icon_custom_emoji_id"] = btn_emoji_id
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(**kw)]])
    raw_ents = bc.get("entities",[])
    ents = [MessageEntity(**d) for d in raw_ents] if raw_ents else None
    pm = None if ents else ParseMode.HTML
    users = _db.execute("SELECT tg_id FROM users").fetchall()
    sent  = 0
    for u in users:
        uid = u["tg_id"]
        try:
            text = bc.get("text","")
            kw_send = {"caption_entities" if (bc.get("photo_id") or bc.get("video_id") or bc.get("anim_id")) else "entities": ents,
                       "parse_mode": pm, "reply_markup": kb}
            if bc.get("photo_id"):
                await bot.send_photo(uid, bc["photo_id"], caption=text, **kw_send)
            elif bc.get("video_id"):
                await bot.send_video(uid, bc["video_id"], caption=text, **kw_send)
            elif bc.get("anim_id"):
                await bot.send_animation(uid, bc["anim_id"], caption=text, **kw_send)
            else:
                await bot.send_message(uid, text, entities=ents, parse_mode=pm, reply_markup=kb)
            sent += 1
            await asyncio.sleep(0.04)
        except Exception as ex:
            logger.warning(f"Broadcast skip {uid}: {ex}")
    return sent

# ── Фоновые задачи ────────────────────────────────────────────────────────
async def subscription_checker():
    await asyncio.sleep(10)
    while True:
        try:
            now = datetime.now(timezone.utc)
            # Истёкшие подписки
            expired = _db.execute("""
                SELECT s.id,s.user_id,u.tg_id FROM subscriptions s
                JOIN users u ON u.tg_id=s.user_id
                WHERE s.is_active=1 AND s.expires_at<=?
            """, (now.isoformat(),)).fetchall()
            for row in expired:
                _db.execute("UPDATE subscriptions SET is_active=0 WHERE id=?", (row["id"],))
                _db.commit()
                try:
                    await bot.ban_chat_member(CHANNEL_ID, row["tg_id"])
                    await asyncio.sleep(0.3)
                    await bot.unban_chat_member(CHANNEL_ID, row["tg_id"])
                except: pass
                try:
                    await bot.send_message(
                        row["tg_id"],
                        f'{EM_BELL} <b>Ваша подписка истекла!</b>\n\n'
                        f'Вы удалены из приватного канала.\n'
                        f'Для продления нажмите /start → <b>Купить</b>.')
                except: pass

            # Предупреждение за 2 дня (только если подписка >= 3 дней)
            warn_threshold = (now + timedelta(days=2)).isoformat()
            to_warn = _db.execute("""
                SELECT s.id,s.user_id,s.expires_at,u.tg_id FROM subscriptions s
                JOIN users u ON u.tg_id=s.user_id
                WHERE s.is_active=1 AND s.warned=0 AND s.expires_at<=?
                AND (julianday(s.expires_at)-julianday(s.started_at))*1440>=4320
            """, (warn_threshold,)).fetchall()
            for row in to_warn:
                remaining = fmt_left(row["expires_at"])
                try:
                    await bot.send_message(
                        row["tg_id"],
                        f'{EM_BELL} <b>Подписка скоро истекает!</b>\n\n'
                        f'Осталось: <b>{remaining}</b>\n\n'
                        f'Для продления: /start → <b>Купить</b>.')
                    _db.execute("UPDATE subscriptions SET warned=1 WHERE id=?", (row["id"],))
                    _db.commit()
                except Exception as ex:
                    logger.warning(f"Warn send failed {row['tg_id']}: {ex}")
        except Exception as ex:
            logger.error(f"subscription_checker error: {ex}")
        await asyncio.sleep(60)

async def crypto_poller():
    if not crypto: return
    await asyncio.sleep(15)
    while True:
        try:
            pending = _db.execute(
                "SELECT invoice_id,user_id FROM payments WHERE method='cryptobot' AND status='pending' AND invoice_id IS NOT NULL"
            ).fetchall()
            if pending:
                ids    = [int(r["invoice_id"]) for r in pending]
                result = await crypto.get_invoices(invoice_ids=ids)
                items  = result if isinstance(result, list) else (result.items if hasattr(result,"items") else [])
                for inv in items:
                    if inv.status == "paid":
                        row = confirm_by_invoice(str(inv.invoice_id))
                        if row:
                            dur_m = int(gs("duration_minutes"))
                            add_subscription(row["user_id"], dur_m)
                            await notify_success(row["user_id"], dur_m)
        except Exception as ex:
            logger.error(f"crypto_poller error: {ex}")
        await asyncio.sleep(30)

# ── Запуск ───────────────────────────────────────────────────────────────
async def set_commands():
    await bot.set_my_commands(
        [BotCommand(command="start",description="Главное меню"),
         BotCommand(command="help", description="Помощь")],
        scope=BotCommandScopeDefault())
    for aid in ADMIN_IDS:
        try:
            await bot.set_my_commands(
                [BotCommand(command="start", description="Главное меню"),
                 BotCommand(command="help",  description="Помощь"),
                 BotCommand(command="admin", description="Панель администратора")],
                scope=BotCommandScopeChat(chat_id=aid))
        except: pass

async def main():
    init_db()
    await set_commands()
    asyncio.create_task(subscription_checker())
    asyncio.create_task(crypto_poller())
    logger.info("Bot started!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
