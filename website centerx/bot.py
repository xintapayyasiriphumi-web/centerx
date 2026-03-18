import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()



# ==================== CONFIG ====================
DISCORD_TOKEN = "MTQ4MzQ3ODczMDUzMjcxNjU0NQ.GZ36zh.yJfOgwOXsBI6t3pAo6YbNGt8FfxmqRUEpmPD3o"
KEYAUTH_SELLER_KEY = "4916a5875668c00ca58280e58aa903e8"
KEYAUTH_APP_NAME = "ULTIMATEX"
ALLOWED_ROLE_ID = 1400021321374502925
# ================================================

KEYAUTH_API_URL = "https://keyauth.win/api/seller/"
 
intents = discord.Intents.default()
intents.message_content = True
 
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
 
 
# ==================== HELPERS ====================
 
async def keyauth_request(params: dict) -> dict:
    params["sellerkey"] = KEYAUTH_SELLER_KEY
    async with aiohttp.ClientSession() as session:
        async with session.get(KEYAUTH_API_URL, params=params) as resp:
            text = await resp.text()
            try:
                return json.loads(text)
            except Exception:
                return {"success": False, "message": text}
 
 
def check_role(interaction: discord.Interaction) -> bool:
    if ALLOWED_ROLE_ID == 0:
        return True
    return discord.utils.get(interaction.user.roles, id=ALLOWED_ROLE_ID) is not None
 
 
# ==================== MODALS ====================
 
class GenKeyModal(discord.ui.Modal, title="🔑 สร้าง Key ใหม่"):
    amount = discord.ui.TextInput(
        label="จำนวน Key (1–10)",
        placeholder="เช่น 3",
        default="1",
        min_length=1,
        max_length=2,
    )
    duration = discord.ui.TextInput(
        label="ระยะเวลา (ตัวเลข)",
        placeholder="เช่น 7",
        default="1",
        min_length=1,
        max_length=4,
    )
    unit = discord.ui.TextInput(
        label="หน่วยเวลา (day / week / month / year)",
        placeholder="day, week, month, year",
        default="day",
        min_length=3,
        max_length=5,
    )
    mask = discord.ui.TextInput(
        label="Mask  (* = สุ่มตัวอักษร)",
        placeholder="เช่น ULTIMATEX-****** หรือ ****-****-****",
        default="ULTIMATEX-******",
        required=False,
    )
 
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
 
        VALID_UNITS = {"day", "week", "month", "year"}
        unit_input = self.unit.value.strip().lower()
 
        try:
            amount_val = int(self.amount.value)
            duration_val = int(self.duration.value)
            assert 1 <= amount_val <= 10
            assert duration_val >= 1
            assert unit_input in VALID_UNITS
        except (ValueError, AssertionError):
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ ข้อมูลไม่ถูกต้อง",
                    description=(
                        "• จำนวน Key ต้องเป็น **1–10**\n"
                        "• ระยะเวลาต้องมากกว่า **0**\n"
                        "• หน่วยเวลา: **day / week / month / year**"
                    ),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return
 
        # ใช้ * เป็น wildcard ตาม KeyAuth จริง
        mask_val = self.mask.value.strip() or "ULTIMATEX-******"
 
        unit_th = {"day": "วัน", "week": "สัปดาห์", "month": "เดือน", "year": "ปี"}
        unit_label = unit_th[unit_input]
 
        # คำนวณเป็นจำนวนวันสำหรับส่ง API
        day_map = {
            "day": duration_val,
            "week": duration_val * 7,
            "month": duration_val * 30,
            "year": duration_val * 365,
        }
        expiry_days = day_map[unit_input]
 
        params = {
            "type": "add",
            "format": "JSON",
            "expiry": expiry_days,
            "amount": amount_val,
            "mask": mask_val,
            "app": KEYAUTH_APP_NAME,
            "character": 1,
            "level": 1,
        }
 
        result = await keyauth_request(params)
 
        if result.get("success"):
            raw_key = result.get("key", "")
            keys = result.get("keys", [])
            if not keys and raw_key:
                keys = [raw_key]
 
            keys_text = "\n".join([f"`{k}`" for k in keys]) if keys else "`ไม่มีข้อมูล`"
            embed = discord.Embed(
                title="✅ สร้าง Key สำเร็จ",
                description=f"สร้างได้ **{len(keys)}** Key | อายุ **{duration_val} {unit_label}**",
                color=discord.Color.green()
            )
            embed.add_field(name="🔑 Keys", value=keys_text, inline=False)
            embed.set_footer(text=f"สร้างโดย {interaction.user} | App: {KEYAUTH_APP_NAME}")
        else:
            embed = discord.Embed(
                title="❌ สร้าง Key ล้มเหลว",
                description=result.get("message", "เกิดข้อผิดพลาดที่ไม่ทราบสาเหตุ"),
                color=discord.Color.red()
            )
 
        await interaction.followup.send(embed=embed, ephemeral=True)
 
 
