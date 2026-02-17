# TechCare Bot - License Enforcement API Spezifikation

## Übersicht

Dieses Dokument beschreibt wie der License Server System-Limits enforcen soll.

---

## API Endpoint

### `POST /api/license/validate`

**Request:**
```json
{
  "license_key": "TECHCARE-PRO-ABC123",
  "system_fingerprint": "a3b5c7d9e1f2..." // Optional, SHA256-Hash
}
```

**Response (Erfolg):**
```json
{
  "valid": true,
  "edition": "pro",
  "expires_at": "2027-12-31T23:59:59Z",
  "max_systems": 1,
  "registered_systems": 1,
  "customer_name": "Max Mustermann"
}
```

**Response (System-Limit erreicht):**
```json
{
  "valid": false,
  "error": "System-Limit erreicht: 1/1 Systeme registriert",
  "registered_systems": 1,
  "max_systems": 1,
  "edition": "pro"
}
```

---

## Backend-Logik (Datenbank)

### Tabelle: `licenses`
```sql
CREATE TABLE licenses (
    id UUID PRIMARY KEY,
    license_key VARCHAR(100) UNIQUE NOT NULL,
    edition VARCHAR(50) NOT NULL, -- community, pro, pro_business, enterprise
    customer_name VARCHAR(200),
    max_systems INT NOT NULL DEFAULT 1, -- 0 = unlimited
    expires_at TIMESTAMP NULL, -- NULL = never expires
    created_at TIMESTAMP DEFAULT NOW(),
    revoked BOOLEAN DEFAULT FALSE
);
```

### Tabelle: `license_activations`
```sql
CREATE TABLE license_activations (
    id UUID PRIMARY KEY,
    license_id UUID REFERENCES licenses(id),
    system_fingerprint VARCHAR(64) NOT NULL, -- SHA256-Hash
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    hostname VARCHAR(200),
    os_info VARCHAR(200),
    UNIQUE(license_id, system_fingerprint)
);
```

---

## Validierungs-Logik

```python
async def validate_license(license_key: str, system_fingerprint: str = None):
    # 1. Lizenz in DB suchen
    license = db.query(License).filter_by(license_key=license_key).first()

    if not license:
        return {"valid": False, "error": "Lizenzschlüssel ungültig"}

    if license.revoked:
        return {"valid": False, "error": "Lizenz wurde widerrufen"}

    # 2. Ablaufdatum prüfen
    if license.expires_at and license.expires_at < datetime.now():
        return {"valid": False, "error": "Lizenz abgelaufen"}

    # 3. System-Fingerprint prüfen (nur wenn mitgeschickt)
    if system_fingerprint:
        # Prüfe ob System bereits registriert ist
        activation = db.query(LicenseActivation).filter_by(
            license_id=license.id,
            system_fingerprint=system_fingerprint
        ).first()

        if activation:
            # System bekannt → Update last_seen
            activation.last_seen = datetime.now()
            db.commit()
        else:
            # Neues System → Prüfe ob max_systems erreicht
            registered_count = db.query(LicenseActivation).filter_by(
                license_id=license.id
            ).count()

            # max_systems = 0 bedeutet unlimited
            if license.max_systems > 0 and registered_count >= license.max_systems:
                return {
                    "valid": False,
                    "error": f"System-Limit erreicht: {registered_count}/{license.max_systems} Systeme registriert",
                    "registered_systems": registered_count,
                    "max_systems": license.max_systems,
                    "edition": license.edition
                }

            # Neues System registrieren
            new_activation = LicenseActivation(
                license_id=license.id,
                system_fingerprint=system_fingerprint
            )
            db.add(new_activation)
            db.commit()

    # 4. Zähle registrierte Systeme
    registered_systems = db.query(LicenseActivation).filter_by(
        license_id=license.id
    ).count()

    # 5. Erfolgreiche Validierung
    return {
        "valid": True,
        "edition": license.edition,
        "expires_at": license.expires_at.isoformat() if license.expires_at else "never",
        "max_systems": license.max_systems,
        "registered_systems": registered_systems,
        "customer_name": license.customer_name
    }
```

---

## System-Deregistrierung

### `POST /api/license/deregister`

User kann System manuell deregistrieren (z.B. bei Hardware-Wechsel):

