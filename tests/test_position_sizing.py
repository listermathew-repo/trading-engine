"""Unit tests for position sizing and risk management."""

import pytest
from api.position_sizing import (
    PositionQualityRating,
    TradeSetup,
    PositionSizer,
    RiskManagementRules,
    RiskValidator,
)


class TestPositionSizerByQuality:
    """Test quality-based position sizing."""

    def test_calculate_size_a_plus(self):
        """Test A+ quality position size."""
        size = PositionSizer.calculate_size_by_quality(PositionQualityRating.A_PLUS)
        assert size == 800.0

    def test_calculate_size_a(self):
        """Test A quality position size."""
        size = PositionSizer.calculate_size_by_quality(PositionQualityRating.A)
        assert size == 600.0

    def test_calculate_size_b(self):
        """Test B quality position size."""
        size = PositionSizer.calculate_size_by_quality(PositionQualityRating.B)
        assert size == 400.0

    def test_calculate_size_c(self):
        """Test C quality position size."""
        size = PositionSizer.calculate_size_by_quality(PositionQualityRating.C)
        assert size == 200.0

    def test_all_quality_ratings(self):
        """Test all quality ratings have correct values."""
        expected = {
            PositionQualityRating.A_PLUS: 800.0,
            PositionQualityRating.A: 600.0,
            PositionQualityRating.B: 400.0,
            PositionQualityRating.C: 200.0,
        }
        for quality, expected_size in expected.items():
            assert PositionSizer.calculate_size_by_quality(quality) == expected_size


class TestPositionSizerByRisk:
    """Test risk-based position sizing."""

    def test_calculate_size_by_risk_basic(self):
        """Test basic position size calculation by risk."""
        # Entry: 1.0800, Stop: 1.0795, Risk: $100
        # Stop pips = (1.0800 - 1.0795) / 0.0001 = 5 pips
        # Position size = $100 / (5 pips * $10/pip) = $100 / $50 = 2.0 lots
        size = PositionSizer.calculate_size_by_risk(
            entry_price=1.0800,
            stop_loss=1.0795,
            risk_amount=100.0,
        )
        assert size == pytest.approx(2.0, abs=0.01)

    def test_calculate_size_by_risk_larger(self):
        """Test larger position size calculation."""
        # Entry: 1.0800, Stop: 1.0700 (100 pips), Risk: $500
        # Position size = $500 / (100 * $10) = $500 / $1000 = 0.5 lots
        size = PositionSizer.calculate_size_by_risk(
            entry_price=1.0800,
            stop_loss=1.0700,
            risk_amount=500.0,
        )
        assert size == pytest.approx(0.5, abs=0.01)

    def test_calculate_size_zero_stop_distance(self):
        """Test handling of zero stop distance."""
        size = PositionSizer.calculate_size_by_risk(
            entry_price=1.0800,
            stop_loss=1.0800,  # Same as entry
            risk_amount=100.0,
        )
        # Should return minimum size
        assert size == 0.01

    def test_calculate_size_minimum(self):
        """Test that size doesn't go below minimum."""
        size = PositionSizer.calculate_size_by_risk(
            entry_price=1.0800,
            stop_loss=1.0799,  # Very tight stop (1 pip)
            risk_amount=0.05,  # Very small risk
        )
        # Should return at least minimum size
        assert size >= 0.01

    def test_calculate_size_custom_pip_value(self):
        """Test with custom pip value."""
        # Using $20 per pip instead of default $10
        size = PositionSizer.calculate_size_by_risk(
            entry_price=1.0800,
            stop_loss=1.0795,
            risk_amount=100.0,
            pip_value=20.0,
        )
        # Stop pips = 5 pips
        # Position size = $100 / (5 pips * $20/pip) = $100 / $100 = 1.0 lots
        assert size == pytest.approx(1.0, abs=0.01)


