
import requests, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, CallbackQueryHandler
from decimal import Decimal
import json 
import sys 

# --- GLOBAL CONFIG ---
# WARNING: This token (8062694333:AAErWFleYN5E6DijX5tTGwkAl9lxtOueedY) previously caused an InvalidToken error. 
# Replace it if the bot fails to start.
TOKEN = "8062694333:AAErWFleYN5E6DijX5tTGwkAl9lxtOueedY" 

# Graph API Key
API_KEY = "17d4434b518ebec513cd3c2f2edda543" 
SUBGRAPH_ID = "GQ8aYQ1kdQPGDSQzeF6cPo9MzdzqkPxqmuCaMCJoNLrF" # Official Liquity V2 Subgraph ID

# V2 Links
APP_LINK = "https://liquity.app"
WHITEPAPER = "https://bafybeibjommrelqjw22vewpddfdnm5geoz747gv2zeuy7njwivpfcy3xa.ipfs.dweb.link/Liquity%20v2%20-%20Whitepaper%20rev.%200.3%20(November%2C%202024)%20(1).pdf"
TELEGRAM_GROUP = "https://t.me/liquityprotocol" 

# --- V2 API ENDPOINTS ---
GRAPHQL_ENDPOINT = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/{SUBGRAPH_ID}" 

# --- LIQUITY BOLD V2 CONSTANTS ---
MCR = Decimal("1.10") 
OBSERVED_AVG_RATE_PERCENT = Decimal("3.25") 

# --- LANGUAGE CONFIG ---
LANG = range(1)
user_lang = {}

TEXT = {
    "en": {"choose":"Choose language","welcome":"LiquityBold_bot – V2 Live Prices!\n\n/p → ETH & BOLD Price\n/stats → V2 Dashboard\n/calc 10 15000 → Trove Risk (New)\n/risk 15000 4.0 → Interest Cost (New)\n/redeem 5000 → Redemption Sim.\n/earn 10000 90 → Yield Sim.\n/alert 2500 15000 10 → CR Alert","calc":"V2 Borrow Calc\n{0} ETH @ {1}% CR\n\nMax BOLD: {2:,.0f}\nLiq Price: ${3:,.0f}\nFee: {4:,.2f} BOLD (Upfront)","btn":["Open Liquity V2","V2 Whitepaper","Official Telegram"]},
    "es": {"choose":"Elige idioma","welcome":"LiquityBold_bot – Precios en vivo V2!","calc":"Calc V2\n{0} ETH al {1}% CR\n\nMax BOLD: {2:,.0f}\nLiq: ${3:,.0f}\nFee: {4:,.2f} BOLD (Adelantada)","btn":["Abrir V2","Whitepaper V2","Telegram Oficial"]},
    "fr": {"choose":"Choisissez la langue","welcome":"LiquityBold_bot – Prix live V2!","calc":"Calc V2\n{0} ETH à {1}% CR\n\nMax BOLD: {2:,.0f}\nLiq: ${3:,.0f}\nFrais: {4:,.2f} BOLD (Initiaux)","btn":["Ouvrir V2","Whitepaper V2","Telegram Officiel"]},
    "nl": {"choose":"Kies taal","welcome":"LiquityBold_bot – Live V2 prijzen!","calc":"Calc V2\n{0} ETH @ {1}% CR\n\nMax BOLD: {2:,.0f}\nLiq: ${3:,.0f}\nKosten: {4:,.2f} BOLD (Vooraf)","btn":["Open V2","Whitepaper V2","Officiële Telegram"]},
    "zh": {"choose":"选择语言","welcome":"LiquityBold_bot – V2 实时价格!","calc":"V2 计算\n{0} ETH @ {1}% CR\n\n最大 BOLD: {2:,.0f}\n清算: ${3:,.0f}\n费用: {4:,.2f} BOLD (预付)","btn":["打开 V2","V2 白皮书","官方 Telegram"]},
    "ar": {"choose":"اختر اللغة","welcome":"بوت LiquityBold – أسعار V2 حية!","calc":"حاسبة V2\n{0} ETH @ {1}% CR\n\nأقصى BOLD: {2:,.0f}\nالتصفية: ${3:,.0f}\nالرسوم: {4:,.2f} BOLD (مقدم)","btn":["فتح V2","الورقة البيضاء V2","Telegram الرسمي"]}
}

