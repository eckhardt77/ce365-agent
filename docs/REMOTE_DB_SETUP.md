# Remote DB Setup - Team Learning

**TechCare Learning System mit zentraler PostgreSQL Datenbank**

Alle Techniker im Team teilen die gleiche Case Library → Jeder lernt von allen!

---

## 🎯 **Überblick**

### **Lokales SQLite (Default)**
- ✅ Einfach, keine Konfiguration nötig
- ✅ Offline-fähig
- ❌ Nur einzelner Techniker lernt
- ❌ Kein Team-Wissen

### **Remote PostgreSQL (Empfohlen für Teams)**
- ✅ Team-weites Learning
- ✅ Zentrale Verwaltung
- ✅ Automatischer Fallback zu SQLite (wenn offline)
- ✅ Backup & Analytics
- ⚠️ Erfordert Server-Setup

---

## 📦 **Option 1: Docker Setup (Einfach)**

### **1. PostgreSQL Server starten**

```bash
# Docker Compose starten
docker-compose -f docker-compose.learning-db.yml up -d

# Logs prüfen
docker-compose -f docker-compose.learning-db.yml logs -f learning-db
```

**Was startet:**
- PostgreSQL Server (Port 5432)
- pgAdmin Web-Interface (Port 5050) - Optional für DB-Verwaltung

### **2. .env konfigurieren**

```bash
# .env erweitern
cat >> .env << EOF

# Learning System - Remote DB
LEARNING_DB_TYPE=postgresql
LEARNING_DB_URL=postgresql://techcare:change_this_password@localhost:5432/techcare_learning
LEARNING_DB_FALLBACK=data/cases.db
EOF
```

**WICHTIG:** Password ändern!
```bash
# docker-compose.learning-db.yml
environment:
  POSTGRES_PASSWORD: dein_sicheres_password
```

### **3. Bestehende Cases migrieren**

```bash
# SQLite Cases zu PostgreSQL übertragen
python tools/migrate_cases.py --source data/cases.db --target remote
```

### **4. Testen**

```bash
# Test-Script ausführen
python test_remote_db.py
```

Erwartete Ausgabe:
```
✓ Remote PostgreSQL verbunden
✓ Test Case gespeichert
✓ Case geladen
✓ Similarity-Suche funktioniert
```

---

## 🖥️ **Option 2: Server-Installation (Production)**

### **Server-Anforderungen**
- OS: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- RAM: 2 GB (min), 4 GB (empfohlen)
- Disk: 10 GB (+ Wachstum je nach Nutzung)
- Netzwerk: Erreichbar für alle Techniker-Laptops

### **1. PostgreSQL installieren**

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**CentOS/RHEL:**
```bash
sudo dnf install postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### **2. Datenbank & User erstellen**

```bash
sudo -u postgres psql

# In psql:
CREATE DATABASE techcare_learning;
CREATE USER techcare WITH ENCRYPTED PASSWORD 'dein_sicheres_password';
GRANT ALL PRIVILEGES ON DATABASE techcare_learning TO techcare;
\q
```

### **3. Remote-Zugriff aktivieren**

```bash
# pg_hba.conf bearbeiten
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Folgende Zeile hinzufügen (am Ende):
host    techcare_learning    techcare    0.0.0.0/0    md5

# postgresql.conf bearbeiten
sudo nano /etc/postgresql/14/main/postgresql.conf

# listen_addresses ändern:
listen_addresses = '*'

# PostgreSQL neu starten
sudo systemctl restart postgresql
```

### **4. Firewall öffnen**

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 5432/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload
```

### **5. Clients konfigurieren**

Auf jedem Techniker-Laptop `.env` erstellen:

```bash
# .env
LEARNING_DB_TYPE=postgresql
LEARNING_DB_URL=postgresql://techcare:password@192.168.1.100:5432/techcare_learning
LEARNING_DB_FALLBACK=data/cases_local.db
```

**Ersetze:**
- `password` → Dein DB-Password
- `192.168.1.100` → Server IP-Adresse

---

## 🔧 **Option 3: Cloud-Hosting**

### **Managed PostgreSQL Services:**

1. **AWS RDS**
   - URL: `postgresql://user:pass@xxx.rds.amazonaws.com:5432/techcare`

2. **Azure Database for PostgreSQL**
   - URL: `postgresql://user@server:pass@xxx.postgres.database.azure.com:5432/techcare`

3. **Google Cloud SQL**
   - URL: `postgresql://user:pass@xxx/techcare`

4. **DigitalOcean Managed Databases**
   - URL: Wird im Dashboard angezeigt

**Vorteile:**
- Automatische Backups
- Skalierbarkeit
- Kein Server-Wartung

**Kosten:**
- ~10-30€/Monat (je nach Anbieter)

---

## 🔄 **Migration & Backup**

### **Cases migrieren**

```bash
# SQLite → PostgreSQL
python tools/migrate_cases.py --source data/cases.db --target remote

# JSON Export (für Backup)
python tools/migrate_cases.py --source data/cases.db --export cases_backup.json
```

### **PostgreSQL Backup**

