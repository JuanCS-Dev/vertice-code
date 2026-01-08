#!/usr/bin/env python3
"""
Disaster Recovery and Backup Automation for Vertice-Code.

Automated backup, recovery, and failover procedures for production resilience.
"""

import asyncio
import subprocess
import shutil
import time
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

from vertice_tui.core.logging import get_system_logger
from vertice_tui.core.data_protection import get_data_protection

logger = get_system_logger()


@dataclass
class BackupConfig:
    """Backup configuration."""

    name: str
    source_paths: List[str]
    destination_path: str
    schedule: str  # cron expression
    retention_days: int = 30
    compression: bool = True
    encryption: bool = True
    include_database: bool = True
    verify_integrity: bool = True


@dataclass
class BackupResult:
    """Result of backup operation."""

    success: bool
    backup_path: Optional[str] = None
    size_bytes: int = 0
    duration_seconds: float = 0.0
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class RecoveryResult:
    """Result of recovery operation."""

    success: bool
    recovered_items: int = 0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class BackupManager:
    """Automated backup management system."""

    def __init__(self, backup_root: str = "/var/backups/vertice"):
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)

        self.data_protection = get_data_protection()

        # Default backup configurations
        self.backup_configs = [
            BackupConfig(
                name="daily_full",
                source_paths=["/opt/vertice/data", "/opt/vertice/config", "/var/log/vertice"],
                destination_path=str(self.backup_root / "daily"),
                schedule="0 2 * * *",  # Daily at 2 AM
                retention_days=30,
                compression=True,
                encryption=True,
                include_database=True,
            ),
            BackupConfig(
                name="hourly_config",
                source_paths=["/opt/vertice/config"],
                destination_path=str(self.backup_root / "hourly"),
                schedule="0 * * * *",  # Hourly
                retention_days=7,
                compression=True,
                encryption=False,
                include_database=False,
            ),
        ]

    async def create_backup(self, config_name: str) -> BackupResult:
        """Create backup according to configuration."""
        start_time = time.time()

        try:
            config = next((c for c in self.backup_configs if c.name == config_name), None)
            if not config:
                raise ValueError(f"Backup configuration '{config_name}' not found")

            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{config_name}_{timestamp}"
            backup_path = Path(config.destination_path) / backup_name
            backup_path.mkdir(parents=True, exist_ok=True)

            total_size = 0
            backed_up_items = 0

            # Backup file systems
            for source_path in config.source_paths:
                source = Path(source_path)
                if source.exists():
                    dest = backup_path / source.name

                    if source.is_file():
                        await self._backup_file(source, dest, config)
                        total_size += dest.stat().st_size
                        backed_up_items += 1
                    elif source.is_dir():
                        size = await self._backup_directory(source, dest, config)
                        total_size += size
                        backed_up_items += 1

            # Backup database if configured
            if config.include_database:
                db_size = await self._backup_database(backup_path)
                total_size += db_size
                backed_up_items += 1

            # Create backup manifest
            manifest = {
                "backup_name": backup_name,
                "config_name": config_name,
                "timestamp": timestamp,
                "total_size": total_size,
                "items_count": backed_up_items,
                "compression": config.compression,
                "encryption": config.encryption,
                "source_paths": config.source_paths,
                "include_database": config.include_database,
            }

            manifest_path = backup_path / "manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)

            # Calculate checksum
            checksum = await self._calculate_checksum(backup_path)

            duration = time.time() - start_time

            # Verify integrity if requested
            if config.verify_integrity:
                await self._verify_backup_integrity(backup_path)

            result = BackupResult(
                success=True,
                backup_path=str(backup_path),
                size_bytes=total_size,
                duration_seconds=duration,
                checksum=checksum,
            )

            logger.info(f"Backup completed: {config_name} ({total_size} bytes, {duration:.2f}s)")
            return result

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Backup failed: {e}"
            logger.error(error_msg)

            return BackupResult(success=False, duration_seconds=duration, error_message=error_msg)

    async def _backup_file(self, source: Path, dest: Path, config: BackupConfig):
        """Backup single file."""
        if config.compression:
            # Compress file
            import gzip

            with open(source, "rb") as src, gzip.open(dest.with_suffix(".gz"), "wb") as dst:
                shutil.copyfileobj(src, dst)
        else:
            shutil.copy2(source, dest)

        if config.encryption:
            await self._encrypt_file(dest)

    async def _backup_directory(self, source: Path, dest: Path, config: BackupConfig) -> int:
        """Backup directory recursively."""
        total_size = 0

        if config.compression:
            # Create compressed archive
            import tarfile

            archive_path = dest.with_suffix(".tar.gz")
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(source, arcname=source.name)
            total_size = archive_path.stat().st_size

            if config.encryption:
                await self._encrypt_file(archive_path)
        else:
            # Copy directory
            shutil.copytree(source, dest, dirs_exist_ok=True)
            total_size = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())

        return total_size

    async def _backup_database(self, backup_path: Path) -> int:
        """Backup database."""
        db_backup_path = backup_path / "database.sql"

        try:
            # PostgreSQL backup (adjust for your database)
            result = await asyncio.create_subprocess_exec(
                "pg_dump",
                "-U",
                "vertice",
                "-h",
                "localhost",
                "vertice_db",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                with open(db_backup_path, "wb") as f:
                    f.write(stdout)

                # Encrypt if configured
                await self._encrypt_file(db_backup_path)

                return db_backup_path.stat().st_size
            else:
                logger.error(f"Database backup failed: {stderr.decode()}")
                return 0

        except Exception as e:
            logger.error(f"Database backup error: {e}")
            return 0

    async def _encrypt_file(self, file_path: Path):
        """Encrypt file using data protection service."""
        try:
            with open(file_path, "rb") as f:
                data = f.read()

            encrypted_data = self.data_protection.encrypt_sensitive_data(data)

            with open(file_path, "w") as f:
                f.write(encrypted_data)

        except Exception as e:
            logger.error(f"File encryption failed for {file_path}: {e}")

    async def _calculate_checksum(self, path: Path) -> str:
        """Calculate checksum for backup verification."""
        import hashlib

        hash_obj = hashlib.sha256()

        if path.is_file():
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
        else:
            # Directory checksum
            for file_path in sorted(path.rglob("*")):
                if file_path.is_file():
                    hash_obj.update(str(file_path).encode())
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_obj.update(chunk)

        return hash_obj.hexdigest()

    async def _verify_backup_integrity(self, backup_path: Path):
        """Verify backup integrity."""
        manifest_path = backup_path / "manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)

                stored_checksum = manifest.get("checksum")
                if stored_checksum:
                    current_checksum = await self._calculate_checksum(backup_path)
                    if current_checksum != stored_checksum:
                        logger.warning(f"Backup integrity check failed for {backup_path}")
                    else:
                        logger.info(f"Backup integrity verified for {backup_path}")

            except Exception as e:
                logger.error(f"Backup integrity check error: {e}")


class RecoveryManager:
    """Disaster recovery management system."""

    def __init__(self, backup_root: str = "/var/backups/vertice"):
        self.backup_root = Path(backup_root)
        self.data_protection = get_data_protection()

    async def recover_from_backup(
        self, backup_name: str, target_path: str, components: Optional[List[str]] = None
    ) -> RecoveryResult:
        """
        Recover from backup.

        Args:
            backup_name: Name of backup to recover from
            target_path: Path to recover to
            components: Specific components to recover (None = all)
        """
        start_time = time.time()

        try:
            # Find backup
            backup_path = self._find_backup(backup_name)
            if not backup_path:
                raise FileNotFoundError(f"Backup '{backup_name}' not found")

            # Read manifest
            manifest_path = backup_path / "manifest.json"
            if not manifest_path.exists():
                raise FileNotFoundError(f"Backup manifest not found: {manifest_path}")

            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            target = Path(target_path)
            target.mkdir(parents=True, exist_ok=True)

            recovered_items = 0

            # Recover file systems
            for source_name in manifest.get("source_paths", []):
                if components and source_name not in components:
                    continue

                source_path = Path(source_name)
                backup_item_path = backup_path / source_path.name

                if backup_item_path.exists():
                    await self._recover_item(backup_item_path, target / source_path.name, manifest)
                    recovered_items += 1

            # Recover database if requested
            if manifest.get("include_database") and (not components or "database" in components):
                db_backup = backup_path / "database.sql"
                if db_backup.exists():
                    await self._recover_database(db_backup, manifest)
                    recovered_items += 1

            duration = time.time() - start_time

            result = RecoveryResult(
                success=True, recovered_items=recovered_items, duration_seconds=duration
            )

            logger.info(f"Recovery completed: {recovered_items} items in {duration:.2f}s")
            return result

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Recovery failed: {e}"
            logger.error(error_msg)

            return RecoveryResult(success=False, duration_seconds=duration, error_message=error_msg)

    def _find_backup(self, backup_name: str) -> Optional[Path]:
        """Find backup by name."""
        for backup_dir in self.backup_root.rglob("*"):
            if backup_dir.is_dir() and backup_dir.name == backup_name:
                return backup_dir
        return None

    async def _recover_item(self, backup_path: Path, target_path: Path, manifest: Dict[str, Any]):
        """Recover single item."""
        try:
            if manifest.get("encryption"):
                # Decrypt file first
                with open(backup_path, "r") as f:
                    encrypted_data = f.read()

                decrypted_data = self.data_protection.decrypt_sensitive_data(encrypted_data)

                # Write decrypted data
                if manifest.get("compression") and backup_path.suffix == ".gz":
                    import gzip

                    with gzip.open(target_path, "wb") as f:
                        f.write(decrypted_data)
                else:
                    with open(target_path, "wb") as f:
                        f.write(decrypted_data)
            else:
                # Direct copy
                if manifest.get("compression") and backup_path.suffix == ".tar.gz":
                    import tarfile

                    with tarfile.open(backup_path, "r:gz") as tar:
                        tar.extractall(target_path.parent)
                else:
                    if backup_path.is_file():
                        shutil.copy2(backup_path, target_path)
                    else:
                        shutil.copytree(backup_path, target_path, dirs_exist_ok=True)

            logger.debug(f"Recovered item: {backup_path} -> {target_path}")

        except Exception as e:
            logger.error(f"Failed to recover item {backup_path}: {e}")
            raise

    async def _recover_database(self, backup_path: Path, manifest: Dict[str, Any]):
        """Recover database from backup."""
        try:
            # Decrypt if needed
            if manifest.get("encryption"):
                with open(backup_path, "r") as f:
                    encrypted_data = f.read()
                sql_data = self.data_protection.decrypt_sensitive_data(encrypted_data)
            else:
                with open(backup_path, "r") as f:
                    sql_data = f.read()

            # Restore database (adjust for your database)
            process = await asyncio.create_subprocess_exec(
                "psql",
                "-U",
                "vertice",
                "-h",
                "localhost",
                "-d",
                "vertice_db",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate(sql_data.encode())

            if process.returncode != 0:
                raise RuntimeError(f"Database restore failed: {stderr.decode()}")

            logger.info("Database recovery completed")

        except Exception as e:
            logger.error(f"Database recovery failed: {e}")
            raise

    def list_available_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        backups = []

        for backup_dir in self.backup_root.rglob("*"):
            if backup_dir.is_dir():
                manifest_path = backup_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, "r") as f:
                            manifest = json.load(f)

                        backups.append(
                            {
                                "name": backup_dir.name,
                                "path": str(backup_dir),
                                "config_name": manifest.get("config_name"),
                                "timestamp": manifest.get("timestamp"),
                                "size": manifest.get("total_size", 0),
                                "items": manifest.get("items_count", 0),
                                "created": datetime.fromisoformat(
                                    manifest.get("timestamp").replace("_", "T")
                                )
                                if manifest.get("timestamp")
                                else None,
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to read backup manifest {manifest_path}: {e}")

        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.get("created") or datetime.min, reverse=True)
        return backups

    async def cleanup_old_backups(self, retention_days: int = 30):
        """Clean up backups older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        freed_space = 0

        for backup in self.list_available_backups():
            if backup.get("created") and backup["created"] < cutoff_date:
                try:
                    backup_path = Path(backup["path"])
                    size = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())

                    shutil.rmtree(backup_path)
                    deleted_count += 1
                    freed_space += size

                    logger.info(f"Cleaned up old backup: {backup['name']}")

                except Exception as e:
                    logger.error(f"Failed to cleanup backup {backup['name']}: {e}")

        logger.info(
            f"Backup cleanup completed: {deleted_count} backups removed, {freed_space} bytes freed"
        )


# Global instances
_backup_manager = BackupManager()
_recovery_manager = RecoveryManager()


def get_backup_manager() -> BackupManager:
    """Get global backup manager instance."""
    return _backup_manager


def get_recovery_manager() -> RecoveryManager:
    """Get global recovery manager instance."""
    return _recovery_manager


async def create_emergency_backup() -> BackupResult:
    """Create emergency backup for immediate disaster recovery."""
    manager = get_backup_manager()

    # Create emergency backup config
    emergency_config = BackupConfig(
        name="emergency_backup",
        source_paths=["/opt/vertice/data", "/opt/vertice/config"],
        destination_path="/var/backups/vertice/emergency",
        schedule="manual",
        retention_days=7,
        compression=True,
        encryption=True,
        include_database=True,
    )

    # Temporarily add emergency config
    manager.backup_configs.append(emergency_config)

    try:
        result = await manager.create_backup("emergency_backup")
        logger.info(
            "Emergency backup created successfully" if result.success else "Emergency backup failed"
        )
        return result
    finally:
        # Remove emergency config
        manager.backup_configs.remove(emergency_config)


async def perform_disaster_recovery(
    backup_name: str, target_path: str = "/opt/vertice/recovered"
) -> RecoveryResult:
    """Perform disaster recovery from specified backup."""
    manager = get_recovery_manager()

    logger.info(f"Starting disaster recovery from backup: {backup_name}")

    result = await manager.recover_from_backup(backup_name, target_path)

    if result.success:
        logger.info(
            f"Disaster recovery completed successfully: {result.recovered_items} items recovered"
        )
    else:
        logger.error(f"Disaster recovery failed: {result.error_message}")

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python disaster_recovery.py <command> [args...]")
        print("Commands:")
        print("  backup <config_name>          - Create backup")
        print("  emergency-backup              - Create emergency backup")
        print("  recover <backup_name> [path]  - Recover from backup")
        print("  list-backups                  - List available backups")
        print("  cleanup [days]               - Clean old backups")
        sys.exit(1)

    command = sys.argv[1]

    if command == "backup" and len(sys.argv) >= 3:
        config_name = sys.argv[2]
        result = asyncio.run(get_backup_manager().create_backup(config_name))
        print(f"Backup {'successful' if result.success else 'failed'}: {result.backup_path}")

    elif command == "emergency-backup":
        result = asyncio.run(create_emergency_backup())
        print(
            f"Emergency backup {'successful' if result.success else 'failed'}: {result.backup_path}"
        )

    elif command == "recover" and len(sys.argv) >= 3:
        backup_name = sys.argv[2]
        target_path = sys.argv[3] if len(sys.argv) > 3 else "/opt/vertice/recovered"
        result = asyncio.run(perform_disaster_recovery(backup_name, target_path))
        print(
            f"Recovery {'successful' if result.success else 'failed'}: {result.recovered_items} items"
        )

    elif command == "list-backups":
        backups = get_recovery_manager().list_available_backups()
        print(f"Available backups: {len(backups)}")
        for backup in backups[:10]:  # Show first 10
            print(f"  {backup['name']} - {backup.get('created')} - {backup['size']} bytes")

    elif command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        asyncio.run(get_recovery_manager().cleanup_old_backups(days))
        print(f"Cleaned up backups older than {days} days")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
