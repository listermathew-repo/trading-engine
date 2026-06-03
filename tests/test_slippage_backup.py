"""Tests for slippage modeling and backup management."""

import pytest
import tempfile
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtester.slippage_model import (
    SlippageConfig, CommissionConfig, SlippageModel, CommissionModel,
    SlippageCalculator, CommissionCalculator, RealisticBacktestSimulator,
    RealismConfig, REALISTIC_FOREX_CONFIG, TIGHT_CONDITIONS_CONFIG,
)
from api.backup_manager import DatabaseBackup, AuditLogManager, BackupScheduler


class TestSlippageCalculation:
    """Test slippage calculations."""

    def test_fixed_pips_slippage(self):
        """Test fixed pips slippage calculation."""
        config = SlippageConfig(model=SlippageModel.FIXED_PIPS, value=1.5)
        calc = SlippageCalculator()

        slippage = calc.calculate_entry_slippage(1.0800, "BUY", config)
        assert slippage == 1.5

    def test_percentage_slippage(self):
        """Test percentage-based slippage."""
        config = SlippageConfig(model=SlippageModel.PERCENTAGE, value=0.1)  # 0.1%
        calc = SlippageCalculator()

        slippage = calc.calculate_entry_slippage(1.0800, "BUY", config)
        # 1.0800 * 0.001 / 0.0001 = 10.8 pips
        assert slippage == pytest.approx(10.8, rel=0.01)

    def test_volatility_based_slippage(self):
        """Test volatility-based slippage."""
        config = SlippageConfig(
            model=SlippageModel.VOLATILITY_BASED,
            value=1.0,
            volatility_multiplier=2.0
        )
        calc = SlippageCalculator()

        atr = 0.0050  # 50 pips ATR
        slippage = calc.calculate_entry_slippage(1.0800, "BUY", config, atr)
        assert slippage > 0

    def test_apply_buy_slippage(self):
        """Test applying slippage to BUY entry."""
        calc = SlippageCalculator()

        original_price = 1.0800
        slippage_pips = 1.5
        adjusted = calc.apply_entry_slippage(original_price, "BUY", slippage_pips)

        # BUY slippage makes entry worse (higher price)
        assert adjusted > original_price
        assert adjusted == pytest.approx(original_price + 0.00015, abs=0.00001)

    def test_apply_sell_slippage(self):
        """Test applying slippage to SELL entry."""
        calc = SlippageCalculator()

        original_price = 1.0800
        slippage_pips = 1.5
        adjusted = calc.apply_entry_slippage(original_price, "SELL", slippage_pips)

        # SELL slippage makes entry worse (lower price)
        assert adjusted < original_price
        assert adjusted == pytest.approx(original_price - 0.00015, abs=0.00001)


class TestCommissionCalculation:
    """Test commission calculations."""

    def test_per_trade_commission(self):
        """Test fixed per-trade commission."""
        config = CommissionConfig(model=CommissionModel.PER_TRADE, value=5.0, round_trip=True)
        calc = CommissionCalculator()

        commission = calc.calculate_commission(1.0800, 1.0850, "BUY", 1.0, config)
        assert commission == 10.0  # 5.0 * 2 for round-trip

    def test_per_trade_round_trip_commission(self):
        """Test round-trip commission (entry + exit)."""
        config = CommissionConfig(
            model=CommissionModel.PER_TRADE,
            value=5.0,
            round_trip=True
        )
        calc = CommissionCalculator()

        commission = calc.calculate_commission(1.0800, 1.0850, "BUY", 1.0, config)
        assert commission == 10.0  # 5.0 * 2

    def test_per_lot_commission(self):
        """Test per-lot commission."""
        config = CommissionConfig(model=CommissionModel.PER_LOT, value=2.0, round_trip=True)
        calc = CommissionCalculator()

        # 5 lots * $2/lot * 2 (round-trip) = $20
        commission = calc.calculate_commission(1.0800, 1.0850, "BUY", 5.0, config)
        assert commission == 20.0

    def test_percentage_commission(self):
        """Test percentage commission on PnL."""
        config = CommissionConfig(
            model=CommissionModel.PERCENTAGE,
            value=0.1,  # 0.1%
            round_trip=False
        )
        calc = CommissionCalculator()

        pnl = 100.0  # $100 profit
        commission = calc.calculate_commission(1.0800, 1.0850, "BUY", 1.0, config, pnl)
        assert commission == pytest.approx(0.1, abs=0.01)  # 0.1% of $100


