# TechCare Bot - Tailscale Deployment

## Überblick

Tailscale bietet ein Mesh VPN für sichere Peer-to-Peer Verbindungen:

- ✅ **Mesh VPN** - Direkte Verbindung zwischen Geräten
- ✅ **Keine öffentliche IP** - NAT Traversal automatisch
- ✅ **Verschlüsselt** - WireGuard-basiert (schnell & sicher)
- ✅ **Zero Config** - Setup in Minuten
- ✅ **Cross-Platform** - Windows, macOS, Linux, iOS, Android

## Voraussetzungen

1. **Tailscale Account** (kostenlos)
2. **Docker & Docker Compose** auf Server
3. **TechCare Lizenz** (Pro Business oder Enterprise empfohlen)
4. **Tailscale auf allen Techniker-Geräten** installiert

## Schritt 1: Tailscale Auth Key erstellen

### 1.1 Tailscale Dashboard öffnen

Gehe zu: **https://login.tailscale.com/admin/settings/keys**

### 1.2 Auth Key generieren

1. Klicke auf **"Generate auth key"**
2. Konfiguration:
   - **Description**: `TechCare Bot Server`
   - **Reusable**: ❌ Nein (One-time use)
   - **Ephemeral**: ❌ Nein (bleibt dauerhaft)
   - **Pre-authenticated**: ✅ Ja (kein Browser Login nötig)
   - **Expiry**: 90 Tage (Standard)

3. Klicke **"Generate key"**
4. **Kopiere den Key** (sieht aus wie: `tskey-auth-...`)

⚠️ **WICHTIG**: Key wird nur EINMAL angezeigt - speichere ihn sicher!

## Schritt 2: TechCare Installation

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
Ihre Wahl (1-4): 2  # Tailscale
```

**3. Tailscale Auth Key:**
```
Tailscale Auth Key: tskey-auth-...
```

**4. Hostname:**
```
Hostname für Tailscale: techcare
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
4. ✓ Startet alle Services (API, Web, PostgreSQL, Redis, Tailscale)

## Schritt 3: Tailscale auf Techniker-Geräten installieren

### 3.1 Installation

**Windows:**
```
Download: https://tailscale.com/download/windows
```

**macOS:**
```bash
brew install tailscale
```

**Linux:**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

**iOS/Android:**
- App Store / Google Play: "Tailscale"

### 3.2 Anmelden

1. Tailscale öffnen
2. Auf "Sign in" klicken
3. Mit deinem Tailscale Account anmelden
4. ✅ Gerät wird automatisch zum Netzwerk hinzugefügt

### 3.3 Server im Tailscale Admin Panel

Nach Installation erscheint der TechCare Server hier:

**https://login.tailscale.com/admin/machines**

Du solltest sehen:
- **Name**: `techcare` (oder dein gewählter Hostname)
- **Status**: 🟢 Online
- **IP**: `100.x.x.x` (Tailscale IP)

## Schritt 4: Zugriff testen

### 4.1 Tailscale IP ermitteln

Im Tailscale Admin Panel:
- Klicke auf den `techcare` Server
- Notiere die **Tailscale IP** (z.B. `100.64.1.5`)

Oder auf dem Server:
```bash
docker-compose exec tailscale tailscale ip
```

### 4.2 TechCare öffnen

Auf jedem Techniker-Gerät (das mit Tailscale verbunden ist):

```
http://techcare
```

oder mit IP:

```
http://100.64.1.5
```

### 4.3 Erfolg! 🎉

Du solltest jetzt die TechCare Login-Seite sehen.

## Optional: MagicDNS aktivieren

### Was ist MagicDNS?

MagicDNS ermöglicht es, Geräte per Name statt IP zu erreichen:

- **Ohne MagicDNS**: `http://100.64.1.5`
- **Mit MagicDNS**: `http://techcare`

### Aktivierung

1. Gehe zu: **https://login.tailscale.com/admin/dns**
2. Scrolle zu **"MagicDNS"**
3. Klicke **"Enable MagicDNS"**

Jetzt können alle Techniker `http://techcare` nutzen! ✨

## Optional: Access Control Lists (ACLs)

### Zugriffsrechte einschränken

Tailscale ACLs erlauben granulare Kontrolle, wer auf was zugreifen darf.

1. Gehe zu: **https://login.tailscale.com/admin/acls**
2. Beispiel ACL für TechCare:

```json
{
  "groups": {
    "group:techcare-team": ["user1@example.com", "user2@example.com"]
  },
  "acls": [
    {
      "action": "accept",
      "src": ["group:techcare-team"],
      "dst": ["techcare:80"]
    }
  ]
}
```

Nur Mitglieder von `techcare-team` können auf TechCare zugreifen.

## Wartung & Management

### Status prüfen

```bash
docker-compose ps
```

Alle Services sollten `Up` Status haben:
```
techcare-api         Up
techcare-web         Up
techcare-postgres    Up
techcare-redis       Up
techcare-tailscale   Up
techcare-nginx       Up
```

### Logs anzeigen

