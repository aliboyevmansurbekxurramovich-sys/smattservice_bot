import os
import json
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
from database import db

# ─── SOZLAMALAR ───────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Admin Telegram ID larini shu yerga kiriting
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "123456789").split(",")]

# ─── HOLATLAR (ConversationHandler uchun) ────────────────────
(
    LANG,
    MAIN_MENU,
    # Buyurtma qabul qilish
    QABUL_MIJOZ_ISMI, QABUL_MIJOZ_TEL, QABUL_MODEL,
    QABUL_MUAMMO, QABUL_NARX, QABUL_USTA, QABUL_TAYYOR,
    # Usta qo'shish
    USTA_ISMI, USTA_TEL, USTA_MUTAXASSIS,
    # Xarajat qo'shish
    XARAJAT_ID, XARAJAT_SUMMA,
    # Status o'zgartirish
    STATUS_ID, STATUS_YANGI,
) = range(17)

# ─── MATNLAR (O'zbek / Rus) ───────────────────────────────────
T = {
    "uz": {
        "til_tanla": "🌐 Tilni tanlang / Выберите язык:",
        "xush_kelibsiz": "👋 Tel Ustaxona botiga xush kelibsiz!\n\nQuyidagi menyudan tanlang:",
        "menu_qabul": "📱 Tel qabul qilish",
        "menu_buyurtmalar": "📋 Buyurtmalar ro'yxati",
        "menu_ustalar": "👨‍🔧 Ustalar",
        "menu_hisobot": "📊 Hisobot",
        "menu_sozlamalar": "⚙️ Sozlamalar",
        "mijoz_ismi": "👤 Mijoz ismini kiriting:",
        "mijoz_tel": "📞 Mijoz telefon raqamini kiriting:\n(+998901234567 yoki ulashish tugmasi)",
        "tel_share": "📞 Telefon ulashish",
        "tel_model": "📱 Telefon modelini kiriting:\n(masalan: iPhone 13 Pro, Samsung A54)",
        "muammo": "🔧 Muammo tavsifini kiriting:\n(masalan: Ekran singan, zaryadlanmaydi)",
        "narx": "💰 Kelishilgan narxni kiriting (so'mda):\n(masalan: 150000)",
        "usta_tanla": "👨‍🔧 Ustani tanlang:",
        "tayyor_vaqt": "⏰ Taxminiy tayyor bo'lish vaqtini kiriting:\n(masalan: 2 kun, Ertaga kechqurun)",
        "qabul_muvaffaq": "✅ Buyurtma qabul qilindi!\n\n📋 Buyurtma #{id}\n👤 {ismi}\n📞 {tel}\n📱 {model}\n🔧 {muammo}\n👨‍🔧 Usta: {usta}\n💰 Narx: {narx:,} so'm\n⏰ Tayyor: {tayyor}\n\n📩 Mijozga xabar yuborildi!",
        "mijoz_xabar": "📱 Assalomu alaykum, {ismi}!\n\nSizning *{model}* telefoningiz ustaxonaga qabul qilindi.\n\n🔧 Muammo: {muammo}\n👨‍🔧 Usta: {usta}\n💰 Kelishilgan narx: {narx:,} so'm\n⏰ Tayyor bo'lish: {tayyor}\n\n📋 Buyurtma #{id}\n\nTayyor bo'lganda xabar beramiz! 🔔",
        "mijoz_tayyor_xabar": "✅ Assalomu alaykum, {ismi}!\n\nSizning *{model}* telefoningiz *TAYYOR*! 🎉\n\n📋 Buyurtma #{id}\n💰 To'lov: {narx:,} so'm\n\nUstaxonaga kelib olishingiz mumkin.",
        "buyurtma_yoq": "📭 Hozircha buyurtma yo'q.",
        "buyurtmalar_royxat": "📋 *Buyurtmalar ro'yxati:*\n\n",
        "status_ozgartir": "🔄 Status o'zgartirish",
        "tayyor_deb_belgi": "✅ Tayyor deb belgilash",
        "berildi": "📦 Berildi deb belgilash",
        "ustalar_yoq": "👷 Hozircha usta yo'q. Avval usta qo'shing.",
        "usta_qosh": "➕ Usta qo'shish",
        "usta_ismi": "👤 Usta ismini kiriting:",
        "usta_tel": "📞 Usta telefon raqamini kiriting:",
        "usta_mutaxassis": "🔧 Mutaxassisligini kiriting:\n(masalan: Ekran, batareya, plata)",
        "usta_qoshildi": "✅ Usta qo'shildi!\n\n👤 {ismi}\n📞 {tel}\n🔧 {mutaxassis}",
        "hisobot_davr": "📊 Hisobot davrini tanlang:",
        "bugun": "📅 Bugungi",
        "haftalik": "📅 Haftalik",
        "oylik": "📅 Oylik",
        "hisobot_sarlavha": "📊 *{davr} hisobot:*\n\n",
        "hisobot_jami": "📦 Jami buyurtma: *{n}* ta\n💵 Jami tushum: *{jami:,}* so'm\n🔴 Xarajatlar: *{xarajat:,}* so'm\n🟢 Sof foyda: *{sof:,}* so'm\n👷 Ish haqi fondi (50%): *{ish:,}* so'm\n\n",
        "usta_hisobot": "👨‍🔧 *{ismi}:*\n  📦 {n} ta buyurtma\n  💵 Tushum: {jami:,} so'm\n  🟢 Sof: {sof:,} so'm\n  💳 Ish haqi: *{ish:,}* so'm\n\n",
        "xarajat_qosh": "💸 Xarajat qo'shish",
        "xarajat_id": "📋 Buyurtma ID sini kiriting:",
        "xarajat_summa": "💰 Xarajat summasini kiriting (so'mda):",
        "xarajat_qoshildi": "✅ Xarajat qo'shildi: {summa:,} so'm\n📋 Buyurtma #{id}",
        "bekor": "❌ Bekor qilish",
        "orqaga": "🔙 Orqaga",
        "admin_emas": "⛔ Siz admin emassiz!",
        "id_topilmadi": "❌ Bunday ID topilmadi.",
        "noto_g_ri": "❌ Noto'g'ri format. Qaytadan kiriting.",
    },
    "ru": {
        "til_tanla": "🌐 Tilni tanlang / Выберите язык:",
        "xush_kelibsiz": "👋 Добро пожаловать в бот Тел Устахона!\n\nВыберите из меню:",
        "menu_qabul": "📱 Принять телефон",
        "menu_buyurtmalar": "📋 Список заказов",
        "menu_ustalar": "👨‍🔧 Мастера",
        "menu_hisobot": "📊 Отчёт",
        "menu_sozlamalar": "⚙️ Настройки",
        "mijoz_ismi": "👤 Введите имя клиента:",
        "mijoz_tel": "📞 Введите номер телефона клиента:\n(+998901234567 или кнопка поделиться)",
        "tel_share": "📞 Поделиться номером",
        "tel_model": "📱 Введите модель телефона:\n(например: iPhone 13 Pro, Samsung A54)",
        "muammo": "🔧 Опишите проблему:\n(например: разбит экран, не заряжается)",
        "narx": "💰 Введите договорную цену (в сумах):\n(например: 150000)",
        "usta_tanla": "👨‍🔧 Выберите мастера:",
        "tayyor_vaqt": "⏰ Введите примерное время готовности:\n(например: 2 дня, завтра вечером)",
        "qabul_muvaffaq": "✅ Заказ принят!\n\n📋 Заказ #{id}\n👤 {ismi}\n📞 {tel}\n📱 {model}\n🔧 {muammo}\n👨‍🔧 Мастер: {usta}\n💰 Цена: {narx:,} сум\n⏰ Готовность: {tayyor}\n\n📩 Клиенту отправлено сообщение!",
        "mijoz_xabar": "📱 Здравствуйте, {ismi}!\n\nВаш телефон *{model}* принят в мастерскую.\n\n🔧 Проблема: {muammo}\n👨‍🔧 Мастер: {usta}\n💰 Договорная цена: {narx:,} сум\n⏰ Готовность: {tayyor}\n\n📋 Заказ #{id}\n\nКогда будет готово — сообщим! 🔔",
        "mijoz_tayyor_xabar": "✅ Здравствуйте, {ismi}!\n\nВаш телефон *{model}* *ГОТОВ*! 🎉\n\n📋 Заказ #{id}\n💰 Оплата: {narx:,} сум\n\nМожете забрать в мастерской.",
        "buyurtma_yoq": "📭 Заказов пока нет.",
        "buyurtmalar_royxat": "📋 *Список заказов:*\n\n",
        "status_ozgartir": "🔄 Изменить статус",
        "tayyor_deb_belgi": "✅ Отметить готовым",
        "berildi": "📦 Отметить выданным",
        "ustalar_yoq": "👷 Мастеров нет. Сначала добавьте мастера.",
        "usta_qosh": "➕ Добавить мастера",
        "usta_ismi": "👤 Введите имя мастера:",
        "usta_tel": "📞 Введите телефон мастера:",
        "usta_mutaxassis": "🔧 Введите специализацию:\n(например: экран, батарея, плата)",
        "usta_qoshildi": "✅ Мастер добавлен!\n\n👤 {ismi}\n📞 {tel}\n🔧 {mutaxassis}",
        "hisobot_davr": "📊 Выберите период отчёта:",
        "bugun": "📅 Сегодня",
        "haftalik": "📅 За неделю",
        "oylik": "📅 За месяц",
        "hisobot_sarlavha": "📊 *Отчёт за {davr}:*\n\n",
        "hisobot_jami": "📦 Всего заказов: *{n}* шт\n💵 Общая выручка: *{jami:,}* сум\n🔴 Расходы: *{xarajat:,}* сум\n🟢 Чистая прибыль: *{sof:,}* сум\n👷 Фонд зарплаты (50%): *{ish:,}* сум\n\n",
        "usta_hisobot": "👨‍🔧 *{ismi}:*\n  📦 {n} заказов\n  💵 Выручка: {jami:,} сум\n  🟢 Чистая: {sof:,} сум\n  💳 Зарплата: *{ish:,}* сум\n\n",
        "xarajat_qosh": "💸 Добавить расход",
        "xarajat_id": "📋 Введите ID заказа:",
        "xarajat_summa": "💰 Введите сумму расхода (в сумах):",
        "xarajat_qoshildi": "✅ Расход добавлен: {summa:,} сум\n📋 Заказ #{id}",
        "bekor": "❌ Отмена",
        "orqaga": "🔙 Назад",
        "admin_emas": "⛔ Вы не являетесь администратором!",
        "id_topilmadi": "❌ Такой ID не найден.",
        "noto_g_ri": "❌ Неверный формат. Введите снова.",
    }
}