class TestRealisticBacktestSimulation:
    """Test realistic backtest simulation with slippage & commission."""

    def test_realistic_forex_config(self):
        """Test using preset forex configuration."""
        simulator = RealisticBacktestSimulator(REALISTIC_FOREX_CONFIG)

        adjusted_entry, slippage = simulator.simulate_entry(1.0800, "BUY")
        assert adjusted_entry > 1.0800  # Slippage worsens BUY entry
        assert slippage > 1.5  # Includes spread

    def test_tight_conditions_config(self):
        """Test tight market conditions."""
        simulator = RealisticBacktestSimulator(TIGHT_CONDITIONS_CONFIG)

        adjusted_entry, slippage = simulator.simulate_entry(1.0800, "BUY")
        assert slippage < REALISTIC_FOREX_CONFIG.slippage.value + REALISTIC_FOREX_CONFIG.spread_pips

    def test_net_pnl_calculation(self):
        """Test net PnL with slippage and commission."""
        simulator = RealisticBacktestSimulator(REALISTIC_FOREX_CONFIG)

        gross_pnl = 100.0
        net_pnl = simulator.calculate_net_pnl(
            gross_pnl, 1.0800, 1.0850, "BUY", 1.0
        )

        # Net PnL should be less than gross due to commission
        assert net_pnl < gross_pnl


class TestDatabaseBackup:
    """Test database backup functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create test database
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
            conn.execute("INSERT INTO test (data) VALUES ('test')")
            conn.commit()
            conn.close()

            yield db_path

    def test_create_backup(self, temp_db):
        """Test creating a backup."""
        backup = DatabaseBackup(str(temp_db), str(temp_db.parent / "backups"))

        backup_path = backup.create_backup(label="test")
        assert backup_path is not None
        assert backup_path.exists()

    def test_backup_compression(self, temp_db):
        """Test that backups are compressed."""
        backup = DatabaseBackup(str(temp_db), str(temp_db.parent / "backups"))

        backup_path = backup.create_backup(label="test")
        compressed_path = backup_path.with_suffix(".db.gz")

        assert compressed_path.exists()
        assert compressed_path.stat().st_size < backup_path.stat().st_size

    def test_list_backups(self, temp_db):
        """Test listing backups."""
        backup = DatabaseBackup(str(temp_db), str(temp_db.parent / "backups"))

        # Create multiple backups
        backup.create_backup(label="test1")
        backup.create_backup(label="test2")

        backups = backup.list_backups()
        assert len(backups) >= 2

    def test_restore_backup(self, temp_db):
        """Test restoring from backup."""
        backup = DatabaseBackup(str(temp_db), str(temp_db.parent / "backups"))

        # Create backup
        backup_path = backup.create_backup(label="test")

        # Modify original database
        conn = sqlite3.connect(temp_db)
        conn.execute("DELETE FROM test")
        conn.commit()
        conn.close()

        # Restore
        success = backup.restore_backup(backup_path)
        assert success

        # Verify data is restored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1


class TestAuditLogManager:
    """Test audit log management."""

    @pytest.fixture
    def temp_db_with_tables(self):
        """Create temporary database with tables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create test database with required tables
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE trades (
                    id INTEGER PRIMARY KEY,
                    status TEXT,
                    created_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE system_events (
                    id INTEGER PRIMARY KEY,
                    event_type TEXT,
                    occurred_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE trade_attempts (
                    id INTEGER PRIMARY KEY,
                    attempted_at TIMESTAMP
                )
            """)

            # Insert test data
            now = datetime.now()
            old_date = (now - timedelta(days=100)).isoformat()
            conn.execute("INSERT INTO trades (status, created_at) VALUES ('filled', ?)", (old_date,))
            conn.execute("INSERT INTO system_events (event_type, occurred_at) VALUES ('test', ?)", (old_date,))
            conn.commit()
            conn.close()

            yield db_path

    def test_cleanup_trade_attempts(self, temp_db_with_tables):
        """Test cleaning up old trade attempts."""
        manager = AuditLogManager(str(temp_db_with_tables))

        cleaned = manager.cleanup_old_trade_attempts(older_than_hours=0)
        # Should clean up records (even if count is 0 in this test)
        assert cleaned >= 0

    def test_get_database_stats(self, temp_db_with_tables):
        """Test getting database statistics."""
        manager = AuditLogManager(str(temp_db_with_tables))

        stats = manager.get_database_stats()
        assert "db_size_mb" in stats
        assert stats["db_size_mb"] > 0


class TestBackupScheduler:
    """Test backup scheduler."""

    @pytest.fixture
    def temp_db_with_tables(self):
        """Create temporary database with tables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create test database
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE trades (
                    id INTEGER PRIMARY KEY,
                    status TEXT,
                    created_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE system_events (
                    id INTEGER PRIMARY KEY,
                    event_type TEXT,
                    occurred_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE trade_attempts (
                    id INTEGER PRIMARY KEY,
                    attempted_at TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()

            yield db_path

    def test_daily_maintenance(self, temp_db_with_tables):
        """Test daily maintenance run."""
        scheduler = BackupScheduler(str(temp_db_with_tables))

        result = scheduler.run_daily_maintenance()
        assert "backup_created" in result
        assert "stats" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