# --- API FUNCTIONS ---

def get_live_price():
    urls = [
        "https://api.coingecko.com/api/v3/simple/price?ids=ethereum,liquity-v2&vs_currencies=usd",
        "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT"
    ]
    
    zero_prices = (0.0, 0.0) 
    
    for url in urls:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "LiquityBot"})
            r.raise_for_status() 
            data = r.json()

            if "ethereum" in data and "usd" in data["ethereum"]:
                eth = float(data["ethereum"]["usd"])
                bold = float(data.get("liquity-v2", {}).get("usd", 1.0))
                return eth, bold
            
            if "price" in data:
                return float(data["price"]), 1.0
        except requests.exceptions.RequestException as e:
            print(f"Price API Request Failed at {url}: {e}", file=sys.stderr)
            time.sleep(0.5)
            continue
        except Exception as e:
            print(f"Error processing price data from {url}: {e}", file=sys.stderr)
            time.sleep(0.5)
            continue
            
    return zero_prices 

def get_prices():
    return get_live_price()

def get_v2_stats():
    query = """
    query LiquityV2GlobalStats {
      protocol(id: "1") { 
        totalValueLockedUSD
        totalBOLDDebtUSD
        stablePoolTotalValueLockedUSD
        averageBorrowRate
      }
    }
    """
    zero_data = {"tvl": 0.0, "debt": 0.0, "avg_rate": 0.0, "sp_value": 0.0}

    try:
        r = requests.post(
            GRAPHQL_ENDPOINT, 
            json={'query': query}, 
            timeout=10, 
            headers={"User-Agent": "LiquityBot"}
        )
        r.raise_for_status() 

        response_data = r.json()

        if 'data' in response_data and response_data['data'].get('protocol'):
            p = response_data['data']['protocol']
            
            tvl = Decimal(p.get("totalValueLockedUSD", 0)) / Decimal("1000000")
            debt = Decimal(p.get("totalBOLDDebtUSD", 0)) / Decimal("1000000")
            sp_value = Decimal(p.get("stablePoolTotalValueLockedUSD", 0)) / Decimal("1000000")
            avg_rate = Decimal(p.get("averageBorrowRate", 0)) * Decimal("100") 
            
            return {"tvl":float(tvl), "debt":float(debt), "avg_rate":float(avg_rate), "sp_value":float(sp_value)}
        
        print("Error: Protocol data not found in Subgraph response or data is empty.", file=sys.stderr)
        return zero_data
        
    except requests.exceptions.RequestException as e:
        print(f"Subgraph API Request Failed (Check Key/Network): {e}", file=sys.stderr)
        return zero_data
    except Exception as e:
        print(f"Processing Error in get_v2_stats: {e}", file=sys.stderr)
        return zero_data

# --- KEYBOARD FUNCTIONS ---
def lang_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("English", callback_data="en"), InlineKeyboardButton("Español", callback_data="es")],
        [InlineKeyboardButton("Français", callback_data="fr"), InlineKeyboardButton("Nederlands", callback_data="nl")],
        [InlineKeyboardButton("中文", callback_data="zh"), InlineKeyboardButton("العربية", callback_data="ar")]
    ])

def main_kb(lang="en"):
    b = TEXT[lang]["btn"]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(b[0], url=APP_LINK)],
        [InlineKeyboardButton(b[1], url=WHITEPAPER)],
        [InlineKeyboardButton(b[2], url=TELEGRAM_GROUP)]
    ])

