# ── SSL-патч для Windows ────────────────────────────────────────────────
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

# ── ID ПРЕМИУМ ЭМОДЗИ (полный набор) ──
EMOJI = {
    # Основные
    'SETTINGS': '5870982283724328568',
    'STATS': '5870921681735781843',
    'CHECK': '5774022692642492953',
    'CROSS': '5774077015388852135',
    'TRASH': '6039522349517115015',
    'INFO': '6028435952299413210',
    'BOT': '6030400221232501136',
    'EYE': '6037397706505195857',
    'EYE_HIDDEN': '6037243349675544634',
    'SEND': '6039573425268201570',
    'DOWNLOAD': '6039802767931871481',
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
    'TIME': '5775896410780079073',
    'LINK': '5769289093221454192',
    'DOCUMENT': '5870528606328852614',
    'PHOTO': '6035128606563241721',
    'VIDEO': '6039391078136681499',
    'MUSIC': '6037364759811068375',
    'GAME': '5938413566624272793',
    'CODE': '5940433880585605708',
    'LOADING': '5345906554510012647',
    'WARNING': '5870657884844462243',
    'CHAT': '5778208881301787450',
    'USER': '6032994772321309200',
    'USERS': '6033125983572201397',
    'PIN': '6042011682497106307',
    'NOTE': '5778299625370817409',
    'SEARCH': '6032850693348399258',
    'COPY': '6039451237743595514',
    'REPLY': '5778208881301787450',
    'FORWARD': '6039422865189638057',
    'ARROW_RIGHT': '6037622221625626773',
    'ARROW_LEFT': '6039519841256214245',
    'ARROW_UP': '6028205772117118673',
    'ARROW_DOWN': '6037157012242960559',
    'LOCK': '6037249452824072506',
    'UNLOCK': '6037496202990194718',
    'FOLDER': '6037475557082403885',
    'FILE': '6034969813032374911',
    'PICTURE': '6030466823290360017',
    'TV': '6039391078136681499',
    'ROBOT': '6030400221232501136',
    'STAR_GOLD': '6030680867280522811',
    'PLUS': '6032924188828767321',
    'EXCLAMATION': '6030563507299160824',
    'PLAY': '5773626993010546707',
    'CLOUD': '6028115612163641653',
    'SHIELD': '6030537007350944596',
    'SLEEP': '5983401171501454028',
    'AGE_18': '5922610170034132416',
    'LOCATION': '6030399199030284183',
    'INBOX': '5776182936638329359',
    'FOOTPRINTS': '5843679481566335204',
    'TIMER': '6037268453759389862',
    'MEDAL': '6037428784888549034',
    'CAMERA': '5767117162619605573',
    'MICROPHONE': '6030722571412967168',
    'STUDIO_MIC': '6030467682283818947',
    'TELEPHONE': '6039605143601680423',
    'THOUGHT': '5904248647972820334',
    'LIGHTBULB': '5891120964468480450',
    'COIN': '5778613750688911681',
    'MONEY_EYES': '5902206159095339799',
    'CYCLONE': '6050588788021793070',
    'DIAMOND': '5776023601941582822',
    'LABEL': '5890974664997477030',
    'HOURGLASS': '5891211339170326418',
    'HAMMER': '6039729023343400390',
    'WALLET': '5769126056262898415',
    'MONEY_BAG': '5904359114531675993',
    'PAGER': '5776118099812028333',
    'LOUDSPEAKER': '6039381989985882045',
    'MEGAPHONE_2': '6039450962865688331',
    'VOLUME_HIGH': '6039454987250044861',
    'VOLUME_MUTE': '6039505337151655702',
    'VOLUME_LOW': '6039853100653612987',
    'BELL_OFF': '6039569594157371705',
    'FILM': '5944777041709633960',
    'SPARKLES': '5778226250149532337',
    'WINDOW': '6035353688619356485',
    'PACKAGE': '5778672437122045013',
    'PUSHPIN': '6043896193887506430',
    'SUN': '5938525265838739643',
    'MOON': '5769143090103193926',
    'COMPASS': '6030687898141987254',
    'NEW': '5895669571058142797',
    'PLANET': '5891156376473836675',
    'BRAIN': '5864019342873598613',
    'SUNGLASSES': '5962882510705660145',
    'NEUTRAL': '6041748912102968702',
    'SCARED': '6043973168291384891',
    'SAD': '6042029429301973188',
    'ANGRY': '6044118213631938928',
    'BEAR': '6044004057696177711',
    'CONFETTI': '6041731551845159060',
    'HAND_WAVE': '6041921818896372382',
    'HAND_POINT_UP': '5884106131822875141',
    'HAND_THUMB_DOWN': '6041716699848249286',
    'HAND_THUMB_UP': '6041720006973067267',
    'CLAP': '5994417835630137549',
    'BEACH_UMBRELLA': '6041933986538721961',
    'BURGER': '6041874690220233085',
    'CAKE': '5922305158636639117',
    'MAP': '5904650558127478452',
    'HOUSE': '6042137469204303531',
    'BATHTUB': '6041963669057703997',
    'HOUSE_GARDEN': '5938537205847822613',
    'FLAG': '6041923781696426657',
    'BRIEFCASE': '5938492039971737551',
    'SIGN': '6042098561095570207',
    'GRADUATION': '5938195768832692153',
    'WHITE_SQUARE': '5884089033558070257',
    'WHITE_CIRCLE': '5884332803016891855',
    'SOCCER': '6042069608721027027',
    'VIDEO_GAME': '5938413566624272793',
    'WATER_GUN': '5767356727305441799',
    'GLASSES': '5882223295469722324',
    'RELOAD': '5767310088255576068',
    'SPEAKING_HEAD': '5769500641835618919',
    'LOWERCASE': '5771851822897566479',
    'SCISSORS': '5771880672192893347',
    'CHART_UP': '5938539885907415367',
    'NOTEBOOK': '5778299625370817409',
    'LOWERCASE_2': '5767262289564536912',
    'LETTER_A': '6030710030108463274',
    'ARROW_LEFT_RIGHT': '5778479949572738874',
    'HISTOGRAM': '5936143551854285132',
    'GLOBE': '5776233299424843260',
    'ATM': '5879814368572478751',
    'SUN_2': '5769527287812723055',
    'PAGE': '6050643982646513651',
    'PAINTBRUSH': '6050679691004612757',
    'SYMBOLS': '5764638872000533034',
    'INFINITY': '6048407885233263063',
    'SPONGE': '5811966564039135541',
    'PILL': '6050677620830376838',
    'WIFI': '6048723247501938454',
    'PENCIL_2': '5771847914477326786',
    'DOTTED_FACE': '5812150667812280629',
    'MAGIC_WAND': '6021792097454002931',
    'DROP': '6050632433479455053',
    'AIRPLANE': '5927118708873892465',
    'ARTIST': '5769635757211784031',
    'CRAYON': '5771798621137670637',
    'COMPUTER': '5942734685976138521',
    'GEAR': '6032742198179532882',
    'SLIDERS': '5776424837786374634',
    'NEWSPAPER': '5895519358871932592',
    'TABBED_FOLDER': '5766994197705921104',
    'REPEAT': '6030657343744644592',
    'DOUBLE_ARROW_UP': '5938437708635443119',
    'KEYBOARD': '6039404727542747508',
    'WRENCH': '5962952497197748583',
    'DOOR': '6035130900075777681',
    'MAGNIFY': '6032850693348399258',
}

def tge(eid, fb=''): 
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