```bash
# Alle Logs
docker-compose logs -f

# Nur Tailscale
docker-compose logs -f tailscale
```

### Tailscale Status

Im Container:
```bash
docker-compose exec tailscale tailscale status
```

Output:
```
100.64.1.5    techcare              user@   linux   -
100.64.2.10   laptop-tech1          user@   windows online
100.64.3.15   laptop-tech2          user@   macOS   online
```

### Gerät aus Netzwerk entfernen

Im Tailscale Admin Panel:
1. **Machines** öffnen
2. Gerät auswählen
3. **⋮ → Disable** oder **Delete**

### Updates

```bash
# Automatisch (wenn aktiviert)
# Watchtower prüft täglich auf neue Versionen

# Manuell
docker-compose pull
docker-compose up -d
```

## Troubleshooting

### Problem: "Connection refused"

**Ursache**: Tailscale Container nicht verbunden

**Lösung**:
```bash
# Tailscale Status prüfen
docker-compose exec tailscale tailscale status

# Tailscale Logs prüfen
docker-compose logs tailscale

# Tailscale neu starten
docker-compose restart tailscale
```

### Problem: "Auth key expired"

**Ursache**: Auth Key ist abgelaufen (90 Tage Standard)

**Lösung**:
1. Neuen Auth Key generieren (siehe Schritt 1.2)
2. `.env` Datei updaten:
   ```bash
   nano .env
   # TAILSCALE_AUTH_KEY=<NEUER_KEY>
   ```
3. Tailscale Container neu starten:
   ```bash
   docker-compose restart tailscale
   ```

### Problem: Hostname nicht erreichbar

**Ursache**: MagicDNS nicht aktiviert

**Lösung**:
1. MagicDNS aktivieren (siehe oben)
2. Oder direkt IP nutzen: `http://100.x.x.x`

### Problem: "Device not authorized"

**Ursache**: ACLs blockieren Zugriff

**Lösung**:
1. Tailscale Admin Panel → ACLs
2. Prüfe ob dein User Zugriff hat
3. ACL anpassen falls nötig

## Vorteile von Tailscale

### Sicherheit

- **WireGuard VPN**: State-of-the-art Verschlüsselung
- **Zero Trust**: Jedes Gerät wird authentifiziert
- **Peer-to-Peer**: Direkte Verbindung, kein zentraler Server
- **End-to-End**: Traffic wird nicht durch Tailscale geroutet

### Performance

- **Direkte Verbindung**: Kein Relay (außer bei NAT-Problemen)
- **Niedriger Overhead**: WireGuard ist extrem schnell
- **NAT Traversal**: Funktioniert hinter Firewalls/NAT
- **Mobile-Optimiert**: Battery-friendly auf Smartphones

### Administration

- **Einfaches Setup**: 5 Minuten von 0 auf produktiv
- **Cross-Platform**: Alle Betriebssysteme unterstützt
- **Zentrale Verwaltung**: Web-Dashboard für alle Geräte
- **Keine Firewall-Regeln**: NAT Traversal automatisch

## Netzwerk-Topologie

```
┌──────────────────────────────────────────────────────────┐
│                  Tailscale Netzwerk                      │
│                  (100.64.0.0/10)                         │
│                                                          │
│  ┌────────────┐      ┌────────────┐     ┌────────────┐ │
│  │ TechCare   │      │ Laptop     │     │ Laptop     │ │
│  │ Server     │◄────►│ Techniker 1│     │ Techniker 2│ │
│  │ 100.64.1.5 │      │ 100.64.2.10│     │ 100.64.3.15│ │
│  └────────────┘      └────────────┘     └────────────┘ │
│        ▲                                                 │
│        │                                                 │
│        │            ┌────────────┐                       │
│        └───────────►│ Smartphone │                       │
│                     │ Techniker 1│                       │
│                     │ 100.64.4.20│                       │
│                     └────────────┘                       │
└──────────────────────────────────────────────────────────┘
```

Alle Geräte können direkt miteinander kommunizieren!

## Kosten

| Tier | Kosten | Features |
|------|--------|----------|
| **Personal** | €0/Monat | Bis 100 Geräte, 1 User |
| **Premium** | $5/User/Monat | Mehrere User, erweiterte Features |
| **Enterprise** | Custom | SLA, Support, erweiterte Kontrolle |

Für kleine Teams reicht **Personal** völlig aus!

## Alternative: Headscale (Self-Hosted)

Tailscale ist Open Source basiert. Du kannst auch den selbst gehosteten Koordinations-Server nutzen:

**Headscale**: https://github.com/juanfont/headscale

Vorteile:
- ✅ Volle Kontrolle über Metadaten
- ✅ Keine externen Dependencies

Nachteile:
- ❌ Mehr Wartungsaufwand
- ❌ Kein Web-Dashboard
- ❌ Keine mobile Apps

Für die meisten Firmen ist der offizielle Tailscale Service besser!

## Support

Bei Problemen:
- 📖 Tailscale Docs: https://tailscale.com/kb/
- 💬 TechCare Support: https://github.com/your-repo/techcare-bot/issues
- 📧 Email: support@techcare.local