# --- COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TEXT["en"]["choose"], reply_markup=lang_kb())
    return LANG

async def lang_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = q.data
    user_lang[q.from_user.id] = lang
    await q.edit_message_text(TEXT[lang]["welcome"], reply_markup=main_kb(lang))
    return ConversationHandler.END

async def p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang.get(update.effective_user.id, "en")
    eth, bold = get_prices()
    
    if eth == 0.0:
        await update.message.reply_text("Price data could not be fetched. Check API connectivity.", reply_markup=main_kb(lang))
        return

    peg = (bold - 1) * 100
    await update.message.reply_text(f"ETH: ${eth:,.2f}\nBOLD: ${bold:.4f} (peg {peg:+.2f}%)", reply_markup=main_kb(lang))

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang.get(update.effective_user.id, "en")
    s = get_v2_stats()
    
    if s['tvl'] == 0.0:
        error_message = "V2 Stats could not be fetched. Check Subgraph configuration and API Key validity."
        await update.message.reply_text(error_message, reply_markup=main_kb(lang))
        return
        
    await update.message.reply_text(
        f"V2 TVL (Collateral): ${s['tvl']:.1f}M\n"
        f"Total BOLD Debt: ${s['debt']:.1f}M\n"
        f"Stability Pool: ${s['sp_value']:.1f}M\n"
        f"Avg. Borrow Rate: {s['avg_rate']:.2f}% APR", 
        reply_markup=main_kb(lang)
    )

async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang.get(update.effective_user.id, "en")
    
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /calc <ETH Collateral> <BOLD Debt>\nEx: /calc 10 15000\n(Calculates liquidation price and risk for your specific Trove)", reply_markup=main_kb(lang))
        return
    
    try:
        eth_collateral = Decimal(context.args[0])
        bold_debt = Decimal(context.args[1])

        if eth_collateral <= 0 or bold_debt <= 0:
            raise ValueError("Both collateral and debt must be positive.")

        eth_price, _ = get_prices()
        if eth_price == 0.0:
            await update.message.reply_text("Error: Cannot fetch ETH price for calculation.", reply_markup=main_kb(lang))
            return
            
        eth_price_dec = Decimal(str(eth_price))
        collateral_value_usd = eth_collateral * eth_price_dec

        MCR_DEC = Decimal("1.10") 

        liq_price = (bold_debt * MCR_DEC) / eth_collateral
        initial_cr = (collateral_value_usd / bold_debt) * Decimal("100")

        liq_ratio = liq_price / eth_price_dec
        
        status_emoji = "🟢"
        risk_level = "Low Liquidation Risk"
        alert_text = "✨ Stable"

        if liq_ratio >= Decimal("0.70"): 
            status_emoji = "🔴"
            risk_level = "High Liquidation Risk"
            alert_text = "**🚨 DANGER: Price is too close!**"
        elif liq_ratio >= Decimal("0.50"): 
            status_emoji = "🟡"
            risk_level = "Medium Liquidation Risk"
            alert_text = "⚠️ Warning: Low buffer"
        
        if initial_cr < Decimal("125"):
            alert_text += " (Low CR!)"

        msg = f"V2 Liquidation Risk Analysis {status_emoji}\n"
        msg += f"Collateral: {eth_collateral:,.2f} ETH\n"
        msg += f"Debt: {bold_debt:,.2f} BOLD\n"
        msg += f"Current ETH Price: ${eth_price:,.2f}\n"
        msg += "-" * 20 + "\n"
        msg += f"**Calculated Liq. Price: ${liq_price:,.2f}**\n"
        msg += f"Initial CR: {initial_cr:,.2f}%\n"
        msg += f"Risk Status: {risk_level}\n"
        msg += f"Buffer (Liq Price/ETH Price): {liq_ratio * 100:.2f}%\n\n"
        msg += f"{alert_text}"
        
        await update.message.reply_text(msg, reply_markup=main_kb(lang))
        
    except Exception as e:
        await update.message.reply_text(f"Error – Check inputs or values: {e}", reply_markup=main_kb(lang))