def t(lang, key, **kwargs):
    text = T.get(lang, T["uz"]).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text

def is_admin(user_id):
    return user_id in ADMIN_IDS

def main_keyboard(lang):
    return ReplyKeyboardMarkup([
        [t(lang, "menu_qabul")],
        [t(lang, "menu_buyurtmalar"), t(lang, "menu_ustalar")],
        [t(lang, "menu_hisobot")],
    ], resize_keyboard=True)

# ─── /start ──────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
         InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
    ])
    await update.message.reply_text(T["uz"]["til_tanla"], reply_markup=keyboard)
    return LANG

async def lang_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    ctx.user_data["lang"] = lang
    db.set_user_lang(query.from_user.id, lang)
    await query.message.reply_text(t(lang, "xush_kelibsiz"), reply_markup=main_keyboard(lang))
    return MAIN_MENU

# ─── ASOSIY MENYU ────────────────────────────────────────────
async def main_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang") or db.get_user_lang(update.effective_user.id) or "uz"
    ctx.user_data["lang"] = lang
    text = update.message.text

    if text == t(lang, "menu_qabul"):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text(t(lang, "admin_emas"))
            return MAIN_MENU
        await update.message.reply_text(t(lang, "mijoz_ismi"))
        return QABUL_MIJOZ_ISMI

    elif text == t(lang, "menu_buyurtmalar"):
        await show_buyurtmalar(update, ctx, lang)
        return MAIN_MENU

    elif text == t(lang, "menu_ustalar"):
        await show_ustalar(update, ctx, lang)
        return MAIN_MENU

    elif text == t(lang, "menu_hisobot"):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t(lang, "bugun"), callback_data="hisobot_bugun"),
             InlineKeyboardButton(t(lang, "haftalik"), callback_data="hisobot_hafta"),
             InlineKeyboardButton(t(lang, "oylik"), callback_data="hisobot_oy")]
        ])
        await update.message.reply_text(t(lang, "hisobot_davr"), reply_markup=keyboard)
        return MAIN_MENU

    return MAIN_MENU

