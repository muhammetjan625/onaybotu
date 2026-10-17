import os
import random
import json
import uuid
import logging
from datetime import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

# =========================
# LOGLAMA AYARLARI
# =========================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# AYARLAR
# =========================
TOKEN = os.getenv("BOT_TOKEN")
SAHIP_ID = 8780868373
DOSYA = "bot_verileri.json"

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN bulunamadı. Lütfen bot token'ını ortam değişkeni olarak tanımlayın."
    )

bot = telebot.TeleBot(TOKEN)

# Geçici durum sözlükleri
red_asamasindakiler = {}
destek_modundakiler = set()

# =========================
# VERİLERİ KAYDET / YÜKLE
# =========================
def verileri_yukle():
    varsayilan = {
        "adminler": {
            str(SAHIP_ID): {
                "rol": "kurucu",
                "kullanici_adi": "Kurucu",
                "eklenme_tarihi": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "ekleyen": "Sistem",
                "onay_sayisi": 0,
                "red_sayisi": 0
            }
        },
        "kanallar": [],
        "bekleyen": {},
        "engellenenler": []
    }
    if not os.path.exists(DOSYA):
        return varsayilan
    try:
        with open(DOSYA, "r", encoding="utf-8") as f:
            veri = json.load(f)
        
        adminler_raw = veri.get("adminler", {str(SAHIP_ID): "kurucu"})
        yeni_adminler = {}
        for uid, val in adminler_raw.items():
            if isinstance(val, str):
                yeni_adminler[uid] = {
                    "rol": val,
                    "kullanici_adi": f"Kullanici_{uid}",
                    "eklenme_tarihi": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "ekleyen": "Bilinmiyor",
                    "onay_sayisi": 0,
                    "red_sayisi": 0
                }
            else:
                val.setdefault("onay_sayisi", 0)
                val.setdefault("red_sayisi", 0)
                yeni_adminler[uid] = val

        yeni_adminler[str(SAHIP_ID)] = {
            "rol": "kurucu",
            "kullanici_adi": "Kurucu",
            "eklenme_tarihi": yeni_adminler.get(str(SAHIP_ID), {}).get("eklenme_tarihi", datetime.now().strftime("%d.%m.%Y %H:%M")),
            "ekleyen": "Sistem",
            "onay_sayisi": yeni_adminler.get(str(SAHIP_ID), {}).get("onay_sayisi", 0),
            "red_sayisi": yeni_adminler.get(str(SAHIP_ID), {}).get("red_sayisi", 0)
        }

        veri["adminler"] = yeni_adminler
        veri.setdefault("kanallar", [])
        veri.setdefault("bekleyen", {})
        veri.setdefault("engellenenler", [])
        return veri
    except (json.JSONDecodeError, OSError):
        return varsayilan


veri = verileri_yukle()
adminler = veri["adminler"]
kanallar = veri["kanallar"]
bekleyen = veri["bekleyen"]
engellenenler = veri["engellenenler"]


def kaydet():
    veri["adminler"] = adminler
    veri["kanallar"] = kanallar
    veri["bekleyen"] = bekleyen
    veri["engellenenler"] = engellenenler
    with open(DOSYA, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)


def yetki_kontrol(user_id):
    info = adminler.get(str(user_id))
    return info["rol"] if info else None


def kurucu_mu(user_id):
    return yetki_kontrol(user_id) == "kurucu"


# =========================
# TELEGRAM MENÜ KOMUTLARI
# =========================
def komutlari_ayarla():
    try:
        komutlar = [
            BotCommand("start", "Botu başlatır"),
            BotCommand("yardim", "Rolünüze özel komut rehberi"),
            BotCommand("destek", "Yöneticiye doğrudan mesaj / soru gönder"),
            BotCommand("panel", "Kurucu kontrol paneli (Kurucu)"),
            BotCommand("adminler", "Yönetici listesi ve liderlik tablosu"),
            BotCommand("kanallar", "Kayıtlı kanalları listele"),
            BotCommand("kanalekle", "Yeni kanal ekle (Kurucu)"),
            BotCommand("kanalsil", "Kanalı kaldır (Kurucu)"),
            BotCommand("adminekle", "Onaycı admin ekle (Kurucu)"),
            BotCommand("admincikar", "Yönetici yetkisini al (Kurucu)"),
            BotCommand("engelle", "Kullanıcıyı engelle (Kurucu)"),
            BotCommand("engelkaldir", "Kullanıcı engelini kaldır (Kurucu)")
        ]
        bot.set_my_commands(komutlar)
        logging.info("Telegram / menü komutları otomatik tanımlandı.")
    except Exception as e:
        logging.error(f"Komutlar ayarlanırken hata: {e}")


