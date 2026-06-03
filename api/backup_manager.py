"""Database backup and audit log retention management."""

import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import gzip
import json


class DatabaseBackup:
    """Manage SQLite database backups."""

    def __init__(self, db_path: str = "trading.db", backup_dir: str = "backups"):
        self.db_path = db_path
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, label: str = None) -> Optional[Path]:
        """
        Create a backup of the database.

        Args:
            label: Optional label for the backup (default: timestamp)

        Returns:
            Path to the backup file if successful, None otherwise
        """
        if not os.path.exists(self.db_path):
            print(f"[WARN] Database not found: {self.db_path}")
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            label = label or timestamp
            backup_filename = f"trading_backup_{label}_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename

            # Copy database file
            shutil.copy2(self.db_path, backup_path)

            # Create compressed version
            compressed_path = backup_path.with_suffix(".db.gz")
            with open(backup_path, "rb") as f_in:
                with gzip.open(compressed_path, "wb") as f_out:
                    f_out.write(f_in.read())

            print(f"[OK] Database backed up: {compressed_path}")
            print(f"     Compressed size: {compressed_path.stat().st_size / 1024:.1f} KB")

            # Keep uncompressed for 24 hours, then delete
            # (keep compressed for longer)
            return backup_path

        except Exception as e:
            print(f"[ERROR] Backup failed: {e}")
            return None

    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore database from a backup.

        Args:
            backup_path: Path to backup file

        Returns:
            True if successful, False otherwise
        """
        if not backup_path.exists():
            print(f"[ERROR] Backup not found: {backup_path}")
            return False

        try:
            # Create a safety copy of current database
            if os.path.exists(self.db_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safety_path = Path(self.db_path).with_stem(f"trading_safety_{timestamp}")
                shutil.copy2(self.db_path, safety_path)
                print(f"[OK] Safety copy created: {safety_path}")

            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            print(f"[OK] Database restored from: {backup_path}")
            return True

        except Exception as e:
            print(f"[ERROR] Restore failed: {e}")
            return False

    def list_backups(self) -> list[dict]:
        """
        List all available backups.

        Returns:
            List of backup metadata dicts
        """
        backups = []

        for backup_file in sorted(self.backup_dir.glob("trading_backup_*.db*")):
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
                "size_kb": stat.st_size / 1024,
                "created": datetime.fromtimestamp(stat.st_ctime),
            })

        return sorted(backups, key=lambda x: x["created"], reverse=True)

    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """
        Delete backups older than keep_days.

        Args:
            keep_days: Keep backups newer than this many days

        Returns:
            Number of backups deleted
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0

        for backup_file in self.backup_dir.glob("trading_backup_*.db*"):
            file_time = datetime.fromtimestamp(backup_file.stat().st_ctime)
            if file_time < cutoff_date:
                try:
                    backup_file.unlink()
                    deleted_count += 1
                    print(f"[OK] Deleted old backup: {backup_file.name}")
                except Exception as e:
                    print(f"[ERROR] Failed to delete {backup_file.name}: {e}")

        return deleted_count