# Переменные для текста с премиум эмодзи
EM_OK = tge(EMOJI['CHECK'], '')
EM_ERR = tge(EMOJI['CROSS'], '')
EM_EYE = tge(EMOJI['EYE'], '')
EM_BOT = tge(EMOJI['BOT'], '')
EM_DEL = tge(EMOJI['TRASH'], '')
EM_STATS = tge(EMOJI['STATS'], '')
EM_INFO = tge(EMOJI['INFO'], '')
EM_GEAR = tge(EMOJI['SETTINGS'], '')
EM_MSG = tge(EMOJI['SPEECH'], '')
EM_SEND = tge(EMOJI['SEND'], '')
EM_BL = tge(EMOJI['BLOCK'], '')
EM_STAR = tge(EMOJI['STAR'], '')
EM_BELL = tge(EMOJI['BELL'], '')
EM_CLOCK = tge(EMOJI['CLOCK'], '')
EM_ARROW_LEFT = tge(EMOJI['ARROW_LEFT'], '')
EM_ARROW_RIGHT = tge(EMOJI['ARROW_RIGHT'], '')
EM_ARROW_UP = tge(EMOJI['ARROW_UP'], '')
EM_ARROW_DOWN = tge(EMOJI['ARROW_DOWN'], '')
EM_WAVE = tge(EMOJI['WAVE'], '')
EM_THUMB = tge(EMOJI['THUMB_UP'], '')
EM_QUESTION = tge(EMOJI['QUESTION'], '')
EM_HEART = tge(EMOJI['HEART'], '')
EM_FIRE = tge(EMOJI['FIRE'], '')
EM_MONEY = tge(EMOJI['MONEY'], '')
EM_CALENDAR = tge(EMOJI['CALENDAR'], '')
EM_TIME = tge(EMOJI['TIME'], '')
EM_LINK = tge(EMOJI['LINK'], '')
EM_FILE = tge(EMOJI['DOCUMENT'], '')
EM_PHOTO = tge(EMOJI['PHOTO'], '')
EM_VIDEO = tge(EMOJI['VIDEO'], '')
EM_MUSIC = tge(EMOJI['MUSIC'], '')
EM_GAME = tge(EMOJI['GAME'], '')
EM_CODE = tge(EMOJI['CODE'], '')
EM_LOADING = tge(EMOJI['LOADING'], '')
EM_WARNING = tge(EMOJI['WARNING'], '')
EM_CHAT = tge(EMOJI['CHAT'], '')
EM_USER = tge(EMOJI['USER'], '')
EM_USERS = tge(EMOJI['USERS'], '')
EM_PIN = tge(EMOJI['PIN'], '')
EM_NOTE = tge(EMOJI['NOTE'], '')
EM_SEARCH = tge(EMOJI['SEARCH'], '')
EM_COPY = tge(EMOJI['COPY'], '')
EM_REPLY = tge(EMOJI['REPLY'], '')
EM_LOCK = tge(EMOJI['LOCK'], '')
EM_UNLOCK = tge(EMOJI['UNLOCK'], '')
EM_FOLDER = tge(EMOJI['FOLDER'], '')
EM_TV = tge(EMOJI['TV'], '')
EM_PLUS = tge(EMOJI['PLUS'], '')
EM_EXCLAMATION = tge(EMOJI['EXCLAMATION'], '')
EM_PLAY = tge(EMOJI['PLAY'], '')
EM_CLOUD = tge(EMOJI['CLOUD'], '')
EM_SHIELD = tge(EMOJI['SHIELD'], '')
EM_SLEEP = tge(EMOJI['SLEEP'], '')
EM_AGE_18 = tge(EMOJI['AGE_18'], '')
EM_LOCATION = tge(EMOJI['LOCATION'], '')
EM_INBOX = tge(EMOJI['INBOX'], '')
EM_TIMER = tge(EMOJI['TIMER'], '')
EM_MEDAL = tge(EMOJI['MEDAL'], '')
EM_CAMERA = tge(EMOJI['CAMERA'], '')
EM_MIC = tge(EMOJI['MICROPHONE'], '')
EM_STUDIO_MIC = tge(EMOJI['STUDIO_MIC'], '')
EM_PHONE = tge(EMOJI['TELEPHONE'], '')
EM_THOUGHT = tge(EMOJI['THOUGHT'], '')
EM_LIGHT = tge(EMOJI['LIGHTBULB'], '')
EM_COIN = tge(EMOJI['COIN'], '')
EM_MONEY_EYES = tge(EMOJI['MONEY_EYES'], '')
EM_CYCLONE = tge(EMOJI['CYCLONE'], '')
EM_DIAMOND = tge(EMOJI['DIAMOND'], '')
EM_LABEL = tge(EMOJI['LABEL'], '')
EM_HOURGLASS = tge(EMOJI['HOURGLASS'], '')
EM_HAMMER = tge(EMOJI['HAMMER'], '')
EM_WALLET = tge(EMOJI['WALLET'], '')
EM_MONEY_BAG = tge(EMOJI['MONEY_BAG'], '')
EM_SPARKLES = tge(EMOJI['SPARKLES'], '')
EM_WINDOW = tge(EMOJI['WINDOW'], '')
EM_PACKAGE = tge(EMOJI['PACKAGE'], '')
EM_PUSHPIN = tge(EMOJI['PUSHPIN'], '')
EM_SUN = tge(EMOJI['SUN'], '')
EM_MOON = tge(EMOJI['MOON'], '')
EM_COMPASS = tge(EMOJI['COMPASS'], '')
EM_NEW = tge(EMOJI['NEW'], '')
EM_PLANET = tge(EMOJI['PLANET'], '')
EM_BRAIN = tge(EMOJI['BRAIN'], '')
EM_GLASSES = tge(EMOJI['GLASSES'], '')
EM_NEUTRAL = tge(EMOJI['NEUTRAL'], '')
EM_SCARED = tge(EMOJI['SCARED'], '')
EM_SAD = tge(EMOJI['SAD'], '')
EM_ANGRY = tge(EMOJI['ANGRY'], '')
EM_BEAR = tge(EMOJI['BEAR'], '')
EM_CONFETTI = tge(EMOJI['CONFETTI'], '')
EM_HAND_POINT = tge(EMOJI['HAND_POINT_UP'], '')
EM_THUMB_DOWN = tge(EMOJI['HAND_THUMB_DOWN'], '')
EM_CLAP = tge(EMOJI['CLAP'], '')
EM_BURGER = tge(EMOJI['BURGER'], '')
EM_CAKE = tge(EMOJI['CAKE'], '')
EM_MAP = tge(EMOJI['MAP'], '')
EM_HOUSE = tge(EMOJI['HOUSE'], '')
EM_BATHTUB = tge(EMOJI['BATHTUB'], '')
EM_FLAG = tge(EMOJI['FLAG'], '')
EM_BRIEFCASE = tge(EMOJI['BRIEFCASE'], '')
EM_GRADUATION = tge(EMOJI['GRADUATION'], '')
EM_SOCCER = tge(EMOJI['SOCCER'], '')
EM_VIDEO_GAME = tge(EMOJI['VIDEO_GAME'], '')
EM_RELOAD = tge(EMOJI['RELOAD'], '')
EM_SPEAKING = tge(EMOJI['SPEAKING_HEAD'], '')
EM_SCISSORS = tge(EMOJI['SCISSORS'], '')
EM_CHART = tge(EMOJI['CHART_UP'], '')
EM_NOTEBOOK = tge(EMOJI['NOTEBOOK'], '')
EM_LETTER_A = tge(EMOJI['LETTER_A'], '')
EM_ARROW_LR = tge(EMOJI['ARROW_LEFT_RIGHT'], '')
EM_GLOBE = tge(EMOJI['GLOBE'], '')
EM_ATM = tge(EMOJI['ATM'], '')
EM_PAGE = tge(EMOJI['PAGE'], '')
EM_PAINTBRUSH = tge(EMOJI['PAINTBRUSH'], '')
EM_INFINITY = tge(EMOJI['INFINITY'], '')
EM_SPONGE = tge(EMOJI['SPONGE'], '')
EM_PILL = tge(EMOJI['PILL'], '')
EM_WIFI = tge(EMOJI['WIFI'], '')
EM_PENCIL_2 = tge(EMOJI['PENCIL_2'], '')
EM_DOTTED_FACE = tge(EMOJI['DOTTED_FACE'], '')
EM_MAGIC_WAND = tge(EMOJI['MAGIC_WAND'], '')
EM_DROP = tge(EMOJI['DROP'], '')
EM_AIRPLANE = tge(EMOJI['AIRPLANE'], '')
EM_ARTIST = tge(EMOJI['ARTIST'], '')
EM_CRAYON = tge(EMOJI['CRAYON'], '')
EM_COMPUTER = tge(EMOJI['COMPUTER'], '')
EM_GEAR_2 = tge(EMOJI['GEAR'], '')
EM_SLIDERS = tge(EMOJI['SLIDERS'], '')
EM_NEWSPAPER = tge(EMOJI['NEWSPAPER'], '')
EM_TABBED_FOLDER = tge(EMOJI['TABBED_FOLDER'], '')
EM_REPEAT = tge(EMOJI['REPEAT'], '')
EM_DOUBLE_ARROW = tge(EMOJI['DOUBLE_ARROW_UP'], '')
EM_KEYBOARD = tge(EMOJI['KEYBOARD'], '')
EM_WRENCH = tge(EMOJI['WRENCH'], '')
EM_DOOR = tge(EMOJI['DOOR'], '')
EM_MAGNIFY = tge(EMOJI['MAGNIFY'], '')

# ID анимированных эффектов
ANIMATED_EFFECTS = {
    'FIREWORKS': '5046509860389126442',
    'LIKE': '5107584321108051014',
    'POOP': '5046589136895476101',
    'FIRE': '5104841245755180586',
    'HEART_ANIMATED': '5159385139981059251',
}

def add_effect(text: str, effect_id: str = None) -> str:
    """Добавляет анимированный эффект к сообщению"""
    if effect_id:
        return f'<tg-message-effect id="{effect_id}">{text}</tg-message-effect>'
    return text

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
class SetTypingSpeed(StatesGroup):
    waiting = State()
class AddUserNote(StatesGroup):
    waiting = State()
class SearchMessages(StatesGroup):
    waiting = State()
class SetKeywordReply(StatesGroup):
    waiting = State()
class SetFilterWord(StatesGroup):
    waiting = State()
