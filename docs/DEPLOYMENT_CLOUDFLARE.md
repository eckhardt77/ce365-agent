# CE365 Agent - Cloudflare Tunnel Deployment

## Überblick

Cloudflare Tunnel bietet die sicherste und einfachste Methode für Remote-Zugriff auf CE365 Agent:

- ✅ **Kein VPN nötig** - Zugriff direkt über HTTPS
- ✅ **Automatisches SSL** - Cloudflare managed Zertifikate
- ✅ **Zero Trust Security** - Eingebaute Access Control
- ✅ **Keine öffentliche IP** - Ausgehende Verbindung nur
- ✅ **DDoS Protection** - Cloudflare's globales Netzwerk

## Voraussetzungen

1. **Cloudflare Account** (kostenlos)
2. **Domain** bei Cloudflare (oder extern, dann NS-Records ändern)
3. **Docker & Docker Compose** auf Server
4. **CE365 Lizenz** (Pro Business oder Enterprise empfohlen)

## Schritt 1: Cloudflare Tunnel erstellen

### 1.1 Cloudflare Dashboard öffnen

Gehe zu: **https://one.dash.cloudflare.com/**

### 1.2 Tunnel erstellen

1. Navigiere zu: **Zero Trust → Networks → Tunnels**
2. Klicke auf **"Create a tunnel"**
3. Wähle **"Cloudflared"** als Tunnel-Typ
4. Gib einen Namen ein: `ce365-prod` (oder beliebig)
5. **Kopiere das Token** (sieht aus wie: `eyJhIjoiZXhhbXBsZSJ9...`)

⚠️ **WICHTIG**: Speichere das Token sicher - du brauchst es für die Installation!

## Schritt 2: CE365 Installation

### 2.1 Installer ausführen

```bash
# Installation starten
bash install.sh
```

### 2.2 Setup-Fragen beantworten

**1. Lizenzschlüssel:**
```
Lizenzschlüssel: <DEIN_LIZENZ_KEY>
```

**2. Netzwerkzugriff:**
```
Ihre Wahl (1-4): 1  # Cloudflare Tunnel
```

**3. Cloudflare Tunnel Token:**
```
Cloudflare Tunnel Token: eyJhIjoiZXhhbXBsZSJ9...
```

**4. Domain:**
```
Ihre Cloudflare Domain: ce365.ihrefirma.de
```

**5. Anthropic API Key:**
```
Anthropic API Key: sk-ant-...
```

**6. Automatische Updates:**
```
Automatische Updates aktivieren? (j/n): j
```

### 2.3 Installation abwarten

Der Installer:
1. ✓ Erstellt `.env` Konfiguration
2. ✓ Erstellt `nginx/nginx.conf`
3. ✓ Lädt Docker Images herunter
4. ✓ Startet alle Services (API, Web, PostgreSQL, Redis, Cloudflared)

## Schritt 3: Cloudflare Tunnel konfigurieren

### 3.1 Public Hostname hinzufügen

Zurück im Cloudflare Dashboard:

1. Navigiere zu: **Zero Trust → Networks → Tunnels**
2. Wähle deinen Tunnel aus (`ce365-prod`)
3. Tab **"Public Hostname"**
4. Klicke **"Add a public hostname"**

### 3.2 Hostname-Details

| Feld | Wert |
|------|------|
| **Subdomain** | `ce365` |
| **Domain** | `ihrefirma.de` |
| **Type** | `HTTP` |
| **URL** | `nginx:80` |

⚠️ **Wichtig**: URL ist `nginx:80` (nicht `localhost`!)

### 3.3 Speichern

Klicke **"Save hostname"**

## Schritt 4: Zugriff testen

### 4.1 DNS-Propagation abwarten

Warte 1-2 Minuten, dann öffne:

```
https://ce365.ihrefirma.de
```

### 4.2 Erfolg! 🎉

Du solltest jetzt die CE365 Login-Seite sehen.

## Optional: Cloudflare Access aktivieren

### Zero Trust Access Control

Schütze CE365 mit zusätzlicher Authentifizierung:

1. Navigiere zu: **Zero Trust → Access → Applications**
2. Klicke **"Add an application"**
3. Wähle **"Self-hosted"**

