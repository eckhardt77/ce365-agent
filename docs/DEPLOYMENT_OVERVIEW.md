# CE365 Agent - Deployment Übersicht

## Einleitung

CE365 Agent ist eine Docker-basierte Web-Applikation für IT-Wartungsteams. Diese Anleitung hilft Ihnen, die richtige Deployment-Methode für Ihre Firma zu wählen.

## Deployment-Optionen im Vergleich

| Feature | Cloudflare Tunnel | Tailscale | Vorhandenes VPN | Nur Lokal |
|---------|------------------|-----------|-----------------|-----------|
| **Setup-Zeit** | ⏱ 10 Min | ⏱ 5 Min | ⏱ 30-60 Min | ⏱ 5 Min |
| **Technisches Know-how** | 🟢 Niedrig | 🟢 Niedrig | 🔴 Hoch | 🟢 Niedrig |
| **Keine öffentliche IP** | ✅ Ja | ✅ Ja | ✅ Ja | ✅ Ja |
| **Automatisches SSL** | ✅ Ja | ❌ Nein | ⚠️ Optional | ❌ Nein |
| **Zero Trust Security** | ✅ Ja | ✅ Ja | ⚠️ Optional | ❌ Nein |
| **Mobile-freundlich** | ✅ Exzellent | ✅ Gut | ⚠️ Variiert | ❌ Nur lokal |
| **Performance** | 🟢 Schnell | 🟢 Sehr schnell | 🟡 Variiert | 🟢 Sehr schnell |
| **Zusätzliche Kosten** | €0-7/Monat | €0-5/Monat | €0 | €0 |
| **Wartungsaufwand** | 🟢 Sehr niedrig | 🟢 Niedrig | 🔴 Hoch | 🟢 Niedrig |
| **Compliance** | ⚠️ Cloud | ⚠️ Cloud (Metadata) | ✅ On-Premise | ✅ On-Premise |
| **Team-Größe** | 1-50+ | 1-100 | 1-1000+ | 1 |

## Entscheidungshilfe

### Wähle Cloudflare Tunnel wenn:

✅ Du **schnelles Setup** möchtest (10 Minuten)
✅ Du **automatisches SSL** brauchst
✅ Du **keine IT-Abteilung** hast
✅ Techniker von **überall** zugreifen sollen
✅ Du **DDoS-Schutz** willst
✅ Deine Firma **Cloud-Services nutzt**

**Kosten**: €0/Monat (Free Tier ausreichend)
**Komplexität**: ⭐⭐☆☆☆
**Empfohlen für**: Start-ups, kleine Firmen, Remote Teams

📖 **Guide**: [DEPLOYMENT_CLOUDFLARE.md](DEPLOYMENT_CLOUDFLARE.md)

---

### Wähle Tailscale wenn:

✅ Du **Mesh VPN** bevorzugst
✅ Du **Peer-to-Peer Verschlüsselung** willst
✅ Du **schnellste Performance** brauchst
✅ Techniker **mobile Geräte** nutzen
✅ Du **kein externes Gateway** möchtest
✅ Deine Firma **WireGuard** vertraut

**Kosten**: €0/Monat (Personal Tier ausreichend)
**Komplexität**: ⭐☆☆☆☆
**Empfohlen für**: Tech-Startups, DevOps-Teams, Remote-first Firmen

📖 **Guide**: [DEPLOYMENT_TAILSCALE.md](DEPLOYMENT_TAILSCALE.md)

---

### Wähle Vorhandenes VPN wenn:

✅ Deine Firma **bereits VPN** nutzt
✅ Du **on-premise bleiben** musst
✅ **Compliance** externe Cloud verbietet
✅ IT-Abteilung **VPN bevorzugt**
✅ Du **keine zusätzlichen Tools** willst
✅ Deine Firma **strikte Richtlinien** hat

**Kosten**: €0 (VPN bereits vorhanden)
**Komplexität**: ⭐⭐⭐⭐☆
**Empfohlen für**: Große Firmen, regulierte Branchen, konservative IT

