import os
import logging
import sqlite3
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "0").split(",") if x.strip()]

DB = "ustaxona.db"
user_state = {}
user_data = {}

def init_db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS ustalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ismi TEXT, tel TEXT, mutaxassis TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS buyurtmalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mijoz_ismi TEXT, mijoz_tel TEXT, model TEXT, muammo TEXT,
        narx INTEGER DEFAULT 0, xarajat INTEGER DEFAULT 0,
        usta_id INTEGER, usta_ismi TEXT, tayyor TEXT,
        status TEXT DEFAULT 'Kutilmoqda',
        sana TEXT DEFAULT (datetime('now')))""")
    con.execute("""CREATE TABLE IF NOT EXISTS foydalanuvchilar (
        chat_id INTEGER PRIMARY KEY, tel TEXT)""")
    con.commit()
    con.close()

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def set_state(uid, state): user_state[uid] = state
def get_state(uid): return user_state.get(uid, "menu")
def set_ud(uid, key, val):
    if uid not in user_data: user_data[uid] = {}
    user_data[uid][key] = val
def get_ud(uid, key, default=None): return user_data.get(uid, {}).get(key, default)
def clear_ud(uid): user_data[uid] = {}
def fmt(n):
    try: return f"{int(n):,}".replace(",", " ") + " so'm"
    except: return "0 so'm"

def main_kb():
    return ReplyKeyboardMarkup([
        ["📱 Tel qabul"],
        ["📋 Buyurtmalar", "👨‍🔧 Ustalar"],
        ["📊 Hisobot"],
    ], resize_keyboard=True)
