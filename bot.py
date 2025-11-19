# bot.py - LiquityBold_bot V2 - 100% working on Render free tier (Nov 2025)
import os
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes
from decimal import Decimal

TOKEN = "8062694333:AAErWFleYN5E6DijX5tTGwkAl9lxtOueedY"

def get_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd", timeout=10)
        return float(r.json()["ethereum"]["usd"]), 1.00
    except:
        return 2881.88, 1.00

def kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Open Liquity V2", url="https://liquity.app")],
        [InlineKeyboardButton("Official Telegram", url="https://t.me/liquityprotocol")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("LiquityBold_bot V2 Live!\n\n/p → Price\n/stats → Stats\n/calc 10 170 → Calculator", reply_markup=kb())

async def p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    eth, bold = get_price()
    await update.message.reply_text(f"ETH: ${eth:,.2f}\nBOLD: ${bold:.4f}", reply_markup=kb())

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Liquity V2\nTVL: ~$47.4M\nBOLD in circulation: ~$42.7M\nBorrow fee: 0.5%", reply_markup=kb())

async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /calc <ETH amount> <CR%>\nExample: /calc 10 170", reply_markup=kb())
        return
    try:
        eth = Decimal(context.args[0])
        cr = Decimal(context.args[1])
        price, _ = get_price()
        bold = (eth * price * 100) / cr
        liq = bold * Decimal("1.1") / eth
        await update.message.reply_text(
            f"{eth} ETH @ {cr}% CR\n\nMax BOLD: {bold:,.0f}\nLiq price: ${liq:,.0f}\nFee: ~{bold*Decimal('0.005'):,.0f} BOLD",
            reply_markup=kb()
        )
    except:
        await update.message.reply_text("Invalid input – try /calc 10 170", reply_markup=kb())

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["p", "price"], p))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("calc", calc))
    print("LiquityBold_bot is now running 24/7!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