# ─── BUYURTMA QABUL QILISH ───────────────────────────────────
async def qabul_mijoz_ismi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "uz")
    ctx.user_data["yangi"] = {"ismi": update.message.text}
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton(t(lang, "tel_share"), request_contact=True)],
         [t(lang, "bekor")]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(t(lang, "mijoz_tel"), reply_markup=kb)
    return QABUL_MIJOZ_TEL

async def qabul_mijoz_tel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "uz")
    if update.message.contact:
        tel = update.message.contact.phone_number
        if not tel.startswith("+"):
            tel = "+" + tel
    else:
        tel = update.message.text
    ctx.user_data["yangi"]["tel"] = tel
    await update.message.reply_text(t(lang, "tel_model"), reply_markup=main_keyboard(lang))
    return QABUL_MODEL

async def qabul_model(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "uz")
    ctx.user_data["yangi"]["model"] = update.message.text
    await update.message.reply_text(t(lang, "muammo"))
    return QABUL_MUAMMO

async def qabul_muammo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "uz")
    ctx.user_data["yangi"]["muammo"] = update.message.text
    await update.message.reply_text(t(lang, "narx"))
    return QABUL_NARX

async def qabul_narx(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "uz")
    try:
        narx = int(update.message.text.replace(" ", "").replace(",", ""))
        ctx.user_data["yangi"]["narx"] = narx
    except:
        await update.message.reply_text(t(lang, "noto_g_ri"))
        return QABUL_NARX

    ustalar = db.get_ustalar()
    if not ustalar:
        await update.message.reply_text(t(lang, "ustalar_yoq"))
        return MAIN_MENU

    buttons = [[InlineKeyboardButton(f"👨‍🔧 {u['ismi']} ({u['mutaxassis']})", callback_data=f"usta_{u['id']}")]
               for u in ustalar]
    await update.message.reply_text(t(lang, "usta_tanla"),
                                    reply_markup=InlineKeyboardMarkup(buttons))
    return QABUL_USTA

