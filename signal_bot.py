import os
 import asyncio
 from datetime import datetime
 import ccxt.async_support as ccxt
 import pandas as pd
 from telegram import Bot
 # ========== 配置（也可以不动，优先读环境变量） ==========
 TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
 CHAT_ID = os.getenv("CHAT_ID")
 SYMBOLS = ["SOL/USDT", "ETH/USDT", "BTC/USDT"]
 TIMEFRAME = "15m"
 CHECK_INTERVAL = 30  # 每轮扫描间隔，单位：秒
 COOLDOWN_SECONDS = 600  # 同一个品种 + 同方向冷却：10 分钟
 # ========================================================
 bot = Bot(token=TELEGRAM_TOKEN)
 last_signal = dict()  # key: f"{symbol}|{side}"
 def get_cn_time() -> str:
     """东八区时间"""
     return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
 async def send_signal(symbol: str, side: str, price: float, reason: str):
     emoji = "🟢" if side == "做多" else "🔴"
     text = (
         f"{emoji} <b>{symbol} {side}</b>\n"
         f"入场参考：{price:.4f}\n"
         f"级别：15 分钟\n"
         f"时间：{get_cn_time()}\n"
         f"备注：{reason}"
     )
     await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")
 async def check_signal(exchange, symbol: str):
     try:
         ohlcv = await exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=100)
         df = pd.DataFrame(ohlcv, columns=["time", "open", "high", "low", "close", "volume"])
         # 和 TradingView 对齐的 EMA
         df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
         df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
         last = df.iloc[-1]
         prev = df.iloc[-2]
         price = float(last["close"])
         key_long = f"{symbol}|做多"
         key_short = f"{symbol}|做空"
         now_ts = datetime.utcnow().timestamp()
         # 金叉：EMA20 上穿 EMA50 → 做多
         if prev["ema20"] <= prev["ema50"] and last["ema20"] > last["ema50"]:
             if key_long not in last_signal or (now_ts - last_signal[key_long]) > COOLDOWN_SECONDS:
                 await send_signal(symbol, "做多", price, "EMA20 上穿 EMA50，金叉")
                 last_signal[key_long] = now_ts
                 return True
         # 死叉：EMA20 下穿 EMA50 → 做空
         if prev["ema20"] >= prev["ema50"] and last["ema20"] < last["ema50"]:
             if key_short not in last_signal or (now_ts - last_signal[key_short]) > COOLDOWN_SECONDS:
                 await send_signal(symbol, "做空", price, "EMA20 下穿 EMA50，死叉")
                 last_signal[key_short] = now_ts
                 return True
         return False
     except Exception as e:
         print(f"[{get_cn_time()}] {symbol} 检查异常：{str(e)}")
         return False
 async def main():
     if not TELEGRAM_TOKEN or not CHAT_ID:
         print("缺少环境变量：TELEGRAM_TOKEN / CHAT_ID")
         return
     exchange = ccxt.binance({
         "enableRateLimit": True,
         "timeout": 15000
     })
     print(f"[{get_cn_time()}] ✅ 信号机器人启动成功，监控：{SYMBOLS}")
     await bot.send_message(
         chat_id=CHAT_ID,
         text=f"✅ 监控已启动\n标的：{', '.join(SYMBOLS)}\n周期：{TIMEFRAME}\n冷却：{COOLDOWN_SECONDS//60} 分钟",
         parse_mode="HTML"
     )
     while True:
         for sym in SYMBOLS:
             await check_signal(exchange, sym)
         await asyncio.sleep(CHECK_INTERVAL)
 if __name__ == "__main__":
     asyncio.run(main())