#### Application Details

| Feld | Wert |
|------|------|
| **Name** | `CE365 Agent` |
| **Application Domain** | `ce365.ihrefirma.de` |
| **Session Duration** | `24 hours` |

#### Access Policy

Erstelle eine Policy für dein Team:

- **Name**: `CE365 Team Access`
- **Include**: `Emails ending in @ihrefirma.de`
- **Action**: `Allow`

Speichern!

Jetzt müssen sich alle User erst mit Cloudflare Access authentifizieren, bevor sie CE365 erreichen.

## Wartung & Management

### Status prüfen

```bash
docker-compose ps
```

Alle Services sollten `Up` Status haben:
```
ce365-api           Up
ce365-web           Up
ce365-postgres      Up
ce365-redis         Up
ce365-cloudflared   Up
ce365-nginx         Up
```

### Logs anzeigen

```bash
# Alle Logs
docker-compose logs -f

# Nur Cloudflared
docker-compose logs -f cloudflared

# Nur API
docker-compose logs -f api
```

### Cloudflare Tunnel Status

Im Cloudflare Dashboard:
- **Zero Trust → Networks → Tunnels**
- Status sollte **"Healthy"** sein
- Letzte Aktivität: wenige Sekunden alt

### Updates

```bash
# Automatisch (wenn aktiviert)
# Watchtower prüft täglich auf neue Versionen

# Manuell
docker-compose pull
docker-compose up -d
```

### Tunnel neu starten

```bash
docker-compose restart cloudflared
```

## Troubleshooting

### Problem: "Bad Gateway" (502)

**Ursache**: Cloudflare erreicht Nginx nicht

**Lösung**:
```bash
# Prüfe ob nginx läuft
docker-compose ps nginx

# Nginx Logs prüfen
docker-compose logs nginx

# Nginx neu starten
docker-compose restart nginx
```

### Problem: "Tunnel is not connected"

**Ursache**: Falsches Token oder Netzwerkproblem

**Lösung**:
```bash
# Cloudflared Logs prüfen
docker-compose logs cloudflared

# Token prüfen in .env
cat .env | grep CLOUDFLARE_TUNNEL_TOKEN

# Cloudflared neu starten
docker-compose restart cloudflared
```

### Problem: "Application not found"

**Ursache**: Public Hostname falsch konfiguriert

**Lösung**:
1. Cloudflare Dashboard → Tunnels
2. Public Hostname prüfen
3. URL MUSS `nginx:80` sein (nicht `localhost`)

### Problem: SSL-Fehler

**Ursache**: Cloudflare SSL-Modus falsch

**Lösung**:
1. Cloudflare Dashboard → SSL/TLS
2. Modus auf **"Flexible"** setzen (da Nginx intern HTTP nutzt)

## Vorteile von Cloudflare Tunnel

### Sicherheit

- **DDoS Protection**: Cloudflare's globales Netzwerk
- **Web Application Firewall**: Automatischer Schutz
- **Bot Management**: Blockiert Scrapers und Bots
- **Zero Trust Access**: Optional, integrierte Authentifizierung

### Performance

- **Global CDN**: 300+ Datacenter weltweit
- **Smart Routing**: Optimierte Verbindungswege
- **HTTP/3 & QUIC**: Moderne Protokolle
- **Caching**: Statische Assets werden gecacht

### Administration

- **Kein Port Forwarding**: Keine Firewall-Regeln
- **Automatisches SSL**: Keine Zertifikatsverwaltung
- **Zentrale Logs**: Traffic-Insights im Dashboard
- **Einfaches Management**: Web-Interface für alles

## Kosten

| Tier | Kosten | Features |
|------|--------|----------|
| **Free** | €0/Monat | Unbegrenzte Tunnel, 50 User |
| **Teams** | €7/User/Monat | Zero Trust Access, erweiterte Logs |
| **Enterprise** | Custom | SLA, erweiterte Sicherheit |

Für die meisten Firmen reicht **Free** völlig aus!

## Support

Bei Problemen:
- 📖 Cloudflare Docs: https://developers.cloudflare.com/cloudflare-one/
- 💬 CE365 Support: https://github.com/your-repo/ce365-agent/issues
- 📧 Email: support@ce365.local
