"""
Simple test for distributed system
"""

import pytest
from prometheus.distributed.skills_discovery import PeerInfo


def test_peer_info():
    """Simple test."""
    peer = PeerInfo(instance_id="test", endpoint="http://localhost:8080")
    assert peer.instance_id == "test"
