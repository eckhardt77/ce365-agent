"""
CE365 Agent - License Service
License Validation (RSA Signature)
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def validate_license(license_key: Optional[str]) -> bool:
    """
    Validate license key

    TODO: Implement RSA signature validation
    - License format: base64(rsa_signature(data))
    - Data: edition,max_users,expiry_date,customer
    - Public key verification

    Args:
        license_key: License key string

    Returns:
        True if valid, False otherwise
    """
    if not license_key:
        return False

    # TODO: Implement actual validation
    # For now: Accept any non-empty key
    logger.warning("License validation not implemented - accepting all keys")

    # Pseudo validation
    if license_key.startswith("CE365-"):
        return True

    return False


async def get_license_info(license_key: str) -> dict:
    """
    Get license information

    Returns:
        Dict with:
            - edition: str
            - max_users: int
            - expiry_date: datetime
            - customer_name: str
    """
    # TODO: Decode license key
    return {
        "edition": "pro",
        "max_users": None,  # Unlimited
        "expiry_date": None,  # No expiry
        "customer_name": "Demo Customer"
    }
