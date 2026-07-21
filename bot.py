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
    con.execute("""CREATE TABLE IF NOT EXISTS ustalar (id INTEGER PRIMARY KEY AUTOINCREMENT, ismi TEXT, tel TEXT, mutaxassis TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS buyurtmalar (id INTEGER PRIMARY KEY AUTOINCREMENT, mijoz_ismi TEXT, mijoz_tel TEXT, model TEXT, muammo TEXT, narx INTEGER DEFAULT 0, xarajat INTEGER DEFAULT 0, usta_id INTEGER, usta_ismi TEXT, tayyor TEXT, status TEXT DEFAULT 'Kutilmoqda', sana TEXT DEFAULT (datetime('now')))""")
    con.execute("""CREATE TABLE IF NOT EXISTS foydalanuvchilar (chat_id INTEGER PRIMARY KEY, tel TEXT)""")
    con.commit()
    con.close()

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def set_state(uid, s): user_state[uid] = s
def get_state(uid): return user_state.get(uid, "menu")
def set_ud(uid, k, v):
    if uid not in user_data: user_data[uid] = {}
    user_data[uid][k] = v
def get_ud(uid, k, d=None): return user_data.get(uid, {}).get(k, d)
def clear_ud(uid): user_data[uid] = {}
def fmt(n):
    try: return f"{int(n):,}".replace(",", " ") + " so'm"
    except: return "0 so'm"
def main_kb():
    return ReplyKeyboardMarkup([["📱 Tel qabul"], ["📋 Buyurtmalar", "👨‍🔧 Ustalar"], ["📊 Hisobot"]], resize_keyboard=True)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_state(uid, "menu")
    clear_ud(uid)
    await update.message.reply_text("👋 Tel Ustaxona botiga xush kelibsiz!\n\nMenyudan tanlang:", reply_markup=main_kb())

async def contact_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if get_state(uid) == "q_tel":
        tel = update.message.contact.phone_number
        if not tel.startswith("+"): tel = "+" + tel
        set_ud(uid, "tel", tel)
        set_state(uid, "q_model")
        con = db()
        con.execute("INSERT OR REPLACE INTO foydalanuvchilar (chat_id, tel) VALUES (?,?)", (uid, tel.replace("+", "")))
        con.commit()
        con.close()
        await update.message.reply_text("📱 Telefon modeli:", reply_markup=main_kb())

async def xarajat_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin emas!")
        return
    set_state(uid, "x_id")
    await update.message.reply_text("📋 Buyurtma ID sini kiriting:")

async def admin_qosh_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    if not ctx.args:
        await update.message.reply_text("📋 Ishlatish: /admin_qosh 123456789\n\nYangi adminning Telegram ID sini yozing.")
        return
    try:
        yangi_id = int(ctx.args[0])
        if yangi_id in ADMIN_IDS:
            await update.message.reply_text("⚠️ Bu odam allaqachon admin!")
            return
        ADMIN_IDS.append(yangi_id)
        await update.message.reply_text(f"✅ Yangi admin qo'shildi!\n🆔 {yangi_id}")
    except:
        await update.message.reply_text("❌ Noto'g'ri ID. Faqat raqam kiriting.")

