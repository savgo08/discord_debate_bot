import discord
from discord.ext import commands
import json
import os
import threading
from flask import Flask
import random

# -------------- CONFIG --------------
TOKEN = os.environ["TOKEN"]  # Replace with your token
STATS_FILE = "stats.json"
# -------------------------------------

# Create bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load stats
def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {}

# Save stats
def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f)

stats = load_stats()

# Calculate rank based on win percentage
def get_rank(win_pct):
    if win_pct >= 90:
        return "Grandmaster"
    elif win_pct >= 75:
        return "Master"
    elif win_pct >= 60:
        return "Advanced"
    elif win_pct >= 50:
        return "Intermediate"
    else:
        return "Beginner"

# ---------------- BOT COMMANDS ----------------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def win(ctx, opponent: discord.Member):
    winner = str(ctx.author.id)
    loser = str(opponent.id)

    for uid in [winner, loser]:
        if uid not in stats:
            stats[uid] = {"wins": 0, "losses": 0}

    stats[winner]["wins"] += 1
    stats[loser]["losses"] += 1
    save_stats(stats)

    await ctx.send(f"{ctx.author.mention} defeated {opponent.mention}!")

@bot.command()
async def record(ctx, member: discord.Member = None):
    member = member or ctx.author
    uid = str(member.id)

    if uid not in stats:
        await ctx.send(f"{member.mention} has no recorded matches.")
        return

    wins = stats[uid]["wins"]
    losses = stats[uid]["losses"]
    total = wins + losses
    win_pct = (wins / total) * 100 if total > 0 else 0
    rank = get_rank(win_pct)

    await ctx.send(
        f"{member.mention} — Wins: {wins}, Losses: {losses}, "
        f"Win %: {win_pct:.1f}%, Rank: {rank}"
    )

@bot.command()
async def leaderboard(ctx):
    if not stats:
        await ctx.send("No matches recorded yet.")
        return

    leaderboard_data = []
    for uid, data in stats.items():
        total = data["wins"] + data["losses"]
        win_pct = (data["wins"] / total) * 100 if total > 0 else 0
        leaderboard_data.append((uid, win_pct, data["wins"], data["losses"]))

    leaderboard_data.sort(key=lambda x: x[1], reverse=True)

    msg = "**Leaderboard (by Win %)**\n"
    for i, (uid, win_pct, wins, losses) in enumerate(leaderboard_data[:10], start=1):
        user = await bot.fetch_user(int(uid))
        msg += f"{i}. {user.name} — {win_pct:.1f}% ({wins}W/{losses}L)\n"

    await ctx.send(msg)

# ---------------- KEEP ALIVE SERVER ----------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ---------------- START BOT & SERVER ----------------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
