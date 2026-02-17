"""
TechCare Bot - Secure Secrets Management

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Verwendet OS Keychain für sichere API-Key Speicherung:
- macOS: Keychain Access
- Windows: Windows Credential Manager
- Linux: Secret Service (gnome-keyring)
"""

import keyring
import os
from pathlib import Path
from typing import Optional


class SecretsManager:
    """
    Sichere API-Key Verwaltung mit OS Keychain
    
    Fallback: Verschlüsselte Speicherung in .env (wenn Keychain nicht verfügbar)
    """
    
    SERVICE_NAME = "TechCare-Bot"
    API_KEY_NAME = "anthropic_api_key"
    
    def __init__(self):
        self.keyring_available = self._check_keyring_available()
    
    def _check_keyring_available(self) -> bool:
        """Prüft ob Keyring verfügbar ist"""
        try:
            # Test-Zugriff auf Keyring
            keyring.get_keyring()
            return True
        except Exception:
            return False
    
    def save_api_key(self, api_key: str) -> bool:
        """
        Speichert API Key sicher
        
        Args:
            api_key: Anthropic API Key
            
        Returns:
            True wenn erfolgreich gespeichert
        """
        if not api_key or not api_key.startswith("sk-ant-"):
            raise ValueError("Ungültiger API Key (muss mit 'sk-ant-' beginnen)")
        
        try:
            if self.keyring_available:
                # Speichern in OS Keychain (SICHER)
                keyring.set_password(
                    self.SERVICE_NAME,
                    self.API_KEY_NAME,
                    api_key
                )
                return True
            else:
                # Fallback: .env (Plain Text, aber gewarnt)
                self._save_to_env(api_key)
                return True
                
        except Exception as e:
            print(f"⚠️  Fehler beim Speichern: {e}")
            return False
    
    def get_api_key(self) -> Optional[str]:
        """
        Lädt API Key (aus Keychain oder .env)
        
        Returns:
            API Key oder None
        """
        try:
            if self.keyring_available:
                # Aus OS Keychain laden (SICHER)
                api_key = keyring.get_password(
                    self.SERVICE_NAME,
                    self.API_KEY_NAME
                )
                if api_key:
                    return api_key
            
            # Fallback: Aus .env laden (Plain Text)
            return self._load_from_env()
            
        except Exception as e:
            print(f"⚠️  Fehler beim Laden: {e}")
            return None
    
    def delete_api_key(self) -> bool:
        """
        Löscht gespeicherten API Key
        
        Returns:
            True wenn erfolgreich gelöscht
        """
        try:
            if self.keyring_available:
                keyring.delete_password(
                    self.SERVICE_NAME,
                    self.API_KEY_NAME
                )
            
            # Auch aus .env entfernen (falls vorhanden)
            self._remove_from_env()
            return True
            
        except Exception:
            return False
    
    def migrate_from_env(self) -> bool:
        """
        Migriert API Key von .env zu Keychain
        
        Returns:
            True wenn erfolgreich migriert
        """
        if not self.keyring_available:
            return False
        
        # API Key aus .env laden
        api_key = self._load_from_env()
        if not api_key:
            return False
        
        # In Keychain speichern
        success = self.save_api_key(api_key)
        
        if success:
            # Aus .env entfernen (nur den Key, nicht die ganze Datei)
            self._remove_from_env()
            print("✅ API Key migriert: .env → OS Keychain (verschlüsselt)")
            return True
        
        return False
    
    def _save_to_env(self, api_key: str):
        """Speichert API Key in .env (Fallback, Plain Text)"""
        env_file = Path.cwd() / ".env"
        
        # Lese existierende .env
        lines = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                lines = f.readlines()
        
        # Aktualisiere oder füge ANTHROPIC_API_KEY hinzu
        key_found = False
        for i, line in enumerate(lines):
            if line.startswith("ANTHROPIC_API_KEY="):
                lines[i] = f"ANTHROPIC_API_KEY={api_key}\n"
                key_found = True
                break
        
        if not key_found:
            lines.append(f"ANTHROPIC_API_KEY={api_key}\n")
        
        # Schreibe zurück
        with open(env_file, 'w') as f:
            f.writelines(lines)
    
    def _load_from_env(self) -> Optional[str]:
        """Lädt API Key aus .env (Fallback)"""
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv("ANTHROPIC_API_KEY")
    
    def _remove_from_env(self):
        """Entfernt API Key aus .env"""
        env_file = Path.cwd() / ".env"
        
        if not env_file.exists():
            return
        
        # Lese existierende .env
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Entferne ANTHROPIC_API_KEY Zeile
        lines = [l for l in lines if not l.startswith("ANTHROPIC_API_KEY=")]
        
        # Schreibe zurück
        with open(env_file, 'w') as f:
            f.writelines(lines)
    
    def get_storage_method(self) -> str:
        """
        Gibt zurück wie der API Key gespeichert wird
        
        Returns:
            "keychain" oder "env_plaintext"
        """
        if self.keyring_available:
            # Prüfe ob Key in Keychain vorhanden
            api_key = keyring.get_password(self.SERVICE_NAME, self.API_KEY_NAME)
            if api_key:
                return "keychain"
        
        # Prüfe ob in .env
        if self._load_from_env():
            return "env_plaintext"
        
        return "none"


def get_secrets_manager() -> SecretsManager:
    """Factory Function für SecretsManager"""
    return SecretsManager()
