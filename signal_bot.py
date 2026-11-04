import os
import asyncio
import ccxt.async_support as ccxt
import pandas as pd
from telegram import Bot
from datetime import datetime

# ====================== 从环境变量读取 ======================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = ["SOL/USDT", "ETH/USDT", "BTC/USDT"]
TIMEFRAME = "15m"
CHECK_INTERVAL = 30
# ==========================================================

bot = Bot(token=TELEGRAM_TOKEN)

async def send_signal(symbol, side, price, rr, reason):
    emoji = "🟢" if side == "做多" else "🔴"
    text = (
        f"{emoji} <b>{symbol} {side} @{price}</b>\n"
        f"胜率中 · RR {rr}:1\n"
        f"级别：15分钟超短线\n"
        f"结论：{side}，符合策略逻辑\n"
        f"时间：{datetime.now().strftime('%H:%M:%S')}\n"
        f"备注：{reason}"
    )
    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")


async def check_signal(exchange, symbol):
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=50)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        
        df["ema20"] = df["close"].ewm(span=20).mean()
        df["ema50"] = df["close"].ewm(span=50).mean()
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        if (prev["ema20"] < prev["ema50"]) and (last["ema20"] > last["ema50"]) and (last["close"] > last["ema20"]):
            price = round(last["close"], 4 if "SOL" in symbol else 2)
            await send_signal(symbol, "做多", price, "1.8", "EMA金叉 + 价格站上均线")
            return True
        
        if (prev["ema20"] > prev["ema50"]) and (last["ema20"] < last["ema50"]) and (last["close"] < last["ema20"]):
            price = round(last["close"], 4 if "SOL" in symbol else 2)
            await send_signal(symbol, "做空", price, "1.6", "EMA死叉 + 价格跌破均线")
            return True
            
    except Exception as e:
        print(f"{symbol} 检查出错: {e}")
    
    return False


async def main():
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("错误：请设置 TELEGRAM_TOKEN 和 CHAT_ID 环境变量")
        return

    exchange = ccxt.binance({"enableRateLimit": True})
    
    print("信号机器人已启动，正在监控...")
    await bot.send_message(chat_id=CHAT_ID, text="✅ 信号机器人已启动，开始监控 SOL / ETH / BTC 15分钟级别")
    
    last_signal_time = {}
    
    while True:
        for symbol in SYMBOLS:
            now = datetime.now().timestamp()
            if symbol in last_signal_time and now - last_signal_time[symbol] < 300:
                continue
                
            triggered = await check_signal(exchange, symbol)
            if triggered:
                last_signal_time[symbol] = now
                
        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