class DeleteKeyModal(discord.ui.Modal, title="🗑️ ลบ Key"):
    key = discord.ui.TextInput(
        label="Key ที่ต้องการลบ",
        placeholder="วาง Key ที่ต้องการลบที่นี่",
    )
 
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        params = {
            "type": "del",
            "key": self.key.value.strip(),
            "app": KEYAUTH_APP_NAME,
            "format": "JSON",
        }
        result = await keyauth_request(params)
        if result.get("success"):
            embed = discord.Embed(
                title="🗑️ ลบ Key สำเร็จ",
                description=f"ลบ Key `{self.key.value.strip()}` เรียบร้อยแล้ว",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="❌ ลบ Key ล้มเหลว",
                description=result.get("message", "เกิดข้อผิดพลาด"),
                color=discord.Color.red()
            )
        embed.set_footer(text=f"ดำเนินการโดย {interaction.user}")
        await interaction.followup.send(embed=embed, ephemeral=True)
 
 
class KeyInfoModal(discord.ui.Modal, title="🔍 ตรวจสอบ Key"):
    key = discord.ui.TextInput(
        label="Key ที่ต้องการตรวจสอบ",
        placeholder="วาง Key ที่ต้องการดูข้อมูลที่นี่",
    )
 
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        params = {
            "type": "info",
            "key": self.key.value.strip(),
            "app": KEYAUTH_APP_NAME,
            "format": "JSON",
        }
        result = await keyauth_request(params)
        if result.get("success"):
            import datetime
 
            duration_raw = result.get("duration", "N/A")
            status       = result.get("status", "N/A")
            level        = result.get("level", "N/A")
            usedby       = result.get("usedby", "") or "ยังไม่ถูกใช้"
            usedon_raw   = result.get("usedon", "") or "N/A"
            created_raw  = result.get("creationdate", "N/A")
 
            # แปลง duration (Unix timestamp วินาที) → วันที่หมดอายุ
            def ts_to_date(val):
                try:
                    ts = int(val)
                    if ts > 1_000_000_000:  # Unix timestamp
                        return datetime.datetime.utcfromtimestamp(ts).strftime("%d/%m/%Y %H:%M UTC")
                    return str(val)
                except (ValueError, TypeError):
                    return str(val) if val else "N/A"
 
            expiry_str  = ts_to_date(duration_raw)
            usedon_str  = ts_to_date(usedon_raw) if usedon_raw != "N/A" else "N/A"
            created_str = ts_to_date(created_raw)
 
            # สถานะ: used / not used / banned
            status_lower = str(status).lower()
            if status_lower == "used":
                status_display = "✅ ถูกใช้แล้ว"
                embed_color = discord.Color.green()
            elif status_lower == "banned":
                status_display = "🚫 ถูก Ban"
                embed_color = discord.Color.red()
            else:
                status_display = "⏳ ยังไม่ถูกใช้"
                embed_color = discord.Color.blue()
 
            embed = discord.Embed(title="🔍 ข้อมูล Key", color=embed_color)
            embed.add_field(name="🔑 Key", value=f"`{self.key.value.strip()}`", inline=False)
            embed.add_field(name="📅 หมดอายุ", value=expiry_str, inline=True)
            embed.add_field(name="🔓 สถานะ", value=status_display, inline=True)
            embed.add_field(name="🏷️ Level", value=str(level), inline=True)
            embed.add_field(name="👤 ใช้โดย", value=usedby, inline=True)
            embed.add_field(name="🕐 ใช้เมื่อ", value=usedon_str, inline=True)
            embed.add_field(name="🗓️ สร้างเมื่อ", value=created_str, inline=True)
        else:
            embed = discord.Embed(
                title="❌ ไม่พบ Key",
                description=result.get("message", "ไม่พบ Key นี้ในระบบ"),
                color=discord.Color.red()
            )
        embed.set_footer(text=f"ตรวจสอบโดย {interaction.user}")
        await interaction.followup.send(embed=embed, ephemeral=True)
 
 