async def qabul_usta_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = ctx.user_data.get("lang", "uz")
    usta_id = int(query.data.split("_")[1])
    usta = db.get_usta(usta_id)
    ctx.user_data["yangi"]["usta_id"] = usta_id
    ctx.user_data["yangi"]["usta_ismi"] = usta["ismi"] if usta else "—"
    await query.message.reply_text(t(lang, "tayyor_vaqt"))
    return QABUL_TAYYOR

async def qabul_tayyor(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "uz")
    yangi = ctx.user_data["yangi"]
    yangi["tayyor"] = update.message.text

    buyurtma_id = db.add_buyurtma(
        mIsmi=yangi["ismi"], mTel=yangi["tel"], model=yangi["model"],
        muammo=yangi["muammo"], narx=yangi["narx"],
        usta_id=yangi["usta_id"], usta_ismi=yangi["usta_ismi"],
        tayyor=yangi["tayyor"]
    )

    await update.message.reply_text(
        t(lang, "qabul_muvaffaq",
          id=buyurtma_id, ismi=yangi["ismi"], tel=yangi["tel"],
          model=yangi["model"], muammo=yangi["muammo"],
          usta=yangi["usta_ismi"], narx=yangi["narx"], tayyor=yangi["tayyor"]),
        parse_mode="Markdown", reply_markup=main_keyboard(lang)
    )

    # Mijozga Telegram orqali xabar yuborish urinishi
    mijoz_chat = db.get_mijoz_chat_id(yangi["tel"])
    if mijoz_chat:
        try:
            await ctx.bot.send_message(
                chat_id=mijoz_chat,
                text=t(lang, "mijoz_xabar",
                       ismi=yangi["ismi"], model=yangi["model"],
                       muammo=yangi["muammo"], usta=yangi["usta_ismi"],
                       narx=yangi["narx"], tayyor=yangi["tayyor"], id=buyurtma_id),
                parse_mode="Markdown"
            )
        except:
            pass

    return MAIN_MENU

# ─── BUYURTMALAR KO'RSATISH ──────────────────────────────────
async def show_buyurtmalar(update: Update, ctx, lang):
    buyurtmalar = db.get_buyurtmalar()
    if not buyurtmalar:
        await update.message.reply_text(t(lang, "buyurtma_yoq"))
        return

    STATUS_EMOJI = {"Kutilmoqda": "⏳", "Jarayonda": "🔧", "Tayyor": "✅", "Berildi": "📦"}
    text = t(lang, "buyurtmalar_royxat")
    buttons = []

    for b in buyurtmalar[-10:]:  # oxirgi 10 ta
        emoji = STATUS_EMOJI.get(b["status"], "📋")
        text += f"{emoji} *#{b['id']}* — {b['mIsmi']} | {b['model']}\n"
        text += f"   👨‍🔧 {b['usta_ismi']} | 💰 {b['narx']:,} so'm | {b['status']}\n\n"
        if b["status"] != "Berildi":
            buttons.append([
                InlineKeyboardButton(f"✅ #{b['id']} Tayyor", callback_data=f"tayyor_{b['id']}"),
                InlineKeyboardButton(f"📦 #{b['id']} Berildi", callback_data=f"berildi_{b['id']}")
            ])

    kb = InlineKeyboardMarkup(buttons) if buttons else None
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)

