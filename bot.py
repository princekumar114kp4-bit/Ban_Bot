#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║   🚫 BOT BAN PRO - TELEGRAM BOT                         ║
║   Ban leaked bot tokens permanently with style          ║
║   Language: English | Features: Referral, Coins, Admin  ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import random
import string
import sqlite3
import requests
from datetime import datetime
from io import BytesIO
from telebot import TeleBot, types

# >>> hyv-injected:backup (added by the implementer bot: owner/admin Export and Import of data files)
import hashlib as _hyv_bk_hash
import inspect as _hyv_bk_inspect
import json as _hyv_bk_json
import os as _hyv_bk_os
import re as _hyv_bk_re
import shutil as _hyv_bk_shutil
import sqlite3 as _hyv_bk_sqlite
import tempfile as _hyv_bk_tmp
import time as _hyv_bk_time
import zipfile as _hyv_bk_zip
from telebot import types as _hyv_bk_types

_HYV_BK_HERE = _hyv_bk_os.path.dirname(_hyv_bk_os.path.abspath(__file__))
_HYV_BK_SELF = _hyv_bk_os.path.basename(__file__)
_HYV_BK_MAX = 50 * 1024 * 1024
_HYV_BK_EXT = (".db", ".sqlite", ".sqlite3", ".json", ".csv", ".txt", ".pkl", ".pickle", ".dat", ".yaml", ".yml", ".xml")
_HYV_BK_DB_EXT = (".db", ".sqlite", ".sqlite3")
_HYV_BK_SKIP_DIRS = {"__pycache__", "venv", ".venv", "env", ".git", "node_modules"}
_HYV_BK_SECRET = _hyv_bk_re.compile(r"(\.env|token|secret|passw|credential|api_?key|private)", _hyv_bk_re.I)
_HYV_BK_CODE_PATH = _hyv_bk_re.compile(r"""["']([^"'\s]+\.(?:db|sqlite3?|json|csv|txt|pkl|pickle|dat|ya?ml|xml))["']""")
_HYV_BK_BTN_EXPORT = "📤 Export"
_HYV_BK_BTN_IMPORT = "📥 Import"
_HYV_BK_BTN_BACK = "🔙 Back"
_HYV_BK_BTN_DB = "🗄 Database Export/Import"   # the button the admin taps to open the backup menu
_HYV_BK_DB_LABELS = (_HYV_BK_BTN_DB, _HYV_BK_BTN_EXPORT, _HYV_BK_BTN_IMPORT)
_HYV_BK_BTN_STYLE = "primary"   # colour of the Database button (blue), same as the bot's option buttons
_hyv_bk_pending = {}   # admin user id -> "import" or staged restore info


_HYV_BK_ADMINS = {8597878282}   # Telegram id of the member who sent the bot file (set when added)


def _hyv_bk_is_admin(uid):
    ids = set(str(x) for x in _HYV_BK_ADMINS)
    for raw in _hyv_bk_os.environ.get("HYV_ADMIN_IDS", "").split(","):
        if raw.strip():
            ids.add(raw.strip())
    return str(uid) in ids


def _hyv_bk_excluded(rel):
    parts = rel.replace("\\", "/").split("/")
    if any(p in _HYV_BK_SKIP_DIRS or p.startswith("hyv_safety") for p in parts[:-1]):
        return True
    name = parts[-1]
    return (name == _HYV_BK_SELF or name.endswith((".zip", ".pyc")) or bool(_HYV_BK_SECRET.search(name)))


def _hyv_bk_sha(path):
    h = _hyv_bk_hash.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _hyv_bk_collect():
    picked = {}
    for root, dirs, files in _hyv_bk_os.walk(_HYV_BK_HERE):
        dirs[:] = [d for d in dirs if d not in _HYV_BK_SKIP_DIRS and not d.startswith("hyv_safety")]
        for f in files:
            full = _hyv_bk_os.path.join(root, f)
            rel = _hyv_bk_os.path.relpath(full, _HYV_BK_HERE).replace(_hyv_bk_os.sep, "/")
            if not _hyv_bk_excluded(rel) and f.lower().endswith(_HYV_BK_EXT):
                picked[rel] = full
    try:
        with open(__file__, "r", encoding="utf-8", errors="ignore") as fh:
            code = fh.read()
    except OSError:
        code = ""
    for m in _HYV_BK_CODE_PATH.finditer(code):
        p = m.group(1)
        if _hyv_bk_os.path.isabs(p):
            continue
        for base in (_HYV_BK_HERE, _hyv_bk_os.getcwd()):
            full = _hyv_bk_os.path.normpath(_hyv_bk_os.path.join(base, p))
            rel = _hyv_bk_os.path.relpath(full, _HYV_BK_HERE).replace(_hyv_bk_os.sep, "/")
            if (_hyv_bk_os.path.isfile(full) and not rel.startswith("..") and not _hyv_bk_excluded(rel)):
                picked[rel] = full
    return picked


def _hyv_bk_make_zip(picked, out_path):
    tmp = _hyv_bk_tmp.mkdtemp(prefix="hyvbk_")
    try:
        entries = []
        for i, (rel, full) in enumerate(sorted(picked.items())):
            src = full
            if rel.lower().endswith(_HYV_BK_DB_EXT):
                src = _hyv_bk_os.path.join(tmp, "snap%d" % i)
                s = _hyv_bk_sqlite.connect(full)
                try:
                    d = _hyv_bk_sqlite.connect(src)
                    try:
                        s.backup(d)   # reads -wal/-shm too, so the copy is consistent
                    finally:
                        d.close()
                finally:
                    s.close()
            entries.append((rel, src))
        manifest = {"app": "hyv-backup", "version": 1,
                    "created": _hyv_bk_time.strftime("%Y-%m-%d %H:%M:%S"), "files": []}
        with _hyv_bk_zip.ZipFile(out_path, "w", _hyv_bk_zip.ZIP_DEFLATED) as z:
            for rel, src in entries:
                manifest["files"].append({"path": rel, "size": _hyv_bk_os.path.getsize(src),
                                          "sha256": _hyv_bk_sha(src)})
                z.write(src, rel)
            z.writestr("manifest.json", _hyv_bk_json.dumps(manifest, indent=2, ensure_ascii=False))
        return manifest
    finally:
        _hyv_bk_shutil.rmtree(tmp, ignore_errors=True)


def _hyv_bk_stage(zip_path):
    """Check the backup fully and unpack it into a temp folder. Nothing in the bot folder is touched."""
    stage = _hyv_bk_tmp.mkdtemp(prefix="hyvbk_in_")
    try:
        if _hyv_bk_os.path.getsize(zip_path) > _HYV_BK_MAX:
            raise ValueError("file 50 MB se badi hai")
        with _hyv_bk_zip.ZipFile(zip_path) as z:
            if z.testzip() is not None:
                raise ValueError("zip file kharab hai")
            manifest = _hyv_bk_json.loads(z.read("manifest.json").decode("utf-8"))
            if manifest.get("app") != "hyv-backup" or not isinstance(manifest.get("files"), list):
                raise ValueError("ye hyv backup file nahi hai")
            names = set(z.namelist())
            total = 0
            staged = []
            for item in manifest["files"]:
                rel = item.get("path")
                if (not isinstance(rel, str) or not rel or rel.startswith(("/", "\\")) or ":" in rel
                        or "\\" in rel or ".." in rel.split("/") or _hyv_bk_excluded(rel)):
                    raise ValueError("unsafe path in backup")
                if rel not in names:
                    raise ValueError("file missing in backup: " + rel)
                info = z.getinfo(rel)
                total += info.file_size
                if info.file_size != item.get("size") or total > _HYV_BK_MAX:
                    raise ValueError("size check failed")
                target = _hyv_bk_os.path.normpath(_hyv_bk_os.path.join(stage, rel))
                if not target.startswith(stage + _hyv_bk_os.sep):
                    raise ValueError("unsafe path in backup")
                _hyv_bk_os.makedirs(_hyv_bk_os.path.dirname(target), exist_ok=True)
                with z.open(rel) as src, open(target, "wb") as dst:
                    _hyv_bk_shutil.copyfileobj(src, dst)
                if _hyv_bk_sha(target) != item.get("sha256"):
                    raise ValueError("checksum mismatch: " + rel)
                staged.append((rel, target))
        return {"stage": stage, "files": staged, "created": manifest.get("created", "?")}
    except Exception:
        _hyv_bk_shutil.rmtree(stage, ignore_errors=True)
        raise


def _hyv_bk_restore(info):
    stamp = _hyv_bk_time.strftime("%Y%m%d_%H%M%S")
    safety = _hyv_bk_os.path.join(_HYV_BK_HERE, "hyv_safety", "before_import_" + stamp)
    for rel, _ in info["files"]:
        cur = _hyv_bk_os.path.join(_HYV_BK_HERE, rel)
        for path in (cur, cur + "-wal", cur + "-shm"):
            if _hyv_bk_os.path.isfile(path):
                dst = _hyv_bk_os.path.join(safety, _hyv_bk_os.path.relpath(path, _HYV_BK_HERE))
                _hyv_bk_os.makedirs(_hyv_bk_os.path.dirname(dst), exist_ok=True)
                _hyv_bk_shutil.copy2(path, dst)
    for rel, tmp_path in info["files"]:
        dst = _hyv_bk_os.path.join(_HYV_BK_HERE, rel)
        _hyv_bk_os.makedirs(_hyv_bk_os.path.dirname(dst), exist_ok=True)
        if rel.lower().endswith(_HYV_BK_DB_EXT):
            for side in ("-wal", "-shm"):
                if _hyv_bk_os.path.isfile(dst + side):
                    _hyv_bk_os.remove(dst + side)   # old sidecar must not replay over the restored db
        _hyv_bk_shutil.copy2(tmp_path, dst)
    return safety


