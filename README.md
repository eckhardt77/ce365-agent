# 🔧 TechCare Bot - Community Edition v2.0.0

**AI-powered IT maintenance assistant for Windows and macOS**

[🇩🇪 Deutsche Version](README_DE.md) | 🇺🇸 English Version

TechCare Bot is an AI-powered IT maintenance assistant that helps you diagnose and repair Windows and macOS systems. With natural language interaction and **30+ integrated tools**, IT maintenance becomes easy!

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Powered by Claude](https://img.shields.io/badge/Powered%20by-Claude%20Sonnet%204.5-blueviolet)](https://anthropic.com)

---

## 🆕 What's New in v2.0

### ✨ New Features

- 🔐 **Technician Password Protection** - Protect TechCare from unauthorized access
- 🔧 **Driver Management** - Check for driver updates (Windows Update + Custom DB)
- 📡 **Monitoring Sensor** - Background service for proactive system monitoring
- 🗑️ **Easy Uninstall** - Simple uninstallation with `techcare --uninstall`
- 🔑 **License System** - Optional licensing for Pro/Enterprise (Community is free!)
- 🌐 **Network Options** - Remote services via VPN/Cloudflare/Tailscale (optional)

### 🎯 All Community Features (Free)

✅ **15 Basic Tools** - Essential diagnostics and repair
✅ **AI-Powered Analysis** - Root cause detection
✅ **Driver Check** - Automatic driver update detection
✅ **Monitoring** - Background system monitoring
✅ **Password Protection** - Secure TechCare access
✅ **Max 10 Repairs/Month** - Perfect for testing
✅ **Multi-Language** - English + German
✅ **Cross-Platform** - Windows, macOS, Linux (exp)

---

## ⚠️ Disclaimer

**IMPORTANT: Use at your own risk!**

TechCare Bot is provided "AS IS", WITHOUT ANY WARRANTY.

**No liability for:**
- ❌ Data loss
- ❌ System damage
- ❌ Incorrect repairs
- ❌ Downtime
- ❌ Security incidents

**Before using:**
- ✅ **Always create backups**
- ✅ **Test in non-production environment first**
- ✅ **Review all commands before approval**
- ✅ **No autonomous repairs** (GO REPAIR lock required)

By using TechCare Bot, you accept full responsibility.

---

## 🚀 Quick Start

### Installation (5 Minutes)

#### 1. Install Python 3.11 or 3.12

**macOS (Homebrew):**
```bash
brew install python@3.12
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

#### 2. Clone Repository

```bash
git clone https://github.com/yourusername/techcare-bot.git
cd techcare-bot
```

#### 3. Create Virtual Environment

```bash
# Create venv
python3.12 -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

#### 4. Install TechCare

```bash
pip install -e .
```

#### 5. Start TechCare

```bash
techcare
```

On first start, the **Setup Wizard** will guide you through:
- Name & Company
- Edition (Community / Pro / Enterprise)
- Anthropic API Key ([Get it free](https://console.anthropic.com))
- Language (English / Deutsch)
- **Optional:** Technician Password
- **Optional:** Network Configuration (for Pro/Enterprise)

---

## 📋 Requirements

- **Python 3.11 or 3.12** (Python 3.14 not yet supported)
- **Anthropic API Key** ([Free tier available](https://console.anthropic.com))
- Internet connection (for Claude API)

---

## 🎮 Usage

### Basic Commands

```bash
# Start TechCare
techcare

# Set/change technician password
techcare --set-password

# Show version
techcare --version

# Uninstall TechCare
techcare --uninstall

# Help
techcare --help
```

### Example Session

```
🔧 TechCare Bot v2.0.0
Session ID: abc123...
💡 Learning: 5 cases saved, 2 reuses
─────────────────────────────────────────────────
Language: English | Type 'exit' to quit
─────────────────────────────────────────────────

🔍 Creating system status report...

[System Info]
🖥️  macOS 14.2, CPU: 8 Cores (12% usage)
RAM: 16.0 GB (8.2 GB free, 48% used)
Disk: 500 GB (120 GB free, 76% used)
Uptime: 3d 2h 15m

✅ System status report complete
💬 How can I help you?
─────────────────────────────────────────────────

> Check for driver updates

🔄 Checking drivers...

📊 Statistics:
   • Installed drivers: 150
   • Outdated drivers: 3
   • Critical updates: 1
   • Recommended updates: 2

🔄 AVAILABLE UPDATES:

🔴 1. NVIDIA GeForce RTX 3080
   Current: 512.95
   Available: 528.49
   Importance: CRITICAL
   Source: windows_update

🟡 2. Intel Wi-Fi 6 AX200
   Current: 22.80.0
   Available: 22.120.0
   Importance: RECOMMENDED
   Source: windows_update

⚠️  RECOMMENDATION:
   Install 1 critical driver update!

> My Windows Update is not working

Let me analyze this...

🎯 ROOT CAUSE FOUND
╔══════════════════════════════════════════════╗
║  Cause: BITS service stuck                   ║
║  Confidence: 87%                             ║
║                                              ║
║  Evidence:                                   ║
║  ✓ Event Log: BITS Error 0x80070057         ║
║  ✓ Service Status: Running but unresponsive ║
║  ✓ Temp folder: 47 incomplete downloads     ║
║                                              ║
║  Solution:                                   ║
║  1. Restart BITS service                    ║
║  2. Clear download queue                    ║
╚══════════════════════════════════════════════╝

Repair Plan:
1. Restart BITS service (wuauserv)
2. Clear Windows Update cache

Please confirm with: GO REPAIR: 1,2

> GO REPAIR: 1,2

✅ Executing repairs...
[Step 1/2] Restarting BITS service... ✓
[Step 2/2] Clearing update cache... ✓

🎉 All repairs completed successfully!
📋 Changelog saved to: data/changelogs/abc123.json
```

---

## 🛠️ Available Tools (30+)

### 📊 Audit Tools (Read-Only)

| Tool | Description |
|------|-------------|
| **System Info** | OS, CPU, RAM, Disk, Uptime |
| **Process Monitor** | Running processes, CPU/RAM usage |
| **System Logs** | Event Log / Syslog analysis |
| **Updates Check** | Pending Windows/macOS updates |
| **Backup Status** | Time Machine / Windows Backup status |
| **Security Audit** | Firewall, Antivirus, Gatekeeper, SIP |
| **Startup Programs** | Autostart apps with impact analysis |
| **Malware Scanner** | Windows Defender / ClamAV integration |
| **🆕 Driver Check** | Check for driver updates |
| **Network Diagnostics** | IP, DNS, Connectivity tests |
| **Stress Tests** | CPU, Memory, Disk speed tests |
| **System Report** | Comprehensive HTML report |
| **Web Search** | Online solution lookup |

### 🔧 Repair Tools (Approval Required)

| Tool | Description |
|------|-------------|
| **Service Manager** | Start/Stop/Restart Windows/macOS services |
| **Disk Cleanup** | Delete temp files, cache, logs |
| **DNS Flush** | Clear DNS cache |
| **Network Reset** | Reset TCP/IP stack |
| **SFC Scan** | System File Checker (Windows) |
| **Disk Repair** | Fix disk permissions (macOS) |
| **Update Installer** | Install Windows/macOS updates |
| **Backup Creator** | Create restore point / Time Machine backup |
| **Startup Manager** | Enable/disable autostart programs |
| **Update Scheduler** | Schedule automatic updates |

### 🧠 AI Analysis Tools

- 🎯 **Root Cause Analysis** - AI-powered problem diagnosis
- 📊 **Pattern Recognition** - Detect recurring issues

---

## 🆕 New Features in Detail

### 🔐 Technician Password Protection

Protect TechCare from unauthorized access:

```bash
# Set password during setup
techcare
# > Set technician password? [Y/n]: y
# > Password: ********

# Or set later
techcare --set-password

# On every start
techcare
# > 🔐 TechCare Access
# > Password: ********
# > ✓ Authenticated
```

**Features:**
- bcrypt-hashed password (secure)
- 3 attempts limit
- Session timeout (configurable)
- Optional (can be skipped)

---

### 🔧 Driver Management

Automatic driver update detection:

```bash
> Check for driver updates

📊 Driver Status Report:
   • Total drivers: 150
   • Outdated: 3
   • Critical: 1
   • Recommended: 2

🔄 Available Updates:
🔴 NVIDIA Graphics Driver (Critical)
🟡 Intel Network Adapter (Recommended)
```

**Sources:**
- Windows Update API (Windows)
- Apple Software Update (macOS)
- Custom Driver Database (JSON-based)

**Custom Database:**
Add your own drivers in `techcare/tools/drivers/driver_database.json`

---

### 📡 Monitoring Sensor

Background service for proactive monitoring:

```bash
# Manual test
python -m techcare.monitoring.sensor

# Install as service
python -m techcare.monitoring.service

# Windows: Windows Service
# macOS: LaunchDaemon
# Linux: systemd Service
```

**Collected Metrics:**
- CPU / RAM / Disk usage
- Critical service status (Firewall, Antivirus)
- Pending updates
- Recent event log errors
- SMART disk health

**Default Interval:** 5 minutes (configurable)

---

### 🗑️ Easy Uninstall

Simple uninstallation:

```bash
techcare --uninstall

# Deletes:
# ✓ .env file (config)
# ✓ data/ directory (sessions, changelogs, cases)
# ✓ ~/.techcare/ (cache, user config)
```

---

## 🔐 Security Features

### 1. GO REPAIR Lock

```
No repairs without your explicit approval:
- Bot creates repair plan
- You review each step
- You approve with: GO REPAIR: 1,2,3
- Only approved steps execute
```

### 2. Technician Password (NEW!)

```
Protect TechCare from unauthorized access:
- Password required on startup
- 3 attempts limit
- bcrypt-hashed (secure)
- Session timeout
```

### 3. Encrypted API Key Storage

```
API keys stored securely in OS Keychain:
- macOS: Keychain Access
- Windows: Credential Manager
- Linux: Secret Service (gnome-keyring)
- Fallback: .env (with migration prompt)
```

### 4. PII Detection (Microsoft Presidio)

```
Automatically detects and anonymizes:
- Credit card numbers
- Email addresses
- Phone numbers
- Passwords
- IP addresses
```

### 5. Audit Trail

```
Every repair is logged:
- Timestamp
- Tool used
- Input parameters
- Result
- Success/Failure status

Saved to: data/changelogs/{session_id}.json
```

---

## 🌍 Multi-Language Support

TechCare Bot supports:
- 🇺🇸 **English**
- 🇩🇪 **Deutsch**

### Change Language

**During setup:**
```
Choose language / Sprache wählen:
1. English
2. Deutsch
```

**After setup:**
```bash
# Via command
techcare --language en

# Interactive
> language de
Language changed to: Deutsch
```

---

## 🧠 Learning System (Pro+)

**Starting from Pro Edition:** TechCare learns from every repair:

```python
# Similar problem detected
💡 Learning: I found a similar case from 3 days ago:
   Problem: "Windows Update failed"
   Solution: Restarted BITS service
   Success: Yes

   Should I apply the same solution? (yes/no)
```

**Benefits:**
- ⚡ Faster resolution (reuses proven solutions)
- 📈 Improves over time
- 🎯 Higher success rate

**Privacy:**
- **Pro/Pro Business:** Stored locally in `data/cases.db`
- **Enterprise:** Optional central team knowledge database (PostgreSQL)
- PII automatically anonymized
- Can be cleared with `techcare --clear-cases`

---

## 🏢 Pro & Enterprise Features (Optional)

Community Edition is **100% free** - perfect for testing with max 10 repairs/month.

For professional and commercial use, we offer:

### TechCare Pro (€49/month)
- ✅ 30+ Tools (instead of 15)
- ✅ Unlimited repairs (instead of max 10)
- ✅ Local learning system (SQLite)
- ✅ Case reuse
- ✅ 1 system
- ✅ Email support

### TechCare Pro Business (€99/month)
- ✅ All Pro features
- ✅ Unlimited systems
- ✅ Central dashboards
- ✅ Fleet management
- ✅ Priority support

### TechCare Enterprise (from €149/month)
- ✅ All Pro Business features
- ✅ Shared team learning database (PostgreSQL)
- ✅ Team management (LDAP/SSO)
- ✅ Central monitoring
- ✅ Custom integrations
- ✅ Dedicated support

**License System:**
- Optional (Community works without license)
- Online + offline validation
- Flexible licensing models
- Contact: sales@eckhardt-marketing.de

---

## 📦 Project Structure

```
techcare-bot/
├── techcare/                          # Main package
│   ├── core/                         # Core functionality
│   │   ├── bot.py                   # Main bot orchestration
│   │   ├── client.py                # Anthropic API client
│   │   ├── session.py               # Session management
│   │   └── license.py               # License validation (optional)
│   ├── tools/                        # Tool system
│   │   ├── audit/                   # Read-only tools
│   │   ├── repair/                  # Repair tools
│   │   ├── drivers/                 # Driver management (NEW!)
│   │   └── analysis/                # AI analysis tools
│   ├── workflow/                     # Workflow state machine
│   ├── learning/                     # Learning system
│   ├── monitoring/                   # Monitoring sensor (NEW!)
│   ├── security/                     # PII detection
│   └── ui/                           # Terminal UI (Rich)
├── data/                             # Local data (gitignored)
│   ├── sessions/                    # Chat sessions
│   ├── changelogs/                  # Repair logs
│   └── cases.db                     # Learning database
├── .env.example                      # Environment template
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

---

## 🔄 Updates

```bash
# Update TechCare
cd techcare-bot
git pull
pip install -r requirements.txt --upgrade

# Check version
techcare --version
```

---

## 🐛 Troubleshooting

### Import Error: No module named 'rich'

```bash
pip install -r requirements.txt
```

### Python 3.14 Compatibility

Python 3.14 is not yet supported. Use Python 3.11 or 3.12:

```bash
brew install python@3.12
python3.12 -m venv venv
source venv/bin/activate
pip install -e .
```

### Driver Check doesn't work

- **Windows:** Requires admin rights (PowerShell)
- **macOS:** Check Terminal permissions
- **Linux:** Install `smartctl`

### "techcare: command not found"

```bash
# Use Python directly
python -m techcare

# Or check PATH
which techcare
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

**Development Setup:**
```bash
git clone https://github.com/yourusername/techcare-bot.git
cd techcare-bot
python3.12 -m venv venv
source venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt  # Dev dependencies
```

---

## 📄 License

**MIT License**

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

[Full MIT License text...]

**Note:** Commercial support and licensing available for businesses.

---

## 🐛 Bug Reports & Security

**Bug Reports:**
- GitHub Issues: https://github.com/yourusername/techcare-bot/issues

**Security Vulnerabilities:**
- **DO NOT** create public issues
- Email: security@eckhardt-marketing.de
- Subject: [SECURITY] TechCare Bot - [Brief Description]

See [SECURITY.md](SECURITY.md) for responsible disclosure policy.

---

## 💬 Support

- 📖 Documentation: [Wiki](https://github.com/yourusername/techcare-bot/wiki)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/techcare-bot/discussions)
- 🐛 Bug Reports: [GitHub Issues](https://github.com/yourusername/techcare-bot/issues)

**Commercial Support:**
- Email: support@eckhardt-marketing.de
- Website: https://techcare.eckhardt-marketing.de

---

## 🙏 Acknowledgments

- **Anthropic Claude** - AI engine
- **Microsoft Presidio** - PII detection
- **Rich** - Beautiful terminal output
- **psutil** - System monitoring
- **spaCy** - NLP processing

---

## 📊 Stats

- **30+ Tools** - Comprehensive IT toolset
- **52 Error Codes** - Built-in knowledge base
- **2 Languages** - English + German
- **3 Platforms** - Windows, macOS, Linux (exp)
- **100% Free** - Community Edition (MIT License)

---

## 🗺️ Roadmap

### v2.1 (Q2 2026)
- [ ] Web Dashboard (optional)
- [ ] Plugin System
- [ ] More languages (French, Spanish)

### v2.2 (Q3 2026)
- [ ] Predictive Maintenance
- [ ] Cloud Backup Integration
- [ ] Mobile Companion App

### v3.0 (Q4 2026)
- [ ] Multi-System Management
- [ ] Scheduled Maintenance
- [ ] Custom Tool Builder

---

Made with ❤️ by Eckhardt-Marketing

**TechCare Bot** - Because IT maintenance should be easy.

**Community Edition v2.0.0** - Free Forever 🎉