async def status_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = ctx.user_data.get("lang") or db.get_user_lang(query.from_user.id) or "uz"

    action, bid = query.data.split("_")
    bid = int(bid)
    buyurtma = db.get_buyurtma(bid)
    if not buyurtma:
        await query.message.reply_text(t(lang, "id_topilmadi"))
        return

    if action == "tayyor":
        db.update_status(bid, "Tayyor")
        mijoz_chat = db.get_mijoz_chat_id(buyurtma["mTel"])
        if mijoz_chat:
            try:
                await ctx.bot.send_message(
                    chat_id=mijoz_chat,
                    text=t(lang, "mijoz_tayyor_xabar",
                           ismi=buyurtma["mIsmi"], model=buyurtma["model"],
                           id=bid, narx=buyurtma["narx"]),
                    parse_mode="Markdown"
                )
            except:
                pass
        await query.message.reply_text(f"✅ #{bid} buyurtma TAYYOR deb belgilandi! Mijozga xabar yuborildi.")

    elif action == "berildi":
        db.update_status(bid, "Berildi")
        await query.message.reply_text(f"📦 #{bid} buyurtma BERILDI deb belgilandi.")

# ─── USTALAR ─────────────────────────────────────────────────
async def show_ustalar(update: Update, ctx, lang):
    ustalar = db.get_ustalar()
    if not ustalar:
        await update.message.reply_text(t(lang, "ustalar_yoq"))
    else:
        text = "👨‍🔧 *Ustalar ro'yxati:*\n\n"
        for u in ustalar:
            stats = db.get_usta_stats(u["id"])
            sof = stats["jami"] - stats["xarajat"]
            ish = int(sof * 0.5)
            text += f"👤 *{u['ismi']}*\n"
            text += f"   📞 {u['tel']} | 🔧 {u['mutaxassis']}\n"
            text += f"   📦 {stats['n']} ta | 💵 {stats['jami']:,} so'm\n"
            text += f"   🟢 Sof: {sof:,} | 💳 Ish haqi: *{ish:,}* so'm\n\n"
        await update.message.reply_text(text, parse_mode="Markdown")

    if is_admin(update.effective_user.id):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t(lang, "usta_qosh"), callback_data="usta_qosh")]
        ])
        await update.message.reply_text("➕ Yangi usta qo'shish:", reply_markup=keyboard)

async def usta_qosh_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = ctx.user_data.get("lang") or db.get_user_lang(query.from_user.id) or "uz"
    await query.message.reply_text(t(lang, "usta_ismi"))
    return USTA_ISMI

async def usta_ismi_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "uz")
    ctx.user_data["yangi_usta"] = {"ismi": update.message.text}
    await update.message.reply_text(t(lang, "usta_tel"))
    return USTA_TEL

async def usta_tel_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "uz")
    ctx.user_data["yangi_usta"]["tel"] = update.message.text
    await update.message.reply_text(t(lang, "usta_mutaxassis"))
    return USTA_MUTAXASSIS

async def usta_mutaxassis_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "uz")
    usta = ctx.user_data["yangi_usta"]
    usta["mutaxassis"] = update.message.text
    db.add_usta(usta["ismi"], usta["tel"], usta["mutaxassis"])
    await update.message.reply_text(
        t(lang, "usta_qoshildi", ismi=usta["ismi"], tel=usta["tel"], mutaxassis=usta["mutaxassis"]),
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU

# ─── XARAJAT QO'SHISH ────────────────────────────────────────
async def xarajat_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "uz")
    await update.message.reply_text(t(lang, "xarajat_id"))
    return XARAJAT_ID

async def xarajat_id_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "uz")
    try:
        bid = int(update.message.text)
        b = db.get_buyurtma(bid)
        if not b:
            await update.message.reply_text(t(lang, "id_topilmadi"))
            return XARAJAT_ID
        ctx.user_data["xarajat_id"] = bid
        await update.message.reply_text(t(lang, "xarajat_summa"))
        return XARAJAT_SUMMA
    except:
        await update.message.reply_text(t(lang, "noto_g_ri"))
        return XARAJAT_ID

