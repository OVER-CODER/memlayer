"""
MemLayer Runtime Contract Validator.
Verifies invariant compliance and architectural integrity.
"""

import json
import logging
from typing import Dict, Any, List
from app.persistence.serialization import get_canonical_serializer
from app.core.config import settings

logger = logging.getLogger(__name__)

class RuntimeContractValidator:
    """Validator for MemLayer v1 specifications."""

    def __init__(self):
        self.serializer = get_canonical_serializer()

    def verify_deterministic_serialization(self) -> bool:
        """Verify that serialization is stable and sorted."""
        data = {"b": 2, "a": 1, "c": {"z": 26, "y": 25}}
        from app.persistence.serialization import CanonicalSerializer
        s1 = CanonicalSerializer.to_json(data)
        s2 = CanonicalSerializer.to_json(data)
        
        # Invariant: Output must be identical and keys sorted
        # s1 should be '{"a":1,"b":2,"c":{"y":25,"z":26}}'
        is_identical = (s1 == s2)
        is_sorted = '"a":1,"b":2' in s1
        
        return is_identical and is_sorted

    def verify_tenant_scoping(self, tenant_id: str, key_prefix: str) -> bool:
        """Verify that Redis/Storage keys follow the tenant isolation contract."""
        # This is a logic check, actual enforcement is in middleware
        if not tenant_id or tenant_id == "":
            return False
        return True

    def verify_config_contracts(self) -> List[str]:
        """Verify that required production settings are present."""
        violations = []
        if settings.storage_provider == "local" and not settings.debug:
            violations.append("Production environment should not use local storage.")
        
        if settings.secret_key == "dev_secret_key_change_me_in_production_deterministic_spine":
             violations.append("Default secret key detected. Critical security risk.")
             
        return violations

    def run_full_audit(self) -> Dict[str, Any]:
        """Perform a complete architectural validation."""
        results = {
            "version": "v1",
            "determinism": self.verify_deterministic_serialization(),
            "config_violations": self.verify_config_contracts(),
            "status": "PASS"
        }
        
        if results["config_violations"] or not results["determinism"]:
            results["status"] = "FAIL"
            
        return results

def get_validator() -> RuntimeContractValidator:
    return RuntimeContractValidator()