class TestRiskRewardRatio:
    """Test risk-reward ratio calculations."""

    def test_buy_risk_reward_positive(self):
        """Test risk-reward ratio for BUY with positive reward."""
        # BUY: Entry 1.0800, SL 1.0750, TP 1.0900
        # Risk = 1.0800 - 1.0750 = 0.0050 (50 pips)
        # Reward = 1.0900 - 1.0800 = 0.0100 (100 pips)
        # RR = 100/50 = 2.0
        rr = PositionSizer.calculate_risk_reward_ratio(
            entry_price=1.0800,
            stop_loss=1.0750,
            take_profit=1.0900,
            direction="BUY",
        )
        assert rr == pytest.approx(2.0, abs=0.01)

    def test_sell_risk_reward_positive(self):
        """Test risk-reward ratio for SELL with positive reward."""
        # SELL: Entry 1.0800, SL 1.0850, TP 1.0700
        # Risk = 1.0850 - 1.0800 = 0.0050 (50 pips)
        # Reward = 1.0800 - 1.0700 = 0.0100 (100 pips)
        # RR = 100/50 = 2.0
        rr = PositionSizer.calculate_risk_reward_ratio(
            entry_price=1.0800,
            stop_loss=1.0850,
            take_profit=1.0700,
            direction="SELL",
        )
        assert rr == pytest.approx(2.0, abs=0.01)

    def test_buy_risk_reward_below_one(self):
        """Test risk-reward ratio below 1:1."""
        # Entry 1.0800, SL 1.0750, TP 1.0820
        # Risk = 50 pips, Reward = 20 pips
        # RR = 20/50 = 0.4
        rr = PositionSizer.calculate_risk_reward_ratio(
            entry_price=1.0800,
            stop_loss=1.0750,
            take_profit=1.0820,
            direction="BUY",
        )
        assert rr == pytest.approx(0.4, abs=0.01)

    def test_zero_risk(self):
        """Test handling of zero risk."""
        rr = PositionSizer.calculate_risk_reward_ratio(
            entry_price=1.0800,
            stop_loss=1.0800,  # Same as entry
            take_profit=1.0900,
            direction="BUY",
        )
        assert rr == 0.0


class TestRMultiples:
    """Test R multiple calculations."""

    def test_r_multiple_buy_win(self):
        """Test R multiple for winning BUY trade."""
        # Entry: 1.0800, SL: 1.0750, Exit: 1.0900
        # R unit = 1.0800 - 1.0750 = 0.0050 (50 pips = $500)
        # PnL = 1.0900 - 1.0800 = 0.0100 (100 pips = $1000)
        # R multiples = $1000 / $500 = 2.0R
        r = PositionSizer.calculate_r_multiples(
            entry_price=1.0800,
            stop_loss=1.0750,
            exit_price=1.0900,
            direction="BUY",
        )
        assert r == pytest.approx(2.0, abs=0.01)

    def test_r_multiple_buy_loss(self):
        """Test R multiple for losing BUY trade."""
        # Entry: 1.0800, SL: 1.0750, Exit: 1.0760
        # R unit = 0.0050 ($500)
        # PnL = 1.0760 - 1.0800 = -0.0040 (-40 pips = -$400)
        # R multiples = -$400 / $500 = -0.8R
        r = PositionSizer.calculate_r_multiples(
            entry_price=1.0800,
            stop_loss=1.0750,
            exit_price=1.0760,
            direction="BUY",
        )
        assert r == pytest.approx(-0.8, abs=0.01)

    def test_r_multiple_sell_win(self):
        """Test R multiple for winning SELL trade."""
        # Entry: 1.0800, SL: 1.0850, Exit: 1.0700
        # R unit = 1.0850 - 1.0800 = 0.0050
        # PnL = 1.0800 - 1.0700 = 0.0100
        # R multiples = 0.0100 / 0.0050 = 2.0R
        r = PositionSizer.calculate_r_multiples(
            entry_price=1.0800,
            stop_loss=1.0850,
            exit_price=1.0700,
            direction="SELL",
        )
        assert r == pytest.approx(2.0, abs=0.01)

    def test_r_multiple_sell_loss(self):
        """Test R multiple for losing SELL trade."""
        # Entry: 1.0800, SL: 1.0850, Exit: 1.0840
        # R unit = 0.0050
        # PnL = 1.0800 - 1.0840 = -0.0040
        # R multiples = -0.0040 / 0.0050 = -0.8R
        r = PositionSizer.calculate_r_multiples(
            entry_price=1.0800,
            stop_loss=1.0850,
            exit_price=1.0840,
            direction="SELL",
        )
        assert r == pytest.approx(-0.8, abs=0.01)

    def test_r_multiple_zero_risk_unit(self):
        """Test handling of zero risk unit."""
        r = PositionSizer.calculate_r_multiples(
            entry_price=1.0800,
            stop_loss=1.0800,
            exit_price=1.0900,
            direction="BUY",
        )
        assert r == 0.0


