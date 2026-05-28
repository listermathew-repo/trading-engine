#!/usr/bin/env python3
"""
TradingView Webhook Testing Script
Tests the webhook endpoint with various payloads and validates responses.
"""

import requests
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime

BASE_URL = "http://localhost:3000/api/alerts"


class WebhookTester:
    """Test suite for TradingView webhook endpoint"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
        self.passed = 0
        self.failed = 0

    def send_request(self, payload: Dict[str, Any]) -> tuple[int, Dict]:
        """Send POST request and return status code and response"""
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            return response.status_code, response.json()
        except requests.RequestException as e:
            return 500, {"error": str(e)}

    def assert_status(self, actual: int, expected: int, test_name: str) -> bool:
        """Check if status code matches expected"""
        if actual == expected:
            self.log_pass(test_name, f"Status {actual} as expected")
            return True
        else:
            self.log_fail(test_name, f"Expected {expected}, got {actual}")
            return False

    def assert_field(self, obj: Dict, field: str, test_name: str) -> bool:
        """Check if field exists in response"""
        if field in obj:
            self.log_pass(test_name, f"Field '{field}' present")
            return True
        else:
            self.log_fail(test_name, f"Field '{field}' missing")
            return False

    def log_pass(self, test_name: str, details: str = ""):
        """Log successful test"""
        self.passed += 1
        self.results.append({
            "test": test_name,
            "status": "PASS",
            "details": details
        })
        print(f"  ✓ {test_name}")
        if details:
            print(f"    └─ {details}")

    def log_fail(self, test_name: str, details: str = ""):
        """Log failed test"""
        self.failed += 1
        self.results.append({
            "test": test_name,
            "status": "FAIL",
            "details": details
        })
        print(f"  ✗ {test_name}")
        if details:
            print(f"    └─ {details}")

    def test_connection(self):
        """Test if server is reachable"""
        print("\n[Test Group] Connection")
        try:
            response = requests.get(self.base_url.replace("/alerts", ""), timeout=2)
            self.log_pass("Server reachable")
        except requests.RequestException as e:
            self.log_fail("Server reachable", str(e))

    def test_valid_long_trade(self):
        """Test valid long trade alert"""
        print("\n[Test Group] Valid Payloads")

        payload = {
            "ticker": "EURUSD",
            "direction": "long",
            "entry_level": 1.16353,
            "stop_level": 1.16170,
            "take_profit": 1.16902,
            "setup_type": "LTF CHOCH FVG",
            "timeframe": "15"
        }

        status, response = self.send_request(payload)

        if self.assert_status(status, 201, "Valid long trade"):
            if self.assert_field(response, "success", "Response has success"):
                if self.assert_field(response, "alertId", "Response has alertId"):
                    self.log_pass("Valid long trade", f"Alert ID: {response['alertId']}")

    def test_valid_short_trade(self):
        """Test valid short trade alert"""
        payload = {
            "ticker": "AAPL",
            "direction": "short",
            "entry_level": 150.50,
            "stop_level": 151.20,
            "take_profit": 149.30,
            "setup_type": "Resistance Breakout",
            "timeframe": "60"
        }

        status, response = self.send_request(payload)
        self.assert_status(status, 201, "Valid short trade")

    def test_crypto_alert(self):
        """Test crypto trade alert"""
        payload = {
            "ticker": "BTCUSD",
            "direction": "long",
            "entry_level": 42500.00,
            "stop_level": 42000.00,
            "take_profit": 45000.00,
            "setup_type": "Support Bounce",
            "timeframe": "D"
        }

        status, response = self.send_request(payload)
        self.assert_status(status, 201, "Crypto alert (BTCUSD)")

    def test_invalid_direction(self):
        """Test invalid direction value"""
        print("\n[Test Group] Validation Errors")

        payload = {
            "ticker": "EURUSD",
            "direction": "invalid",
            "entry_level": 1.16353,
            "stop_level": 1.16170,
            "take_profit": 1.16902,
            "setup_type": "Test",
            "timeframe": "15"
        }

        status, response = self.send_request(payload)

        if self.assert_status(status, 400, "Invalid direction"):
            if self.assert_field(response, "error", "Response has error"):
                self.log_pass("Invalid direction", "Validation error detected")

    def test_missing_ticker(self):
        """Test missing ticker field"""
        payload = {
            "direction": "long",
            "entry_level": 1.16353,
            "stop_level": 1.16170,
            "take_profit": 1.16902,
            "setup_type": "Test",
            "timeframe": "15"
        }

        status, response = self.send_request(payload)
        self.assert_status(status, 400, "Missing ticker field")

    def test_missing_direction(self):
        """Test missing direction field"""
        payload = {
            "ticker": "EURUSD",
            "entry_level": 1.16353,
            "stop_level": 1.16170,
            "take_profit": 1.16902,
            "setup_type": "Test",
            "timeframe": "15"
        }

        status, response = self.send_request(payload)
        self.assert_status(status, 400, "Missing direction field")

    def test_negative_entry_level(self):
        """Test negative entry level"""
        payload = {
            "ticker": "EURUSD",
            "direction": "long",
            "entry_level": -1.16353,
            "stop_level": 1.16170,
            "take_profit": 1.16902,
            "setup_type": "Test",
            "timeframe": "15"
        }

        status, response = self.send_request(payload)
        self.assert_status(status, 400, "Negative entry level")

    def test_zero_entry_level(self):
        """Test zero entry level"""
        payload = {
            "ticker": "EURUSD",
            "direction": "long",
            "entry_level": 0,
            "stop_level": 1.16170,
            "take_profit": 1.16902,
            "setup_type": "Test",
            "timeframe": "15"
        }

        status, response = self.send_request(payload)
        self.assert_status(status, 400, "Zero entry level")

    def test_invalid_json(self):
        """Test invalid JSON"""
        print("\n[Test Group] Invalid Input")

        try:
            response = requests.post(
                self.base_url,
                data="invalid json",
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            if response.status_code == 400:
                self.log_pass("Invalid JSON handling", "400 Bad Request")
            else:
                self.log_fail("Invalid JSON handling", f"Got {response.status_code}")
        except requests.RequestException as e:
            self.log_fail("Invalid JSON handling", str(e))

    def test_get_alerts(self):
        """Test GET endpoint"""
        print("\n[Test Group] API Endpoints")

        try:
            response = requests.get(self.base_url, timeout=5)

            if self.assert_status(response.status_code, 200, "GET /api/alerts"):
                data = response.json()
                if self.assert_field(data, "stats", "Response has stats"):
                    stats = data.get("stats", {})
                    total = stats.get("total", 0)
                    self.log_pass("GET /api/alerts", f"Total alerts: {total}")
        except requests.RequestException as e:
            self.log_fail("GET /api/alerts", str(e))

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print(f"TradingView Webhook Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        # Test connection
        self.test_connection()

        # Test valid payloads
        self.test_valid_long_trade()
        self.test_valid_short_trade()
        self.test_crypto_alert()

        # Test validation errors
        self.test_invalid_direction()
        self.test_missing_ticker()
        self.test_missing_direction()
        self.test_negative_entry_level()
        self.test_zero_entry_level()

        # Test invalid input
        self.test_invalid_json()

        # Test API endpoints
        self.test_get_alerts()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0

        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests:  {total}")
        print(f"Passed:       {self.passed} ✓")
        print(f"Failed:       {self.failed} ✗")
        print(f"Success Rate: {percentage:.1f}%")
        print("="*60 + "\n")

        return self.failed == 0


def main():
    """Main entry point"""
    print("Checking server connection...", end="", flush=True)

    try:
        requests.get(BASE_URL.replace("/alerts", ""), timeout=2)
        print(" ✓\n")
    except requests.RequestException:
        print(" ✗")
        print(f"\n❌ Could not connect to {BASE_URL}")
        print("Make sure the server is running: npm run dev\n")
        sys.exit(1)

    tester = WebhookTester()
    tester.run_all_tests()

    sys.exit(0 if tester.failed == 0 else 1)


if __name__ == "__main__":
    main()