async def admin_list_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    msg = "👑 *Adminlar ro'yxati:*\n\n"
    for i, aid in enumerate(ADMIN_IDS, 1):
        msg += f"{i}. `{aid}`\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def hisobot_korsat(update, start_d, end_d, davr_txt):
    con = db()
    s = con.execute(
        "SELECT COUNT(*) n, COALESCE(SUM(narx),0) j, COALESCE(SUM(xarajat),0) x FROM buyurtmalar WHERE sana>=? AND sana<=?",
        (start_d, end_d)).fetchone()
    ustalar = con.execute("SELECT * FROM ustalar").fetchall()
    con.close()
    sof = s["j"] - s["x"]
    msg = f"📊 *{davr_txt} hisobot:*\n\n📦 Jami: *{s['n']}* ta\n💵 Tushum: *{fmt(s['j'])}*\n🔴 Xarajat: *{fmt(s['x'])}*\n🟢 Sof foyda: *{fmt(sof)}*\n💳 Ish haqi fondi: *{fmt(sof//2)}*\n\n"
    for u in ustalar:
        con = db()
        us = con.execute(
            "SELECT COUNT(*) n, COALESCE(SUM(narx),0) j, COALESCE(SUM(xarajat),0) x FROM buyurtmalar WHERE usta_id=? AND sana>=? AND sana<=?",
            (u["id"], start_d, end_d)).fetchone()
        con.close()
        if us["n"] > 0:
            s2 = us["j"] - us["x"]
            msg += f"👨‍🔧 *{u['ismi']}:* {us['n']} ta | Sof: {fmt(s2)} | 💳 *{fmt(s2//2)}*\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data

    if data.startswith("usta_") and data != "usta_qosh":
        parts = data.split("_", 2)
        set_ud(uid, "usta_id", int(parts[1]))
        set_ud(uid, "usta_ismi", parts[2])
        set_state(uid, "q_tayyor")
        await q.message.reply_text("⏰ Tayyor bo'lish vaqti (masalan: 2 kun):")

    elif data == "usta_qosh":
        set_state(uid, "usta_ismi")
        await q.message.reply_text("👤 Usta ismini kiriting:")

    elif data.startswith("tayyor_"):
        bid = int(data.split("_")[1])
        con = db()
        b = con.execute("SELECT * FROM buyurtmalar WHERE id=?", (bid,)).fetchone()
        con.execute("UPDATE buyurtmalar SET status='Tayyor' WHERE id=?", (bid,))
        con.commit()
        con.close()
        await q.message.reply_text(f"✅ #{bid} TAYYOR!")
        if b:
            con = db()
            m = con.execute("SELECT chat_id FROM foydalanuvchilar WHERE tel=?", (b["mijoz_tel"].replace("+", ""),)).fetchone()
            con.close()
            if m:
                try:
                    await ctx.bot.send_message(chat_id=m["chat_id"], text=f"✅ {b['mijoz_ismi']}, *{b['model']}* TAYYOR! 🎉\n💰 {fmt(b['narx'])}\n📋 #{bid}", parse_mode="Markdown")
                except: pass

    elif data.startswith("berildi_"):
        bid = int(data.split("_")[1])
        con = db()
        con.execute("UPDATE buyurtmalar SET status='Berildi' WHERE id=?", (bid,))
        con.commit()
        con.close()
        await q.message.reply_text(f"📦 #{bid} BERILDI!")

    elif data.startswith("narx_"):
        bid = int(data.split("_")[1])
        set_ud(uid, "tahrir_id", bid)
        set_state(uid, "tahrir_narx")
        await q.message.reply_text(f"💰 #{bid} buyurtma uchun yangi narxni kiriting:")

    elif data.startswith("filter_"):
        status = data.split("_")[1]
        con = db()
        if status == "barchasi":
            rows = con.execute("SELECT * FROM buyurtmalar ORDER BY id DESC LIMIT 20").fetchall()
        else:
            rows = con.execute("SELECT * FROM buyurtmalar WHERE status=? ORDER BY id DESC", (status,)).fetchall()
        con.close()
        if not rows:
            await q.message.reply_text("📭 Buyurtma yo'q.")
            return
        STATUS = {"Kutilmoqda": "⏳", "Jarayonda": "🔧", "Tayyor": "✅", "Berildi": "📦"}
        msg = f"📋 *{status} buyurtmalar:*\n\n"
        btns = []
        for b in rows:
            msg += f"{STATUS.get(b['status'], '📋')} *#{b['id']}* {b['mijoz_ismi']}\n"
            msg += f"   📞 {b['mijoz_tel']} | 📱 {b['model']}\n"
            msg += f"   🔧 {b['muammo']}\n"
            msg += f"   👨‍🔧 {b['usta_ismi']} | 💰 {fmt(b['narx'])} | ⏰ {b['tayyor']}\n\n"
            if b["status"] != "Berildi":
                btns.append([
                    InlineKeyboardButton(f"✅ #{b['id']} Tayyor", callback_data=f"tayyor_{b['id']}"),
                    InlineKeyboardButton(f"📦 #{b['id']} Berildi", callback_data=f"berildi_{b['id']}"),
                    InlineKeyboardButton(f"✏️ #{b['id']} Narx", callback_data=f"narx_{b['id']}")
                ])
        await q.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(btns) if btns else None)

    elif data == "h_sana":
        set_state(uid, "h_sana_kirit")
        await q.message.reply_text("🗓 Sanani kiriting (masalan: 15.07.2026):")

    elif data == "h_oraliq":
        set_state(uid, "h_oraliq_kirit")
        await q.message.reply_text("📆 Kun oralig'ini kiriting (masalan: 15-19):")

    elif data.startswith("h_"):
        davr = data[2:]
        now = datetime.datetime.now()
        if davr == "bugun":
            start_d = now.strftime("%Y-%m-%d 00:00:00")
            end_d = now.strftime("%Y-%m-%d 23:59:59")
            davr_txt = "Bugungi"
        elif davr == "hafta":
            start_d = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            end_d = now.strftime("%Y-%m-%d 23:59:59")
            davr_txt = "Haftalik"
        else:
            start_d = now.strftime("%Y-%m-01 00:00:00")
            end_d = now.strftime("%Y-%m-%d 23:59:59")
            davr_txt = "Oylik"
        con = db()
        s = con.execute("SELECT COUNT(*) n, COALESCE(SUM(narx),0) j, COALESCE(SUM(xarajat),0) x FROM buyurtmalar WHERE sana>=? AND sana<=?", (start_d, end_d)).fetchone()
        ustalar = con.execute("SELECT * FROM ustalar").fetchall()
        con.close()
        sof = s["j"] - s["x"]
        msg = f"📊 *{davr_txt} hisobot:*\n\n📦 Jami: *{s['n']}* ta\n💵 Tushum: *{fmt(s['j'])}*\n🔴 Xarajat: *{fmt(s['x'])}*\n🟢 Sof foyda: *{fmt(sof)}*\n💳 Ish haqi fondi: *{fmt(sof//2)}*\n\n"
        for u in ustalar:
            con = db()
            us = con.execute("SELECT COUNT(*) n, COALESCE(SUM(narx),0) j, COALESCE(SUM(xarajat),0) x FROM buyurtmalar WHERE usta_id=? AND sana>=? AND sana<=?", (u["id"], start_d, end_d)).fetchone()
            con.close()
            if us["n"] > 0:
                s2 = us["j"] - us["x"]
                msg += f"👨‍🔧 *{u['ismi']}:* {us['n']} ta | Sof: {fmt(s2)} | 💳 *{fmt(s2//2)}*\n"
        await q.message.reply_text(msg, parse_mode="Markdown")