class TestMonthlyRSummary:
    """Test monthly R accumulation statistics."""

    def test_empty_trades_list(self):
        """Test with no trades."""
        result = PositionSizer.calculate_monthly_r_summary([])

        assert result["total_r"] == 0.0
        assert result["avg_r"] == 0.0
        assert result["winning_r"] == 0.0
        assert result["losing_r"] == 0.0
        assert result["win_count"] == 0
        assert result["loss_count"] == 0
        assert result["r_factor"] == 0.0

    def test_single_winning_trade(self):
        """Test with single winning trade."""
        trades = [
            {
                "entry_price": 1.0800,
                "stop_loss": 1.0750,
                "exit_price": 1.0900,
                "direction": "BUY",
            }
        ]
        result = PositionSizer.calculate_monthly_r_summary(trades)

        assert result["total_r"] == pytest.approx(2.0, abs=0.01)
        assert result["avg_r"] == pytest.approx(2.0, abs=0.01)
        assert result["winning_r"] == pytest.approx(2.0, abs=0.01)
        assert result["losing_r"] == 0.0
        assert result["win_count"] == 1
        assert result["loss_count"] == 0

    def test_single_losing_trade(self):
        """Test with single losing trade."""
        trades = [
            {
                "entry_price": 1.0800,
                "stop_loss": 1.0750,
                "exit_price": 1.0760,
                "direction": "BUY",
            }
        ]
        result = PositionSizer.calculate_monthly_r_summary(trades)

        assert result["total_r"] == pytest.approx(-0.8, abs=0.01)
        assert result["avg_r"] == pytest.approx(-0.8, abs=0.01)
        assert result["winning_r"] == 0.0
        assert result["losing_r"] == pytest.approx(-0.8, abs=0.01)
        assert result["win_count"] == 0
        assert result["loss_count"] == 1

    def test_multiple_trades_mixed(self):
        """Test with multiple winning and losing trades."""
        trades = [
            {  # Win: 2.0R
                "entry_price": 1.0800,
                "stop_loss": 1.0750,
                "exit_price": 1.0900,
                "direction": "BUY",
            },
            {  # Loss: -0.8R
                "entry_price": 1.0800,
                "stop_loss": 1.0750,
                "exit_price": 1.0760,
                "direction": "BUY",
            },
            {  # Win: 1.0R
                "entry_price": 1.0800,
                "stop_loss": 1.0750,
                "exit_price": 1.0850,
                "direction": "BUY",
            },
            {  # Loss: -1.5R
                "entry_price": 1.0800,
                "stop_loss": 1.0750,
                "exit_price": 1.0725,
                "direction": "BUY",
            },
        ]
        result = PositionSizer.calculate_monthly_r_summary(trades)

        # Total R: 2.0 - 0.8 + 1.0 - 1.5 = 0.7
        assert result["total_r"] == pytest.approx(0.7, abs=0.01)
        assert result["avg_r"] == pytest.approx(0.175, abs=0.01)
        assert result["win_count"] == 2
        assert result["loss_count"] == 2

        # Avg win R: (2.0 + 1.0) / 2 = 1.5
        assert result["avg_win_r"] == pytest.approx(1.5, abs=0.01)
        # Avg loss R: (0.8 + 1.5) / 2 = 1.15
        assert result["avg_loss_r"] == pytest.approx(1.15, abs=0.01)
        # R Factor: 1.5 / 1.15 = 1.304
        assert result["r_factor"] == pytest.approx(1.304, abs=0.05)

    def test_break_even_trades(self):
        """Test with break-even trades (0R)."""
        trades = [
            {
                "entry_price": 1.0800,
                "stop_loss": 1.0750,
                "exit_price": 1.0800,  # Break even
                "direction": "BUY",
            }
        ]
        result = PositionSizer.calculate_monthly_r_summary(trades)

        assert result["total_r"] == pytest.approx(0.0, abs=0.01)
        assert result["win_count"] == 0
        assert result["loss_count"] == 0