**Request:**
```json
{
  "license_key": "TECHCARE-PRO-ABC123",
  "system_fingerprint": "a3b5c7d9e1f2..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "System erfolgreich deregistriert"
}
```

**Backend-Logik:**
```python
async def deregister_system(license_key: str, system_fingerprint: str):
    license = db.query(License).filter_by(license_key=license_key).first()

    if not license:
        return {"success": False, "error": "Lizenz nicht gefunden"}

    activation = db.query(LicenseActivation).filter_by(
        license_id=license.id,
        system_fingerprint=system_fingerprint
    ).first()

    if not activation:
        return {"success": False, "error": "System nicht registriert"}

    db.delete(activation)
    db.commit()

    return {"success": True, "message": "System erfolgreich deregistriert"}
```

---

## Trial-System

**❌ KEIN TRIAL-SYSTEM**

**Entscheidung:** Pro/Pro Business/Enterprise können **NICHT kostenlos getestet** werden.

**Begründung:**
- Verhindert Missbrauch (endlose Trials mit neuen Emails)
- Community Edition ist für kostenloses Testen verfügbar
- Klare Trennung: Community = kostenlos, Paid = Lizenz erforderlich

**Wenn User testen will:**
→ Community Edition nutzen (max 10 Reparaturen/Monat, 15 Tools)

---

## Edition-Spezifische Limits

| Edition | max_systems | Trial möglich | Ablaufdatum |
|---------|-------------|---------------|-------------|
| **Community** | N/A (kein Key) | ❌ Nein (ist kostenlos) | Nie |
| **Pro** | 1 | ❌ **Nein** | Optional (Abo) |
| **Pro Business** | 0 (unlimited) | ❌ **Nein** | Optional (Abo) |
| **Enterprise** | 0 (unlimited) | ❌ **Nein** | Optional (Vertrag) |

---

## Offline-Cache Handling (Client)

**Problem:** User könnte offline weiterlaufen

**Lösung:**
```python
# In license.py:
CACHE_MAX_AGE_DAYS = 1  # Statt 7 Tage nur 1 Tag!

# Bei jedem Bot-Start:
if cache_age > 24 hours:
    # Erzwinge Online-Check
    result = await validate_online(...)
    if result["error"]:
        return {
            "valid": False,
            "error": "Online-Validierung erforderlich (Cache zu alt)"
        }
```

---

## Admin-Dashboard Features

### Lizenz-Übersicht
```
Lizenz: TECHCARE-PRO-ABC123
Edition: Pro
Kunde: Max Mustermann
Max. Systeme: 1
Registrierte Systeme: 1/1

Aktive Systeme:
- System 1: a3b5c7d9e1f2...
  Hostname: pc-max-mustermann
  OS: Windows 11
  Zuletzt gesehen: vor 2 Stunden

[ System deaktivieren ]
```

### Lizenz-Widerruf
```python
def revoke_license(license_key: str, reason: str):
    license = db.query(License).filter_by(license_key=license_key).first()
    license.revoked = True
    license.revoked_at = datetime.now()
    license.revoked_reason = reason
    db.commit()
```

---

## Sicherheits-Maßnahmen

1. **Rate-Limiting:** Max 10 Validierungen pro Minute pro IP
2. **Brute-Force-Schutz:** Nach 5 fehlgeschlagenen Versuchen → temporärer Block
3. **Key-Format-Validierung:** `TECHCARE-{EDITION}-{RANDOM}`
4. **HTTPS erforderlich:** Alle API-Calls via HTTPS
5. **API-Key für Backend:** License Server braucht Auth

---

## Zusammenfassung

**Enforcement-Mechanismen:**
1. ✅ **System-Fingerprint** verhindert Mehrfachnutzung einer Lizenz
2. ✅ **Backend registriert** jedes neue System
3. ✅ **max_systems Check** vor Aktivierung
4. ✅ **Trial-System** mit automatischem Ablauf
5. ✅ **Offline-Cache** auf 24h begrenzt
6. ✅ **Deregistrierung** möglich bei Hardware-Wechsel

**Missbrauch-Schutz:**
- Pro-Lizenz (€49) kann nur auf 1 System laufen ✅
- Pro Business/Enterprise (€99+) können unbegrenzt Systeme haben ✅
- Nach Trial-Ende automatisch Community Edition ✅
- Offline-Nutzung max 24h, dann Online-Check erforderlich ✅