# =========================
# TEMEL KOMUTLAR
# =========================
@bot.message_handler(commands=["start"])
def start(message):
    logging.info(f"Kullanıcı /start kullandı: {message.from_user.id}")
    bot.reply_to(
        message,
        "👋 **Merhaba!**\n\nBana metin, fotoğraf, video veya belge gönder.\n"
        "Gönderdiğin içerik yönetici onayından geçtikten sonra kayıtlı kanallarda paylaşılacaktır. 🚀\n\n"
        "💬 Yöneticiye doğrudan soru sormak için `/destek` yazabilirsin.\n"
        "💡 Tüm komutları görmek için `/yardim` yazabilirsin.",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["yardim"])
def yardim(message):
    user_id = message.from_user.id
    rol = yetki_kontrol(user_id)

    metin = (
        "📚 **BOT KULLANIM REHBERİ**\n\n"
        "👤 **Kullanıcı Komutları:**\n"
        "• `/start` - Botu başlatır.\n"
        "• `/destek` - Yöneticilere doğrudan mesaj/destek talebi gönderir.\n"
        "• `/yardim` - Yetkinize uygun rehberi açar.\n\n"
        "📌 *Nasıl İçerik Gönderilir?*\n"
        "Bota direkt medya veya metin atabilirsiniz. Onaylandığında imzalı olarak kanallarda yayınlanır.\n"
    )

    if rol:
        metin += (
            "\n🛡️ **Yönetici Komutları:**\n"
            "• `/kanallar` - Paylaşım yapılan kanalları listeler.\n"
            "• `/adminler` - Yönetici detaylarını ve performans liderlik tablosunu gösterir.\n"
        )

    if rol == "kurucu":
        metin += (
            "\n🔑 **Kurucu Komutları:**\n"
            "• `/panel` - İnteraktif mini kontrol panelini açar.\n"
            "• `/kanalekle @kanaladi` - Yeni kanal kaydeder.\n"
            "• `/kanalsil @kanaladi` - Kanalı sistemden siler.\n"
            "• `/adminekle [ID]` - Yeni onaycı admin ekler.\n"
            "• `/admincikar [ID]` - Yönetici yetkisini alır.\n"
            "• `/engelle [ID]` - Kullanıcının botu kullanmasını engeller.\n"
            "• `/engelkaldir [ID]` - Kullanıcının engelini kaldırır.\n"
        )

    bot.reply_to(message, metin, parse_mode="Markdown")


# =========================
# DESTEK / GERİ BİLDİRİM SİSTEMİ
# =========================
@bot.message_handler(commands=["destek"])
def destek_baslat(message):
    user_id = message.from_user.id
    if user_id in engellenenler:
        bot.reply_to(message, "⛔ Botu kullanma yetkiniz engellenmiş.")
        return
    destek_modundakiler.add(user_id)
    bot.reply_to(
        message,
        "💬 **Destek Hattı Aktif!**\n\nLütfen yöneticiye iletmek istediğiniz mesajı, soru veya önerinizi şimdi yazıp gönderin:",
        parse_mode="Markdown"
    )


