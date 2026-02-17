# CE365 Agent - Vorhandenes VPN nutzen

## Überblick

Falls Ihre Firma bereits ein VPN betreibt, können Sie CE365 direkt darüber erreichen:

- ✅ **Keine zusätzliche Software** - Nutzen Sie vorhandenes VPN
- ✅ **Compliance** - Bleibt in bestehender IT-Infrastruktur
- ✅ **Keine Cloud** - Komplett on-premise
- ✅ **Bewährte Prozesse** - IT-Team kennt sich aus

## Unterstützte VPN-Technologien

CE365 funktioniert mit **allen** VPN-Lösungen:

- ✅ WireGuard
- ✅ OpenVPN
- ✅ Cisco AnyConnect
- ✅ Fortinet FortiClient
- ✅ SonicWall Global VPN
- ✅ Palo Alto GlobalProtect
- ✅ IPsec/L2TP
- ✅ PPTP (nicht empfohlen)
- ✅ Proprietary Enterprise VPNs

**Grund**: CE365 ist eine normale Web-Applikation. Sobald Techniker per VPN verbunden sind, greifen sie per HTTP auf den Server zu.

## Voraussetzungen

1. **VPN bereits eingerichtet** - Techniker können sich verbinden
2. **Server im internen Netz** - CE365 läuft auf Server im Firmennetzwerk
3. **Docker & Docker Compose** auf Server
4. **CE365 Lizenz** (alle Editionen unterstützt)

## Schritt 1: Server IP ermitteln

### 1.1 Interne IP des Servers

Auf dem Server:

**Linux/macOS:**
```bash
ip addr show
# oder
ifconfig
```

**Windows:**
```powershell
ipconfig
```

Notiere die **interne IP** (z.B. `192.168.1.100` oder `10.0.0.50`)

### 1.2 Erreichbarkeit testen

Von einem Techniker-Gerät (über VPN verbunden):

```bash
ping 192.168.1.100
```

Sollte erfolgreich sein! ✅

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
Ihre Wahl (1-4): 3  # Vorhandenes VPN
```

**3. Server IP:**
```
Interne IP-Adresse dieses Servers: 192.168.1.100
```

**4. Anthropic API Key:**
```
Anthropic API Key: sk-ant-...
```

**5. Automatische Updates:**
```
Automatische Updates aktivieren? (j/n): j
```

### 2.3 Installation abwarten

Der Installer:
1. ✓ Erstellt `.env` Konfiguration
2. ✓ Erstellt `nginx/nginx.conf`
3. ✓ Lädt Docker Images herunter
4. ✓ Startet alle Services (API, Web, PostgreSQL, Redis)

## Schritt 3: Firewall konfigurieren

### 3.1 Port freigeben (falls Firewall aktiv)

**Linux (ufw):**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp  # Falls SSL später gewünscht
```

**Linux (firewalld):**
```bash
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

**Windows Firewall:**
```powershell
New-NetFirewallRule -DisplayName "CE365 HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow
```

### 3.2 Server Firewall prüfen

Falls der Server hinter einer Hardware-Firewall ist, stelle sicher dass Port 80/443 vom internen Netz erreichbar ist.

## Schritt 4: Zugriff testen

### 4.1 VPN verbinden

Techniker verbinden sich mit dem Firmen-VPN (wie gewohnt).

### 4.2 CE365 öffnen

```
http://192.168.1.100
```

### 4.3 Erfolg! 🎉

Du solltest jetzt die CE365 Login-Seite sehen.

## Optional: Internes DNS

### Hostname statt IP nutzen

Statt IP-Adresse kann dein IT-Team einen internen DNS-Namen einrichten:

**Beispiel**: `ce365.internal` → `192.168.1.100`

#### Windows Server DNS

1. DNS Manager öffnen
2. Forward Lookup Zone auswählen
3. Neuen A-Record erstellen:
   - **Name**: `ce365`
   - **IP**: `192.168.1.100`

#### Linux (dnsmasq)

```bash
echo "192.168.1.100 ce365.internal" | sudo tee -a /etc/hosts
```

Jetzt können Techniker zugreifen mit:
```
http://ce365.internal
```

Viel leichter zu merken! ✨

## Optional: SSL/TLS Zertifikat

### Warum SSL im internen Netz?

- ✅ Bessere Sicherheit (verschlüsselter Traffic)
- ✅ Moderne Browser erwarten HTTPS
- ✅ Compliance-Anforderungen (z.B. ISO 27001)

### Variante 1: Self-Signed Certificate (schnell)

```bash
# SSL-Verzeichnis erstellen
mkdir -p nginx/ssl

