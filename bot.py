import os
import json
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
from database import db

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "123456789").split(",")]

(
    LANG,
    MAIN_MENU,
    QABUL_MIJOZ_ISMI, QABUL_MIJOZ_TEL, QABUL_MODEL,
    QABUL_MUAMMO, QABUL_NARX, QABUL_USTA, QABUL_TAYYOR,
    USTA_ISMI, USTA_TEL, USTA_MUTAXASSIS,
    XARAJAT_ID, XARAJAT_SUMMA,
    STATUS_ID, STATUS_YANGI,
) = range(16)