class AuditLogManager:
    """Manage audit log retention and archival."""

    def __init__(self, db_path: str = "trading.db", archive_dir: str = "audit_archives"):
        self.db_path = db_path
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(exist_ok=True)

    def archive_old_trades(self, older_than_days: int = 90) -> int:
        """
        Archive trades older than threshold to JSON.

        Args:
            older_than_days: Archive trades older than this many days

        Returns:
            Number of trades archived
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get cutoff date
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            cutoff_timestamp = cutoff_date.isoformat()

            # Fetch old trades
            cursor.execute(
                "SELECT * FROM trades WHERE created_at < ?",
                (cutoff_timestamp,)
            )
            old_trades = [dict(row) for row in cursor.fetchall()]

            if not old_trades:
                print(f"[INFO] No trades older than {older_than_days} days")
                return 0

            # Archive to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = self.archive_dir / f"trades_archive_{timestamp}.json"

            with open(archive_file, "w") as f:
                json.dump(old_trades, f, indent=2, default=str)

            print(f"[OK] Archived {len(old_trades)} trades to: {archive_file}")

            # Delete from database
            cursor.execute(
                "DELETE FROM trades WHERE created_at < ?",
                (cutoff_timestamp,)
            )
            conn.commit()
            conn.close()

            return len(old_trades)

        except Exception as e:
            print(f"[ERROR] Archive failed: {e}")
            return 0

    def archive_old_events(self, older_than_days: int = 180) -> int:
        """
        Archive system events older than threshold.

        Args:
            older_than_days: Archive events older than this many days

        Returns:
            Number of events archived
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get cutoff date
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            cutoff_timestamp = cutoff_date.isoformat()

            # Fetch old events
            cursor.execute(
                "SELECT * FROM system_events WHERE occurred_at < ?",
                (cutoff_timestamp,)
            )
            old_events = [dict(row) for row in cursor.fetchall()]

            if not old_events:
                print(f"[INFO] No events older than {older_than_days} days")
                return 0

            # Archive to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = self.archive_dir / f"events_archive_{timestamp}.json"

            with open(archive_file, "w") as f:
                json.dump(old_events, f, indent=2, default=str)

            print(f"[OK] Archived {len(old_events)} events to: {archive_file}")

            # Delete from database
            cursor.execute(
                "DELETE FROM system_events WHERE occurred_at < ?",
                (cutoff_timestamp,)
            )
            conn.commit()
            conn.close()

            return len(old_events)

        except Exception as e:
            print(f"[ERROR] Archive failed: {e}")
            return 0

    def cleanup_old_trade_attempts(self, older_than_hours: int = 24) -> int:
        """
        Clean up old trade attempt records.

        Args:
            older_than_hours: Delete attempts older than this many hours

        Returns:
            Number of records deleted
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get cutoff timestamp
            cutoff_date = datetime.now() - timedelta(hours=older_than_hours)
            cutoff_timestamp = cutoff_date.isoformat()

            # Delete old attempts
            cursor.execute(
                "DELETE FROM trade_attempts WHERE attempted_at < ?",
                (cutoff_timestamp,)
            )
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted_count > 0:
                print(f"[OK] Cleaned up {deleted_count} old trade attempts")

            return deleted_count

        except Exception as e:
            print(f"[ERROR] Cleanup failed: {e}")
            return 0

    def get_database_stats(self) -> dict:
        """
        Get database statistics.

        Returns:
            Dictionary with table row counts and database size
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            stats = {
                "total_trades": 0,
                "total_pending": 0,
                "total_filled": 0,
                "total_events": 0,
                "db_size_mb": os.path.getsize(self.db_path) / (1024 * 1024),
            }

            # Get trade counts
            cursor.execute("SELECT status, COUNT(*) FROM trades GROUP BY status")
            for status, count in cursor.fetchall():
                if status == "filled":
                    stats["total_filled"] = count
                elif status == "pending":
                    stats["total_pending"] = count
                stats["total_trades"] += count

            # Get event count
            cursor.execute("SELECT COUNT(*) FROM system_events")
            stats["total_events"] = cursor.fetchone()[0]

            conn.close()
            return stats

        except Exception as e:
            print(f"[ERROR] Failed to get stats: {e}")
            return {}


class BackupScheduler:
    """Schedule automated backups and archival."""

    def __init__(self, db_path: str = "trading.db"):
        self.backup = DatabaseBackup(db_path)
        self.audit = AuditLogManager(db_path)

    def run_daily_maintenance(self) -> dict:
        """
        Run daily maintenance tasks:
        - Create database backup
        - Clean up old trade attempts
        - Generate stats

        Returns:
            Dictionary with maintenance results
        """
        print("\n[INFO] Running daily maintenance...")
        print("=" * 70)

        backup_path = self.backup.create_backup(label="daily")
        trade_attempts_cleaned = self.audit.cleanup_old_trade_attempts(older_than_hours=24)
        stats = self.audit.get_database_stats()

        print("\n[INFO] Database Statistics:")
        print(f"       Total Trades: {stats.get('total_trades', 0)}")
        print(f"       Pending: {stats.get('total_pending', 0)} | Filled: {stats.get('total_filled', 0)}")
        print(f"       System Events: {stats.get('total_events', 0)}")
        print(f"       Database Size: {stats.get('db_size_mb', 0):.1f} MB")
        print(f"       Trade Attempts Cleaned: {trade_attempts_cleaned}")
        print("=" * 70 + "\n")

        return {
            "backup_created": backup_path is not None,
            "backup_path": str(backup_path) if backup_path else None,
            "trade_attempts_cleaned": trade_attempts_cleaned,
            "stats": stats,
        }

    def run_monthly_maintenance(self) -> dict:
        """
        Run monthly maintenance tasks:
        - Archive trades older than 90 days
        - Archive events older than 180 days
        - Clean up old backups (keep 30 days)
        - Create full backup

        Returns:
            Dictionary with maintenance results
        """
        print("\n[INFO] Running monthly maintenance...")
        print("=" * 70)

        trades_archived = self.audit.archive_old_trades(older_than_days=90)
        events_archived = self.audit.archive_old_events(older_than_days=180)
        backups_deleted = self.backup.cleanup_old_backups(keep_days=30)
        backup_path = self.backup.create_backup(label="monthly")

        print(f"\n[OK] Monthly Maintenance Complete:")
        print(f"     Trades Archived: {trades_archived}")
        print(f"     Events Archived: {events_archived}")
        print(f"     Old Backups Deleted: {backups_deleted}")
        print(f"     Backup Created: {backup_path is not None}")
        print("=" * 70 + "\n")

        return {
            "trades_archived": trades_archived,
            "events_archived": events_archived,
            "backups_deleted": backups_deleted,
            "backup_created": backup_path is not None,
            "backup_path": str(backup_path) if backup_path else None,
        }