📖 **Guide**: [DEPLOYMENT_VPN.md](DEPLOYMENT_VPN.md)

---

### Wähle Nur Lokal wenn:

✅ Du **nur testen** möchtest
✅ **Einzelplatz-Setup** ausreicht
✅ Alle arbeiten **im selben Büro**
✅ Du **maximale Einfachheit** willst
✅ **Kein Fernzugriff** nötig

**Kosten**: €0
**Komplexität**: ⭐☆☆☆☆
**Empfohlen für**: Tests, Demo, Einzelnutzer

## Quick Start

### 1. Docker installieren

**macOS/Windows:**
```
https://www.docker.com/products/docker-desktop
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### 2. CE365 herunterladen

```bash
git clone https://github.com/your-repo/ce365-agent.git
cd ce365-agent
```

### 3. Installer ausführen

```bash
bash install.sh
```

Der Installer fragt nach:
1. **Lizenzschlüssel** (oder leer für Community)
2. **Netzwerkzugriff** (1-4 wählen)
3. **Spezifische Konfiguration** (je nach Auswahl)
4. **Anthropic API Key**
5. **Auto-Updates** (ja/nein)

### 4. Fertig! 🎉

Nach Installation läuft CE365 und ist erreichbar über:
- **Cloudflare**: `https://ce365.ihrefirma.de`
- **Tailscale**: `http://ce365` (MagicDNS)
- **VPN**: `http://192.168.1.100`
- **Lokal**: `http://localhost`

## Architektur

### Docker Services

CE365 besteht aus mehreren Docker Containern:

```
┌─────────────────────────────────────────────────────┐
│                   CE365 Stack                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │   Web    │◄─┤  Nginx   │◄─┤  Cloudflared /   │ │
│  │ (Next.js)│  │ (Proxy)  │  │  Tailscale       │ │
│  └────┬─────┘  └──────────┘  │  (Optional)      │ │
│       │                       └──────────────────┘ │
│       │                                             │
│  ┌────▼─────┐  ┌──────────┐  ┌──────────────────┐ │
│  │   API    │◄─┤PostgreSQL│  │  Watchtower      │ │
│  │ (FastAPI)│  │ (Daten)  │  │  (Auto-Update)   │ │
│  └────┬─────┘  └──────────┘  │  (Optional)      │ │
│       │                       └──────────────────┘ │
│       │                                             │
│  ┌────▼─────┐                                      │
│  │  Redis   │                                      │
│  │ (Cache)  │                                      │
│  └──────────┘                                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Ports

| Service | Internal Port | External Port | Beschreibung |
|---------|--------------|---------------|-------------|
| Nginx | 80 | 80 | HTTP (oder via Tunnel) |
| Nginx | 443 | 443 | HTTPS (falls SSL aktiviert) |
| API | 8000 | - | Intern (via Nginx) |
| Web | 3000 | - | Intern (via Nginx) |
| PostgreSQL | 5432 | - | Intern |
| Redis | 6379 | - | Intern |

### Volumes (Persistent Data)

| Volume | Beschreibung | Backup wichtig? |
|--------|-------------|-----------------|
| `postgres_data` | Datenbank (Fälle, Learning) | ✅ **JA** |
| `ce365_data` | Uploads, Logs | ✅ Ja |
| `redis_data` | Cache, Sessions | ❌ Nein |
| `ce365_logs` | Application Logs | ⚠️ Optional |

## Security Best Practices

### 1. Starke Passwörter

Der Installer generiert automatisch sichere Passwörter für:
- PostgreSQL
- Redis
- JWT Secrets

Diese werden in `.env` gespeichert (chmod 600).

### 2. API Key Protection

Anthropic API Key wird verschlüsselt gespeichert und nie in Logs ausgegeben.

### 3. Rate Limiting

Nginx limitiert Requests automatisch:
- API: 10 req/s (Burst: 20)
- Web: 30 req/s (Burst: 50)

### 4. Updates

Aktiviere Auto-Updates für Security Patches:

```bash
# Bei Installation
Automatische Updates aktivieren? (j/n): j
```

Oder manuell:
```bash
docker-compose pull
docker-compose up -d
```

### 5. Backups

**Automatische Backups einrichten:**

```bash
# Cron Job erstellen (täglich 2 Uhr)
crontab -e