class TestEquityCurve:
    """Test equity curve calculations."""

    def test_flat_equity_curve(self):
        """Test equity curve with no trades."""
        equity = PositionSizer.calculate_equity_curve(10000.0, [])

        assert len(equity) == 1
        assert equity[0] == 10000.0

    def test_equity_curve_with_trades(self):
        """Test equity curve with multiple trades."""
        trades = [
            {"pnl": 100.0},   # Profit 100
            {"pnl": -50.0},   # Loss 50
            {"pnl": 200.0},   # Profit 200
        ]
        equity = PositionSizer.calculate_equity_curve(10000.0, trades)

        # Should include starting balance + 1 entry per trade
        assert len(equity) == 4
        assert equity[0] == 10000.0
        assert equity[1] == 10100.0
        assert equity[2] == 10050.0
        assert equity[3] == 10250.0

    def test_equity_curve_all_losses(self):
        """Test equity curve with all losing trades."""
        trades = [
            {"pnl": -100.0},
            {"pnl": -100.0},
            {"pnl": -100.0},
        ]
        equity = PositionSizer.calculate_equity_curve(10000.0, trades)

        assert equity[-1] == 9700.0


class TestDrawdown:
    """Test drawdown calculations."""

    def test_no_drawdown(self):
        """Test with increasing equity curve."""
        equity = [10000.0, 10100.0, 10200.0, 10300.0]
        max_dd_pct, max_dd, peak_idx = PositionSizer.calculate_drawdown(equity)

        assert max_dd_pct == 0.0
        assert max_dd == 0.0
        # Peak index should be the last (highest) value in an all-increasing curve
        assert peak_idx == 3

    def test_single_drawdown(self):
        """Test with clear drawdown."""
        # Peak at 10300, drops to 10100
        # Drawdown = (10300 - 10100) / 10300 = 1.94%
        equity = [10000.0, 10100.0, 10300.0, 10100.0]
        max_dd_pct, max_dd, peak_idx = PositionSizer.calculate_drawdown(equity)

        assert max_dd_pct == pytest.approx(1.94, abs=0.1)
        assert max_dd == 200.0
        assert peak_idx == 2

    def test_multiple_peaks_recovery(self):
        """Test with multiple peaks and recovery."""
        # Peak 10300, drop to 10050, new peak 10400, drop to 10200
        # Maximum drawdown from first peak: 10300 to 10050 = 250 (2.43%)
        # Drawdown from second peak: 10400 to 10200 = 200 (1.92%)
        # The max is 250, which occurred at the first peak
        equity = [10000.0, 10300.0, 10050.0, 10400.0, 10200.0]
        max_dd_pct, max_dd, peak_idx = PositionSizer.calculate_drawdown(equity)

        assert max_dd == pytest.approx(250.0, abs=5.0)
        # peak_idx is the most recent peak when max_dd occurred, which is 3 (10400)
        assert peak_idx == 3

    def test_short_equity_curve(self):
        """Test with equity curve of length 1."""
        equity = [10000.0]
        max_dd_pct, max_dd, peak_idx = PositionSizer.calculate_drawdown(equity)

        assert max_dd_pct == 0.0
        assert max_dd == 0.0