def _hyv_bk_bar(done, total=5):
    return "▰" * done + "▱" * (total - done)


def _hyv_bk_admin_chat(chat_id):
    """True when the chat is the private chat of an admin (in a private chat chat_id is the user id)."""
    return chat_id is not None and not isinstance(chat_id, bool) and _hyv_bk_is_admin(chat_id)


def _hyv_bk_btn(label):
    """The Database button as the dict telebot keeps in a keyboard row, with its colour (style). A telebot version
    whose KeyboardButton does not take style gets the style added to the dict, so it still reaches Telegram."""
    try:
        return _hyv_bk_types.KeyboardButton(label, style=_HYV_BK_BTN_STYLE).to_dict()
    except TypeError:
        btn = _hyv_bk_types.KeyboardButton(label).to_dict()
        btn["style"] = _HYV_BK_BTN_STYLE
        return btn


def _hyv_bk_tb_markup(markup):
    """The same reply keyboard with the Database button in one extra last row. The original object is not changed."""
    if not isinstance(markup, _hyv_bk_types.ReplyKeyboardMarkup):
        return markup
    rows = [list(row) for row in (markup.keyboard or [])]
    texts = [b.get("text") if isinstance(b, dict) else getattr(b, "text", b) for row in rows for b in row]
    if any(t in _HYV_BK_DB_LABELS for t in texts):
        return markup
    rows.append([_hyv_bk_btn(_HYV_BK_BTN_DB)])
    return _hyv_bk_types.ReplyKeyboardMarkup(
        resize_keyboard=markup.resize_keyboard, one_time_keyboard=markup.one_time_keyboard,
        selective=markup.selective, row_width=markup.row_width,
        input_field_placeholder=markup.input_field_placeholder, is_persistent=markup.is_persistent, keyboard=rows)


def _hyv_bk_tb_wrap(fn, sig):
    def send(*args, **kwargs):
        try:
            bound = sig.bind_partial(*args, **kwargs)
        except TypeError:
            return fn(*args, **kwargs)
        if _hyv_bk_admin_chat(bound.arguments.get("chat_id")) and bound.arguments.get("reply_markup") is not None:
            bound.arguments["reply_markup"] = _hyv_bk_tb_markup(bound.arguments["reply_markup"])
        return fn(*bound.args, **bound.kwargs)
    send.__name__ = fn.__name__
    return send


def _hyv_bk_patch_telebot(bot):
    """pyTelegramBotAPI: the send_* methods of this bot object that take a reply keyboard add the Database row
    when the chat is an admin's private chat."""
    for name in dir(type(bot)):
        fn = getattr(bot, name, None) if name.startswith("send_") else None
        if fn is None or not callable(fn):
            continue
        sig = _hyv_bk_inspect.signature(fn)
        if "reply_markup" in sig.parameters:
            setattr(bot, name, _hyv_bk_tb_wrap(fn, sig))


def _hyv_bk_register(bot):
    _hyv_bk_patch_telebot(bot)
    def admin_private(m):
        return m.chat.type == "private" and _hyv_bk_is_admin(m.from_user.id)

    def menu(chat_id, text):
        kb = _hyv_bk_types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add(_hyv_bk_types.KeyboardButton(_HYV_BK_BTN_EXPORT), _hyv_bk_types.KeyboardButton(_HYV_BK_BTN_IMPORT))
        kb.add(_hyv_bk_types.KeyboardButton(_HYV_BK_BTN_BACK))
        bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")

    def show_menu(m):
        _hyv_bk_pending.pop(m.from_user.id, None)
        menu(m.chat.id, "🗄 <b>Database Export / Import</b>\n━━━━━━━━━━━━━━\n"
                        "📤 <b>Export</b> — sab data ek zip file mein\n"
                        "📥 <b>Import</b> — zip file se data wapas laao\n\n"
                        "ℹ️ Import ke baad bot ko restart karna hoga.")

    def export(m):
        if not _hyv_bk_is_admin(m.from_user.id):
            return
        pm = bot.send_message(m.chat.id, "📦 <b>Export shuru</b>\n" + _hyv_bk_bar(0), parse_mode="HTML")
        try:
            for step in range(1, 5):
                bot.edit_message_text("📦 <b>Export ho raha hai</b>\n" + _hyv_bk_bar(step), m.chat.id,
                                      pm.message_id, parse_mode="HTML")
            picked = _hyv_bk_collect()
            if not picked:
                bot.edit_message_text("⚠️ Export ke liye koi data file nahi mili.", m.chat.id, pm.message_id)
                return
            tmp = _hyv_bk_tmp.mkdtemp(prefix="hyvbk_out_")
            try:
                out = _hyv_bk_os.path.join(tmp, "hyv_backup_%s.zip" % _hyv_bk_time.strftime("%Y%m%d_%H%M%S"))
                manifest = _hyv_bk_make_zip(picked, out)
                if _hyv_bk_os.path.getsize(out) > _HYV_BK_MAX:
                    bot.edit_message_text("⚠️ Backup 50 MB se badi hai, Telegram par nahi bhej sakte.",
                                          m.chat.id, pm.message_id)
                    return
                bot.edit_message_text("📦 <b>Export</b>\n" + _hyv_bk_bar(5) + "\n✅ Ho gaya", m.chat.id,
                                      pm.message_id, parse_mode="HTML")
                with open(out, "rb") as fh:
                    bot.send_document(m.chat.id, fh, caption="🗄 <b>Backup ready</b>\n📄 Files: %d\n"
                                      "🕒 %s" % (len(manifest["files"]), manifest["created"]),
                                      parse_mode="HTML", visible_file_name=_hyv_bk_os.path.basename(out))
            finally:
                _hyv_bk_shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            bot.edit_message_text("⚠️ <b>Export nahi ho paya.</b> Thodi der baad dobara try karo.",
                                  m.chat.id, pm.message_id, parse_mode="HTML")

    def start_import(m):
        if not _hyv_bk_is_admin(m.from_user.id):
            return
        _hyv_bk_pending[m.from_user.id] = "import"
        menu(m.chat.id, "📥 <b>Import</b>\n━━━━━━━━━━━━━━\nAb hyv backup wali .zip file bhejo.\n"
                        "Cancel karne ke liye 🔙 Back dabao.")

    def on_document(m):
        state = _hyv_bk_pending.get(m.from_user.id)
        if state != "import":
            return
        if (m.document.file_size or 0) > _HYV_BK_MAX:
            bot.send_message(m.chat.id, "⚠️ File 50 MB se badi hai.")
            return
        tmp = _hyv_bk_tmp.mkdtemp(prefix="hyvbk_dl_")
        try:
            file_info = bot.get_file(m.document.file_id)
            data = bot.download_file(file_info.file_path)
            zip_path = _hyv_bk_os.path.join(tmp, "upload.zip")
            with open(zip_path, "wb") as fh:
                fh.write(data)
            info = _hyv_bk_stage(zip_path)
        except Exception:
            _hyv_bk_shutil.rmtree(tmp, ignore_errors=True)
            bot.send_message(m.chat.id, "❌ <b>Ye file import ke liye sahi nahi hai (bot 20 MB tak ki file leta hai).</b>\n"
                                        "Hyv backup wali .zip bhejo.", parse_mode="HTML")
            return
        _hyv_bk_shutil.rmtree(tmp, ignore_errors=True)
        _hyv_bk_pending[m.from_user.id] = info
        kb = _hyv_bk_types.InlineKeyboardMarkup()
        kb.row(_hyv_bk_types.InlineKeyboardButton("✅ Haan, restore karo", callback_data="hyvbk:yes"),
               _hyv_bk_types.InlineKeyboardButton("❌ Cancel", callback_data="hyvbk:no"))
        bot.send_message(m.chat.id, "🔎 <b>Backup check ho gaya</b>\n━━━━━━━━━━━━━━\n"
                                    "📄 Files: %d\n🕒 Backup time: %s\n\n"
                                    "⚠️ Current data pehle safety copy mein save hoga.\n"
                                    "Restore karein?" % (len(info["files"]), info["created"]),
                         parse_mode="HTML", reply_markup=kb)

    def on_confirm(c):
        if not _hyv_bk_is_admin(c.from_user.id):
            return
        info = _hyv_bk_pending.get(c.from_user.id)
        chat = c.message.chat.id
        if c.data == "hyvbk:no" or not isinstance(info, dict):
            _hyv_bk_pending.pop(c.from_user.id, None)
            if isinstance(info, dict):
                _hyv_bk_shutil.rmtree(info["stage"], ignore_errors=True)
            bot.answer_callback_query(c.id, "Cancel ho gaya")
            bot.edit_message_text("❌ Import cancel ho gaya.", chat, c.message.message_id)
            return
        bot.answer_callback_query(c.id, "Restore shuru")
        pm = bot.send_message(chat, "♻️ <b>Restore shuru</b>\n" + _hyv_bk_bar(0), parse_mode="HTML")
        try:
            for step in range(1, 5):
                bot.edit_message_text("♻️ <b>Restore ho raha hai</b>\n" + _hyv_bk_bar(step), chat,
                                      pm.message_id, parse_mode="HTML")
            safety = _hyv_bk_restore(info)
            bot.edit_message_text("✅ <b>Restore ho gaya</b>\n" + _hyv_bk_bar(5) + "\n\n"
                                  "🛟 Purana data safety copy mein hai: <code>%s</code>\n\n"
                                  "🔁 <b>Ab bot ko restart karo</b>, tab naya data chalega." %
                                  _hyv_bk_os.path.relpath(safety, _HYV_BK_HERE), chat, pm.message_id,
                                  parse_mode="HTML")
        except Exception:
            bot.edit_message_text("⚠️ <b>Restore nahi ho paya.</b> Kuch files nahi badli.", chat,
                                  pm.message_id, parse_mode="HTML")
        finally:
            _hyv_bk_pending.pop(c.from_user.id, None)
            _hyv_bk_shutil.rmtree(info["stage"], ignore_errors=True)

    def back(m):
        _hyv_bk_pending.pop(m.from_user.id, None)
        bot.send_message(m.chat.id, "🔙 Wapas aa gaye.", reply_markup=_hyv_bk_types.ReplyKeyboardRemove())

    before_m = len(bot.message_handlers)
    before_c = len(bot.callback_query_handlers)
    bot.message_handler(func=lambda m: admin_private(m) and m.text in ("/backup", "/hyvbackup", _HYV_BK_BTN_DB))(show_menu)
    bot.message_handler(func=lambda m: admin_private(m) and m.text == _HYV_BK_BTN_EXPORT)(export)
    bot.message_handler(func=lambda m: admin_private(m) and m.text == _HYV_BK_BTN_IMPORT)(start_import)
    bot.message_handler(func=lambda m: admin_private(m) and m.text == _HYV_BK_BTN_BACK)(back)
    bot.message_handler(content_types=["document"], func=lambda m: (
        m.chat.type == "private" and _hyv_bk_pending.get(m.from_user.id) == "import"))(on_document)
    bot.callback_query_handler(func=lambda c: (c.data or "").startswith("hyvbk:") and
                               _hyv_bk_is_admin(c.from_user.id))(on_confirm)
    # run before the bot's own handlers, but only for the exact buttons above (other messages pass through)
    new_m = bot.message_handlers[before_m:]
    del bot.message_handlers[before_m:]
    bot.message_handlers[0:0] = new_m
    new_c = bot.callback_query_handlers[before_c:]
    del bot.callback_query_handlers[before_c:]
    bot.callback_query_handlers[0:0] = new_c
