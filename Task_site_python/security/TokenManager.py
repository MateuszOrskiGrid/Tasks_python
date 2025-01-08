import os
import json
import hmac
import secrets
import hashlib
from datetime import datetime, timedelta
from base64 import b64encode, b64decode

class TokenManager:
    def __init__(self, config_dir="../config", data_dir="../data"):
        self.salt_file = os.path.join(config_dir, "salt.key")
        self.config_file = os.path.join(data_dir, "token_config.json")

        # Create directories if they don't exist
        os.makedirs(config_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)

        self.salt = self._load_or_generate_salt()
        self._load_config()

    def _load_or_generate_salt(self):
        if os.path.exists(self.salt_file):
            with open(self.salt_file, "rb") as f:
                return f.read()
        else:
            salt = secrets.token_bytes(32)
            with open(self.salt_file, "wb") as f:
                f.write(salt)
            return salt

    def _load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "token_hash": None,
                "expiry": None,
                "max_failed_attempts": 5,
                "failed_attempts": 0,
                "lockout_until": None
            }
            self._save_config()

    def _save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

    def _hash_token(self, token):
        return hashlib.pbkdf2_hmac(
            'sha256',
            token.encode(),
            self.salt,
            100000
        ).hex()

    def generate_token(self):
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)

        self.config["token_hash"] = token_hash
        self.config["expiry"] = (datetime.now() + timedelta(hours=24)).isoformat()
        self.config["failed_attempts"] = 0
        self.config["lockout_until"] = None

        self._save_config()
        return token

    def validate_token(self, provided_token):
        if self.config["lockout_until"]:
            lockout_time = datetime.fromisoformat(self.config["lockout_until"])
            if datetime.now() < lockout_time:
                return False, "System is locked due to too many failed attempts"

        if not self.config["token_hash"] or not self.config["expiry"]:
            return False, "No valid token configured"

        expiry_time = datetime.fromisoformat(self.config["expiry"])
        if datetime.now() > expiry_time:
            return False, "Token has expired"

        try:
            provided_hash = self._hash_token(provided_token)
            if not hmac.compare_digest(
                provided_hash.encode(),
                self.config["token_hash"].encode()
            ):
                self._handle_failed_attempt()
                return False, "Invalid token"

            self.config["failed_attempts"] = 0
            self._save_config()
            return True, "Token validated successfully"

        except Exception as e:
            return False, f"Token validation error: {str(e)}"

    def _handle_failed_attempt(self):
        self.config["failed_attempts"] += 1
        if self.config["failed_attempts"] >= self.config["max_failed_attempts"]:
            self.config["lockout_until"] = (
                datetime.now() + timedelta(minutes=30)
            ).isoformat()
            self.config["failed_attempts"] = 0
        self._save_config()