async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text or ""
    state = get_state(uid)

    if text == "📱 Tel qabul":
        if uid not in ADMIN_IDS:
            await update.message.reply_text("⛔ Siz admin emassiz!")
            return
        clear_ud(uid)
        set_state(uid, "q_ismi")
        await update.message.reply_text("👤 Mijoz ismini kiriting:")

    elif state == "q_ismi":
        set_ud(uid, "ismi", text)
        set_state(uid, "q_tel")
        kb = ReplyKeyboardMarkup([[KeyboardButton("📞 Telefon ulashish", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("📞 Mijoz telefon raqami:", reply_markup=kb)

    elif state == "q_tel":
        set_ud(uid, "tel", text)
        set_state(uid, "q_model")
        await update.message.reply_text("📱 Telefon modeli:", reply_markup=main_kb())

    elif state == "q_model":
        set_ud(uid, "model", text)
        set_state(uid, "q_muammo")
        await update.message.reply_text("🔧 Muammo tavsifi:")

    elif state == "q_muammo":
        set_ud(uid, "muammo", text)
        set_state(uid, "q_narx")
        await update.message.reply_text("💰 Kelishilgan narx (so'mda):")

    elif state == "q_narx":
        try:
            narx = int(text.replace(" ", "").replace(",", ""))
            set_ud(uid, "narx", narx)
        except:
            await update.message.reply_text("❌ Faqat raqam kiriting!")
            return
        con = db()
        ustalar = con.execute("SELECT * FROM ustalar").fetchall()
        con.close()
        if not ustalar:
            await update.message.reply_text("⚠️ Avval usta qo'shing!")
            set_state(uid, "menu")
            return
        buttons = [[InlineKeyboardButton(f"👨‍🔧 {u['ismi']} ({u['mutaxassis']})", callback_data=f"usta_{u['id']}_{u['ismi']}")] for u in ustalar]
        set_state(uid, "q_usta")
        await update.message.reply_text("👨‍🔧 Ustani tanlang:", reply_markup=InlineKeyboardMarkup(buttons))

    elif state == "q_tayyor":
        ismi = get_ud(uid, "ismi")
        tel = get_ud(uid, "tel")
        model = get_ud(uid, "model")
        muammo = get_ud(uid, "muammo")
        narx = get_ud(uid, "narx")
        usta_id = get_ud(uid, "usta_id")
        usta_ismi = get_ud(uid, "usta_ismi")
        con = db()
        cur = con.execute("INSERT INTO buyurtmalar (mijoz_ismi, mijoz_tel, model, muammo, narx, usta_id, usta_ismi, tayyor) VALUES (?,?,?,?,?,?,?,?)", (ismi, tel, model, muammo, narx, usta_id, usta_ismi, text))
        bid = cur.lastrowid
        con.commit()
        con.close()
        set_state(uid, "menu")
        clear_ud(uid)
        await update.message.reply_text(f"✅ Buyurtma qabul qilindi!\n\n📋 #{bid}\n👤 {ismi}\n📞 {tel}\n📱 {model}\n🔧 {muammo}\n👨‍🔧 {usta_ismi}\n💰 {fmt(narx)}\n⏰ {text}", reply_markup=main_kb())

    elif text == "📋 Buyurtmalar":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏳ Kutilmoqda", callback_data="filter_Kutilmoqda"),
             InlineKeyboardButton("🔧 Jarayonda", callback_data="filter_Jarayonda")],
            [InlineKeyboardButton("✅ Tayyor", callback_data="filter_Tayyor"),
             InlineKeyboardButton("📦 Berildi", callback_data="filter_Berildi")],
            [InlineKeyboardButton("📋 Barchasi", callback_data="filter_barchasi")]
        ])
        await update.message.reply_text("📋 Qaysi buyurtmalarni ko'rmoqchisiz?", reply_markup=buttons)

    elif text == "👨‍🔧 Ustalar":
        con = db()
        ustalar = con.execute("SELECT * FROM ustalar").fetchall()
        con.close()
        msg = "👨‍🔧 *Ustalar:*\n\n"
        for u in ustalar:
            con = db()
            s = con.execute("SELECT COUNT(*) n, COALESCE(SUM(narx),0) j, COALESCE(SUM(xarajat),0) x FROM buyurtmalar WHERE usta_id=?", (u["id"],)).fetchone()
            con.close()
            sof = s["j"] - s["x"]
            msg += f"👤 *{u['ismi']}* | {u['mutaxassis']}\n   📦 {s['n']} ta | 💵 {fmt(s['j'])}\n   🟢 Sof: {fmt(sof)} | 💳 *{fmt(sof//2)}*\n\n"
        if not ustalar:
            msg = "👷 Usta yo'q."
        buttons = [[InlineKeyboardButton("➕ Usta qo'shish", callback_data="usta_qosh")]] if uid in ADMIN_IDS else []
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons) if buttons else None)

    elif state == "usta_ismi":
        set_ud(uid, "u_ismi", text)
        set_state(uid, "usta_tel")
        await update.message.reply_text("📞 Usta telefoni:")

    elif state == "usta_tel":
        set_ud(uid, "u_tel", text)
        set_state(uid, "usta_mut")
        await update.message.reply_text("🔧 Mutaxassisligi:")

    elif state == "usta_mut":
        con = db()
        con.execute("INSERT INTO ustalar (ismi, tel, mutaxassis) VALUES (?,?,?)", (get_ud(uid, "u_ismi"), get_ud(uid, "u_tel"), text))
        con.commit()
        con.close()
        set_state(uid, "menu")
        await update.message.reply_text(f"✅ Usta qo'shildi!\n👤 {get_ud(uid, 'u_ismi')}", reply_markup=main_kb())

    elif text == "📊 Hisobot":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Bugun", callback_data="h_bugun"),
             InlineKeyboardButton("📅 Haftalik", callback_data="h_hafta"),
             InlineKeyboardButton("📅 Oylik", callback_data="h_oy")],
            [InlineKeyboardButton("🗓 Aniq sana", callback_data="h_sana"),
             InlineKeyboardButton("📆 Oraliq (15-19)", callback_data="h_oraliq")]
        ])
        await update.message.reply_text("📊 Davr tanlang:", reply_markup=buttons)

    elif state == "h_sana_kirit":
        try:
            sana = datetime.datetime.strptime(text.strip(), "%d.%m.%Y")
            start_d = sana.strftime("%Y-%m-%d 00:00:00")
            end_d = sana.strftime("%Y-%m-%d 23:59:59")
            await hisobot_korsat(update, start_d, end_d, f"{text.strip()} kuni")
            set_state(uid, "menu")
        except:
            await update.message.reply_text("❌ Sana formati noto'g'ri. Masalan: 15.07.2026")

    elif state == "h_oraliq_kirit":
        try:
            parts = text.strip().split("-")
            kun1 = int(parts[0].strip())
            kun2 = int(parts[1].strip())
            now = datetime.datetime.now()
            start_d = now.replace(day=kun1, hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
            end_d = now.replace(day=kun2, hour=23, minute=59, second=59).strftime("%Y-%m-%d %H:%M:%S")
            await hisobot_korsat(update, start_d, end_d, f"{kun1}-{kun2} kunlar oralig'i")
            set_state(uid, "menu")
        except:
            await update.message.reply_text("❌ Format noto'g'ri. Masalan: 15-19")

    elif state == "tahrir_narx":
        try:
            narx = int(text.replace(" ", "").replace(",", ""))
            bid = get_ud(uid, "tahrir_id")
            con = db()
            con.execute("UPDATE buyurtmalar SET narx=? WHERE id=?", (narx, bid))
            con.commit()
            con.close()
            set_state(uid, "menu")
            await update.message.reply_text(f"✅ #{bid} narx yangilandi: {fmt(narx)}", reply_markup=main_kb())
        except:
            await update.message.reply_text("❌ Raqam kiriting.")

    elif state == "x_id":
        try:
            bid = int(text)
            con = db()
            b = con.execute("SELECT * FROM buyurtmalar WHERE id=?", (bid,)).fetchone()
            con.close()
            if not b:
                await update.message.reply_text("❌ Topilmadi.")
                return
            set_ud(uid, "x_bid", bid)
            set_state(uid, "x_summa")
            await update.message.reply_text(f"💰 #{bid} ga xarajat summasini kiriting:")
        except:
            await update.message.reply_text("❌ Raqam kiriting.")

    elif state == "x_summa":
        try:
            summa = int(text.replace(" ", "").replace(",", ""))
            bid = get_ud(uid, "x_bid")
            con = db()
            con.execute("UPDATE buyurtmalar SET xarajat=xarajat+? WHERE id=?", (summa, bid))
            con.commit()
            con.close()
            set_state(uid, "menu")
            await update.message.reply_text(f"✅ Xarajat: {fmt(summa)}\n📋 #{bid}", reply_markup=main_kb())
        except:
            await update.message.reply_text("❌ Raqam kiriting.")

    else:
        await update.message.reply_text("Menyudan tanlang:", reply_markup=main_kb())

async def main():
    init_db()
    logger.info("Bot ishga tushdi!")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin_qosh", admin_qosh_command))
    app.add_handler(CommandHandler("adminlar", admin_list_command))
    app.add_handler(CommandHandler("xarajat", xarajat_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await __import__("asyncio").Event().wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
