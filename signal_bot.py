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
     await bot.send_message(chat_id=CHAT_ID, tex
