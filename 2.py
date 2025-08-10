# bot.py
import discord
from discord.ext import commands
import json
import os
from keep_alive import keep_alive  # giữ bot sống 24/24

TOKEN = os.getenv("TOKEN")  # lấy token từ Secrets trên Replit
DATA_FILE = "status_data.json"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ====== Load / Save Data ======
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ====== View nhập thông tin ======
class InfoView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.button(label="Bạn đang chơi game gì", style=discord.ButtonStyle.primary)
    async def game_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Không phải form của bạn.", ephemeral=True)
        await interaction.response.send_modal(InputModal(self.user_id, "game", "Nhập game bạn đang chơi"))

    @discord.ui.button(label="Có NY chưa", style=discord.ButtonStyle.primary)
    async def ny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Không phải form của bạn.", ephemeral=True)
        await interaction.response.send_modal(InputModal(self.user_id, "ny", "Bạn có NY chưa?"))

    @discord.ui.button(label="Có sục không", style=discord.ButtonStyle.primary)
    async def suc_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Không phải form của bạn.", ephemeral=True)
        await interaction.response.send_modal(InputModal(self.user_id, "suc", "Bạn có sục không?"))

    @discord.ui.button(label="Link Facebook", style=discord.ButtonStyle.success)
    async def fb_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Không phải form của bạn.", ephemeral=True)
        await interaction.response.send_modal(InputModal(self.user_id, "facebook", "Nhập link Facebook"))

    @discord.ui.button(label="SĐT (nếu có)", style=discord.ButtonStyle.success)
    async def sdt_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Không phải form của bạn.", ephemeral=True)
        await interaction.response.send_modal(InputModal(self.user_id, "sdt", "Nhập số điện thoại"))

# ====== Modal nhập dữ liệu ======
class InputModal(discord.ui.Modal):
    def __init__(self, user_id, field, title):
        super().__init__(title=title)
        self.user_id = user_id
        self.field = field
        self.input = discord.ui.TextInput(label="Nhập thông tin", style=discord.TextStyle.short, required=False)
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        user_data = data.get(str(self.user_id), {})
        user_data[self.field] = self.input.value
        data[str(self.user_id)] = user_data
        save_data(data)
        await interaction.response.send_message("✅ Đã lưu thông tin!", ephemeral=True)

# ====== Lệnh nhập mới ======
@bot.command()
async def new(ctx):
    try:
        await ctx.author.send("📋 Nhập thông tin của bạn:", view=InfoView(ctx.author.id))
        await ctx.send("📩 Mình đã gửi form qua DM của bạn!")
    except discord.Forbidden:
        await ctx.send("❌ Không thể gửi DM, vui lòng bật tin nhắn riêng.")

# ====== Lệnh chỉnh sửa ======
@bot.command()
async def edit(ctx):
    try:
        await ctx.author.send("✏ Chỉnh sửa thông tin của bạn:", view=InfoView(ctx.author.id))
        await ctx.send("📩 Mình đã gửi form qua DM của bạn!")
    except discord.Forbidden:
        await ctx.send("❌ Không thể gửi DM, vui lòng bật tin nhắn riêng.")

# ====== Lệnh tìm kiếm ======
@bot.command()
async def timkiem(ctx, member: discord.Member):
    data = load_data()
    user_info = data.get(str(member.id), None)

    # Trạng thái online/offline
    status_text = {
        discord.Status.online: "🟢 Online",
        discord.Status.offline: "⚫ Offline",
        discord.Status.idle: "🌙 Idle",
        discord.Status.dnd: "⛔ Do Not Disturb"
    }.get(member.status, "❓ Không rõ")

    # Custom Status
    custom_status = None
    for activity in member.activities:
        if isinstance(activity, discord.CustomActivity):
            emoji = f"{activity.emoji} " if activity.emoji else ""
            custom_status = f"{emoji}{activity.name or ''}"
            break

    embed = discord.Embed(title=f"Thông tin của {member.display_name}", color=0x00ffcc)
    embed.add_field(name="Trạng thái", value=status_text, inline=False)
    embed.add_field(name="Custom Status", value=custom_status or "(Không đặt)", inline=False)

    if user_info:
        for key, value in user_info.items():
            embed.add_field(name=key.capitalize(), value=value if value else "(Chưa nhập)", inline=True)
    else:
        embed.add_field(name="Thông tin", value="(Người này chưa nhập !new)", inline=False)

    await ctx.send(embed=embed)
    try:
        await ctx.author.send(embed=embed)
    except:
        pass

# ====== Lệnh FA ======
@bot.command()
async def FA(ctx):
    data = load_data()
    missing_users = []
    for member in ctx.guild.members:
        if not member.bot and str(member.id) not in data:
            missing_users.append(member.mention)

    if missing_users:
        await ctx.send("💔 Những người chưa nhập thông tin: " + ", ".join(missing_users))
    else:
        await ctx.send("🎉 Ai cũng đã nhập thông tin!")

# === Chạy bot ===
keep_alive()  # giữ bot sống 24/24
bot.run(TOKEN)