async def xarajat_summa_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "uz")
    try:
        summa = int(update.message.text.replace(" ", "").replace(",", ""))
        bid = ctx.user_data["xarajat_id"]
        db.add_xarajat(bid, summa)
        await update.message.reply_text(
            t(lang, "xarajat_qoshildi", summa=summa, id=bid),
            reply_markup=main_keyboard(lang)
        )
        return MAIN_MENU
    except:
        await update.message.reply_text(t(lang, "noto_g_ri"))
        return XARAJAT_SUMMA

# ─── HISOBOT ─────────────────────────────────────────────────
async def hisobot_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = ctx.user_data.get("lang") or db.get_user_lang(query.from_user.id) or "uz"

    davr_key = query.data.split("_")[1]
    davr_text = {"bugun": t(lang, "bugun"), "hafta": t(lang, "haftalik"), "oy": t(lang, "oylik")}

    stats = db.get_hisobot(davr_key)
    sof = stats["jami"] - stats["xarajat"]
    ish = int(sof * 0.5)

    text = t(lang, "hisobot_sarlavha", davr=davr_text.get(davr_key, ""))
    text += t(lang, "hisobot_jami", n=stats["n"], jami=stats["jami"],
              xarajat=stats["xarajat"], sof=sof, ish=ish)

    usta_stats = db.get_all_usta_stats(davr_key)
    for us in usta_stats:
        s = us["jami"] - us["xarajat"]
        text += t(lang, "usta_hisobot",
                  ismi=us["ismi"], n=us["n"],
                  jami=us["jami"], sof=s, ish=int(s * 0.5))

    await query.message.reply_text(text, parse_mode="Markdown")

# ─── /xarajat BUYRUQ ─────────────────────────────────────────
async def xarajat_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang") or db.get_user_lang(update.effective_user.id) or "uz"
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(t(lang, "admin_emas"))
        return MAIN_MENU
    await update.message.reply_text(t(lang, "xarajat_id"))
    return XARAJAT_ID

# ─── BEKOR QILISH ────────────────────────────────────────────
async def bekor(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "uz")
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_keyboard(lang))
    return MAIN_MENU

# ─── BOTNI ISHGA TUSHIRISH ───────────────────────────────────
def main():
    db.init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [CallbackQueryHandler(lang_callback, pattern="^lang_")],
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu),
                CallbackQueryHandler(hisobot_callback, pattern="^hisobot_"),
                CallbackQueryHandler(status_callback, pattern="^(tayyor|berildi)_"),
                CallbackQueryHandler(usta_qosh_callback, pattern="^usta_qosh$"),
            ],
            QABUL_MIJOZ_ISMI: [MessageHandler(filters.TEXT, qabul_mijoz_ismi)],
            QABUL_MIJOZ_TEL: [
                MessageHandler(filters.CONTACT, qabul_mijoz_tel),
                MessageHandler(filters.TEXT, qabul_mijoz_tel),
            ],
            QABUL_MODEL: [MessageHandler(filters.TEXT, qabul_model)],
            QABUL_MUAMMO: [MessageHandler(filters.TEXT, qabul_muammo)],
            QABUL_NARX: [MessageHandler(filters.TEXT, qabul_narx)],
            QABUL_USTA: [CallbackQueryHandler(qabul_usta_callback, pattern="^usta_\\d+$")],
            QABUL_TAYYOR: [MessageHandler(filters.TEXT, qabul_tayyor)],
            USTA_ISMI: [MessageHandler(filters.TEXT, usta_ismi_input)],
            USTA_TEL: [MessageHandler(filters.TEXT, usta_tel_input)],
            USTA_MUTAXASSIS: [MessageHandler(filters.TEXT, usta_mutaxassis_input)],
            XARAJAT_ID: [MessageHandler(filters.TEXT, xarajat_id_input)],
            XARAJAT_SUMMA: [MessageHandler(filters.TEXT, xarajat_summa_input)],
        },
        fallbacks=[
            CommandHandler("bekor", bekor),
            CommandHandler("xarajat", xarajat_command),
            MessageHandler(filters.Regex("^(❌ Bekor qilish|❌ Отмена)$"), bekor),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    print("✅ Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