# Eintrag hinzufügen:
0 2 * * * cd /pfad/zu/ce365-agent && docker-compose exec -T postgres pg_dump -U ce365 ce365 | gzip > backup_$(date +\%Y\%m\%d).sql.gz
```

### 6. Monitoring

**Logs prüfen:**

```bash
# Alle Logs
docker-compose logs -f

# Nur Fehler
docker-compose logs --tail=100 | grep ERROR
```

**Health Checks:**

```bash
# Service Status
docker-compose ps

# Health Endpoint
curl http://localhost/health
```

## Nützliche Befehle

### Status & Logs

```bash
# Service Status
docker-compose ps

# Alle Logs (live)
docker-compose logs -f

# Nur ein Service
docker-compose logs -f api

# Letzte 100 Zeilen
docker-compose logs --tail=100

# Nur Fehler
docker-compose logs | grep ERROR
```

### Start & Stop

```bash
# Alle Services starten
docker-compose up -d

# Alle Services stoppen
docker-compose stop

# Services neustarten
docker-compose restart

# Herunterfahren (Container löschen)
docker-compose down

# Herunterfahren + Volumes löschen (⚠️ DATEN GEHEN VERLOREN!)
docker-compose down -v
```

### Updates

```bash
# Images aktualisieren
docker-compose pull

# Mit neuen Images neu starten
docker-compose up -d

# Alte Images aufräumen
docker image prune -a
```

### Backup & Restore

```bash
# Datenbank Backup
docker-compose exec postgres pg_dump -U ce365 ce365 > backup.sql

# Datenbank Restore
cat backup.sql | docker-compose exec -T postgres psql -U ce365 ce365

# Volumes Backup (komplett)
docker run --rm \
  -v ce365-agent_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/backup_$(date +%Y%m%d).tar.gz /data
```

### Troubleshooting

```bash
# Service neu starten
docker-compose restart api

# Service neu bauen
docker-compose up -d --build api

# In Container Shell
docker-compose exec api bash

# Resource Usage prüfen
docker stats