async def risk_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang.get(update.effective_user.id, "en")

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /risk <BOLD Debt> <Your Annual Rate %>\nEx: /risk 15000 4.0\n(Compares your rate to the 3.25% average to assess redemption risk)", reply_markup=main_kb(lang))
        return

    try:
        bold_loan_amount = Decimal(context.args[0])
        user_rate_percent = Decimal(context.args[1])
        
        avg_rate_percent = OBSERVED_AVG_RATE_PERCENT 
        user_annual_rate_decimal = user_rate_percent / Decimal("100")
        annual_interest_cost_bold = bold_loan_amount * user_annual_rate_decimal
        
        status_emoji = "🟡" 
        redemption_risk = "Medium Redemption Risk"
        
        if user_rate_percent <= avg_rate_percent * Decimal("0.90"):
            status_emoji = "🔴"
            redemption_risk = "**High Redemption Risk**"
        
        elif user_rate_percent >= avg_rate_percent * Decimal("1.10"):
            status_emoji = "🟢"
            redemption_risk = "Low Redemption Risk"

        msg = (
            f"Trove Interest & Redemption Risk {status_emoji}\n"
            f"Loan Amount: {bold_loan_amount:,.2f} BOLD\n"
            f"Your Annual Rate: {user_rate_percent:.2f}%\n"
            f"Protocol Avg. Rate: {avg_rate_percent:.2f}%\n"
            f"---"
            f"**Est. Annual Interest Cost: {annual_interest_cost_bold:,.2f} BOLD**\n"
            f"Redemption Risk: {redemption_risk}\n\n"
            f"Note: Lower interest rates (Red) mean your Trove is a preferred target for BOLD redemptions."
        )
        await update.message.reply_text(msg, reply_markup=main_kb(lang))
        
    except Exception as e:
        await update.message.reply_text(f"Error – Check inputs or values: {e}", reply_markup=main_kb(lang))


async def redeem_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang.get(update.effective_user.id, "en")
    
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /redeem <BOLD Amt>\nEx: /redeem 5000\n(Simulates the cost to redeem BOLD for ETH/LST collateral)", reply_markup=main_kb(lang))
        return

    try:
        bold_amt = Decimal(context.args[0])
        sim_base_rate = Decimal("0.005") 
        fee_rate = Decimal("0.005") + sim_base_rate 
        
        fee_bold = bold_amt * fee_rate
        eth_price, _ = get_prices()
        
        if eth_price == 0.0:
            await update.message.reply_text("Error: Cannot fetch ETH price for redemption calculation.", reply_markup=main_kb(lang))
            return
            
        usd_received = bold_amt - fee_bold
        eth_received = usd_received / Decimal(str(eth_price))

        msg = (
            f"V2 Redemption Simulation 🔄\n"
            f"{bold_amt:,.0f} BOLD @ $1.00\n"
            f"Simulated Fee Rate: {fee_rate*100:.2f}%\n"
            f"Fee Paid: {fee_bold:,.2f} BOLD\n"
            f"Est. Value Received: ${usd_received:,.2f}\n"
            f"Est. ETH Received: {eth_received:,.4f} ETH"
        )
        await update.message.reply_text(msg, reply_markup=main_kb(lang))
        
    except Exception as e:
        await update.message.reply_text(f"Error – try /redeem 5000: {e}", reply_markup=main_kb(lang))

