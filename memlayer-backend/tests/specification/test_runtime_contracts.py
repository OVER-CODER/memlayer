"""
MemLayer Runtime Contract Verification Suite.
Validates core invariants against the v1 specification.
"""

import unittest
import json
from app.persistence.serialization import CanonicalSerializer
from app.security.authentication import AuthContext
from app.security.rbac import Role, Permission, ROLE_PERMISSIONS

class TestRuntimeContracts(unittest.TestCase):
    """Verifies architectural compliance with the v1 specification."""

    def test_canonical_serialization_stability(self):
        """Invariant: JSON serialization must be deterministic and sorted."""
        data = {"z": 100, "a": 1, "m": 50, "extra": {"foo": "bar", "abc": 123}}
        json_str = CanonicalSerializer.to_json(data)
        
        # Keys must be alphabetically sorted at all levels
        self.assertTrue(json_str.startswith('{"a":1,"extra":{"abc":123,"foo":"bar"},"m":50,"z":100}'))
        
        # Second pass must be identical
        self.assertEqual(json_str, CanonicalSerializer.to_json(data))

    def test_auth_context_immutability(self):
        """Invariant: AuthContext must be frozen to prevent identity drift."""
        auth = AuthContext(subject="agent_1", tenant_id="tenant_a", role="developer", auth_type="jwt")
        
        with self.assertRaises(Exception):
            auth.subject = "hacker_1"  # Pydantic frozen=True

    def test_rbac_permission_determinism(self):
        """Invariant: Role-permission mappings must be stable."""
        # Viewer should never have snapshot restore permission
        viewer_perms = ROLE_PERMISSIONS.get(Role.VIEWER)
        self.assertNotIn(Permission.SNAPSHOT_RESTORE, viewer_perms)
        
        # Platform Admin must have all permissions
        admin_perms = ROLE_PERMISSIONS.get(Role.PLATFORM_ADMIN)
        self.assertIn(Permission.PLATFORM_ADMIN, admin_perms)

    def test_lineage_hash_stability(self):
        """Invariant: Checksum computation must be stable across runs."""
        state = [{"id": 1, "text": "Hello"}, {"id": 2, "text": "World"}]
        h1 = CanonicalSerializer.compute_checksum(state)
        h2 = CanonicalSerializer.compute_checksum(state)
        
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64) # SHA256 length

if __name__ == "__main__":
    unittest.main()