# ==================== PERSISTENT VIEW ====================
 
class KeygenPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(
        label="🔑  สร้าง Key",
        style=discord.ButtonStyle.success,
        custom_id="persistent_btn_genkey"
    )
    async def btn_genkey(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_role(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ ไม่มีสิทธิ์",
                    description="คุณไม่มี Role ที่อนุญาตให้ใช้ฟีเจอร์นี้",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return
        await interaction.response.send_modal(GenKeyModal())
 
    @discord.ui.button(
        label="🗑️  ลบ Key",
        style=discord.ButtonStyle.danger,
        custom_id="persistent_btn_deletekey"
    )
    async def btn_deletekey(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_role(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(title="❌ ไม่มีสิทธิ์", color=discord.Color.red()),
                ephemeral=True
            )
            return
        await interaction.response.send_modal(DeleteKeyModal())
 
    @discord.ui.button(
        label="🔍  ตรวจสอบ Key",
        style=discord.ButtonStyle.primary,
        custom_id="persistent_btn_keyinfo"
    )
    async def btn_keyinfo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_role(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(title="❌ ไม่มีสิทธิ์", color=discord.Color.red()),
                ephemeral=True
            )
            return
        await interaction.response.send_modal(KeyInfoModal())
 
 
# ==================== SLASH COMMANDS ====================
 
@tree.command(name="setup_keygen", description="ส่งแผงปุ่ม KeyGen ไปยังห้องที่กำหนด (Admin only)")
@app_commands.describe(channel="ห้องที่ต้องการส่งแผง KeyGen")
@app_commands.checks.has_permissions(administrator=True)
async def setup_keygen(interaction: discord.Interaction, channel: discord.TextChannel):
    embed = discord.Embed(
        title="🔑  KeyAuth Key Manager",
        description=(
            "กดปุ่มด้านล่างเพื่อจัดการ Key\n\n" 
            "🟢 **สร้าง Key** — กรอกจำนวน, ระยะเวลา, รูปแบบ\n"
            "🔴 **ลบ Key** — ลบ Key ออกจากระบบ\n"
            "🔵 **ตรวจสอบ Key** — ดูวันหมดอายุ, ผู้ใช้, สถานะ\n\n"
            "*เฉพาะผู้มีสิทธิ์เท่านั้น | ผลลัพธ์เห็นเฉพาะตัวเอง*"
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"App : {KEYAUTH_APP_NAME}")
 
    await channel.send(embed=embed, view=KeygenPanelView())
    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ ตั้งค่าสำเร็จ",
            description=f"ส่งแผง KeyGen ไปยัง {channel.mention} แล้ว",
            color=discord.Color.green()
        ),
        ephemeral=True
    )
 
 
@setup_keygen.error
async def setup_keygen_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ ต้องการสิทธิ์ Administrator",
                description="คำสั่งนี้ใช้ได้เฉพาะ Admin เท่านั้น",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
 
 
# ==================== EVENTS ====================
 
@bot.event
async def on_ready():
    bot.add_view(KeygenPanelView())
    await tree.sync()
    print(f"✅ Bot พร้อมใช้งาน: {bot.user}")
    print(f"📦 App: {KEYAUTH_APP_NAME}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="🔑 INSIDEX SYSTEM"
        )
    )
 
 
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)