# Self-Signed Zertifikat erstellen
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/ce365.key \
  -out nginx/ssl/ce365.crt \
  -subj "/CN=ce365.internal"
```

**Nachteil**: Browser zeigen Warnung (muss manuell akzeptiert werden)

### Variante 2: Interne CA (empfohlen)

Falls deine Firma eine interne Certificate Authority hat:

1. Certificate Signing Request (CSR) erstellen:
```bash
openssl req -new -newkey rsa:2048 -nodes \
  -keyout nginx/ssl/ce365.key \
  -out nginx/ssl/ce365.csr \
  -subj "/CN=ce365.internal"
```

2. CSR an IT-Team senden
3. Signiertes Zertifikat erhalten
4. Als `nginx/ssl/ce365.crt` speichern

**Vorteil**: Keine Browser-Warnungen (CA ist im Firmennetzwerk vertraut)

### Variante 3: Let's Encrypt (nur mit öffentlicher Domain)

Falls CE365 über eine öffentliche Domain erreichbar ist:

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx

# Zertifikat erstellen
sudo certbot --nginx -d ce365.ihrefirma.de
```

**Achtung**: Funktioniert nur mit öffentlicher Domain + offenen Port 80/443

### Nginx SSL-Konfiguration

Nach Zertifikat-Erstellung, `nginx/nginx.conf` anpassen:

```nginx
server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /etc/nginx/ssl/ce365.crt;
    ssl_certificate_key /etc/nginx/ssl/ce365.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ... rest der Konfiguration ...
}

# HTTP zu HTTPS Redirect
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}
```

Container neu starten:
```bash
docker-compose restart nginx
```

Jetzt mit HTTPS zugreifen:
```
https://192.168.1.100
# oder
https://ce365.internal
```

## Wartung & Management

### Status prüfen

```bash
docker-compose ps
```

Alle Services sollten `Up` Status haben:
```
ce365-api       Up
ce365-web       Up
ce365-postgres  Up
ce365-redis     Up
ce365-nginx     Up
```

### Logs anzeigen

```bash
# Alle Logs
docker-compose logs -f

# Nur API
docker-compose logs -f api
```

### Updates

```bash
# Automatisch (wenn aktiviert)
# Watchtower prüft täglich auf neue Versionen

# Manuell
docker-compose pull
docker-compose up -d
```

### Backup erstellen

**Datenbank Backup:**
```bash
docker-compose exec postgres pg_dump -U ce365 ce365 > backup_$(date +%Y%m%d).sql
```

**Volumes Backup:**
```bash
docker run --rm \
  -v ce365-agent_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz /data
```

## Troubleshooting

### Problem: "Connection refused" über VPN

**Ursache 1**: Firewall blockiert Port

**Lösung**:
```bash
# Prüfe ob Port offen
sudo netstat -tulpn | grep :80

# Firewall-Regel prüfen
sudo ufw status
```

**Ursache 2**: Docker nutzt falsches Network Interface

**Lösung**:
```bash
# docker-compose.yml anpassen
services:
  nginx:
    ports:
      - "0.0.0.0:80:80"  # Explizit auf alle Interfaces binden
```

### Problem: Langsame Performance über VPN

**Ursache**: VPN-Bandbreite oder Latenz

**Lösung**:
1. **Nginx Caching aktivieren**: Statische Assets werden gecacht
2. **Compression**: Gzip ist bereits aktiviert
3. **VPN-Performance prüfen**: `iperf3` für Bandbreiten-Test

### Problem: "Site can't be reached" aber Ping funktioniert

**Ursache**: Port 80 ist blockiert, ICMP (Ping) nicht

**Lösung**:
```bash
# Prüfe Port-Erreichbarkeit
telnet 192.168.1.100 80
# oder
nc -zv 192.168.1.100 80
```

