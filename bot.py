# bot.py - LiquityBold_bot V2 - 24/7 cloud version
import os, requests, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, CallbackQueryHandler
from decimal import Decimal

TOKEN = os.getenv("TOKEN", "8062694333:AAErWFleYN5E6DijX5tTGwkAl9lxtOueedY")

APP_LINK = "https://liquity.app"
WHITEPAPER = "https://bafybeibjommrelqjw22vewpddgfdnm5geoz747gv2zeuy7njwivpfcy3xa.ipfs.dweb.link/Liquity%20v2%20-%20Whitepaper%20rev.%200.3%20(November%2C%202024)%20(1).pdf"
TELEGRAM_GROUP = "https://t.me/liquityprotocol"

LANG = range(1)
user_lang = {}

TEXT = {
    "en": {"choose":"Choose language 🌍","welcome":"LiquityBold_bot – V2 Live!\n\n/p → ETH & BOLD price\n/stats → Dashboard\n/calc 10 170 → Calculator","calc":"Borrow Calc\n{0} ETH @ {1}% CR\n\nMax BOLD: {2:,.0f}\nLiq price: ${3:,.2f}\nFee: {4:,.0f} BOLD","btn":["Open Liquity V2","V2 Whitepaper","Official Telegram"]},
}

def get_price():
    for _ in range(3):
        try:
            r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum,liquity-v2&vs_currencies=usd", timeout=10)
            d = r.json()
            return float(d["ethereum"]["usd"]), float(d.get("liquity-v2", {"usd":1.0})["usd"])
        except:
            time.sleep(1)
    return 2881.88, 1.00

def lang_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("English", callback_data="en")]])

def main_kb():
    b = TEXT["en"]["btn"]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(b[0], url=APP_LINK)],
        [InlineKeyboardButton(b[1], url=WHITEPAPER)],
        [InlineKeyboardButton(b[2], url=TELEGRAM_GROUP)]
    ])

async def start(update: Update, context): 
    await update.message.reply_text(TEXT["en"]["choose"], reply_markup=lang_kb())
    return LANG

async def lang_selected(update: Update, context):
    q = update.callback_query
    await q.answer()
    user_lang[q.from_user.id] = "en"
    await q.edit_message_text(TEXT["en"]["welcome"], reply_markup=main_kb())
    return ConversationHandler.END

async def p(update: Update, context):
    eth, bold = get_price()
    await update.message.reply_text(f"ETH: ${eth:,.2f}\nBOLD: ${bold:.4f}", reply_markup=main_kb())

async def stats(update: Update, context):
    await update.message.reply_text("V2 TVL: ~$47M\nBOLD Debt: ~$42M\nBorrow Fee: 0.5%", reply_markup=main_kb())

async def calc(update: Update, context):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /calc <ETH amount> <CR%>\nExample: /calc 10 170", reply_markup=main_kb())
        return
    try:
        eth_amt = Decimal(context.args[0])
        cr = Decimal(context.args[1])
        eth_price, _ = get_price()
        bold = (eth_amt * eth_price * 100) / cr
        liq_price = bold * Decimal("1.1") / eth_amt
        fee = bold * Decimal("0.005")
        msg = TEXT["en"]["calc"].format(eth_amt, cr, bold, liq_price, fee)
        await update.message.reply_text(msg, reply_markup=main_kb())
    except:
        await update.message.reply_text("Invalid input – try /calc 10 170", reply_markup=main_kb())

def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(entry_points=[CommandHandler("start", start)], states={LANG: [CallbackQueryHandler(lang_selected)]}, fallbacks=[])
    app.add_handler(conv)
    app.add_handler(CommandHandler(["p", "price"], p))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("calc", calc))
    print("LiquityBold_bot is running 24/7!")
    app.run_polling()

if __name__ == "__main__":
    main()