# Network prüfen
docker network inspect ce365-agent_ce365-internal
```

## Migration von CLI zu Docker

Falls du bereits die CLI-Version nutzt, hier ist der Migrationspfad:

### 1. Daten exportieren

```bash
# Aus CLI-Version
cd ~/.ce365/data/
cp -r cases.db ~/backup/
```

### 2. Docker installieren

```bash
cd ~/ce365-agent
bash install.sh
```

### 3. Daten importieren

```bash
# In PostgreSQL importieren (Script noch zu erstellen)
python3 tools/migrate_cli_to_docker.py ~/backup/cases.db
```

## Lizenzierung

### Community Edition (€0)

- ✅ Max 10 Reparaturen/Monat
- ✅ Lokale SQLite Datenbank
- ✅ Alle Basis-Features
- ✅ Docker Deployment

### Pro Edition (€49/Monat)

- ✅ **Unbegrenzte** Reparaturen
- ✅ **1 System** (Einzelnutzer)
- ✅ PostgreSQL Datenbank
- ✅ Priorität Support

### Pro Business Edition (€99/Monat)

- ✅ **Unbegrenzte** Reparaturen
- ✅ **∞ Systeme** (Multi-Client)
- ✅ Shared Learning Database
- ✅ Team-Features
- ✅ Priorität Support

### Enterprise Edition (ab €149/Seat)

- ✅ **Unbegrenzte** Reparaturen
- ✅ **Team Shared Learning**
- ✅ Zentrale Wissensdatenbank
- ✅ Multi-User Management
- ✅ Advanced Security
- ✅ SLA & Premium Support

**Volumenrabatte:**
- 6-9 Lizenzen: €139/Seat
- 10-24 Lizenzen: €129/Seat
- 25+ Lizenzen: €119/Seat

## Support

### Dokumentation

- 📖 [Cloudflare Deployment](DEPLOYMENT_CLOUDFLARE.md)
- 📖 [Tailscale Deployment](DEPLOYMENT_TAILSCALE.md)
- 📖 [VPN Deployment](DEPLOYMENT_VPN.md)
- 📖 [Edition Vergleich](EDITION_VERGLEICH.md)
- 📖 [Produktbeschreibung](PRODUKTBESCHREIBUNG.md)

### Community & Support

- 💬 GitHub Issues: https://github.com/your-repo/ce365-agent/issues
- 📧 Email Support: support@ce365.local
- 📚 Knowledge Base: https://docs.ce365.local
- 💡 Feature Requests: https://feedback.ce365.local

### Enterprise Support

Für Enterprise-Kunden:
- 🚨 24/7 Priority Support
- 📞 Telefon Hotline
- 👨‍💼 Dedicated Account Manager
- 🎓 Onboarding & Training

## FAQ

### Kann ich von Community zu Pro upgraden?

✅ Ja! Einfach Lizenzschlüssel in `.env` eintragen und Container neu starten:

```bash
nano .env
# LICENSE_KEY=<NEUER_KEY>
docker-compose restart
```

### Wie viele Techniker können gleichzeitig arbeiten?

- **Community**: 1 Techniker
- **Pro**: 1 Techniker
- **Pro Business**: Unbegrenzt (aber eigene Datenbanken)
- **Enterprise**: Unbegrenzt (shared Database)

### Funktioniert CE365 offline?

⚠️ **Teilweise**: Diagnose-Tools funktionieren offline, aber Claude AI braucht Internet. Für vollständig offline Szenarien kontaktiere Enterprise Sales.

### Wie lange dauert Setup?

- **Cloudflare**: ~10 Minuten
- **Tailscale**: ~5 Minuten
- **VPN**: ~30-60 Minuten (je nach IT)
- **Lokal**: ~5 Minuten

### Welche Ressourcen braucht der Server?

**Minimum:**
- CPU: 2 Cores
- RAM: 4 GB
- Disk: 20 GB
- OS: Linux (Ubuntu 20.04+), macOS 11+, Windows Server 2019+

**Empfohlen:**
- CPU: 4 Cores
- RAM: 8 GB
- Disk: 50 GB SSD
- OS: Ubuntu 22.04 LTS

### Kann ich CE365 auf Synology/QNAP NAS laufen lassen?

✅ **Ja!** Solange Docker unterstützt wird. Die meisten modernen NAS-Systeme (x86) funktionieren perfekt.

### Ist meine Daten sicher?

✅ **Ja!**
- Alle Passwörter verschlüsselt
- API Keys nie in Logs
- PostgreSQL verschlüsselt Daten at-rest
- Optional: SSL/TLS für Transport-Verschlüsselung
- Compliance-ready (DSGVO, HIPAA, ISO 27001)

## Roadmap

### Q2 2026
- ✨ Windows Agent (lokale CLI statt Web)
- ✨ Slack/Teams Integration
- ✨ Mobile App (iOS/Android)

### Q3 2026
- ✨ Multi-Tenancy (MSP-Features)
- ✨ LDAP/Active Directory Integration
- ✨ Advanced Analytics Dashboard

### Q4 2026
- ✨ Offline Mode (lokales LLM)
- ✨ Plugin-System (Custom Tools)
- ✨ White-Label Option (Enterprise)

## Feedback willkommen!

Wir verbessern CE365 ständig. Dein Feedback ist wertvoll:

- 🌟 GitHub Stars helfen uns!
- 💡 Feature Requests: https://feedback.ce365.local
- 🐛 Bug Reports: https://github.com/your-repo/ce365-agent/issues

---

**Viel Erfolg mit CE365 Agent! 🔧**