async def earn_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang.get(update.effective_user.id, "en")
    
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /earn <BOLD Amt> <Days>\nEx: /earn 10000 90\n(Project BOLD earnings in the Stability Pool)", reply_markup=main_kb(lang))
        return

    try:
        bold_amt = Decimal(context.args[0])
        days = Decimal(context.args[1])

        s = get_v2_stats()
        
        if s['avg_rate'] == 0.0:
            error_message = "Error: Cannot fetch current average rate for earnings calculation. Check /stats."
            await update.message.reply_text(error_message, reply_markup=main_kb(lang))
            return
            
        avg_rate_percent = Decimal(str(s['avg_rate']))
        annual_rate = avg_rate_percent / Decimal("100") 
        
        earnings = bold_amt * annual_rate * (days / Decimal("365"))

        msg = (
            f"V2 Earn (Stability Pool) Projection 💰\n"
            f"Deposit: {bold_amt:,.0f} BOLD\n"
            f"Duration: {days:,.0f} Days\n"
            f"---"
            f"Est. Annual APR: {avg_rate_percent:.2f}%\n"
            f"Projected Earnings: {earnings:,.2f} BOLD"
        )
        await update.message.reply_text(msg, reply_markup=main_kb(lang))
        
    except Exception as e:
        await update.message.reply_text(f"Error – try /earn 10000 90: {e}", reply_markup=main_kb(lang))

async def alert_calc_v2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang.get(update.effective_user.id, "en")

    if len(context.args) != 3:
        await update.message.reply_text("Usage: /alert <Target ETH Price> <BOLD Debt> <ETH Collateral>\nEx: /alert 2500 15000 10\n(Check your CR at a future ETH price to manage risk)", reply_markup=main_kb(lang))
        return

    try:
        target_eth_price = Decimal(context.args[0])
        current_bold_debt = Decimal(context.args[1])
        eth_collateral = Decimal(context.args[2])

        collateral_value = eth_collateral * target_eth_price
        new_cr = (collateral_value / current_bold_debt) * Decimal("100")
        
        MCR_ALERT = Decimal("110") 
        
        status = "SAFE"
        if new_cr < MCR_ALERT:
            status = "**AT RISK OF LIQUIDATION** 🚨"
        elif new_cr < Decimal("125"):
            status = "**WARNING: LOW CR** ⚠️"

        msg = (
            f"V2 Risk Check (Alert Sim) 🛡️\n"
            f"If ETH reaches ${target_eth_price:,.2f}:\n"
            f"Debt: {current_bold_debt:,.0f} BOLD\n"
            f"Collateral: {eth_collateral:,.2f} ETH\n"
            f"---"
            f"**New CR will be: {new_cr:,.2f}%**\n"
            f"Status: {status}"
        )
        await update.message.reply_text(msg, reply_markup=main_kb(lang))
        
    except Exception as e:
        await update.message.reply_text(f"Error – try /alert 2500 15000 10: {e}", reply_markup=main_kb(lang))


# --- MAIN RUNNER ---
def main():
    if TOKEN == "YOUR_VALID_TELEGRAM_TOKEN_HERE":
        print("\n*** BOT STARTUP FAILED ***")
        print("CRITICAL: Please replace 'YOUR_VALID_TELEGRAM_TOKEN_HERE' with a valid, regenerated Telegram bot token from BotFather.")
        sys.exit(1) 

    app = Application.builder().token(TOKEN).build()
    
    conv = ConversationHandler(entry_points=[CommandHandler("start", start)],
                               states={LANG: [CallbackQueryHandler(lang_selected)]},
                               fallbacks=[])
    app.add_handler(conv)
    
    app.add_handler(CommandHandler(["p","price"], p))
    app.add_handler(CommandHandler("stats", stats))
    
    app.add_handler(CommandHandler("calc", calc)) 
    app.add_handler(CommandHandler("risk", risk_check)) 
    
    app.add_handler(CommandHandler(["redeem", "r"], redeem_calc))
    app.add_handler(CommandHandler(["earn", "e"], earn_calc))
    app.add_handler(CommandHandler("alert", alert_calc_v2)) 

    print("LiquityBold_bot FINAL REAL-TIME VERSION RUNNING – ETH always live!")
    app.run_polling()

if __name__ == "__main__":
    main()