```bash
# Manuelles Backup
docker exec techcare-learning-db pg_dump -U techcare techcare_learning > backups/learning_$(date +%Y%m%d).sql

# Restore
cat backups/learning_20260217.sql | docker exec -i techcare-learning-db psql -U techcare techcare_learning
```

### **Automatisches Backup (Cronjob)**

```bash
# /etc/cron.daily/techcare-backup
#!/bin/bash
docker exec techcare-learning-db pg_dump -U techcare techcare_learning > /path/to/backups/learning_$(date +%Y%m%d).sql

# Nur letzte 30 Tage behalten
find /path/to/backups -name "learning_*.sql" -mtime +30 -delete
```

---

## 🧪 **Testing & Monitoring**

### **Connection Test**

```bash
# Von Laptop aus
psql "postgresql://techcare:password@server-ip:5432/techcare_learning" -c "SELECT COUNT(*) FROM cases;"
```

### **pgAdmin Web-Interface**

```
http://localhost:5050

Login:
  Email: admin@techcare.local
  Password: admin (ändern!)

Server hinzufügen:
  Host: learning-db
  Port: 5432
  User: techcare
  Password: [dein_password]
```

### **TechCare Test**

```bash
python test_remote_db.py
```

Erwartete Ausgabe:
```
✓ Remote PostgreSQL verbunden
✓ Case speichern funktioniert
✓ Similarity-Suche funktioniert
✓ Statistiken funktionieren
```

---

## 🐛 **Troubleshooting**

### **Problem: "Connection refused"**

**Ursache:** PostgreSQL nicht erreichbar

**Lösung:**
```bash
# 1. PostgreSQL läuft?
docker ps | grep learning-db
# oder
sudo systemctl status postgresql

# 2. Port offen?
netstat -tulpn | grep 5432

# 3. Firewall?
sudo ufw status
```

---

### **Problem: "Authentication failed"**

**Ursache:** Falsches Password oder User

**Lösung:**
```bash
# Password überprüfen
docker exec -it techcare-learning-db psql -U techcare -d techcare_learning

# Wenn Zugriff funktioniert, .env prüfen
cat .env | grep LEARNING_DB_URL
```

---

### **Problem: "Fallback zu SQLite aktiv"**

**Ursache:** Remote-DB nicht erreichbar

**TechCare Verhalten:**
- ✓ Funktioniert weiter mit lokalem SQLite
- ⚠️ Kein Team-Learning
- ℹ️ Versucht bei jedem Start erneut Remote zu verbinden

**Lösung:**
```bash
# Remote-DB Status prüfen
python -c "from techcare.learning.database import get_db_manager; print('Remote:', get_db_manager().is_remote())"

# Retry manuell
python test_remote_db.py  # Testet Connection
```

---

### **Problem: "Duplicate key error" bei Migration**

**Ursache:** Cases bereits in Ziel-DB vorhanden

**Lösung:**
- Normal! Migration überspringt Duplikate automatisch
- Nur neue Cases werden hinzugefügt

---

## 📊 **Team-Nutzung Best Practices**

### **Empfohlener Workflow:**

1. **Zentraler Server:**
   - Docker-Host oder dedizierter Server
   - PostgreSQL 24/7 laufend
   - Automatische Backups (täglich)

2. **Techniker-Laptops:**
   - `.env` mit Remote-DB URL
   - Fallback zu lokalem SQLite (für Offline-Einsätze)
   - Bei Internet: Automatisch Remote-DB
   - Ohne Internet: Lokales SQLite

3. **Monitoring:**
   - pgAdmin für DB-Übersicht
   - Regelmäßig Stats checken: `techcare stats`

---

## 🎉 **Erfolg prüfen**

Nach Setup sollte jeder Techniker sehen:

```bash
$ techcare

✓ Remote Learning-DB verbunden: postgresql://techcare:****@server:5432/techcare_learning
💡 Learning: 237 Fälle gespeichert, 1453 Wiederverwendungen
```

**Team-Learning aktiv!** 🧠

Wenn Techniker A ein Problem löst, sieht Techniker B beim nächsten ähnlichen Fall:

```
🎯 BEKANNTES PROBLEM ERKANNT!

Ähnlichkeit: 85%
Lösung: [von Techniker A]
Bereits 3x erfolgreich (100%)

Möchtest du diese Lösung verwenden?
1. Ja (schnell)
2. Nein (vollständiger Audit)
```

---

## 🔐 **Sicherheit**

### **Empfehlungen:**

1. **Starkes Password:**
   ```bash
   # Generieren
   openssl rand -base64 32
   ```

2. **SSL/TLS Verbindung:**
   ```bash
   LEARNING_DB_URL=postgresql://user:pass@host:5432/db?sslmode=require
   ```

3. **Firewall:**
   - Nur Team-IPs erlauben
   - Keine öffentliche Exposition

4. **Backups verschlüsseln:**
   ```bash
   pg_dump [...] | gpg --encrypt > backup.sql.gpg
   ```

---

## 📚 **Weitere Infos**

- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **Docker Compose Docs:** https://docs.docker.com/compose/

---

**Implementiert:** 2026-02-17
**Version:** v0.4.0 (mit Remote DB Support)
