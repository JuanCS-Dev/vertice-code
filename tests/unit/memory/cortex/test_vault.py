"""
Unit tests for the KnowledgeVault.
"""

import pytest
from memory.cortex.vault import KnowledgeVault, VaultEntryType, SensitivityLevel


@pytest.fixture
def vault(tmp_path):
    """Provides a KnowledgeVault instance with a temporary database."""
    db_path = tmp_path / "test_vault.db"
    return KnowledgeVault(db_path, password="test_password")


def test_store_and_get_entry(vault):
    """Test storing and retrieving a vault entry."""
    vault.store(
        name="api_key",
        value="secret_key",
        entry_type=VaultEntryType.API_KEY,
        sensitivity_level=SensitivityLevel.HIGH,
    )
    entry = vault.get("api_key")
    assert entry is not None
    assert entry.name == "api_key"
    assert entry.value == "secret_key"
    assert entry.entry_type == VaultEntryType.API_KEY
    assert entry.sensitivity_level == SensitivityLevel.HIGH


def test_get_nonexistent_entry(vault):
    """Test that getting a nonexistent entry returns None."""
    entry = vault.get("nonexistent")
    assert entry is None


def test_delete_entry(vault):
    """Test deleting a vault entry."""
    vault.store("to_delete", "value", VaultEntryType.NOTE)
    assert vault.exists("to_delete")
    assert vault.delete("to_delete") is True
    assert not vault.exists("to_delete")


def test_delete_nonexistent_entry(vault):
    """Test that deleting a nonexistent entry returns False."""
    assert vault.delete("nonexistent") is False


def test_list_entries(vault):
    """Test listing vault entries."""
    vault.store("entry1", "value1", VaultEntryType.NOTE)
    vault.store("entry2", "value2", VaultEntryType.BOOKMARK)
    entries = vault.list_entries()
    assert len(entries) == 2
    assert entries[0]["name"] == "entry1"
    assert entries[1]["name"] == "entry2"
    assert entries[0]["value"] == "[REDACTED]"


def test_list_entries_with_values(vault):
    """Test listing vault entries with their values."""
    vault.store("entry1", "value1", VaultEntryType.NOTE)
    entries = vault.list_entries(include_values=True)
    assert len(entries) == 1
    assert entries[0]["value"] == "value1"


def test_list_entries_by_type(vault):
    """Test filtering vault entries by type."""
    vault.store("note1", "v1", VaultEntryType.NOTE)
    vault.store("bookmark1", "v2", VaultEntryType.BOOKMARK)
    notes = vault.list_entries(entry_type=VaultEntryType.NOTE)
    assert len(notes) == 1
    assert notes[0]["name"] == "note1"