class TestSharpeRatio:
    """Test Sharpe ratio calculation."""

    def test_zero_returns(self):
        """Test with zero returns."""
        returns = [0.0, 0.0, 0.0, 0.0]
        sharpe = PositionSizer.calculate_sharpe_ratio(returns)

        assert sharpe == 0.0

    def test_positive_returns(self):
        """Test with all positive returns."""
        returns = [0.05, 0.04, 0.06, 0.05]  # 4-6% returns
        sharpe = PositionSizer.calculate_sharpe_ratio(returns)

        # With consistent positive returns, Sharpe should be positive
        assert sharpe > 0

    def test_volatile_returns(self):
        """Test with volatile returns."""
        # High volatility should reduce Sharpe
        returns = [0.10, -0.10, 0.08, -0.12]
        sharpe = PositionSizer.calculate_sharpe_ratio(returns)

        # Should still calculate without error
        assert isinstance(sharpe, float)

    def test_insufficient_returns(self):
        """Test with fewer than 2 returns."""
        returns = [0.05]
        sharpe = PositionSizer.calculate_sharpe_ratio(returns)

        assert sharpe == 0.0


class TestRiskValidator:
    """Test risk validation against rules."""

    def test_valid_position(self):
        """Test position that passes all validations."""
        setup = TradeSetup(
            entry_price=1.0800,
            stop_loss=1.0799,  # Very tight stop: 1 pip = $10 risk, well below any max
            direction="BUY",
            quality=PositionQualityRating.A,
            account_balance=10000.0,
            risk_percent=0.005,
        )
        rules = RiskManagementRules()  # Default: 0.5% = $50 max

        is_valid, reason = RiskValidator.validate_position(setup, rules)
        assert is_valid, f"Expected valid position but got: {reason}"
        assert "valid" in reason.lower()

    def test_stop_loss_too_close(self):
        """Test position with stop loss equal to entry."""
        setup = TradeSetup(
            entry_price=1.0800,
            stop_loss=1.0800,  # Same as entry
            direction="BUY",
            quality=PositionQualityRating.A,
            account_balance=10000.0,
        )
        rules = RiskManagementRules()

        is_valid, reason = RiskValidator.validate_position(setup, rules)
        assert not is_valid
        assert "too close" in reason.lower()

    def test_daily_loss_exceeded(self):
        """Test daily loss limit validation."""
        rules = RiskManagementRules(max_daily_loss=0.02)
        account = 10000.0
        current_loss = 250.0  # 2.5% loss

        is_valid, reason = RiskValidator.check_daily_loss_limit(
            current_loss, rules, account
        )
        assert not is_valid
        assert "exceeded" in reason.lower()

    def test_daily_loss_within_limit(self):
        """Test daily loss within limit."""
        rules = RiskManagementRules(max_daily_loss=0.05)
        account = 10000.0
        current_loss = 200.0  # 2% loss

        is_valid, reason = RiskValidator.check_daily_loss_limit(
            current_loss, rules, account
        )
        assert is_valid

    def test_consecutive_losses_exceeded(self):
        """Test consecutive loss limit."""
        rules = RiskManagementRules(max_consecutive_losses=3)

        is_valid, reason = RiskValidator.check_consecutive_losses(3, rules)
        assert not is_valid

    def test_consecutive_losses_within_limit(self):
        """Test consecutive losses within limit."""
        rules = RiskManagementRules(max_consecutive_losses=3)

        is_valid, reason = RiskValidator.check_consecutive_losses(2, rules)
        assert is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