# =========================
# KURUCU ÖZEL PANEL
# =========================
@bot.message_handler(commands=["panel"])
def kurucu_paneli(message):
    if not kurucu_mu(message.from_user.id):
        bot.reply_to(message, "⛔ Bu komut sadece kurucuya açıktır.")
        return

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📢 Kanallar", callback_data="panel_kanallar"),
        InlineKeyboardButton("👥 Adminler & Liderlik", callback_data="panel_adminler"),
        InlineKeyboardButton("📊 İstatistikler", callback_data="panel_stats"),
        InlineKeyboardButton("🔄 Yenile", callback_data="panel_yenile")
    )
    
    panel_metni = (
        "🎛️ **KURUCU KONTROL PANELİ**\n\n"
        f"📌 Kayıtlı Kanal: `{len(kanallar)}`\n"
        f"👑 Toplam Yönetici: `{len(adminler)}`\n"
        f"🚫 Engellenen Üye: `{len(engellenenler)}`\n"
        f"⏳ Bekleyen Başvuru: `{len([b for b in bekleyen.values() if b['durum'] == 'bekliyor'])}`"
    )
    bot.reply_to(message, panel_metni, reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith("panel_"))
def panel_butonlari(call):
    if not kurucu_mu(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ Yetkiniz yok!", show_alert=True)
        return

    islem = call.data.split("_")[1]
    if islem == "kanallar":
        if not kanallar:
            bot.answer_callback_query(call.id, "Kayıtlı kanal yok.", show_alert=True)
            return
        liste = "\n".join([f"• {k['ad']} (`@{k.get('username', k['id'])}`)" for k in kanallar])
        bot.send_message(call.message.chat.id, f"📢 **Kayıtlı Kanallar:**\n\n{liste}", parse_mode="Markdown")
    elif islem == "adminler":
        liste = ""
        for uid, info in adminler.items():
            liste += f"• `{uid}` ({info['kullanici_adi']}) - Onay: {info.get('onay_sayisi', 0)} | Red: {info.get('red_sayisi', 0)}\n"
        bot.send_message(call.message.chat.id, f"👥 **Admin Performans Tablosu:**\n\n{liste}", parse_mode="Markdown")
    elif islem == "stats":
        b_sayi = len([b for b in bekleyen.values() if b["durum"] == "bekliyor"])
        o_sayi = len([b for b in bekleyen.values() if b["durum"] == "onaylandi"])
        r_sayi = len([b for b in bekleyen.values() if b["durum"] == "reddedildi"])
        bot.answer_callback_query(call.id, f"Bekleyen: {b_sayi} | Onay: {o_sayi} | Red: {r_sayi}", show_alert=True)
    elif islem == "yenile":
        bot.answer_callback_query(call.id, "✅ Panel güncellendi.")


# =========================
# ADMIN LİSTESİ & LİDERLİK TABLOSU
# =========================
@bot.message_handler(commands=["adminler"])
def adminleri_listele(message):
    if not yetki_kontrol(message.from_user.id):
        bot.reply_to(message, "⛔ Bu komutu sadece yöneticiler kullanabilir.")
        return

    metin = "🏆 **YÖNETİCİLER & PERFORMANS LİDERLİK TABLOSU**\n\n"
    siralilar = sorted(adminler.items(), key=lambda x: x[1].get("onay_sayisi", 0), reverse=True)
    
    for i, (uid, info) in enumerate(siralilar, 1):
        metin += (
            f"{i}. 🔹 **{info['kullanici_adi']}** (`{uid}`)\n"
            f"   👑 Rol: `{info['rol'].upper()}`\n"
            f"   ✅ Onaylanan: **{info.get('onay_sayisi', 0)}** | ❌ Reddedilen: **{info.get('red_sayisi', 0)}**\n"
            f"   📅 Eklenme: {info['eklenme_tarihi']} (Ekleyen: {info['ekleyen']})\n"
            "-----------------------------------\n"
        )
    bot.reply_to(message, metin, parse_mode="Markdown")


# =========================
# BAN / KARA LİSTE SİSTEMİ
# =========================
@bot.message_handler(commands=["engelle"])
def kullanici_engelle(message):
    if not kurucu_mu(message.from_user.id):
        bot.reply_to(message, "⛔ Bu komut sadece kurucuya açıktır.")
        return
    try:
        hedef = int(message.text.split()[1])
        if hedef == SAHIP_ID:
            bot.reply_to(message, "⚠️ Kurucu kendine engel atamaz.")
            return
        if hedef not in engellenenler:
            engellenenler.append(hedef)
            kaydet()
            bot.reply_to(message, f"✅ `{hedef}` ID'li kullanıcı karalisteye alındı.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ Bu kullanıcı zaten engellenmiş.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Kullanım: /engelle 123456789")


@bot.message_handler(commands=["engelkaldir"])
def engel_kaldir(message):
    if not kurucu_mu(message.from_user.id):
        bot.reply_to(message, "⛔ Bu komut sadece kurucuya açıktır.")
        return
    try:
        hedef = int(message.text.split()[1])
        if hedef in engellenenler:
            engellenenler.remove(hedef)
            kaydet()
            bot.reply_to(message, f"✅ `{hedef}` ID'li kullanıcının engeli kaldırıldı.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ Bu kullanıcı engelli listesinde değil.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Kullanım: /engelkaldir 123456789")


# =========================
# KANAL VE ADMİN YÖNETİMİ
# =========================
@bot.message_handler(commands=["kanalekle"])
def kanal_ekle(message):
    if not kurucu_mu(message.from_user.id):
        bot.reply_to(message, "⛔ Bu komut sadece kurucuya açıktır.")
        return
    try:
        hedef = message.text.split(maxsplit=1)[1].strip()
        chat = bot.get_chat(hedef)
        if chat.type != "channel":
            bot.reply_to(message, "❌ Bu adres bir kanal değil.")
            return
        bot_uye = bot.get_chat_member(chat.id, bot.get_me().id)
        if bot_uye.status != "administrator" or not getattr(bot_uye, "can_post_messages", False):
            bot.reply_to(message, "❌ Bot bu kanalda yönetici ve mesaj gönderme yetkisine sahip olmalıdır.")
            return
        kanal_id = str(chat.id)
        if any(k["id"] == kanal_id for k in kanallar):
            bot.reply_to(message, "⚠️ Bu kanal zaten kayıtlı.")
            return
        kanallar.append({"id": kanal_id, "ad": chat.title or kanal_id, "username": getattr(chat, "username", None)})
        kaydet()
        bot.reply_to(message, f"✅ Kanal eklendi: {chat.title}")
    except Exception as e:
        bot.reply_to(message, f"❌ Kanal eklenemedi: {e}")


@bot.message_handler(commands=["kanalsil"])
def kanal_sil(message):
    if not kurucu_mu(message.from_user.id):
        bot.reply_to(message, "⛔ Kurucuya açıktır.")
        return
    try:
        hedef = message.text.split(maxsplit=1)[1].strip()
        if hedef.startswith("@"):
            hedef = str(bot.get_chat(hedef).id)
        eski = len(kanallar)
        kanallar[:] = [k for k in kanallar if k["id"] != hedef]
        if len(kanallar) == eski:
            bot.reply_to(message, "⚠️ Kanal listede yok.")
            return
        kaydet()
        bot.reply_to(message, "✅ Kanal silindi.")
    except Exception as e:
        bot.reply_to(message, f"❌ Hata: {e}")


@bot.message_handler(commands=["kanallar"])
def kanallari_goster(message):
    if not yetki_kontrol(message.from_user.id):
        bot.reply_to(message, "⛔ Yalnızca yöneticiler görebilir.")
        return
    if not kanallar:
        bot.reply_to(message, "Kayıtlı kanal yok.")
        return
    metin = "📢 KAYITLI KANALLAR:\n\n"
    for i, k in enumerate(kanallar, 1):
        metin += f"{i}. {k['ad']} (`@{k.get('username', k['id'])}`)\n"
    bot.reply_to(message, metin, parse_mode="Markdown")


@bot.message_handler(commands=["adminekle"])
def admin_ekle(message):
    if not kurucu_mu(message.from_user.id):
        bot.reply_to(message, "⛔ Yalnızca kurucu.")
        return
    try:
        yeni_id = int(message.text.split()[1])
        yeni_id_str = str(yeni_id)
        if yeni_id_str in adminler:
            bot.reply_to(message, "⚠️ Zaten yönetici.")
            return
        try:
            c = bot.get_chat(yeni_id)
            k_adi = c.first_name or c.username or "Admin"
        except Exception:
            k_adi = "Yeni Admin"

        adminler[yeni_id_str] = {
            "rol": "onayci",
            "kullanici_adi": k_adi,
            "eklenme_tarihi": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "ekleyen": f"{message.from_user.first_name}",
            "onay_sayisi": 0,
            "red_sayisi": 0
        }
        kaydet()
        bot.reply_to(message, f"✅ {yeni_id} onaycı olarak eklendi.")
    except Exception:
        bot.reply_to(message, "Kullanım: /adminekle ID")


@bot.message_handler(commands=["admincikar"])
def admin_cikar(message):
    if not kurucu_mu(message.from_user.id):
        return
    try:
        hedef = str(int(message.text.split()[1]))
        if hedef == str(SAHIP_ID) or hedef not in adminler:
            bot.reply_to(message, "⚠️ İşlem geçersiz.")
            return
        del adminler[hedef]
        kaydet()
        bot.reply_to(message, "✅ Yönetici çıkarıldı.")
    except Exception:
        bot.reply_to(message, "Kullanım: /admincikar ID")


# =========================
# KULLANICI MESAJ / GÖNDERİ ALIMI
# =========================
@bot.message_handler(content_types=["text", "photo", "video", "document", "audio"])
def mesaj_al(message):
    user_id = message.from_user.id
    user_id_str = str(user_id)

    if user_id in engellenenler:
        bot.reply_to(message, "⛔ Botu kullanma yetkiniz engellenmiştir.")
        return

    # Destek modu kontrolü
    if user_id in destek_modundakiler:
        destek_modundakiler.remove(user_id)
        ad = message.from_user.first_name or "Kullanıcı"
        destek_metni = f"💬 **Yeni Destek Talebi!**\n\n👤 Gönderen: {ad} (`{user_id}`)\n📝 Mesaj:\n{message.text}"
        for admin_id in adminler.keys():
            try:
                bot.send_message(int(admin_id), destek_metni, parse_mode="Markdown")
            except Exception:
                pass
        bot.reply_to(message, "✅ Destek mesajınız yöneticilere iletildi. En kısa sürede dönüş yapılacaktır.")
        return

    # Red sebebi yazma kontrolü
    if user_id_str in red_asamasindakiler:
        basvuru_id = red_asamasindakiler.pop(user_id_str)
        sebep = message.text
        basvuru = bekleyen.get(basvuru_id)
        
        if basvuru:
            basvuru["durum"] = "reddedildi"
            adminler[user_id_str]["red_sayisi"] = adminler[user_id_str].get("red_sayisi", 0) + 1
            kaydet()
            try:
                bot.send_message(basvuru["gonderen_id"], f"Üzgünüz, mesajınız onaylanmadı. ❌\n\n**Gerekçe:** {sebep}", parse_mode="Markdown")
            except Exception:
                pass
            bot.reply_to(message, f"❌ Başvuru reddedildi. Gerekçe kullanıcıya iletildi.")
        return

    if message.chat.type != "private" or (message.text and message.text.startswith("/")):
        return
    if not kanallar:
        bot.reply_to(message, "⚠️ Henüz paylaşım kanalı eklenmemiş.")
        return

    basvuru_id = uuid.uuid4().hex[:12]
    ad = message.from_user.first_name or "Kullanıcı"
    if message.from_user.last_name:
        ad += " " + message.from_user.last_name
    
    username_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {user_id}"

    bekleyen[basvuru_id] = {
        "gonderen_id": user_id,
        "kaynak_mesaj_id": message.message_id,
        "durum": "bekliyor",
        "gonderen_ad": ad,
        "gonderen_bilgi": username_info
    }
    kaydet()

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton(f"👤 {ad}", url=f"tg://user?id={user_id}"))
    markup.add(
        InlineKeyboardButton("✅ Onayla", callback_data=f"onay_{basvuru_id}", style="success"),
        InlineKeyboardButton("❌ Reddet", callback_data=f"red_{basvuru_id}", style="danger")
    )

    for admin_id in adminler.keys():
        try:
            bot.copy_message(int(admin_id), message.chat.id, message.message_id, reply_markup=markup)
        except Exception:
            pass

    bot.reply_to(message, "⏳ Mesajınız yönetici onayına gönderildi.")


