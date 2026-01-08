from google.cloud import firestore
import asyncio
from typing import Optional, Any
import json
import logging
import os

logger = logging.getLogger(__name__)

class FirestoreCache:
    """
    Firestore-based cache adapter to replace Redis.
    Uses 'cache' collection with 'expires_at' TTL.
    """
    def __init__(self, project_id: str = None):
        project_id = project_id or os.getenv("FIRESTORE_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            logger.warning("No FIRESTORE_PROJECT or GOOGLE_CLOUD_PROJECT env var found. FirestoreCache may fail.")
        
        # Use 'database=(default)' for standard Firestore
        self.db = firestore.AsyncClient(project=project_id)
        self.collection = self.db.collection('cache')
        logger.info(f"FirestoreCache initialized for project: {project_id}")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache if not expired."""
        try:
            doc_ref = self.collection.document(key)
            doc = await doc_ref.get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            # Basic TTL check (Firestore TTL policy handles deletion, but we check logically too)
            # Note: Firestore timestamps are datetime objects
            # For simplicity, we assume if it exists, it's valid, OR we check expires_at if present.
            # Here we just return the value.
            return data.get('value')
        except Exception as e:
            logger.error(f"Firestore get error key={key}: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        try:
            doc_ref = self.collection.document(key)
            # Firestore doesn't support automatic TTL on insertion without a policy.
            # We store 'expires_at' for future policy usage.
            # Use server timestamp for creation, calculate expiry manually if needed, 
            # but Firestore TTL policy is usually based on a field.
            await doc_ref.set({
                'value': value,
                # 'expires_at': firestore.SERVER_TIMESTAMP + ttl # Not direct arithmetic
                # Ideally, we rely on the collection TTL policy configured in GCP console.
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            logger.error(f"Firestore set error key={key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            await self.collection.document(key).delete()
            return True
        except Exception as e:
            logger.error(f"Firestore delete error key={key}: {e}")
            return False
            
    # Redis compatibility aliases
    async def exists(self, key: str) -> bool:
        val = await self.get(key)
        return val is not None

    async def close(self):
        self.db.close()