# <<< hyv-injected:backup


# >>> hyv-injected:web (added by the implementer bot: starts one background web server)
try:
    import threading as _hyv_threading
    import os as _hyv_os
    from http.server import BaseHTTPRequestHandler as _hyv_Base, ThreadingHTTPServer as _hyv_Server

    class _hyv_WebHandler(_hyv_Base):
        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path in ("/", "/health"):
                code, body = 200, b"ok"
            else:
                code, body = 404, b"not found"
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass

    def _hyv_serve_web():
        try:
            _hyv_port = int(_hyv_os.environ.get("PORT", "10000"))
            _hyv_Server(("0.0.0.0", _hyv_port), _hyv_WebHandler).serve_forever()
        except Exception:
            print("web server could not start", flush=True)

    _hyv_threading.Thread(target=_hyv_serve_web, daemon=True).start()
except Exception:
    print("web server could not start", flush=True)
# <<< hyv-injected:web
# >>> hyv-injected:pinger (added by the implementer bot: pings RENDER_EXTERNAL_URL in a background thread)
try:
    import threading as _hyv_threading2
    import os as _hyv_os2
    import time as _hyv_time
    import urllib.request as _hyv_urlreq

    def _hyv_ping_minutes():
        try:
            _hyv_m = int(_hyv_os2.environ.get("PING_MINUTES", "5").strip())
        except ValueError:
            return 5
        return _hyv_m if 1 <= _hyv_m <= 60 else 5

    def _hyv_ping_loop():
        _hyv_time.sleep(30)
        while True:
            try:
                _hyv_url = _hyv_os2.environ.get("RENDER_EXTERNAL_URL", "").strip()
                if _hyv_url.lower().startswith(("http://", "https://")):
                    try:
                        with _hyv_urlreq.urlopen(_hyv_url, timeout=30) as _hyv_resp:
                            _hyv_code = str(_hyv_resp.status)
                    except _hyv_urlreq.HTTPError as _hyv_err:
                        _hyv_code = str(_hyv_err.code)
                    except Exception:
                        _hyv_code = "down"
                    print("keep-alive ping:", _hyv_code, flush=True)
            except Exception:
                pass
            _hyv_time.sleep(_hyv_ping_minutes() * 60)

    _hyv_threading2.Thread(target=_hyv_ping_loop, daemon=True).start()
except Exception:
    print("pinger could not start", flush=True)
# <<< hyv-injected:pinger


# ============================================================
# ⚙️ CONFIGURATION - EDIT THESE VALUES
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")       # Get from @BotFather
ADMIN_ID = 8597878282                    # Your Telegram ID (get from @userinfobot)
BOT_USERNAME = "Ban Bot"        # Without @, e.g., "BotBanProBot"
BANNED_BOT_IMAGE_URL = "https://i.ibb.co/wF29FM3W/3340.png"  # DP for banned bots

# ============================================================
# 📁 DATABASE SETUP
# ============================================================
DB_PATH = "botbanpro.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        coins INTEGER DEFAULT 0,
        referred_by INTEGER DEFAULT 0,
        referral_count INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        join_date TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS redeem_codes (
        code TEXT PRIMARY KEY,
        coins INTEGER DEFAULT 0,
        used INTEGER DEFAULT 0,
        used_by INTEGER DEFAULT 0,
        created_by INTEGER DEFAULT 0,
        created_date TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS ban_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bot_username TEXT,
        bot_token_preview TEXT,
        status TEXT,
        date TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("refer_coins", "5"))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("ban_cost", "5"))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("required_referrals", "1"))
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================
# 🤖 BOT INITIALIZATION
# ============================================================
bot = TeleBot(BOT_TOKEN)
_hyv_bk_register(bot)  # hyv-injected:backup-register
init_db()

# Download banned bot image once at startup
BANNED_BOT_IMAGE = None
try:
    resp = requests.get(BANNED_BOT_IMAGE_URL, timeout=15)
    if resp.status_code == 200:
        BANNED_BOT_IMAGE = BytesIO(resp.content)
        BANNED_BOT_IMAGE.name = "banned.jpg"
        print("✅ Banned bot profile image loaded successfully")
except Exception as e:
    print(f"⚠️  Could not load banned bot image: {e}")

# ============================================================
# ⌨️ KEYBOARD MARKUPS
# ============================================================
def main_keyboard(is_admin=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_ban = types.KeyboardButton("🚫 Ban Bot")
    btn_profile = types.KeyboardButton("👤 My Profile")
    btn_refer = types.KeyboardButton("🔗 Refer & Earn")
    btn_redeem = types.KeyboardButton("🎁 Redeem Code")
    btn_help = types.KeyboardButton("🆘 Help")
    btn_owner = types.KeyboardButton("👑 Owner")
    
    markup.add(btn_ban, btn_profile)
    markup.add(btn_refer, btn_redeem)
    markup.add(btn_help, btn_owner)
    
    if is_admin:
        markup.add(types.KeyboardButton("⚙️ Admin Panel"))
    
    return markup

def admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("📢 Broadcast"), types.KeyboardButton("💰 Add Coins"))
    markup.add(types.KeyboardButton("💸 Remove Coins"), types.KeyboardButton("🚫 Ban User"))
    markup.add(types.KeyboardButton("✅ Unban User"), types.KeyboardButton("🎟️ Create Redeem"))
    markup.add(types.KeyboardButton("🗑️ Delete Redeem"), types.KeyboardButton("📊 Stats"))
    markup.add(types.KeyboardButton("📜 Ban Logs"), types.KeyboardButton("👥 All Users"))
    markup.add(types.KeyboardButton("⚙️ Settings"), types.KeyboardButton("🔙 Back to Menu"))
    return markup

def back_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Back to Menu"))
    return markup

# ============================================================
# 🛠️ HELPER FUNCTIONS
# ============================================================
def is_admin_user(user_id):
    if user_id == ADMIN_ID:
        return True
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row and row['is_admin'] == 1

