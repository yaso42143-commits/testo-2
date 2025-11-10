import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
import threading

# 🧩 دالة البحث كما في الكود الأصلي
def search_videos(title1):
    url = f'https://freshporno.net/search/{title1}/'
    headers = {"User-Agent": "Mozilla/5.0"}
    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    results = []
    for v in soup.select("div.thumbs-inner"):
        a, img = v.find("a"), v.find("img")
        title = a.get("title") or (a.text.strip() if a else "")
        link = a.get("href") if a else ""
        img_link = ""
        if img:
            for attr in ["data-src", "data-original", "data-lazy", "data-thumb", "src"]:
                img_link = img.get(attr)
                if img_link and not img_link.startswith("data:image"):
                    break
        if img_link:
            img_link = "https:" + img_link if img_link.startswith("//") else (
                "https://freshporno.net" + img_link if img_link.startswith("/") else img_link
            )
        if link and not link.startswith("http"):
            link = "https://freshporno.net" + link

        if title:
            video_info = {"title": title, "link": link, "img": img_link, "downloads": []}

            try:
                vid_soup = BeautifulSoup(requests.get(link, headers=headers).text, "html.parser")
                downloads = vid_soup.select("ul.download-list li a")
                if downloads:
                    for d in downloads:
                        q, dl = d.text.strip(), d.get("href")
                        if dl and not dl.startswith("http"):
                            dl = "https://freshporno.net" + dl
                        video_info["downloads"].append((q, dl))
            except Exception as e:
                video_info["downloads"].append((f"❌ خطأ أثناء التحميل", str(e)))

            results.append(video_info)
    return results

# 🧠 دالة الرد على المستخدم
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text(f"🔍 جاري البحث عن: {query} ...")

    results = search_videos(query)
    if results:
        for vid in results:
            caption = f"🎬 *{vid['title']}*\n\n🔗 [رابط الصفحة]({vid['link']})"
            if vid["downloads"]:
                caption += "\n\n⬇️ *روابط التحميل:*"
                for q, dl in vid["downloads"]:
                    caption += f"\n- [{q}]({dl})"
            else:
                caption += "\n⚠️ لا توجد روابط تحميل."

            if vid["img"]:
                await update.message.reply_photo(photo=vid["img"], caption=caption, parse_mode="Markdown")
            else:
                await update.message.reply_markdown(caption)
    else:
        await update.message.reply_text("❌ لم يتم العثور على نتائج.")

# 🚀 دالة الترحيب لما المستخدم يبدأ محادثة خاصة مع البوت
async def greet_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = update.my_chat_member
    if chat_member.new_chat_member.status == "member" or chat_member.new_chat_member.status == "creator":
        await context.bot.send_message(
            chat_id=chat_member.chat.id,
            text="👋 أهلاً بيك! أرسل اسم الفيديو اللي عايز تبحث عنه 🔍"
        )

# 🚀 إعداد البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً! أرسل اسم الفيديو للبحث.")

# ====== Web server صغير علشان Render يعتبر الخدمة web ويخليها شغالة مجانًا ======
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    # لو Render أو أي بيئة عطت PORT، استخدمه؛ غير كده استخدم 10000
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

# ====== main ======
def main():
    TOKEN = "8011123235:AAHlLzHctq9Frtp2ZBNYSVcHQpTYnZ8S7i4"  # ← استبدل بالتوكن الحقيقي من @BotFather
    # شغّل الويب سيرفر في ثريد منفصل (daemon) علشان ما يمنعش run_polling
    threading.Thread(target=run_web, daemon=True).start()

    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(CommandHandler("start", start))
    from telegram.ext import ChatMemberHandler
    app_bot.add_handler(ChatMemberHandler(greet_new_user, ChatMemberHandler.MY_CHAT_MEMBER))

    print("🤖 البوت يعمل الآن...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
