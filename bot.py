# bot.py - LiquityBold_bot V2 - Render 24/7 Fixed for v20.8
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from decimal import Decimal

TOKEN = "8062694333:AAErWFleYN5E6DijX5tTGwkAl9lxtOueedY"

def get_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd", timeout=10)
        return float(r.json()["ethereum"]["usd"]), 1.00
    except:
        return 2881.88, 1.00

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Open Liquity V2", url="https://liquity.app")],
        [InlineKeyboardButton("V2 Whitepaper", url="https://bafybeibjommrelqjw22vewpddgfdnm5geoz747gv2zeuy7njwivpfcy3xa.ipfs.dweb.link/Liquity%20v2%20-%20Whitepaper%20rev.%200.3%20(November%2C%202024)%20(1).pdf")],
        [InlineKeyboardButton("Official Telegram", url="https://t.me/liquityprotocol")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "LiquityBold_bot – V2 Live!\n\n/p → Price\n/stats → Dashboard\n/calc 10 170 → Calculator",
        reply_markup=main_kb()
    )

async def p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    eth, bold = get_price()
    await update.message.reply_text(f"ETH: ${eth:,.2f}\nBOLD: ${bold:.4f}", reply_markup=main_kb())

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Liquity V2\nTVL: ~$47.4M\nBOLD Debt: ~$42.7M\nBorrow Fee: 0.5%", reply_markup=main_kb())

async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /calc <ETH> <CR%>\nEx: /calc 10 170", reply_markup=main_kb())
        return
    try:
        eth_amt = Decimal(context.args[0])
        cr = Decimal(context.args[1])
        eth_price, _ = get_price()
        bold = (eth_amt * eth_price * 100) / cr
        liq = bold * Decimal("1.1") / eth_amt
        await update.message.reply_text(
            f"{eth_amt} ETH @ {cr}% CR\n\nMax BOLD: {bold:,.0f}\nLiq price: ${liq:,.0f}\nFee: ~{bold*0.005:,.0f} BOLD",
            reply_markup=main_kb()
        )
    except:
        await update.message.reply_text("Error – try /calc 10 170", reply_markup=main_kb())

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["p", "price"], p))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("calc", calc))
    print("LiquityBold_bot 24/7 started!")
    app.run_polling()

if __name__ == "__main__":
    main()
