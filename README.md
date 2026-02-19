# CE365 Agent

**AI-powered IT maintenance assistant for Windows and macOS**

[![License: BSL-1.1](https://img.shields.io/badge/License-BSL--1.1-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](https://agent.ce365.de)

CE365 Agent is your AI sidekick in the terminal. It diagnoses IT problems, suggests repairs and documents everything automatically. Powered by Claude, GPT-4o or any OpenRouter model (BYOK).

---

## Quick Start

```bash
pip install ce365-agent
python -m ce365 --setup
```

The setup wizard will guide you through provider selection and API key configuration.

```bash
python -m ce365
```

---

## Features

### Community (Free)
- 7 diagnostic tools (System Info, Logs, Processes, Updates, Backup, Security, Startup)
- 3 basic repair tools (Service Manager, Disk Cleanup, DNS Flush)
- 5 repairs per month
- PII detection (Microsoft Presidio)
- Local learning system (SQLite)
- Multi-provider: Claude, GPT-4o, OpenRouter (BYOK)
- Multi-language: English + Deutsch
- Password protection

### Pro (Paid)
- **Everything in Community, plus:**
- 30+ tools (advanced audit, repair, stress tests, drivers, malware scan)
- Unlimited repairs
- Web search + AI root cause analysis
- Multi-Agent system (5 specialist agents)
- System report (HTML)
- Shared learning database (PostgreSQL)
- Commercial use license
- Auto-updates

[Get Pro](https://agent.ce365.de)

---

## How It Works

```
$ ce365

Hey, I'm Steve — your IT sidekick. What's going on?

> Client reports: Laptop extremely slow for 2 weeks

Got it. Running a full diagnostic...

 Diagnostic complete (7 tools, 12 sec)

  Disk: 97% full (only 4 GB free)
  14 startup programs (boot time: 3m 20s)
  RAM: 7.2/8 GB used (Chrome: 4.1 GB)
  CPU temp: 62C (OK)

My suggestion:
  1. Clean temp files (~18 GB recoverable)
  2. Disable 9 unnecessary startup programs
  3. Optimize Chrome profile

Shall I proceed? Type GO REPAIR: 1,2,3
```

No repairs run without your explicit approval via `GO REPAIR`.

---

## Multi-Agent System

Steve is the orchestrator. For complex problems, he consults specialist agents:

| Agent | Focus |
|-------|-------|
| **WindowsDoc** | Event Logs, Registry, BSOD, Services, Energy |
| **MacDoc** | system_profiler, Unified Logging, APFS, LaunchAgents |
| **NetDoc** | DNS, WLAN, Firewall, VPN, Latency, Routing |
| **SecurityDoc** | Malware, Autostart, Certificates, Suspicious Processes |
| **PerfDoc** | CPU, RAM, Disk I/O, Thermal Throttling, Bottleneck |

Each specialist runs their own diagnosis and reports back to Steve with structured findings.

---

## Requirements

- Python 3.11 or 3.12
- API key for one of: Anthropic (Claude), OpenAI (GPT-4o), or OpenRouter
- Windows, macOS, or Linux

---

## Security

- **GO REPAIR lock** — No system changes without explicit approval
- **PII detection** — Personal data automatically anonymized before API calls
- **Password protection** — Optional bcrypt-secured access
- **Audit trail** — Every action logged to changelog
- **Privacy** — All data stays local, GDPR compliant

---

## Development

```bash
git clone https://github.com/carsteneckhardt/ce365-agent.git
cd ce365-agent
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

---

## Project Structure

```
ce365-agent/
  ce365/
    core/           Bot, providers, license, session, agents
    tools/          30+ audit, repair, research, analysis tools
    config/         Settings, system prompt, i18n
    workflow/       State machine, execution lock
    learning/       Case library, similarity matching
    security/       PII detection (Presidio)
    ui/             Rich terminal UI
  license-server/   FastAPI license server
  website/          Landing page (DE + EN)
  scripts/          Build and deployment tools
```

---

## License

Business Source License 1.1 (BSL-1.1)

- Reading, modifying, non-commercial use: **allowed**
- Commercial use: requires a [Pro license](https://agent.ce365.de)
- After 2030-02-19: becomes Apache 2.0

See [LICENSE](LICENSE) for details.

---

## Support

- Issues: [GitHub Issues](https://github.com/carsteneckhardt/ce365-agent/issues)
- Email: info@eckhardt-marketing.de
- Website: [agent.ce365.de](https://agent.ce365.de)

---

Made by [Eckhardt-Marketing](https://eckhardt-marketing.de)