Falls nicht erreichbar → Firewall-Regel hinzufügen

### Problem: SSL-Zertifikat wird nicht vertraubt

**Ursache**: Self-Signed Certificate

**Lösung 1**: Interne CA nutzen (siehe oben)

**Lösung 2**: Zertifikat manuell vertrauen

**Windows:**
1. Zertifikat in Browser öffnen
2. "Zertifikat anzeigen"
3. "In Zertifikatspeicher installieren"
4. "Vertrauenswürdige Stammzertifizierungsstellen"

**macOS:**
1. Zertifikat in Schlüsselbundverwaltung importieren
2. Doppelklick auf Zertifikat
3. "Vertrauen" → "Beim Verwenden immer vertrauen"

## Netzwerk-Topologie

```
┌──────────────────────────────────────────────────────────┐
│                   Firmennetzwerk                         │
│                   (10.0.0.0/8 oder 192.168.0.0/16)       │
│                                                          │
│                  ┌────────────────┐                      │
│                  │ VPN Gateway    │                      │
│                  │ (OpenVPN/etc.) │                      │
│                  └───────┬────────┘                      │
│                          │                               │
│         ┌────────────────┼────────────────┐             │
│         │                │                │             │
│    ┌────▼─────┐    ┌────▼─────┐    ┌────▼─────┐       │
│    │ CE365 │    │ Laptop   │    │ Laptop   │       │
│    │ Server   │    │ Tech 1   │    │ Tech 2   │       │
│    │10.0.0.50 │    │10.0.0.101│    │10.0.0.102│       │
│    └──────────┘    └──────────┘    └──────────┘       │
│                                                          │
└──────────────────────────────────────────────────────────┘
         ▲                    ▲                ▲
         │                    │                │
         │          ┌─────────┴────────┐       │
         │          │   Internet       │       │
         └──────────┤                  ├───────┘
                    │  Techniker       │
                    │  im Außendienst  │
                    └──────────────────┘
```

Techniker verbinden sich per VPN, dann normaler HTTP-Zugriff!

## Vorteile

### Compliance & Kontrolle

- ✅ **Volle Kontrolle**: Daten bleiben im Firmennetzwerk
- ✅ **Audit-Logs**: VPN-Logs zeigen alle Zugriffe
- ✅ **Compliance**: DSGVO/HIPAA/ISO konform
- ✅ **Bewährte Infrastruktur**: IT-Team kennt VPN bereits

### Sicherheit

- ✅ **Verschlüsselung**: VPN-Tunnel encrypted
- ✅ **Authentifizierung**: VPN-User Management
- ✅ **Firewall**: Schutz durch Firewall-Regeln
- ✅ **Kein Cloud**: Keine externe Abhängigkeit

### Kosten

- ✅ **Keine zusätzlichen Kosten**: VPN bereits vorhanden
- ✅ **Keine SaaS-Fees**: Kein Cloudflare/Tailscale Abo

## Nachteile (vs. Cloudflare/Tailscale)

- ❌ **Komplexeres Setup**: Firewall-Regeln, DNS, etc.
- ❌ **VPN-Overhead**: Performance-Impact durch VPN
- ❌ **Wartungsaufwand**: IT-Team muss VPN warten
- ❌ **Mobile Probleme**: VPN auf Smartphones oft instabil

## Fazit

**Wann VPN-Variante nutzen?**

- ✅ Firma hat bereits gut funktionierendes VPN
- ✅ Compliance erfordert on-premise Lösung
- ✅ IT-Team bevorzugt bewährte Infrastruktur
- ✅ Kein Budget für Cloud-Services

**Wann Alternativen besser?**

- 🚫 VPN ist langsam oder instabil
- 🚫 Kein internes IT-Team vorhanden
- 🚫 Viele mobile Techniker unterwegs
- 🚫 Einfaches Setup gewünscht

Für die meisten kleinen/mittleren Firmen ist **Cloudflare Tunnel** oder **Tailscale** die bessere Wahl - einfacher, schneller, zuverlässiger!

## Support

Bei Problemen:
- 💬 CE365 Support: https://github.com/your-repo/ce365-agent/issues
- 📧 Email: support@ce365.local