class CreateTemplate(StatesGroup):
    waiting = State()
class QuickReply(StatesGroup):
    waiting = State()

# ==================== БД ====================
def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with db() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS settings(
            owner_id INTEGER PRIMARY KEY,
            spy_enabled INTEGER DEFAULT 1,
            log_msgs INTEGER DEFAULT 1,
            auto_reply TEXT DEFAULT '',
            welcome_message TEXT DEFAULT '',
            typing_speed REAL DEFAULT 1.0,
            reply_chance INTEGER DEFAULT 30
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS msg_cache(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            chat_id INTEGER, msg_id INTEGER, user_id INTEGER,
            username TEXT, first_name TEXT, text TEXT,
            file_id TEXT, file_type TEXT, caption TEXT, ts TEXT,
            UNIQUE(owner_id, chat_id, msg_id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS user_stats(
            owner_id INTEGER,
            user_id INTEGER,
            username TEXT, first_name TEXT,
            chat_id INTEGER, msg_count INTEGER DEFAULT 0,
            first_seen TEXT, last_seen TEXT,
            PRIMARY KEY(owner_id, user_id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS blacklist(
            owner_id INTEGER,
            user_id INTEGER,
            username TEXT,
            reason TEXT,
            ts TEXT,
            PRIMARY KEY(owner_id, user_id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS whitelist(
            owner_id INTEGER,
            user_id INTEGER,
            username TEXT,
            note TEXT,
            ts TEXT,
            PRIMARY KEY(owner_id, user_id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS user_notes(
            owner_id INTEGER,
            user_id INTEGER,
            note TEXT,
            ts TEXT,
            PRIMARY KEY(owner_id, user_id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS daily_stats(
            owner_id INTEGER,
            date TEXT,
            messages INTEGER DEFAULT 0,
            users INTEGER DEFAULT 0,
            PRIMARY KEY(owner_id, date))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS action_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            action TEXT,
            user_id INTEGER,
            details TEXT,
            ts TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS keyword_replies(
            owner_id INTEGER,
            keyword TEXT,
            reply TEXT,
            PRIMARY KEY(owner_id, keyword))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS filter_words(
            owner_id INTEGER,
            word TEXT,
            action TEXT,
            PRIMARY KEY(owner_id, word))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS message_templates(
            owner_id INTEGER,
            name TEXT,
            content TEXT,
            PRIMARY KEY(owner_id, name))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS user_activity(
            owner_id INTEGER,
            user_id INTEGER,
            last_message_time TEXT,
            message_count_today INTEGER DEFAULT 0,
            warning_count INTEGER DEFAULT 0,
            PRIMARY KEY(owner_id, user_id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS pinned_messages(
            owner_id INTEGER,
            chat_id INTEGER,
            message_id INTEGER,
            pinned_by INTEGER,
            ts TEXT,
            PRIMARY KEY(owner_id, chat_id, message_id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS quick_replies(
            owner_id INTEGER,
            shortcut TEXT,
            content TEXT,
            PRIMARY KEY(owner_id, shortcut))''')

def get_setting(owner_id, key):
    with db() as c:
        r = c.execute(f'SELECT {key} FROM settings WHERE owner_id=?', (owner_id,)).fetchone()
        if r:
            return r[0]
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
            
            today = datetime.now().strftime('%Y-%m-%d')
            c.execute('''INSERT INTO user_activity(owner_id, user_id, last_message_time, message_count_today)
                VALUES(?,?,?,1) ON CONFLICT(owner_id, user_id) DO UPDATE SET
                last_message_time=excluded.last_message_time,
                message_count_today=message_count_today+1''',
                (owner_id, u.id, now))
            
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

def get_top_users(owner_id, limit=10):
    with db() as c:
        return c.execute('SELECT user_id, username, first_name, msg_count FROM user_stats WHERE owner_id=? ORDER BY msg_count DESC LIMIT ?', (owner_id, limit)).fetchall()

def get_recent_users(owner_id, limit=10):
    with db() as c:
        return c.execute('SELECT user_id, username, first_name, last_seen FROM user_stats WHERE owner_id=? ORDER BY last_seen DESC LIMIT ?', (owner_id, limit)).fetchall()

def get_user_activity(owner_id, user_id):
    with db() as c:
        return c.execute('SELECT * FROM user_activity WHERE owner_id=? AND user_id=?', (owner_id, user_id)).fetchone()

def add_keyword_reply(owner_id, keyword, reply):
    with db() as c:
        c.execute('INSERT OR REPLACE INTO keyword_replies(owner_id, keyword, reply) VALUES(?,?,?)',
                  (owner_id, keyword.lower(), reply))
    log_action(owner_id, 'add_keyword', None, f'{keyword} -> {reply[:50]}')

def get_keyword_reply(owner_id, text):
    if not text:
        return None
    text_lower = text.lower()
    with db() as c:
        rows = c.execute('SELECT keyword, reply FROM keyword_replies WHERE owner_id=?', (owner_id,)).fetchall()
        for row in rows:
            if row['keyword'] in text_lower:
                return row['reply']
    return None

def get_all_keywords(owner_id):
    with db() as c:
        return c.execute('SELECT keyword, reply FROM keyword_replies WHERE owner_id=?', (owner_id,)).fetchall()

def remove_keyword(owner_id, keyword):
    with db() as c:
        c.execute('DELETE FROM keyword_replies WHERE owner_id=? AND keyword=?', (owner_id, keyword.lower()))
    log_action(owner_id, 'remove_keyword', None, keyword)

def add_filter_word(owner_id, word, action='delete'):
    with db() as c:
        c.execute('INSERT OR REPLACE INTO filter_words(owner_id, word, action) VALUES(?,?,?)',
                  (owner_id, word.lower(), action))
    log_action(owner_id, 'add_filter', None, word)

def check_filter(owner_id, text):
    if not text:
        return None
    text_lower = text.lower()
    with db() as c:
        rows = c.execute('SELECT word, action FROM filter_words WHERE owner_id=?', (owner_id,)).fetchall()
        for row in rows:
            if row['word'] in text_lower:
                return row['action']
    return None

def save_template(owner_id, name, content):
    with db() as c:
        c.execute('INSERT OR REPLACE INTO message_templates(owner_id, name, content) VALUES(?,?,?)',
                  (owner_id, name, content))
    log_action(owner_id, 'save_template', None, name)

def get_template(owner_id, name):
    with db() as c:
        r = c.execute('SELECT content FROM message_templates WHERE owner_id=? AND name=?', (owner_id, name)).fetchone()
        return r['content'] if r else None

def get_all_templates(owner_id):
    with db() as c:
        return c.execute('SELECT name, content FROM message_templates WHERE owner_id=?', (owner_id,)).fetchall()

def delete_template(owner_id, name):
    with db() as c:
        c.execute('DELETE FROM message_templates WHERE owner_id=? AND name=?', (owner_id, name))
    log_action(owner_id, 'delete_template', None, name)

def save_quick_reply(owner_id, shortcut, content):
    with db() as c:
        c.execute('INSERT OR REPLACE INTO quick_replies(owner_id, shortcut, content) VALUES(?,?,?)',
                  (owner_id, shortcut, content))
    log_action(owner_id, 'save_quick_reply', None, shortcut)

def get_quick_reply(owner_id, shortcut):
    with db() as c:
        r = c.execute('SELECT content FROM quick_replies WHERE owner_id=? AND shortcut=?', (owner_id, shortcut)).fetchone()
        return r['content'] if r else None

def get_all_quick_replies(owner_id):
    with db() as c:
        return c.execute('SELECT shortcut, content FROM quick_replies WHERE owner_id=?', (owner_id,)).fetchall()

def delete_quick_reply(owner_id, shortcut):
    with db() as c:
        c.execute('DELETE FROM quick_replies WHERE owner_id=? AND shortcut=?', (owner_id, shortcut))
    log_action(owner_id, 'delete_quick_reply', None, shortcut)

def pin_message(owner_id, chat_id, message_id, pinned_by):
    with db() as c:
        c.execute('INSERT OR REPLACE INTO pinned_messages(owner_id, chat_id, message_id, pinned_by, ts) VALUES(?,?,?,?,?)',
                  (owner_id, chat_id, message_id, pinned_by, datetime.now().isoformat()))
    log_action(owner_id, 'pin_message', None, f'chat:{chat_id} msg:{message_id}')

def unpin_message(owner_id, chat_id, message_id):
    with db() as c:
        c.execute('DELETE FROM pinned_messages WHERE owner_id=? AND chat_id=? AND message_id=?', (owner_id, chat_id, message_id))
    log_action(owner_id, 'unpin_message', None, f'chat:{chat_id} msg:{message_id}')

def get_pinned_messages(owner_id, chat_id):
    with db() as c:
        return c.execute('SELECT message_id, pinned_by, ts FROM pinned_messages WHERE owner_id=? AND chat_id=? ORDER BY ts DESC', (owner_id, chat_id)).fetchall()

# ==================== КЛАВИАТУРЫ С ПРЕМИУМ ЭМОДЗИ ====================

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{EM_STATS} Статистика", callback_data='stats',
                               icon_custom_emoji_id=EMOJI['STATS']),
            InlineKeyboardButton(text=f"{EM_USERS} Пользователи", callback_data='users',
                               icon_custom_emoji_id=EMOJI['USERS'])
        ],
        [
            InlineKeyboardButton(text=f"{EM_BL} ЧС", callback_data='blacklist',
                               icon_custom_emoji_id=EMOJI['BLOCK']),
            InlineKeyboardButton(text=f"{EM_HEART} Белый", callback_data='whitelist',
                               icon_custom_emoji_id=EMOJI['HEART'])
        ],
        [
            InlineKeyboardButton(text=f"{EM_GEAR} Настройки", callback_data='settings',
                               icon_custom_emoji_id=EMOJI['SETTINGS']),
            InlineKeyboardButton(text=f"{EM_SEND} Рассылка", callback_data='broadcast',
                               icon_custom_emoji_id=EMOJI['MEGAPHONE'])
        ],
        [
            InlineKeyboardButton(text=f"{EM_NOTE} Заметки", callback_data='notes',
                               icon_custom_emoji_id=EMOJI['NOTE']),
            InlineKeyboardButton(text=f"{EM_FIRE} Активность", callback_data='activity',
                               icon_custom_emoji_id=EMOJI['FIRE'])
        ],
        [
            InlineKeyboardButton(text=f"{EM_KEYBOARD} Ключевые слова", callback_data='keywords',
                               icon_custom_emoji_id=EMOJI['KEYBOARD']),
            InlineKeyboardButton(text=f"{EM_WARNING} Фильтр", callback_data='filters',
                               icon_custom_emoji_id=EMOJI['WARNING'])
        ],
        [
            InlineKeyboardButton(text=f"{EM_COPY} Шаблоны", callback_data='templates',
                               icon_custom_emoji_id=EMOJI['COPY']),
            InlineKeyboardButton(text=f"{EM_REPLY} Быстрые ответы", callback_data='quick_replies',
                               icon_custom_emoji_id=EMOJI['REPLY'])
        ],
        [
            InlineKeyboardButton(text=f"{EM_SEARCH} Поиск", callback_data='search',
                               icon_custom_emoji_id=EMOJI['SEARCH']),
            InlineKeyboardButton(text=f"{EM_PIN} Закреплённые", callback_data='pinned',
                               icon_custom_emoji_id=EMOJI['PIN'])
        ],
        [
            InlineKeyboardButton(text=f"{EM_INFO} Команды", callback_data='chat_commands',
                               icon_custom_emoji_id=EMOJI['INFO']),
            InlineKeyboardButton(text=f"{EM_DEL} Очистить", callback_data='clear_cache',
                               icon_custom_emoji_id=EMOJI['TRASH'])
        ]
    ])

def back_kb(cb='back'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{EM_ARROW_LEFT} Назад", callback_data=cb,
                            icon_custom_emoji_id=EMOJI['ARROW_LEFT'])]
    ])

def settings_kb(owner_id):
    spy = "✅" if get_setting(owner_id, 'spy_enabled') else "❌"
    log = "✅" if get_setting(owner_id, 'log_msgs') else "❌"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{spy} {EM_EYE} Слежка", callback_data='toggle_spy',
                            icon_custom_emoji_id=EMOJI['EYE'])],
        [InlineKeyboardButton(text=f"{log} {EM_FILE} Логирование", callback_data='toggle_log',
                            icon_custom_emoji_id=EMOJI['FILE'])],
        [InlineKeyboardButton(text=f"{EM_MSG} Авто-ответ", callback_data='set_auto_reply',
                            icon_custom_emoji_id=EMOJI['SPEECH'])],
        [InlineKeyboardButton(text=f"{EM_WAVE} Приветствие", callback_data='set_welcome',
                            icon_custom_emoji_id=EMOJI['WAVE'])],
        [InlineKeyboardButton(text=f"{EM_CLOCK} Скорость: x{get_setting(owner_id, 'typing_speed')}", 
                            callback_data='set_speed', icon_custom_emoji_id=EMOJI['CLOCK'])],
        [InlineKeyboardButton(text=f"{EM_ARROW_LEFT} Назад", callback_data='back',
                            icon_custom_emoji_id=EMOJI['ARROW_LEFT'])]
    ])

def user_menu_kb(user_id, username):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{EM_NOTE} Заметка", callback_data=f'note_add_{user_id}',
                               icon_custom_emoji_id=EMOJI['NOTE']),
            InlineKeyboardButton(text=f"{EM_BL} В ЧС", callback_data=f'bl_add_{user_id}',
                               icon_custom_emoji_id=EMOJI['BLOCK'])
        ],
        [
            InlineKeyboardButton(text=f"{EM_HEART} В белый", callback_data=f'wl_add_{user_id}',
                               icon_custom_emoji_id=EMOJI['HEART']),
            InlineKeyboardButton(text=f"{EM_STATS} Статистика", callback_data=f'user_stats_{user_id}',
                               icon_custom_emoji_id=EMOJI['STATS'])
        ],
        [InlineKeyboardButton(text=f"{EM_ARROW_LEFT} Назад", callback_data='users',
                            icon_custom_emoji_id=EMOJI['ARROW_LEFT'])]
    ])

def keyword_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{EM_PLUS} Добавить ключевое слово", callback_data='add_keyword',
                            icon_custom_emoji_id=EMOJI['PLUS'])],
        [InlineKeyboardButton(text=f"{EM_SEARCH} Список ключевых слов", callback_data='list_keywords',
                            icon_custom_emoji_id=EMOJI['SEARCH'])],
        [InlineKeyboardButton(text=f"{EM_DEL} Удалить", callback_data='remove_keyword',
                            icon_custom_emoji_id=EMOJI['TRASH'])],
        [InlineKeyboardButton(text=f"{EM_ARROW_LEFT} Назад", callback_data='back',
                            icon_custom_emoji_id=EMOJI['ARROW_LEFT'])]
    ])

def filter_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{EM_PLUS} Добавить слово", callback_data='add_filter',
                            icon_custom_emoji_id=EMOJI['PLUS'])],
        [InlineKeyboardButton(text=f"{EM_SEARCH} Список слов", callback_data='list_filters',
                            icon_custom_emoji_id=EMOJI['SEARCH'])],
        [InlineKeyboardButton(text=f"{EM_DEL} Удалить", callback_data='remove_filter',
                            icon_custom_emoji_id=EMOJI['TRASH'])],
        [InlineKeyboardButton(text=f"{EM_ARROW_LEFT} Назад", callback_data='back',
                            icon_custom_emoji_id=EMOJI['ARROW_LEFT'])]
    ])

def templates_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{EM_PLUS} Создать шаблон", callback_data='create_template',
                            icon_custom_emoji_id=EMOJI['PLUS'])],
        [InlineKeyboardButton(text=f"{EM_SEARCH} Список шаблонов", callback_data='list_templates',
                            icon_custom_emoji_id=EMOJI['SEARCH'])],
        [InlineKeyboardButton(text=f"{EM_DEL} Удалить", callback_data='delete_template',
                            icon_custom_emoji_id=EMOJI['TRASH'])],
        [InlineKeyboardButton(text=f"{EM_ARROW_LEFT} Назад", callback_data='back',
                            icon_custom_emoji_id=EMOJI['ARROW_LEFT'])]
    ])

def quick_reply_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{EM_PLUS} Добавить быстрый ответ", callback_data='add_quick_reply',
                            icon_custom_emoji_id=EMOJI['PLUS'])],
        [InlineKeyboardButton(text=f"{EM_SEARCH} Список быстрых ответов", callback_data='list_quick_replies',
                            icon_custom_emoji_id=EMOJI['SEARCH'])],
        [InlineKeyboardButton(text=f"{EM_DEL} Удалить", callback_data='delete_quick_reply',
                            icon_custom_emoji_id=EMOJI['TRASH'])],
        [InlineKeyboardButton(text=f"{EM_ARROW_LEFT} Назад", callback_data='back',
                            icon_custom_emoji_id=EMOJI['ARROW_LEFT'])]
    ])

# ==================== ОСНОВНЫЕ ФУНКЦИИ ====================

@dp.message(Command('start'))
async def cmd_start(msg: types.Message):
    welcome_text = add_effect(
        f"{EM_BOT} <b>Business Monitor Bot</b>\n\n"
        f"{EM_WAVE} <b>Привет! Я бот для мониторинга бизнес-аккаунта</b>\n\n"
        f"{EM_STAR} <b>Мои возможности:</b>\n\n"
        f"{EM_EYE} <b>Слежка</b> — перехват удалённых сообщений\n"
        f"{EM_BL} <b>Чёрный список</b> — блокировка по ID/username\n"
        f"{EM_HEART} <b>Белый список</b> — доверенные пользователи\n"
        f"{EM_KEYBOARD} <b>Авто-ответ по ключевым словам</b>\n"
        f"{EM_WARNING} <b>Фильтр слов</b> — автоматическое удаление\n"
        f"{EM_COPY} <b>Шаблоны сообщений</b> — быстрые ответы\n"
        f"{EM_REPLY} <b>Быстрые ответы</b> — короткие команды\n"
        f"{EM_NOTE} <b>Заметки</b> — информация о пользователях\n"
        f"{EM_FIRE} <b>Активность</b> — аналитика и графики\n"
        f"{EM_PIN} <b>Закрепление</b> — важные сообщения\n\n"
        f"{EM_CHAT} <b>Команды в чате (ответьте на сообщение):</b>\n\n"
        f"{EM_ARROW_RIGHT} <code>.i</code> — информация о пользователе\n"
        f"{EM_ARROW_RIGHT} <code>.d</code> — удалить сообщение\n"
        f"{EM_ARROW_RIGHT} <code>.b</code> — добавить в чёрный список\n"
        f"{EM_ARROW_RIGHT} <code>.w</code> — добавить в белый список\n"
        f"{EM_ARROW_RIGHT} <code>.n [текст]</code> — добавить заметку\n"
        f"{EM_ARROW_RIGHT} <code>.m</code> — статистика пользователя\n"
        f"{EM_ARROW_RIGHT} <code>.p</code> — закрепить сообщение\n"
        f"{EM_ARROW_RIGHT} <code>.u</code> — открепить сообщение\n"
        f"{EM_ARROW_RIGHT} <code>.c</code> — скопировать текст\n"
        f"{EM_ARROW_RIGHT} <code>.r [шаблон]</code> — ответить шаблоном\n"
        f"{EM_ARROW_RIGHT} <code>.q [команда]</code> — быстрый ответ\n\n"
        f"{EM_THUMB} <i>Используйте кнопки ниже для управления</i>",
        ANIMATED_EFFECTS['FIREWORKS']
    )
    await msg.answer(welcome_text, reply_markup=main_kb(), parse_mode=ParseMode.HTML)

# ==================== КОМАНДЫ В ЧАТЕ ====================

@dp.business_message()
async def handle_chat_commands(msg: types.Message):
    try:
        bc_id = msg.business_connection_id
        if not bc_id or bc_id not in biz_con:
            return
        
        owner_id = biz_con[bc_id]
        
        if msg.from_user and msg.from_user.id == owner_id:
            return
        
        if msg.reply_to_message:
            target_msg = msg.reply_to_message
            target_user = target_msg.from_user
            text = msg.text or msg.caption or ''
            
            # .i - информация о пользователе
            if text == '.i':
                user_activity = get_user_activity(owner_id, target_user.id)
                user_note = get_user_note(owner_id, target_user.id)
                
                info_text = add_effect(
                    f"{EM_USER} <b>Информация о пользователе</b>\n\n"
                    f"🆔 <b>ID:</b> <code>{target_user.id}</code>\n"
                    f"👤 <b>Имя:</b> {target_user.first_name or '?'}\n"
                    f"🔖 <b>Username:</b> @{target_user.username or 'нет'}\n"
                    f"{EM_CHAT} <b>Chat ID:</b> <code>{msg.chat.id}</code>\n"
                    f"{EM_CALENDAR} <b>Активность:</b>\n"
                    f"   • Сообщений сегодня: {user_activity['message_count_today'] if user_activity else 0}\n"
                    f"   • Предупреждений: {user_activity['warning_count'] if user_activity else 0}\n"
                    f"{EM_NOTE} <b>Заметка:</b> {user_note or 'нет'}\n"
                    f"{EM_BL} <b>В ЧС:</b> {'✅' if is_blacklisted(owner_id, target_user.id) else '❌'}\n"
                    f"{EM_HEART} <b>В белом:</b> {'✅' if is_whitelisted(owner_id, target_user.id) else '❌'}",
                    ANIMATED_EFFECTS['HEART_ANIMATED']
                )
                
                await bot.send_message(chat_id=msg.chat.id, text=info_text,
                                       business_connection_id=bc_id,
                                       reply_to_message_id=msg.message_id,
                                       parse_mode=ParseMode.HTML)
                await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                        business_connection_id=bc_id)
                return
            
            # .d - удалить сообщение
            elif text == '.d':
                if is_main_admin(owner_id):
                    await bot.delete_message(chat_id=msg.chat.id, message_id=target_msg.message_id,
                                            business_connection_id=bc_id)
                    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                            business_connection_id=bc_id)
                return
            
            # .b - добавить в чёрный список
            elif text == '.b':
                if is_main_admin(owner_id):
                    add_to_blacklist(owner_id, target_user.id, target_user.username or '', 'Добавлено через команду .b')
                    await bot.send_message(chat_id=msg.chat.id, 
                                          text=f"{EM_OK} Пользователь добавлен в чёрный список",
                                          business_connection_id=bc_id,
                                          reply_to_message_id=msg.message_id,
                                          parse_mode=ParseMode.HTML)
                    await asyncio.sleep(2)
                    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                            business_connection_id=bc_id)
                return
            
            # .w - добавить в белый список
            elif text == '.w':
                if is_main_admin(owner_id):
                    with db() as c:
                        c.execute('INSERT OR REPLACE INTO whitelist(owner_id, user_id, username, ts) VALUES(?,?,?,?)',
                                  (owner_id, target_user.id, target_user.username or '', datetime.now().isoformat()))
                    await bot.send_message(chat_id=msg.chat.id,
                                          text=f"{EM_OK} Пользователь добавлен в белый список",
                                          business_connection_id=bc_id,
                                          reply_to_message_id=msg.message_id,
                                          parse_mode=ParseMode.HTML)
                    await asyncio.sleep(2)
                    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                            business_connection_id=bc_id)
                return
            
            # .m - статистика пользователя
            elif text == '.m':
                user_activity = get_user_activity(owner_id, target_user.id)
                with db() as c:
                    user_stats = c.execute('SELECT msg_count, first_seen, last_seen FROM user_stats WHERE owner_id=? AND user_id=?',
                                          (owner_id, target_user.id)).fetchone()
                
                stats_text = add_effect(
                    f"{EM_STATS} <b>Статистика пользователя</b>\n\n"
                    f"👤 {target_user.first_name or '?'}\n"
                    f"🆔 <code>{target_user.id}</code>\n"
                    f"{EM_MSG} Всего сообщений: {user_stats['msg_count'] if user_stats else 0}\n"
                    f"{EM_TIME} Сообщений сегодня: {user_activity['message_count_today'] if user_activity else 0}\n"
                    f"{EM_CALENDAR} Первое сообщение: {user_stats['first_seen'][:16] if user_stats and user_stats['first_seen'] else '?'}\n"
                    f"{EM_CLOCK} Последнее сообщение: {user_stats['last_seen'][:16] if user_stats and user_stats['last_seen'] else '?'}\n"
                    f"{EM_WARNING} Предупреждений: {user_activity['warning_count'] if user_activity else 0}",
                    ANIMATED_EFFECTS['FIRE']
                )
                
                await bot.send_message(chat_id=msg.chat.id, text=stats_text,
                                       business_connection_id=bc_id,
                                       reply_to_message_id=msg.message_id,
                                       parse_mode=ParseMode.HTML)
                await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                        business_connection_id=bc_id)
                return
            
            # .n - добавить заметку
            elif text.startswith('.n '):
                note_text = text[3:].strip()
                if note_text:
                    add_user_note(owner_id, target_user.id, note_text)
                    await bot.send_message(chat_id=msg.chat.id,
                                          text=f"{EM_OK} Заметка добавлена\n\n<blockquote>{note_text}</blockquote>",
                                          business_connection_id=bc_id,
                                          reply_to_message_id=msg.message_id,
                                          parse_mode=ParseMode.HTML)
                    await asyncio.sleep(2)
                    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                            business_connection_id=bc_id)
                return
            
            # .p - закрепить сообщение
            elif text == '.p':
                if is_main_admin(owner_id):
                    try:
                        await bot.pin_chat_message(chat_id=msg.chat.id, message_id=target_msg.message_id,
                                                   business_connection_id=bc_id)
                        pin_message(owner_id, msg.chat.id, target_msg.message_id, owner_id)
                        await bot.send_message(chat_id=msg.chat.id,
                                              text=f"{EM_PIN} Сообщение закреплено",
                                              business_connection_id=bc_id,
                                              reply_to_message_id=msg.message_id,
                                              parse_mode=ParseMode.HTML)
                        await asyncio.sleep(2)
                        await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                                business_connection_id=bc_id)
                    except Exception as e:
                        print(f"pin error: {e}")
                return
            
            # .u - открепить сообщение
            elif text == '.u':
                if is_main_admin(owner_id):
                    try:
                        await bot.unpin_chat_message(chat_id=msg.chat.id, message_id=target_msg.message_id,
                                                     business_connection_id=bc_id)
                        unpin_message(owner_id, msg.chat.id, target_msg.message_id)
                        await bot.send_message(chat_id=msg.chat.id,
                                              text=f"{EM_OK} Сообщение откреплено",
                                              business_connection_id=bc_id,
                                              reply_to_message_id=msg.message_id,
                                              parse_mode=ParseMode.HTML)
                        await asyncio.sleep(2)
                        await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                                business_connection_id=bc_id)
                    except Exception as e:
                        print(f"unpin error: {e}")
                return
            
            # .c - скопировать текст
            elif text == '.c':
                copy_text = target_msg.text or target_msg.caption or ''
                if copy_text:
                    await bot.send_message(chat_id=msg.chat.id,
                                          text=f"{EM_COPY} <b>Скопированный текст:</b>\n\n<blockquote>{copy_text}</blockquote>",
                                          business_connection_id=bc_id,
                                          reply_to_message_id=msg.message_id,
                                          parse_mode=ParseMode.HTML)
                    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                            business_connection_id=bc_id)
                return
            
            # .r - ответ шаблоном
            elif text.startswith('.r '):
                template_name = text[3:].strip()
                template_content = get_template(owner_id, template_name)
                if template_content:
                    await bot.send_message(chat_id=msg.chat.id, text=template_content,
                                           business_connection_id=bc_id,
                                           reply_to_message_id=target_msg.message_id,
                                           parse_mode=ParseMode.HTML)
                    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                            business_connection_id=bc_id)
                else:
                    await bot.send_message(chat_id=msg.chat.id,
                                          text=f"{EM_ERR} Шаблон '{template_name}' не найден",
                                          business_connection_id=bc_id,
                                          reply_to_message_id=msg.message_id,
                                          parse_mode=ParseMode.HTML)
                    await asyncio.sleep(2)
                    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                            business_connection_id=bc_id)
                return
            
            # .q - быстрый ответ
            elif text.startswith('.q '):
                shortcut = text[3:].strip()
                quick_reply = get_quick_reply(owner_id, shortcut)
                if quick_reply:
                    await bot.send_message(chat_id=msg.chat.id, text=quick_reply,
                                           business_connection_id=bc_id,
                                           reply_to_message_id=target_msg.message_id,
                                           parse_mode=ParseMode.HTML)
                    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                            business_connection_id=bc_id)
                else:
                    await bot.send_message(chat_id=msg.chat.id,
                                          text=f"{EM_ERR} Быстрый ответ '{shortcut}' не найден",
                                          business_connection_id=bc_id,
                                          reply_to_message_id=msg.message_id,
                                          parse_mode=ParseMode.HTML)
                    await asyncio.sleep(2)
                    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                            business_connection_id=bc_id)
                return
        
        # Авто-ответ по ключевым словам
        text = msg.text or msg.caption or ''
        if text and not msg.reply_to_message:
            # Проверяем фильтр слов
            filter_action = check_filter(owner_id, text)
            if filter_action == 'delete':
                await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                        business_connection_id=bc_id)
                await bot.send_message(chat_id=msg.chat.id,
                                      text=f"{EM_WARNING} Сообщение удалено (содержит запрещённое слово)",
                                      business_connection_id=bc_id,
                                      parse_mode=ParseMode.HTML)
                return
            
            # Проверяем ключевые слова для автоответа
            keyword_reply = get_keyword_reply(owner_id, text)
            if keyword_reply and not is_blacklisted(owner_id, msg.from_user.id):
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await bot.send_message(chat_id=msg.chat.id, text=keyword_reply,
                                       business_connection_id=bc_id,
                                       reply_to_message_id=msg.message_id,
                                       parse_mode=ParseMode.HTML)
                return
            
            # Приветствие для нового пользователя
            with db() as c:
                cnt = c.execute('SELECT COUNT(*) FROM msg_cache WHERE owner_id=? AND user_id=?', 
                               (owner_id, msg.from_user.id)).fetchone()[0]
            if cnt == 1:
                welcome = get_setting(owner_id, 'welcome_message')
                if welcome:
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    await bot.send_message(chat_id=msg.chat.id, text=welcome,
                                           business_connection_id=bc_id,
                                           reply_to_message_id=msg.message_id,
                                           parse_mode=ParseMode.HTML)
                    return
            
            # Авто-ответ (общий)
            auto_reply = get_setting(owner_id, 'auto_reply')
            if auto_reply and cnt == 1:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await bot.send_message(chat_id=msg.chat.id, text=auto_reply,
                                       business_connection_id=bc_id,
                                       reply_to_message_id=msg.message_id,
                                       parse_mode=ParseMode.HTML)
        
    except Exception as e:
        print(f"handle_chat_commands err: {e}")
        import traceback
        traceback.print_exc()

# ==================== ОБРАБОТЧИКИ КНОПОК ====================

@dp.callback_query(F.data == 'stats')
async def show_stats(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    u, m, bl, wl, tm = get_stats(owner_id)
    today_msgs, today_users = get_today_stats(owner_id)
    top = get_top_users(owner_id, 5)
    
    top_text = '\n'.join([f"{i+1}. {r['username'] or r['first_name'] or r['user_id']} — {r['msg_count']}"
                          for i, r in enumerate(top)]) or "нет данных"
    
    stats_text = add_effect(
        f"{EM_STATS} <b>Статистика</b>\n\n"
        f"{EM_USERS} Всего пользователей: <b>{u}</b>\n"
        f"{EM_MSG} Всего сообщений: <b>{m}</b>\n"
        f"{EM_BL} В чёрном списке: <b>{bl}</b>\n"
        f"{EM_HEART} В белом списке: <b>{wl}</b>\n"
        f"{EM_STAR} Всего сообщений: <b>{tm}</b>\n\n"
        f"{EM_CALENDAR} <b>Сегодня:</b>\n"
        f"• Сообщений: {today_msgs}\n"
        f"• Новых: {today_users}\n\n"
        f"{EM_FIRE} <b>Топ-5 активных:</b>\n{top_text}",
        ANIMATED_EFFECTS['FIREWORKS']
    )
    
    await cb.message.edit_text(stats_text, reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    await cb.answer()

@dp.callback_query(F.data == 'users')
async def show_users(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    users = get_all_users(owner_id)
    
    if not users:
        await cb.message.edit_text(f"{EM_INFO} Пользователей пока нет.", reply_markup=back_kb(), parse_mode=ParseMode.HTML)
        await cb.answer()
        return
    
    lines = []
    for u in users[:15]:
        name = u['username'] or u['first_name'] or str(u['user_id'])
        lines.append(f"{EM_USER} <code>{u['user_id']}</code> {name} — {u['msg_count']}")
    
    text = f"{EM_USERS} <b>Пользователи ({len(users)})</b>\n\n" + '\n'.join(lines)
    if len(users) > 15:
        text += f"\n\n<i>и ещё {len(users) - 15}...</i>"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{EM_SEARCH} Поиск", callback_data='search_user',
                            icon_custom_emoji_id=EMOJI['SEARCH'])],
        [InlineKeyboardButton(text=f"{EM_ARROW_LEFT} Назад", callback_data='back',
                            icon_custom_emoji_id=EMOJI['ARROW_LEFT'])]
    ])
    
    await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await cb.answer()

@dp.callback_query(F.data == 'search_user')
async def search_user_start(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.edit_text(
        f"{EM_SEARCH} <b>Поиск пользователя</b>\n\n"
        f"Введите ID или @username:",
        reply_markup=back_kb(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(AddToBlacklist.waiting)
    await cb.answer()

@dp.message(AddToBlacklist.waiting)
async def search_user_result(msg: types.Message, state: FSMContext):
    owner_id = msg.from_user.id
    query = msg.text.strip()
    
    with db() as c:
        if query.isdigit():
            user = c.execute('SELECT * FROM user_stats WHERE owner_id=? AND user_id=?', (owner_id, int(query))).fetchone()
        else:
            user = c.execute('SELECT * FROM user_stats WHERE owner_id=? AND username=?', (owner_id, query.replace('@', ''))).fetchone()
    
    if user:
        note = get_user_note(owner_id, user['user_id'])
        user_text = add_effect(
            f"{EM_USER} <b>Пользователь найден</b>\n\n"
            f"🆔 ID: <code>{user['user_id']}</code>\n"
            f"👤 Имя: {user['first_name'] or '?'}\n"
            f"🔖 Username: @{user['username'] or 'нет'}\n"
            f"{EM_MSG} Сообщений: {user['msg_count']}\n"
            f"{EM_CALENDAR} Первое появление: {user['first_seen'][:16] if user['first_seen'] else '?'}\n"
            f"{EM_CLOCK} Последний раз: {user['last_seen'][:16] if user['last_seen'] else '?'}\n\n"
            f"{EM_NOTE} Заметка: {note or 'нет'}",
            ANIMATED_EFFECTS['HEART_ANIMATED']
        )
        await msg.answer(user_text, reply_markup=user_menu_kb(user['user_id'], user['username']), parse_mode=ParseMode.HTML)
    else:
        await msg.answer(f"{EM_ERR} Пользователь не найден.", reply_markup=back_kb(), parse_mode=ParseMode.HTML)
    
    await state.clear()

@dp.callback_query(F.data == 'settings')
async def show_settings(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    await cb.message.edit_text(
        f"{EM_GEAR} <b>Настройки бота</b>\n\n"
        f"Выберите параметр:",
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
    await cb.answer(f"{EM_EYE} Слежка {'включена' if new else 'выключена'}")
    await show_settings(cb)

@dp.callback_query(F.data == 'toggle_log')
async def toggle_log(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    current = get_setting(owner_id, 'log_msgs')
    new = 0 if current else 1
    update_setting(owner_id, 'log_msgs', new)
    await cb.answer(f"{EM_FILE} Логирование {'включено' if new else 'выключено'}")
    await show_settings(cb)

@dp.callback_query(F.data == 'set_auto_reply')
async def set_auto_reply_start(cb: types.CallbackQuery, state: FSMContext):
    owner_id = cb.from_user.id
    current = get_setting(owner_id, 'auto_reply')
    
    await cb.message.edit_text(
        f"{EM_MSG} <b>Авто-ответ</b>\n\n"
        f"Текущий:\n<blockquote>{current or 'не задан'}</blockquote>\n\n"
        f"Отправьте текст (или <code>-</code> чтобы выключить):",
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
    await msg.answer(f"{EM_OK} Авто-ответ {'выключен' if text=='-' else 'установлен'}.", reply_markup=main_kb(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == 'set_welcome')
async def set_welcome_start(cb: types.CallbackQuery, state: FSMContext):
    owner_id = cb.from_user.id
    current = get_setting(owner_id, 'welcome_message')
    
    await cb.message.edit_text(
        f"{EM_WAVE} <b>Приветственное сообщение</b>\n\n"
        f"Текущее:\n<blockquote>{current or 'не задано'}</blockquote>\n\n"
        f"Отправьте текст (или <code>-</code> чтобы выключить):",
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
    await msg.answer(f"{EM_OK} Приветствие {'выключено' if text=='-' else 'установлено'}.", reply_markup=main_kb(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == 'set_speed')
async def set_speed_start(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    current = get_setting(owner_id, 'typing_speed')
    
    await cb.message.edit_text(
        f"{EM_CLOCK} <b>Скорость печати</b>\n\n"
        f"Текущая: <b>x{current}</b>\n\n"
        f"Выберите скорость:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{EM_SLEEP} Медленно (x0.5)", callback_data='speed_0.5',
                                 icon_custom_emoji_id=EMOJI['SLEEP'])],
            [InlineKeyboardButton(text=f"{EM_THUMB} Нормально (x1.0)", callback_data='speed_1.0',
                                 icon_custom_emoji_id=EMOJI['THUMB_UP'])],
            [InlineKeyboardButton(text=f"{EM_FIRE} Быстро (x1.5)", callback_data='speed_1.5',
                                 icon_custom_emoji_id=EMOJI['FIRE'])],
            [InlineKeyboardButton(text=f"{EM_ROCKET} Очень быстро (x2.0)", callback_data='speed_2.0',
                                 icon_custom_emoji_id=EMOJI['ROCKET'])],
            [InlineKeyboardButton(text=f"{EM_LIGHTNING} Максимум (x3.0)", callback_data='speed_3.0',
                                 icon_custom_emoji_id=EMOJI['LIGHTNING'])],
            [InlineKeyboardButton(text=f"{EM_ARROW_LEFT} Назад", callback_data='settings',
                                 icon_custom_emoji_id=EMOJI['ARROW_LEFT'])]
        ]),
        parse_mode=ParseMode.HTML
    )
    await cb.answer()

@dp.callback_query(F.data.startswith('speed_'))
async def set_speed(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    speed = float(cb.data.split('_')[1])
    update_setting(owner_id, 'typing_speed', speed)
    await cb.answer(f"{EM_CLOCK} Скорость x{speed}")
    await show_settings(cb)

@dp.callback_query(F.data == 'keywords')
async def show_keywords_menu(cb: types.CallbackQuery):
    await cb.message.edit_text(
        f"{EM_KEYBOARD} <b>Ключевые слова для автоответа</b>\n\n"
        f"При вводе ключевого слова в чате, бот автоматически ответит заданным текстом.\n\n"
        f"Выберите действие:",
        reply_markup=keyword_kb(),
        parse_mode=ParseMode.HTML
    )
    await cb.answer()

@dp.callback_query(F.data == 'add_keyword')
async def add_keyword_start(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.edit_text(
        f"{EM_PLUS} <b>Добавление ключевого слова</b>\n\n"
        f"Введите ключевое слово и ответ через <code>|</code>\n\n"
        f"Пример: <code>привет|Привет! Чем могу помочь?</code>",
        reply_markup=back_kb(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(SetKeywordReply.waiting)
    await cb.answer()

@dp.message(SetKeywordReply.waiting)
async def process_add_keyword(msg: types.Message, state: FSMContext):
    owner_id = msg.from_user.id
    text = msg.text.strip()
    
    if '|' not in text:
        await msg.answer(f"{EM_ERR} Неверный формат. Используйте: <code>ключевое слово|ответ</code>", parse_mode=ParseMode.HTML)
        return
    
    keyword, reply = text.split('|', 1)
    keyword = keyword.strip().lower()
    reply = reply.strip()
    
    if keyword and reply:
        add_keyword_reply(owner_id, keyword, reply)
        await msg.answer(f"{EM_OK} Ключевое слово <code>{keyword}</code> добавлено!", parse_mode=ParseMode.HTML)
        await state.clear()
        await show_keywords_menu(await msg.answer("..."))
    else:
        await msg.answer(f"{EM_ERR} Ключевое слово и ответ не могут быть пустыми", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == 'list_keywords')
async def list_keywords(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    keywords = get_all_keywords(owner_id)
    
    if not keywords:
        await cb.message.edit_text(
            f"{EM_INFO} Ключевые слова не добавлены.",
            reply_markup=back_kb('keywords'),
            parse_mode=ParseMode.HTML
        )
    else:
        lines = []
        for kw in keywords[:20]:
            lines.append(f"{EM_KEYBOARD} <code>{kw['keyword']}</code> → {kw['reply'][:50]}...")
        
        text = f"{EM_KEYBOARD} <b>Ключевые слова ({len(keywords)})</b>\n\n" + '\n'.join(lines)
        await cb.message.edit_text(text, reply_markup=back_kb('keywords'), parse_mode=ParseMode.HTML)
    await cb.answer()

@dp.callback_query(F.data == 'remove_keyword')
async def remove_keyword_start(cb: types.CallbackQuery, state: FSMContext):
    owner_id = cb.from_user.id
    keywords = get_all_keywords(owner_id)
    
    if not keywords:
        await cb.answer("Нет ключевых слов для удаления", show_alert=True)
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=kw['keyword'], callback_data=f'remove_kw_{kw["keyword"]}',
                            icon_custom_emoji_id=EMOJI['TRASH'])] 
        for kw in keywords[:10]
    ] + [[InlineKeyboardButton(text=f"{EM_ARROW_LEFT} Назад", callback_data='keywords',
                               icon_custom_emoji_id=EMOJI['ARROW_LEFT'])]])
    
    await cb.message.edit_text(
        f"{EM_DEL} <b>Выберите ключевое слово для удаления:</b>",
        reply_markup=kb,
        parse_mode=ParseMode.HTML
    )
    await cb.answer()

@dp.callback_query(F.data.startswith('remove_kw_'))
async def remove_keyword(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    keyword = cb.data.replace('remove_kw_', '')
    remove_keyword(owner_id, keyword)
    await cb.answer(f"Удалено: {keyword}")
    await list_keywords(cb)

@dp.callback_query(F.data == 'filters')
async def show_filters_menu(cb: types.CallbackQuery):
    await cb.message.edit_text(
        f"{EM_WARNING} <b>Фильтр запрещённых слов</b>\n\n"
        f"Сообщения, содержащие запрещённые слова, будут автоматически удалены.\n\n"
        f"Выберите действие:",
        reply_markup=filter_kb(),
        parse_mode=ParseMode.HTML
    )
    await cb.answer()

@dp.callback_query(F.data == 'add_filter')
async def add_filter_start(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.edit_text(
        f"{EM_PLUS} <b>Добавление слова в фильтр</b>\n\n"
        f"Введите слово для фильтрации:",
        reply_markup=back_kb(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(SetFilterWord.waiting)
    await cb.answer()

@dp.message(SetFilterWord.waiting)
async def process_add_filter(msg: types.Message, state: FSMContext):
    owner_id = msg.from_user.id
    word = msg.text.strip().lower()
    
    if word:
        add_filter_word(owner_id, word, 'delete')
        await msg.answer(f"{EM_OK} Слово <code>{word}</code> добавлено в фильтр!", parse_mode=ParseMode.HTML)
        await state.clear()
        await show_filters_menu(await msg.answer("..."))
    else:
        await msg.answer(f"{EM_ERR} Слово не может быть пустым", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == 'templates')
async def show_templates_menu(cb: types.CallbackQuery):
    await cb.message.edit_text(
        f"{EM_COPY} <b>Шаблоны сообщений</b>\n\n"
        f"Шаблоны можно использовать командой <code>.r [название]</code>\n\n"
        f"Выберите действие:",
        reply_markup=templates_kb(),
        parse_mode=ParseMode.HTML
    )
    await cb.answer()

@dp.callback_query(F.data == 'create_template')
async def create_template_start(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.edit_text(
        f"{EM_PLUS} <b>Создание шаблона</b>\n\n"
        f"Введите название и содержимое через <code>|</code>\n\n"
        f"Пример: <code>приветствие|Здравствуйте! Чем могу помочь?</code>",
        reply_markup=back_kb(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(CreateTemplate.waiting)
    await cb.answer()

@dp.message(CreateTemplate.waiting)
async def process_create_template(msg: types.Message, state: FSMContext):
    owner_id = msg.from_user.id
    text = msg.text.strip()
    
    if '|' not in text:
        await msg.answer(f"{EM_ERR} Неверный формат. Используйте: <code>название|содержимое</code>", parse_mode=ParseMode.HTML)
        return
    
    name, content = text.split('|', 1)
    name = name.strip()
    content = content.strip()
    
    if name and content:
        save_template(owner_id, name, content)
        await msg.answer(f"{EM_OK} Шаблон <code>{name}</code> создан!", parse_mode=ParseMode.HTML)
        await state.clear()
        await show_templates_menu(await msg.answer("..."))
    else:
        await msg.answer(f"{EM_ERR} Название и содержимое не могут быть пустыми", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == 'list_templates')
async def list_templates(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    templates = get_all_templates(owner_id)
    
    if not templates:
        await cb.message.edit_text(
            f"{EM_INFO} Шаблоны не созданы.",
            reply_markup=back_kb('templates'),
            parse_mode=ParseMode.HTML
        )
    else:
        lines = []
        for t in templates[:20]:
            lines.append(f"{EM_COPY} <code>{t['name']}</code> → {t['content'][:50]}...")
        
        text = f"{EM_COPY} <b>Шаблоны ({len(templates)})</b>\n\n" + '\n'.join(lines)
        await cb.message.edit_text(text, reply_markup=back_kb('templates'), parse_mode=ParseMode.HTML)
    await cb.answer()

@dp.callback_query(F.data == 'quick_replies')
async def show_quick_replies_menu(cb: types.CallbackQuery):
    await cb.message.edit_text(
        f"{EM_REPLY} <b>Быстрые ответы</b>\n\n"
        f"Быстрые ответы можно использовать командой <code>.q [команда]</code>\n\n"
        f"Выберите действие:",
        reply_markup=quick_reply_kb(),
        parse_mode=ParseMode.HTML
    )
    await cb.answer()

@dp.callback_query(F.data == 'add_quick_reply')
async def add_quick_reply_start(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.edit_text(
        f"{EM_PLUS} <b>Добавление быстрого ответа</b>\n\n"
        f"Введите команду и содержимое через <code>|</code>\n\n"
        f"Пример: <code>help|Список команд: /start - главное меню</code>",
        reply_markup=back_kb(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(QuickReply.waiting)
    await cb.answer()

@dp.message(QuickReply.waiting)
async def process_add_quick_reply(msg: types.Message, state: FSMContext):
    owner_id = msg.from_user.id
    text = msg.text.strip()
    
    if '|' not in text:
        await msg.answer(f"{EM_ERR} Неверный формат. Используйте: <code>команда|содержимое</code>", parse_mode=ParseMode.HTML)
        return
    
    shortcut, content = text.split('|', 1)
    shortcut = shortcut.strip().lower()
    content = content.strip()
    
    if shortcut and content:
        save_quick_reply(owner_id, shortcut, content)
        await msg.answer(f"{EM_OK} Быстрый ответ <code>.q {shortcut}</code> создан!", parse_mode=ParseMode.HTML)
        await state.clear()
        await show_quick_replies_menu(await msg.answer("..."))
    else:
        await msg.answer(f"{EM_ERR} Команда и содержимое не могут быть пустыми", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == 'list_quick_replies')
async def list_quick_replies(cb: types.CallbackQuery):
    owner_id = cb.from_user.id
    replies = get_all_quick_replies(owner_id)
    
    if not replies:
        await cb.message.edit_text(
            f"{EM_INFO} Быстрые ответы не добавлены.",
            reply_markup=back_kb('quick_replies'),
            parse_mode=ParseMode.HTML
        )
    else:
        lines = []
        for r in replies[:20]:
            lines.append(f"{EM_REPLY} <code>.q {r['shortcut']}</code> → {r['content'][:50]}...")
        
        text = f"{EM_REPLY} <b>Быстрые ответы ({len(replies)})</b>\n\n" + '\n'.join(lines)
        await cb.message.edit_text(text, reply_markup=back_kb('quick_replies'), parse_mode=ParseMode.HTML)
    await cb.answer()

@dp.callback_query(F.data == 'back')
async def back_to_main(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    welcome_text = add_effect(
        f"{EM_BOT} <b>Business Monitor Bot</b>\n\n"
        f"{EM_WAVE} <b>Главное меню</b>\n\n"
        f"Выберите действие:",
        ANIMATED_EFFECTS['HEART_ANIMATED']
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
                
                delete_text = add_effect(
                    f"{EM_DEL} <b>Удалено сообщение!</b>\n\n"
                    f"{EM_USER} <b>Кто:</b> {u_name}\n"
                    f"🆔 <b>ID:</b> <code>{cached['user_id']}</code>\n"
                    f"{EM_CHAT} <b>Чат:</b> <code>{event.chat.id}</code>\n"
                    f"{EM_TIME} <b>Время:</b> {cached['ts'][:16] if cached['ts'] else '?'}\n"
                    + (f"\n<b>Текст:</b>\n<blockquote expandable>{content[:500]}</blockquote>" if content else ""),
                    ANIMATED_EFFECTS['POOP']
                )
                
                try:
                    await bot.send_message(owner_id, delete_text, parse_mode=ParseMode.HTML)
                except Exception as e:
                    print(f"notify err: {e}")

@dp.business_message()
async def on_biz_msg(msg: types.Message):
    try:
        bc_id = msg.business_connection_id
        if not bc_id or bc_id not in biz_con:
            return
        
        owner_id = biz_con[bc_id]
        
        cache_msg(owner_id, msg)
        
        if msg.from_user and msg.from_user.id == owner_id:
            return
        
        uid = msg.from_user.id if msg.from_user else 0
        
        if is_blacklisted(owner_id, uid):
            print(f"User {uid} в чёрном списке")
            return
        
        text = msg.text or msg.caption or ''
        
        # Проверяем фильтр слов
        if text:
            filter_action = check_filter(owner_id, text)
            if filter_action == 'delete':
                await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id,
                                        business_connection_id=bc_id)
                await bot.send_message(chat_id=msg.chat.id,
                                      text=f"{EM_WARNING} Сообщение удалено (содержит запрещённое слово)",
                                      business_connection_id=bc_id,
                                      parse_mode=ParseMode.HTML)
                return
        
        # Проверяем ключевые слова
        if text:
            keyword_reply = get_keyword_reply(owner_id, text)
            if keyword_reply:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await bot.send_message(chat_id=msg.chat.id, text=keyword_reply,
                                       business_connection_id=bc_id,
                                       reply_to_message_id=msg.message_id,
                                       parse_mode=ParseMode.HTML)
                return
        
        # Приветствие для нового пользователя
        with db() as c:
            cnt = c.execute('SELECT COUNT(*) FROM msg_cache WHERE owner_id=? AND user_id=?', 
                           (owner_id, uid)).fetchone()[0]
        
        if cnt == 1:
            welcome = get_setting(owner_id, 'welcome_message')
            if welcome:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await bot.send_message(chat_id=msg.chat.id, text=welcome,
                                       business_connection_id=bc_id,
                                       reply_to_message_id=msg.message_id,
                                       parse_mode=ParseMode.HTML)
                return
            
            auto_reply = get_setting(owner_id, 'auto_reply')
            if auto_reply:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await bot.send_message(chat_id=msg.chat.id, text=auto_reply,
                                       business_connection_id=bc_id,
                                       reply_to_message_id=msg.message_id,
                                       parse_mode=ParseMode.HTML)
        
    except Exception as e:
        print(f"on_biz_msg err: {e}")
        import traceback
        traceback.print_exc()

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
        types.BotCommand(command="block", description="Добавить в ЧС"),
        types.BotCommand(command="unblock", description="Удалить из ЧС"),
    ])
    print(f"🤖 Business Bot запущен! Подключений: {len(biz_con)}")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