# =========================
# ONAY / RED & OTOMATİK İMZA SİSTEMİ
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith("onay_") or call.data.startswith("red_"))
def buton_islemi(call):
    admin_id_str = str(call.from_user.id)
    if not yetki_kontrol(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ Yetkiniz yok!", show_alert=True)
        return

    islem, basvuru_id = call.data.split("_", 1)
    basvuru = bekleyen.get(basvuru_id)
    if not basvuru or basvuru["durum"] != "bekliyor":
        bot.answer_callback_query(call.id, "⚠️ Başvuru zaten işlenmiş.", show_alert=True)
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except Exception:
            pass
        return

    if islem == "red":
        red_asamasindakiler[admin_id_str] = basvuru_id
        bot.answer_callback_query(call.id, "Lütfen red sebebini mesaj olarak yazın.")
        bot.send_message(call.message.chat.id, "❌ **Red Sebebi Girin:**\nBu mesajı neden reddettiğinizi buraya yazın:", parse_mode="Markdown")
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except Exception:
            pass
        return

    # ONAY İŞLEMİ & OTOMATİK İMZA
    basvuru["durum"] = "isleniyor"
    adminler[admin_id_str]["onay_sayisi"] = adminler[admin_id_str].get("onay_sayisi", 0) + 1
    kaydet()

    gonderen_id = basvuru["gonderen_id"]
    kaynak_mesaj_id = basvuru["kaynak_mesaj_id"]
    gonderen_ad = basvuru["gonderen_ad"]
    gonderen_bilgi = basvuru["gonderen_bilgi"]

    try:
        stiller_havuzu = [
            ("danger", "success", "primary"),
            ("primary", "danger", "success"),
            ("success", "primary", "danger")
        ]
        secilen_stil = random.choice(stiller_havuzu)

        kanal_markup = InlineKeyboardMarkup(row_width=3)
        kanal_markup.add(
            InlineKeyboardButton("🔗 Link 1", url="https://pin.it/4SJ6PXhhT", style=secilen_stil[0]),
            InlineKeyboardButton("📌 Link 2", url="https://t.me/spotify_muzikleri", style=secilen_stil[1]),
            InlineKeyboardButton("🌐 Link 3", url="https://t.me/spotify_muzikleri", style=secilen_stil[2])
        )

        basarili = []
        for kanal in list(kanallar):
            try:
                # Önce içeriği kopyala
                bot.copy_message(
                    chat_id=kanal["id"],
                    from_chat_id=gonderen_id,
                    message_id=kaynak_mesaj_id,
                    reply_markup=kanal_markup
                )
                
                # Ardından otomatik imza/etiket mesajı gönder
                imza_metni = f"✍️ *Gönderen:* [{gonderen_ad}](tg://user?id={gonderen_id})"
                bot.send_message(kanal["id"], imza_metni, parse_mode="Markdown")
                
                basarili.append(kanal["ad"])
            except Exception as e:
                logging.error(f"Kanal gönderim hatası ({kanal['id']}): {e}")

        if not basarili:
            basvuru["durum"] = "bekliyor"
            kaydet()
            bot.answer_callback_query(call.id, "Gönderim başarısız oldu.", show_alert=True)
            return

        basvuru["durum"] = "onaylandi"
        kaydet()

        try:
            bot.send_message(gonderen_id, "🎉 Mesajınız onaylandı ve kanallarda imzalı olarak paylaşıldı!")
        except Exception:
            pass

        bot.send_message(call.message.chat.id, f"✅ Gönderim tamamlandı. Başarılı kanallar:\n" + "\n".join(basarili))
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except Exception:
            pass
        bot.answer_callback_query(call.id, "İşlem başarılı!")
    except Exception as e:
        logging.error(f"Onay hatası: {e}")
        basvuru["durum"] = "bekliyor"
        kaydet()
        bot.answer_callback_query(call.id, "Bir hata oluştu.", show_alert=True)


# Komutları yükle ve botu çalıştır
komutlari_ayarla()
logging.info("🚀 Kapsamlı Telegram Kanal Yönetim Botu çalışıyor!")
bot.infinity_polling(skip_pending=False)