def is_user_banned(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row and row['is_banned'] == 1

def get_user(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def add_user(user_id, username, first_name, referred_by=0):
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""INSERT OR IGNORE INTO users 
        (user_id, username, first_name, coins, referred_by, referral_count, is_banned, is_admin, join_date)
        VALUES (?, ?, ?, 0, ?, 0, 0, 0, ?)""",
        (user_id, username, first_name, referred_by, now))
    conn.commit()
    conn.close()

def update_coins(user_id, amount):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_setting(key):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row['value'] if row else "0"

def set_setting(key, value):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def can_access_bot(user_id):
    """User needs at least N referrals to access ban feature"""
    user = get_user(user_id)
    if not user:
        return False
    required = int(get_setting("required_referrals"))
    if user_id == ADMIN_ID or is_admin_user(user_id):
        return True
    return user['referral_count'] >= required

# ============================================================
# 🔐 TELEGRAM BOT API - BANNING FUNCTIONS
# ============================================================
def call_bot_api(token, method, data=None, files=None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        if files:
            r = requests.post(url, files=files, timeout=20)
        elif data:
            r = requests.post(url, json=data, timeout=15)
        else:
            r = requests.get(url, timeout=15)
        return r.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}

def set_banned_profile_photo(token):
    """Set the banned bot's profile picture using the custom image"""
    global BANNED_BOT_IMAGE
    if BANNED_BOT_IMAGE is None:
        # Try loading again
        try:
            resp = requests.get(BANNED_BOT_IMAGE_URL, timeout=15)
            if resp.status_code == 200:
                BANNED_BOT_IMAGE = BytesIO(resp.content)
                BANNED_BOT_IMAGE.name = "banned.jpg"
            else:
                return {"ok": False, "description": "Image download failed"}
        except Exception as e:
            return {"ok": False, "description": str(e)}
    
    try:
        BANNED_BOT_IMAGE.seek(0)
        files = {"photo": ("banned.jpg", BANNED_BOT_IMAGE, "image/jpeg")}
        data = {"photo": '{"type":"static","photo":"attach://photo"}'}
        url = f"https://api.telegram.org/bot{token}/setMyProfilePhoto"
        r = requests.post(url, data=data, files=files, timeout=20)
        return r.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}

def ban_bot_token(token):
    """Full bot banning pipeline - makes the token permanently unusable"""
    results = []
    
    # Step 1: Validate token and get bot info
    me = call_bot_api(token, "getMe")
    if not me.get("ok"):
        return {
            "success": False, 
            "error": me.get("description", "Invalid token or bot already dead"),
            "steps": results
        }
    
    bot_username = me['result'].get('username', 'Unknown')
    bot_id = me['result'].get('id', 'Unknown')
    results.append(f"✅ Bot found: @{bot_username} (ID: {bot_id})")
    
    # Step 2: Change bot name to indicate it's dead
    try:
        r = call_bot_api(token, "setMyName", {"name": "⚠️ BANNED BOT ⚠️"})
        results.append(f"📛 Name changed: {'✅ Success' if r.get('ok') else '⚠️ Skipped'}")
    except:
        results.append("📛 Name change: ⚠️ Skipped")
    
    # Step 3: Set custom banned profile picture
    try:
        r = set_banned_profile_photo(token)
        results.append(f"🖼️ Profile picture set: {'✅ Success' if r.get('ok') else '⚠️ Skipped'}")
    except:
        results.append("🖼️ Profile picture: ⚠️ Skipped")
    
    # Step 4: Clear all bot commands
    try:
        r = call_bot_api(token, "setMyCommands", {"commands": []})
        results.append(f"📋 Commands cleared: {'✅ Success' if r.get('ok') else '⚠️ Skipped'}")
    except:
        results.append("📋 Commands: ⚠️ Skipped")
    
    # Step 5: Set warning description
    try:
        r = call_bot_api(token, "setMyDescription", {
            "description": "⚠️ THIS BOT HAS BEEN COMPROMISED AND PERMANENTLY DISABLED ⚠️ | Token invalidated via BOT BAN PRO"
        })
        results.append(f"📝 Description updated: {'✅ Success' if r.get('ok') else '⚠️ Skipped'}")
    except:
        results.append("📝 Description: ⚠️ Skipped")
    
    # Step 6: Set warning about text
    try:
        r = call_bot_api(token, "setMyShortDescription", {
            "short_description": "⚠️ BANNED & DISABLED BOT ⚠️"
        })
        results.append(f"📄 Short description: {'✅ Success' if r.get('ok') else '⚠️ Skipped'}")
    except:
        results.append("📄 Short description: ⚠️ Skipped")
    
    # Step 7: Delete webhook if any
    try:
        r = call_bot_api(token, "deleteWebhook", {"drop_pending_updates": True})
        results.append(f"🔗 Webhook deleted: {'✅ Success' if r.get('ok') else '⚠️ Skipped'}")
    except:
        results.append("🔗 Webhook: ⚠️ Skipped")
    
    # Step 8: Logout - THIS MAKES THE TOKEN PERMANENTLY INVALID
    try:
        r = call_bot_api(token, "logOut")
        if r.get("ok"):
            results.append("🚪 Logged out: ✅ TOKEN INVALIDATED")
            results.append("\n🔒 BOT PERMANENTLY BANNED - TOKEN CANNOT BE USED AGAIN!")
        else:
            results.append(f"🚪 Logout: ⚠️ {r.get('description', 'May have failed')}")
    except Exception as e:
        results.append(f"🚪 Logout: ⚠️ {str(e)}")
    
    return {
        "success": True,
        "bot_username": bot_username,
        "bot_id": bot_id,
        "steps": results
    }

# ============================================================
# 🎬 ANIMATION SEQUENCES
# ============================================================
BAN_ANIMATIONS = [
    "🔌 **Connecting to Telegram API...**",
    "🔍 **Scanning bot token...**",
    "📡 **Establishing secure connection...**",
    "⚡ **Authenticating credentials...**",
    "🔧 **Accessing bot configuration...**",
    "🖥️ **Loading bot profile data...**",
    "📛 **Changing bot identity...**",
    "🖼️ **Applying banned profile picture...**",
    "📋 **Clearing all bot commands...**",
    "📝 **Updating bot description...**",
    "🔗 **Removing webhook connections...**",
    "🚪 **Logging out bot session...**",
    "🔒 **Invalidating bot token...**",
    "✅ **BOT PERMANENTLY BANNED!**"
]

# ============================================================
# 📱 /START COMMAND
# ============================================================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or "None"
    first_name = message.from_user.first_name or "User"
    
    if is_user_banned(user_id):
        bot.reply_to(message, "❌ You are banned from this bot!")
        return
    
    # Handle referral parameter
    referred_by = 0
    if len(message.text.split()) > 1:
        try:
            ref_id = int(message.text.split()[1])
            if ref_id != user_id:
                referred_by = ref_id
        except:
            pass
    
    # Register user
    add_user(user_id, username, first_name, referred_by)
    
    # Process referral bonus
    if referred_by > 0:
        referrer = get_user(referred_by)
        if referrer and not is_user_banned(referred_by):
            bonus = int(get_setting("refer_coins"))
            update_coins(referred_by, bonus)
            
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?", (referred_by,))
            conn.commit()
            conn.close()
            
            try:
                bot.send_message(referred_by,
                    f"🎉 **New Referral!**\n\n"
                    f"👤 {first_name} joined using your link\n"
                    f"💰 +{bonus} coins added to your balance!",
                    parse_mode="Markdown")
            except:
                pass
    
    is_admin = is_admin_user(user_id)
    can_access = can_access_bot(user_id)
    
    welcome_text = f"""
👋 **Welcome {first_name}!**

🚫 Welcome to **BOT BAN PRO**

Permanently disable your leaked bot tokens with professional style.

📋 **Use the buttons below the keyboard:**
• 🚫 Ban Bot — Permanently disable a bot token
• 👤 My Profile — View your account details
• 🔗 Refer & Earn — Invite friends & earn coins
• 🎁 Redeem Code — Get coins from redeem codes
• 🆘 Help — How to use this bot
• 👑 Owner — Contact the owner

💡 **Note:** You need at least 1 referral to use the Ban Bot feature!
"""
    
    if not can_access and not is_admin:
        required = int(get_setting("required_referrals"))
        welcome_text += (
            f"\n\n⚠️ **ACCESS LOCKED!**\n"
            f"Refer at least {required} friend(s) to unlock the Ban Bot feature."
        )
    
    bot.reply_to(message, welcome_text,
                 reply_markup=main_keyboard(is_admin),
                 parse_mode="Markdown")

# ============================================================
# 💬 MAIN TEXT HANDLER
# ============================================================
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    text = message.text
    
    if is_user_banned(user_id):
        bot.reply_to(message, "❌ You are banned from this bot!")
        return
    
    user = get_user(user_id)
    if not user:
        bot.reply_to(message, "Please start the bot with /start first.")
        return
    
    is_admin = is_admin_user(user_id)
    
    # ============ MAIN MENU ============
    if text == "🚫 Ban Bot":
        handle_ban_bot(message)
    
    elif text == "👤 My Profile":
        show_profile(message)
    
    elif text == "🔗 Refer & Earn":
        show_referral(message)
    
    elif text == "🎁 Redeem Code":
        ask_redeem_code(message)
    
    elif text == "🆘 Help":
        show_help(message)
    
    elif text == "👑 Owner":
        show_owner(message)
    
    elif text == "🔙 Back to Menu":
        bot.reply_to(message, "🏠 Returned to main menu!",
                     reply_markup=main_keyboard(is_admin))
    
    # ============ ADMIN PANEL ============
    elif text == "⚙️ Admin Panel" and is_admin:
        bot.reply_to(message, "⚙️ **Admin Panel**\n\nChoose an option below:",
                     reply_markup=admin_keyboard(), parse_mode="Markdown")
    
    elif text == "📢 Broadcast" and is_admin:
        msg = bot.reply_to(message, "📢 Send the message to broadcast:",
                          reply_markup=back_keyboard())
        bot.register_next_step_handler(msg, broadcast_message)
    
    elif text == "💰 Add Coins" and is_admin:
        msg = bot.reply_to(message, "💰 Format: `user_id coins`\n\nExample: `123456789 50`",
                          reply_markup=back_keyboard(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, admin_add_coins)
    
    elif text == "💸 Remove Coins" and is_admin:
        msg = bot.reply_to(message, "💸 Format: `user_id coins`\n\nExample: `123456789 20`",
                          reply_markup=back_keyboard(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, admin_remove_coins)
    
    elif text == "🚫 Ban User" and is_admin:
        msg = bot.reply_to(message, "🚫 Send the user ID to ban:",
                          reply_markup=back_keyboard())
        bot.register_next_step_handler(msg, admin_ban_user)
    
    elif text == "✅ Unban User" and is_admin:
        msg = bot.reply_to(message, "✅ Send the user ID to unban:",
                          reply_markup=back_keyboard())
        bot.register_next_step_handler(msg, admin_unban_user)
    
    elif text == "🎟️ Create Redeem" and is_admin:
        msg = bot.reply_to(message, "🎟️ Send coin amount for the new code:\n\nExample: `100`",
                          reply_markup=back_keyboard(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, admin_create_redeem)
    
    elif text == "🗑️ Delete Redeem" and is_admin:
        msg = bot.reply_to(message, "🗑️ Send the redeem code to delete:",
                          reply_markup=back_keyboard())
        bot.register_next_step_handler(msg, admin_delete_redeem)
    
    elif text == "📊 Stats" and is_admin:
        show_admin_stats(message)
    
    elif text == "📜 Ban Logs" and is_admin:
        show_ban_logs(message)
    
    elif text == "👥 All Users" and is_admin:
        show_all_users(message)
    
    elif text == "⚙️ Settings" and is_admin:
        show_admin_settings(message)

# ============================================================
# 🚫 BAN BOT FEATURE
# ============================================================
def handle_ban_bot(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    is_admin = is_admin_user(user_id)
    
    if not can_access_bot(user_id) and not is_admin:
        required = int(get_setting("required_referrals"))
        bot.reply_to(message,
            f"⚠️ **ACCESS LOCKED!**\n\n"
            f"You need at least **{required} referral(s)** to use the Ban Bot feature.\n\n"
            f"🔗 Go to **Refer & Earn** to get your referral link.",
            parse_mode="Markdown")
        return
    
    ban_cost = int(get_setting("ban_cost"))
    
    if not is_admin and user['coins'] < ban_cost:
        bot.reply_to(message,
            f"❌ **Not Enough Coins!**\n\n"
            f"💰 Your balance: **{user['coins']} coins**\n"
            f"💸 Cost per ban: **{ban_cost} coins**\n\n"
            f"🔗 Earn coins by referring friends!",
            parse_mode="Markdown")
        return
    
    msg = bot.reply_to(message,
        f"🚫 **Bot Ban System**\n\n"
        f"💸 Cost per ban: **{ban_cost} coins**\n"
        f"💰 Your balance: **{user['coins']} coins**\n\n"
        f"📤 Send the bot token to ban:",
        reply_markup=back_keyboard(),
        parse_mode="Markdown")
    
    bot.register_next_step_handler(msg, process_ban_token)

def process_ban_token(message):
    if message.text == "🔙 Back to Menu":
        is_admin = is_admin_user(message.from_user.id)
        bot.reply_to(message, "🏠 Returned to main menu!",
                     reply_markup=main_keyboard(is_admin))
        return
    
    user_id = message.from_user.id
    user = get_user(user_id)
    is_admin = is_admin_user(user_id)
    token = message.text.strip()
    
    ban_cost = int(get_setting("ban_cost"))
    
    if not is_admin and user['coins'] < ban_cost:
        bot.reply_to(message, "❌ Not enough coins!",
                     reply_markup=main_keyboard(is_admin))
        return
    
    # Basic token validation
    if ':' not in token or len(token) < 20:
        bot.reply_to(message, "❌ Invalid bot token format! Please send a valid token.",
                     reply_markup=main_keyboard(is_admin))
        return
    
    # Send first animation frame
    msg = bot.send_message(message.chat.id, BAN_ANIMATIONS[0], parse_mode="Markdown")
    
    # Play animation
    for anim in BAN_ANIMATIONS[1:]:
        time.sleep(0.6)
        try:
            bot.edit_message_text(chat_id=message.chat.id,
                                message_id=msg.message_id,
                                text=anim,
                                parse_mode="Markdown")
        except:
            pass
    
    # Execute actual ban
    result = ban_bot_token(token)
    
    # Deduct coins for non-admin
    if not is_admin and result.get("success"):
        update_coins(user_id, -ban_cost)
    
    # Log to database
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bot_uname = result.get('bot_username', 'Failed') if result.get('success') else 'Failed'
    token_preview = token[:15] + "..." if len(token) > 15 else token
    status = "Success" if result.get('success') else "Failed"
    c.execute("""INSERT INTO ban_logs (user_id, bot_username, bot_token_preview, status, date)
                 VALUES (?, ?, ?, ?, ?)""",
              (user_id, bot_uname, token_preview, status, now))
    conn.commit()
    conn.close()
    
    # Build result message
    if result.get("success"):
        steps_text = "\n".join(result['steps'])
        final_text = f"""
✅ **BOT PERMANENTLY BANNED!**

🤖 Bot: @{result['bot_username']}
🆔 Bot ID: `{result['bot_id']}`
👤 Banned by: {message.from_user.first_name}
💰 Cost: {0 if is_admin else ban_cost} coins

📋 **Process Steps:**
{steps_text}

🔒 **This bot token is now PERMANENTLY invalid and cannot be reused!**
"""
    else:
        final_text = f"""
❌ **Failed to Ban Bot!**

📝 Reason: {result.get('error', 'Unknown error')}

💡 Tips:
• Double-check the token is correct
• The bot may already be dead/disabled
• Make sure there are no spaces in the token
"""
    
    try:
        bot.edit_message_text(chat_id=message.chat.id,
                            message_id=msg.message_id,
                            text=final_text,
                            parse_mode="Markdown",
                            reply_markup=main_keyboard(is_admin))
    except:
        bot.send_message(message.chat.id, final_text,
                        parse_mode="Markdown",
                        reply_markup=main_keyboard(is_admin))

# ============================================================
# 👤 PROFILE & REFERRAL
# ============================================================
def show_profile(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    is_admin = is_admin_user(user_id)
    can_access = can_access_bot(user_id)
    
    text = f"""
👤 **My Profile**

🆔 ID: `{user_id}`
👤 Name: {user['first_name']}
📱 Username: @{user['username']}
💰 Coins: **{user['coins']}**
🔗 Referrals: **{user['referral_count']}**
📅 Join Date: {user['join_date']}

⚡ Status: {'✅ Access Granted' if can_access or is_admin else '⚠️ Access Locked (Refer friends)'}
👑 Role: {'Admin' if is_admin else 'User'}
"""
    
    bot.reply_to(message, text, parse_mode="Markdown",
                 reply_markup=main_keyboard(is_admin))

def show_referral(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    is_admin = is_admin_user(user_id)
    refer_coins = get_setting("refer_coins")
    
    refer_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    
    text = f"""
🔗 **Refer & Earn**

💰 Bonus per referral: **+{refer_coins} coins**
🔗 Your referral count: **{user['referral_count']}**

📎 **Your referral link:**
`{refer_link}`

📋 **How to earn:**
1. Share your link with friends
2. Friends join via your link
3. You instantly get {refer_coins} coins
4. {refer_coins} coins = 1 free bot ban!

💡 **Tip:** More referrals = more coins = unlimited bans!
"""
    
    bot.reply_to(message, text, parse_mode="Markdown",
                 reply_markup=main_keyboard(is_admin))

# ============================================================
# 🎁 REDEEM CODE SYSTEM
# ============================================================
def ask_redeem_code(message):
    is_admin = is_admin_user(message.from_user.id)
    msg = bot.reply_to(message, "🎁 Enter your redeem code:",
                      reply_markup=back_keyboard())
    bot.register_next_step_handler(msg, process_redeem_code)

def process_redeem_code(message):
    if message.text == "🔙 Back to Menu":
        is_admin = is_admin_user(message.from_user.id)
        bot.reply_to(message, "🏠 Returned to main menu!",
                     reply_markup=main_keyboard(is_admin))
        return
    
    user_id = message.from_user.id
    is_admin = is_admin_user(user_id)
    code = message.text.strip().upper()
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM redeem_codes WHERE code = ?", (code,))
    row = c.fetchone()
    
    if not row:
        bot.reply_to(message, "❌ Invalid redeem code! Please check and try again.",
                     reply_markup=main_keyboard(is_admin))
        conn.close()
        return
    
    if row['used'] == 1:
        bot.reply_to(message, "❌ This code has already been used!",
                     reply_markup=main_keyboard(is_admin))
        conn.close()
        return
    
    coins = row['coins']
    c.execute("UPDATE redeem_codes SET used = 1, used_by = ? WHERE code = ?",
              (user_id, code))
    conn.commit()
    conn.close()
    
    update_coins(user_id, coins)
    
    bot.reply_to(message,
        f"🎉 **Code Redeemed Successfully!**\n\n"
        f"💰 +**{coins} coins** have been added to your account!\n\n"
        f"You can now ban bot tokens!",
        parse_mode="Markdown",
        reply_markup=main_keyboard(is_admin))

# ============================================================
# 🆘 HELP & OWNER
# ============================================================
def show_help(message):
    is_admin = is_admin_user(message.from_user.id)
    text = f"""
🆘 **Help Guide**

📋 **How to use:**

1️⃣ **🔗 Refer & Earn**
   • Share your link with friends
   • Earn +{get_setting('refer_coins')} coins per referral

2️⃣ **🚫 Ban Bot**
   • Send the bot token
   • Costs {get_setting('ban_cost')} coins per ban
   • Professional animation + permanent ban

3️⃣ **👤 My Profile**
   • View your details, coins & referrals

4️⃣ **🎁 Redeem Code**
   • Get a code from the owner
   • Redeem it for free coins

💡 **Important:** You need at least 1 referral to unlock the Ban Bot feature!

🔒 **What happens when a bot is banned:**
   • Bot name changed to "⚠️ BANNED BOT ⚠️"
   • Profile picture replaced with banned image
   • All commands cleared
   • Warning description set
   • Token permanently invalidated via logout
"""
    bot.reply_to(message, text, parse_mode="Markdown",
                 reply_markup=main_keyboard(is_admin))

def show_owner(message):
    is_admin = is_admin_user(message.from_user.id)
    text = f"""
👑 **Owner Contact**

📱 Contact the owner for any help or issues:

• 🆔 Admin ID: `{ADMIN_ID}`
• 💬 Message for any questions or problems

⏰ Response time: Within 24 hours
"""
    bot.reply_to(message, text, parse_mode="Markdown",
                 reply_markup=main_keyboard(is_admin))

# ============================================================
# ⚙️ ADMIN FUNCTIONS
# ============================================================
def broadcast_message(message):
    if message.text == "🔙 Back to Menu":
        bot.reply_to(message, "⚙️ Admin Panel:", reply_markup=admin_keyboard())
        return
    
    broadcast_text = message.text
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned = 0")
    users = c.fetchall()
    conn.close()
    
    success = 0
    failed = 0
    
    for u in users:
        try:
            bot.send_message(u['user_id'],
                f"📢 **BROADCAST MESSAGE**\n\n{broadcast_text}",
                parse_mode="Markdown")
            success += 1
        except:
            failed += 1
    
    bot.reply_to(message,
        f"📢 **Broadcast Complete!**\n\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total: {success + failed}",
        parse_mode="Markdown",
        reply_markup=admin_keyboard())

def admin_add_coins(message):
    if message.text == "🔙 Back to Menu":
        bot.reply_to(message, "⚙️ Admin Panel:", reply_markup=admin_keyboard())
        return
    
    try:
        parts = message.text.split()
        user_id = int(parts[0])
        coins = int(parts[1])
        
        update_coins(user_id, coins)
        user = get_user(user_id)
        
        bot.reply_to(message,
            f"💰 **Coins Added!**\n\n"
            f"👤 User: @{user['username'] if user else 'Unknown'}\n"
            f"🆔 ID: `{user_id}`\n"
            f"💵 Added: +{coins} coins\n"
            f"💰 New balance: {user['coins'] if user else 'N/A'} coins",
            parse_mode="Markdown",
            reply_markup=admin_keyboard())
    except:
        bot.reply_to(message, "❌ Wrong format! Try again.",
                     reply_markup=admin_keyboard())

def admin_remove_coins(message):
    if message.text == "🔙 Back to Menu":
        bot.reply_to(message, "⚙️ Admin Panel:", reply_markup=admin_keyboard())
        return
    
    try:
        parts = message.text.split()
        user_id = int(parts[0])
        coins = int(parts[1])
        
        update_coins(user_id, -coins)
        user = get_user(user_id)
        
        bot.reply_to(message,
            f"💸 **Coins Removed!**\n\n"
            f"👤 User: @{user['username'] if user else 'Unknown'}\n"
            f"🆔 ID: `{user_id}`\n"
            f"💵 Removed: -{coins} coins\n"
            f"💰 New balance: {user['coins'] if user else 'N/A'} coins",
            parse_mode="Markdown",
            reply_markup=admin_keyboard())
    except:
        bot.reply_to(message, "❌ Wrong format! Try again.",
                     reply_markup=admin_keyboard())

def admin_ban_user(message):
    if message.text == "🔙 Back to Menu":
        bot.reply_to(message, "⚙️ Admin Panel:", reply_markup=admin_keyboard())
        return
    
    try:
        user_id = int(message.text.strip())
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        bot.reply_to(message,
            f"🚫 **User Banned!**\n\n🆔 ID: `{user_id}`",
            parse_mode="Markdown",
            reply_markup=admin_keyboard())
    except:
        bot.reply_to(message, "❌ Invalid ID! Try again.",
                     reply_markup=admin_keyboard())

def admin_unban_user(message):
    if message.text == "🔙 Back to Menu":
        bot.reply_to(message, "⚙️ Admin Panel:", reply_markup=admin_keyboard())
        return
    
    try:
        user_id = int(message.text.strip())
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        bot.reply_to(message,
            f"✅ **User Unbanned!**\n\n🆔 ID: `{user_id}`",
            parse_mode="Markdown",
            reply_markup=admin_keyboard())
    except:
        bot.reply_to(message, "❌ Invalid ID! Try again.",
                     reply_markup=admin_keyboard())

def admin_create_redeem(message):
    if message.text == "🔙 Back to Menu":
        bot.reply_to(message, "⚙️ Admin Panel:", reply_markup=admin_keyboard())
        return
    
    try:
        coins = int(message.text.strip())
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        conn = get_db()
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""INSERT INTO redeem_codes (code, coins, used, used_by, created_by, created_date)
                     VALUES (?, ?, 0, 0, ?, ?)""",
                  (code, coins, message.from_user.id, now))
        conn.commit()
        conn.close()
        
        bot.reply_to(message,
            f"🎟️ **Redeem Code Created!**\n\n"
            f"🔑 Code: `{code}`\n"
            f"💰 Value: **{coins} coins**\n\n"
            f"Users can redeem this code for {coins} coins.",
            parse_mode="Markdown",
            reply_markup=admin_keyboard())
    except:
        bot.reply_to(message, "❌ Wrong format! Send only a number.",
                     reply_markup=admin_keyboard())

def admin_delete_redeem(message):
    if message.text == "🔙 Back to Menu":
        bot.reply_to(message, "⚙️ Admin Panel:", reply_markup=admin_keyboard())
        return
    
    code = message.text.strip().upper()
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM redeem_codes WHERE code = ?", (code,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    
    if deleted > 0:
        bot.reply_to(message, f"🗑️ Code `{code}` deleted!",
                     parse_mode="Markdown", reply_markup=admin_keyboard())
    else:
        bot.reply_to(message, "❌ Code not found!",
                     reply_markup=admin_keyboard())

def show_admin_stats(message):
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) as cnt FROM users")
    total_users = c.fetchone()['cnt']
    
    c.execute("SELECT COUNT(*) as cnt FROM users WHERE is_banned = 1")
    banned_users = c.fetchone()['cnt']
    
    c.execute("SELECT COUNT(*) as cnt FROM users WHERE is_admin = 1")
    admin_users = c.fetchone()['cnt']
    
    c.execute("SELECT COALESCE(SUM(coins), 0) as total FROM users")
    total_coins = c.fetchone()['total']
    
    c.execute("SELECT COUNT(*) as cnt FROM ban_logs")
    total_bans = c.fetchone()['cnt']
    
    c.execute("SELECT COUNT(*) as cnt FROM ban_logs WHERE status = 'Success'")
    successful_bans = c.fetchone()['cnt']
    
    c.execute("SELECT COUNT(*) as cnt FROM redeem_codes")
    total_codes = c.fetchone()['cnt']
    
    c.execute("SELECT COUNT(*) as cnt FROM redeem_codes WHERE used = 1")
    used_codes = c.fetchone()['cnt']
    
    conn.close()
    
    text = f"""
📊 **Admin Statistics**

👥 **Users:**
• Total users: {total_users}
• Active users: {total_users - banned_users}
• Banned users: {banned_users}
• Admins: {admin_users}

💰 **Economy:**
• Total coins in circulation: {total_coins}
• Total bot bans: {total_bans}
• Successful bans: {successful_bans}

🎟️ **Redeem Codes:**
• Total codes: {total_codes}
• Used codes: {used_codes}
• Available: {total_codes - used_codes}

⚙️ **Current Settings:**
• Referral bonus: {get_setting('refer_coins')} coins
• Ban cost: {get_setting('ban_cost')} coins
• Required referrals: {get_setting('required_referrals')}
"""
    
    bot.reply_to(message, text, parse_mode="Markdown",
                 reply_markup=admin_keyboard())

def show_ban_logs(message):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM ban_logs ORDER BY id DESC LIMIT 20")
    logs = c.fetchall()
    conn.close()
    
    if not logs:
        bot.reply_to(message, "📜 No ban logs yet.",
                     reply_markup=admin_keyboard())
        return
    
    text = "📜 **Recent Ban Logs (Last 20)**\n\n"
    for log in logs:
        status_icon = "✅" if log['status'] == "Success" else "❌"
        text += f"{status_icon} @{log['bot_username']} | 👤 {log['user_id']} | 📅 {log['date'][:10]}\n"
    
    bot.reply_to(message, text, parse_mode="Markdown",
                 reply_markup=admin_keyboard())

def show_all_users(message):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY coins DESC LIMIT 30")
    users = c.fetchall()
    conn.close()
    
    text = "👥 **Top 30 Users (by coins)**\n\n"
    for i, u in enumerate(users, 1):
        status = "🚫" if u['is_banned'] else "👑" if u['is_admin'] else "✅"
        text += f"{i}. {status} @{u['username']} | 💰{u['coins']} | 🔗{u['referral_count']}\n"
    
    bot.reply_to(message, text, reply_markup=admin_keyboard())

def show_admin_settings(message):
    text = f"""
⚙️ **Settings**

Current values:
• 🔗 Referral bonus: `{get_setting('refer_coins')}` coins
• 🚫 Ban cost: `{get_setting('ban_cost')}` coins
• 📋 Required referrals: `{get_setting('required_referrals')}`

To change, send:
`set refer_coins 10`
`set ban_cost 10`
`set required_referrals 2`
"""
    msg = bot.reply_to(message, text, parse_mode="Markdown",
                      reply_markup=back_keyboard())
    bot.register_next_step_handler(msg, process_admin_settings)

def process_admin_settings(message):
    if message.text == "🔙 Back to Menu":
        bot.reply_to(message, "⚙️ Admin Panel:", reply_markup=admin_keyboard())
        return
    
    try:
        parts = message.text.lower().split()
        if parts[0] == 'set' and len(parts) == 3:
            key = parts[1]
            value = parts[2]
            if key in ['refer_coins', 'ban_cost', 'required_referrals']:
                set_setting(key, value)
                bot.reply_to(message, f"✅ Setting updated: `{key}` = `{value}`",
                             parse_mode="Markdown", reply_markup=admin_keyboard())
                return
        bot.reply_to(message, "❌ Wrong format! Use: `set key value`",
                     parse_mode="Markdown", reply_markup=admin_keyboard())
    except:
        bot.reply_to(message, "❌ Error processing command!",
                     reply_markup=admin_keyboard())

# ============================================================
# 🔗 FORCE JOIN SYSTEM + CREDIT DEDUCTION FIX  (ADDED - NO ORIGINAL CODE CHANGED)
# ============================================================
FJ_BTN_ADD = "➕ Add ForceJoin"
FJ_BTN_REMOVE = "➖ Remove ForceJoin"
_fj_admin_state = {}  # admin_user_id -> 'await_add' / 'await_remove'

def _md_escape(s):
    """Escape Markdown special chars in dynamic text (prevents 'can't parse entities' error)."""
    bs = chr(92)  # backslash character
    s = str(s)
    for ch in ("_", "*", "`", "["):
        s = s.replace(ch, bs + ch)
    return s

def fj_init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS force_join_channels (
        chat_id TEXT PRIMARY KEY,
        title TEXT,
        invite_link TEXT,
        added_date TEXT
    )''')
    conn.commit()
    conn.close()

fj_init_db()

def fj_get_channels():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM force_join_channels ORDER BY added_date ASC")
    rows = c.fetchall()
    conn.close()
    return rows

def fj_add_channel(chat_id, title, invite_link):
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""INSERT OR REPLACE INTO force_join_channels (chat_id, title, invite_link, added_date)
                 VALUES (?, ?, ?, ?)""", (str(chat_id), title, invite_link, now))
    conn.commit()
    conn.close()

def fj_remove_channel(chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM force_join_channels WHERE chat_id = ?", (str(chat_id),))
    conn.commit()
    conn.close()

def fj_check_user(user_id):
    """Returns list of channels the user has NOT joined yet. Empty list = all joined."""
    not_joined = []
    for ch in fj_get_channels():
        try:
            cid = int(ch['chat_id'])
        except Exception:
            cid = ch['chat_id']
        try:
            member = bot.get_chat_member(cid, user_id)
            if member.status in ('left', 'kicked'):
                not_joined.append(ch)
        except Exception:
            # Bot is not admin in this channel / cannot check -> skip requirement
            pass
    return not_joined

# Wrap the original admin keyboard so Force Join buttons appear (original function untouched)
_original_admin_keyboard = admin_keyboard
def admin_keyboard():
    markup = _original_admin_keyboard()
    markup.add(types.KeyboardButton(FJ_BTN_ADD), types.KeyboardButton(FJ_BTN_REMOVE))
    return markup

def _fj_handle_admin(message, user_id, text):
    """Handle admin Force Join buttons + next-step states. Returns True if handled."""
    state = _fj_admin_state.get(user_id)

    if text == FJ_BTN_ADD:
        _fj_admin_state[user_id] = 'await_add'
        bot.reply_to(message,
            "➕ **Add Force-Join Channel**\n\n"
            "Send the channel **username** (e.g. @MyChannel) OR the channel **chat ID**.\n\n"
            "⚠️ IMPORTANT: This bot must be an ADMIN in that channel (needed to check membership).",
            parse_mode="Markdown", reply_markup=back_keyboard())
        return True

    if text == FJ_BTN_REMOVE:
        channels = fj_get_channels()
        if not channels:
            bot.reply_to(message, "📭 No force-join channels are set yet.", reply_markup=admin_keyboard())
            return True
        listing = "\n".join(f"{i+1}. {_md_escape(ch['title'])} (`{ch['chat_id']}`)" for i, ch in enumerate(channels))
        _fj_admin_state[user_id] = 'await_remove'
        bot.reply_to(message,
            f"➖ **Remove Force-Join Channel**\n\n{listing}\n\nReply with the **number** you want to remove.",
            parse_mode="Markdown", reply_markup=back_keyboard())
        return True

    if text == "🔙 Back to Menu" and state:
        _fj_admin_state.pop(user_id, None)
        bot.reply_to(message, "⚙️ Admin Panel:", reply_markup=admin_keyboard())
        return True

    if state == 'await_add':
        _fj_admin_state.pop(user_id, None)
        raw = text.strip()
        chat_ref = int(raw) if raw.lstrip('-').isdigit() else raw
        try:
            chat = bot.get_chat(chat_ref)
            chat_id = chat.id
            title = getattr(chat, 'title', None) or raw
            invite_link = None
            if getattr(chat, 'username', None):
                invite_link = f"https://t.me/{chat.username}"
            else:
                try:
                    invite_link = bot.export_chat_invite_link(chat_id)
                except Exception:
                    invite_link = None
            if not invite_link:
                bot.reply_to(message,
                    "❌ Could not get an invite link for this channel.\n\n"
                    "Make this bot an ADMIN (with invite-link permission) in that channel, "
                    "or give the channel a public username, then try again.",
                    parse_mode="Markdown", reply_markup=admin_keyboard())
                return True
            fj_add_channel(chat_id, title, invite_link)
            bot.reply_to(message,
                f"✅ **Force-Join Channel Added!**\n\n📢 {_md_escape(title)}\n🔗 {_md_escape(invite_link)}\n\n"
                "Now every user MUST join this channel before they can use the bot.",
                parse_mode="Markdown", reply_markup=admin_keyboard())
        except Exception as e:
            bot.reply_to(message,
                f"❌ Failed to add channel: `{e}`\n\n"
                "Check the username/ID and make sure this bot is an admin of that channel.",
                parse_mode="Markdown", reply_markup=admin_keyboard())
        return True

    if state == 'await_remove':
        _fj_admin_state.pop(user_id, None)
        channels = fj_get_channels()
        try:
            idx = int(text.strip()) - 1
            ch = channels[idx]
            fj_remove_channel(ch['chat_id'])
            bot.reply_to(message, f"✅ Removed force-join channel: **{_md_escape(ch['title'])}**",
                         parse_mode="Markdown", reply_markup=admin_keyboard())
        except Exception:
            bot.reply_to(message, "❌ Invalid number. Nothing removed.", reply_markup=admin_keyboard())
        return True

    return False

# "I Joined" verification button
@bot.callback_query_handler(func=lambda call: call.data == "fj_check")
def _fj_check_callback(call):
    user_id = call.from_user.id
    not_joined = fj_check_user(user_id)
    if not not_joined:
        bot.answer_callback_query(call.id, "✅ Verified! You can now use the bot.")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        is_admin = is_admin_user(user_id)
        bot.send_message(call.message.chat.id,
            "✅ **Verification successful!**\n\nYou can now use all bot features. Tap /start or use the menu buttons.",
            parse_mode="Markdown", reply_markup=main_keyboard(is_admin))
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined all channels yet!", show_alert=True)

def _credit_referral_if_new(message, user_id, text):
    """If a brand-new user arrives via referral link, credit the referrer once.
    Called even when /start is blocked by force-join, so referral always works."""
    try:
        parts = text.split()
        if len(parts) < 2:
            return
        ref_id = int(parts[1])
        if ref_id == user_id:
            return
        if get_user(user_id):
            return  # already registered -> never credit twice
        uname = getattr(message.from_user, 'username', None) or "None"
        fname = getattr(message.from_user, 'first_name', None) or "User"
        add_user(user_id, uname, fname, ref_id)
        referrer = get_user(ref_id)
        if not referrer or is_user_banned(ref_id):
            return
        bonus = int(get_setting("refer_coins"))
        update_coins(ref_id, bonus)
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?", (ref_id,))
        conn.commit()
        conn.close()
        try:
            bot.send_message(ref_id,
                "🎉 **New Referral!**\n\n"
                + f"👤 {fname} joined using your link\n"
                + f"💰 +{bonus} coins added to your balance!",
                parse_mode="Markdown")
        except Exception:
            pass
    except Exception:
        pass

# Intercept every incoming message BEFORE original handlers (via monkey-patch)
_original_process_new_messages = bot.process_new_messages

def _interceptor_process_new_messages(messages):
    allowed = []
    for message in messages:
        if not hasattr(message, 'from_user') or message.from_user is None:
            allowed.append(message)
            continue
        user_id = message.from_user.id
        text = getattr(message, 'text', None) or ""
        is_admin = is_admin_user(user_id) or user_id == ADMIN_ID

        # Admin Force Join flow (add/remove buttons + their reply steps)
        if is_admin and text and _fj_handle_admin(message, user_id, text):
            continue  # fully handled here, do not pass to original handler

        # Force join gate for normal users (skipped automatically when no channel is configured)
        if not is_admin:
            try:
                not_joined = fj_check_user(user_id)
            except Exception:
                not_joined = []
            if not_joined:
                # Credit referral even when /start is blocked, so referral always works
                if text.startswith("/start"):
                    _credit_referral_if_new(message, user_id, text)
                try:
                    lines = []
                    markup = types.InlineKeyboardMarkup()
                    for i, ch in enumerate(not_joined, 1):
                        lines.append(f"{i}. {_md_escape(ch['title'])}")
                        markup.add(types.InlineKeyboardButton(f"📢 Join {ch['title']}", url=ch['invite_link']))
                    markup.add(types.InlineKeyboardButton("✅ I Joined — Check Again", callback_data="fj_check"))
                    bot.send_message(message.chat.id,
                        "🔒 **Access Locked!**\n\n"
                        "You must join ALL of the following channels to use this bot:\n" +
                        "\n".join(lines) +
                        "\n\nAfter joining, tap the button below to verify.",
                        parse_mode="Markdown", reply_markup=markup)
                except Exception as e:
                    print("Force join prompt error:", e)
                continue  # block this message from original handlers

        allowed.append(message)

    _original_process_new_messages(allowed)

bot.process_new_messages = _interceptor_process_new_messages

# ============================================================
# 💰 CREDIT DEDUCTION FIX
#    Ban now deducts the set ban_cost coins for EVERY user,
#    including owner/admin. Original code left untouched above.
# ============================================================
_BAN_SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_BAN_STEPS_PREMIUM = [
    "🔌 Connecting to Telegram API",
    "🔍 Verify bot token & identity",
    "⚙️ Access bot configuration",
    "📛 Rewrite bot name & description",
    "🖼️ Apply banned profile mark",
    "📋 Clear commands & remove webhook",
    "🔒 Logout & invalidate token",
    "✅ Seal permanent ban",
]

def _run_premium_ban_animation(chat_id, message_id):
    """Premium live ban animation (~12s). Constant motion: spinner, progress bar,
    live step checklist, percentage and elapsed timer. Fully self-contained."""
    total_frames = 28
    step_frames = 3
    bar_width = 20
    start_t = time.time()
    for i in range(total_frames + 1):
        pct = min(100, int(i * 100 / total_frames))
        filled = int(pct * bar_width / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        spinner = _BAN_SPINNER[i % len(_BAN_SPINNER)]
        current_step = min(i // step_frames, len(_BAN_STEPS_PREMIUM) - 1)
        elapsed = time.time() - start_t
        lines = [
            "🚫 **EXECUTING PERMANENT BAN**",
            "━━━━━━━━━━━━━━━━━━━━━━",
        ]
        for idx, step in enumerate(_BAN_STEPS_PREMIUM):
            if idx < current_step:
                lines.append("✅ " + step)
            elif idx == current_step:
                lines.append(spinner + " " + step)
            else:
                lines.append("○  " + step)
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("`[" + bar + "]`  **" + str(pct) + "%**   ⏱ " + format(elapsed, ".1f") + "s")
        lines.append("_⚠️ Please wait — do not send any message_")
        frame = "\n".join(lines)
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                  text=frame, parse_mode="Markdown")
        except Exception:
            pass
        if i < total_frames:
            time.sleep(0.45)

def process_ban_token(message):
    if message.text == "🔙 Back to Menu":
        is_admin = is_admin_user(message.from_user.id)
        bot.reply_to(message, "🏠 Returned to main menu!",
                     reply_markup=main_keyboard(is_admin))
        return

    user_id = message.from_user.id
    user = get_user(user_id)
    is_admin = is_admin_user(user_id)
    token = message.text.strip()

    ban_cost = int(get_setting("ban_cost"))

    # Coin check now applies to EVERYONE (including owner/admin) — THE FIX
    if user['coins'] < ban_cost:
        bot.reply_to(message,
            f"❌ **Not enough coins!**\n\n"
            f"💰 Your balance: **{user['coins']}** coins\n"
            f"💸 Cost per ban: **{ban_cost}** coins\n\n"
            "Get more coins via 🔗 Refer & Earn or 🎁 Redeem Code.",
            parse_mode="Markdown", reply_markup=main_keyboard(is_admin))
        return

    # Basic token validation
    if ':' not in token or len(token) < 20:
        bot.reply_to(message, "❌ Invalid bot token format! Please send a valid token.",
                     reply_markup=main_keyboard(is_admin))
        return

    # Premium live ban animation (~12s, constant motion, professional look)
    msg = bot.send_message(message.chat.id,
        "🚫 **INITIALIZING BAN SEQUENCE...**\n\n⏳ Establishing secure connection...",
        parse_mode="Markdown")
    _run_premium_ban_animation(message.chat.id, msg.message_id)

    # Execute actual ban
    result = ban_bot_token(token)

    # Deduct coins for EVERY user on successful ban — THE FIX (no more admin exemption)
    if result.get("success"):
        update_coins(user_id, -ban_cost)

    # Log to database
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bot_uname = result.get('bot_username', 'Failed') if result.get('success') else 'Failed'
    token_preview = token[:15] + "..." if len(token) > 15 else token
    status = "Success" if result.get('success') else "Failed"
    c.execute("""INSERT INTO ban_logs (user_id, bot_username, bot_token_preview, status, date)
                 VALUES (?, ?, ?, ?, ?)""",
              (user_id, bot_uname, token_preview, status, now))
    conn.commit()
    conn.close()

    # Build result message
    if result.get("success"):
        steps_text = "\n".join(result['steps'])
        new_balance = user['coins'] - ban_cost
        final_text = f"""
✅ **BOT PERMANENTLY BANNED!**

🤖 Bot: @{result['bot_username']}
🆔 Bot ID: `{result['bot_id']}`
👤 Banned by: {message.from_user.first_name}
💰 Cost: {ban_cost} coins
💼 New balance: {new_balance} coins

📋 **Process Steps:**
{steps_text}

🔒 **This bot token is now PERMANENTLY invalid and cannot be reused!**
"""
    else:
        final_text = f"""
❌ **Failed to Ban Bot!**

📝 Reason: {result.get('error', 'Unknown error')}

💡 Tips:
• Double-check the token is correct
• The bot may already be dead/disabled
• Make sure there are no spaces in the token
"""

    try:
        bot.edit_message_text(chat_id=message.chat.id,
                            message_id=msg.message_id,
                            text=final_text,
                            parse_mode="Markdown",
                            reply_markup=main_keyboard(is_admin))
    except:
        bot.send_message(message.chat.id, final_text,
                        parse_mode="Markdown",
                        reply_markup=main_keyboard(is_admin))

print("🔗 Force Join system loaded | 💰 Credit deduction fix applied")

# ============================================================
# 🚀 MAIN
# ============================================================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║   🚫 BOT BAN PRO - TELEGRAM BOT                         ║
║   Starting...                                           ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Ensure admin exists in DB
        add_user(ADMIN_ID, "admin", "Admin", 0)
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (ADMIN_ID,))
        conn.commit()
        conn.close()
        
        print("✅ Bot started successfully!")
        print(f"👑 Admin ID: {ADMIN_ID}")
        print(f"🤖 Bot: @{BOT_USERNAME}")
        print(f"🖼️  Banned bot image: {BANNED_BOT_IMAGE_URL}")
        print("\nPress Ctrl+C to stop")
        
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
        
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped gracefully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
