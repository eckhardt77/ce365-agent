# CE365 Agent — Datenschutzhinweise

**Stand:** Februar 2026 | Version 2.0.0

---

## 1. Welche Daten werden erhoben?

### Lokal gespeichert (auf dem Techniker-PC)

| Daten | Speicherort | Zweck |
|-------|-------------|-------|
| Changelogs (Reparatur-Protokolle) | `data/changelogs/` | Audit-Trail, Nachvollziehbarkeit |
| Learning Cases (Problemlösungen) | `data/cases.db` | Wiederverwendung bewährter Lösungen |
| Usage-Tracking (Repair-Zähler) | `~/.ce365/usage.json` | Community-Limit (5 Repairs/Monat) |
| Lizenz-Cache | `~/.ce365/cache/license.json` | Offline-Validierung (24h) |
| Konfiguration | `~/.ce365/config.json` | Benutzereinstellungen |

### An externe Dienste übertragen

| Empfänger | Daten | Zweck |
|-----------|-------|-------|
| LLM-Provider (Anthropic/OpenAI/OpenRouter) | Anonymisierte Problembeschreibungen, System-Infos (OS, CPU, RAM) | KI-Analyse und Problemlösung |
| DuckDuckGo (optional, nur Pro) | Anonymisierte Suchbegriffe | Web-Recherche nach Lösungen |
| CE365 Lizenzserver (nur Pro) | Lizenzschlüssel-Hash, System-Fingerprint-Hash | Lizenzvalidierung |

---

## 2. PII-Schutz (Personenbezogene Daten)

CE365 Agent nutzt **Microsoft Presidio** zur automatischen Erkennung und Anonymisierung personenbezogener Daten:

- E-Mail-Adressen, Telefonnummern, Namen
- IP-Adressen, IBANs, Kreditkartennummern
- Passwörter, URLs mit personenbezogenen Daten

**PII wird anonymisiert BEVOR Daten an LLM-Provider oder in Changelogs geschrieben werden.**

Konfiguration via `.env`:
```
PII_DETECTION_ENABLED=true
PII_DETECTION_LEVEL=high    # high, medium, low
PII_SHOW_WARNINGS=true
```

---

## 3. Datensicherheit

- Alle lokalen Dateien werden mit restriktiven Berechtigungen gespeichert (nur Owner lesbar)
- Lizenz-Cache speichert nur Hashes, keine Klartext-Schlüssel
- System-Fingerprint wird als SHA256-Hash übertragen (nicht rekonstruierbar)
- HMAC-Signaturen schützen Cache-Daten vor Manipulation

---

## 4. Betroffenenrechte (DSGVO)

### Recht auf Auskunft (Art. 15)
Tippe `datenschutz` oder `privacy` im Chat um eine Übersicht aller gespeicherten Daten zu sehen.

### Recht auf Löschung (Art. 17)
Tippe `datenschutz` > Option 2 um alle lokalen Daten zu löschen.

### Recht auf Datenportabilität (Art. 20)
Tippe `datenschutz` > Option 1 um alle Daten als JSON zu exportieren.

### Retention Policy
Changelogs werden nach 90 Tagen, Learning Cases nach 180 Tagen automatisch bereinigt (via `datenschutz` > Option 3).

---

## 5. LLM-Provider Datenschutz

CE365 Agent sendet anonymisierte Daten an den konfigurierten LLM-Provider. Bitte beachte die jeweiligen Datenschutzrichtlinien:

- **Anthropic:** https://www.anthropic.com/privacy
- **OpenAI:** https://openai.com/privacy
- **OpenRouter:** https://openrouter.ai/privacy

API-Daten werden von diesen Anbietern **nicht für Modell-Training verwendet** (gemäß deren API-Nutzungsbedingungen).

---

## 6. Kontakt

Bei Datenschutzfragen: info@eckhardt-marketing.de

---

**CE365 Agent speichert keine Daten in der Cloud. Alle Daten liegen lokal beim Techniker oder auf dem selbst konfigurierten Datenbankserver.**
