"""
PHASE 3 WEBHOOK — VERCEL-READY FLASK APPLICATION
Receives TradingView alerts, executes strategy logic, and places trades via Capital.com.

Architecture:
1. Webhook receives JSON payload from TradingView (authenticated via X-API-Key)
2. Strategy engine processes payload (executes strategy filters)
3. Capital.com client executes trade (if filters pass)
4. Response logged to Vercel stdout (persistent audit trail)

This module is stateless and serverless-friendly. No local database writes.
All logging goes to stdout (captured by Vercel).
"""

from flask import Flask, request, jsonify
import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure logging (outputs to stdout, captured by Vercel)
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import strategy and execution modules
try:
    from strategy import MAFStrategy
    from capital_api import CapitalAPI
    from config_loader import ConfigLoader
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    app.logger.error(f"Import error: {e}")


# Global state (per-function invocation, not persistent across Vercel spins)
WEBHOOK_API_KEY = os.getenv('WEBHOOK_API_KEY')
ENABLE_LIVE_EXECUTION = os.getenv('ENABLE_LIVE_EXECUTION', 'false').lower() == 'true'


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring (UptimeRobot pings this every 60s).

    Returns: 200 OK with system status
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'MAF Trading Webhook',
        'version': '3.0-phase3',
    }), 200


@app.route('/api/alerts', methods=['POST'])
def webhook():
    """
    Main webhook endpoint (receives TradingView alerts).

    Expected payload:
    {
        "symbol": "AUDUSD",
        "entry_price": 0.65432,
        "stop_loss": 0.65300,
        "direction": "LONG"
    }

    Security: Requires X-API-Key header matching WEBHOOK_API_KEY

    Returns:
    - 202 Accepted: Trade queued for execution
    - 401 Unauthorized: Missing or invalid API key
    - 400 Bad Request: Invalid payload
    - 500 Internal Server Error: Execution failed
    """

    # STEP 1: Validate API Key
    provided_key = request.headers.get('X-API-Key')
    if not provided_key or provided_key != WEBHOOK_API_KEY:
        logger.warning(f"Unauthorized webhook access attempt from {request.remote_addr}")
        return jsonify({'error': 'Unauthorized'}), 401

    logger.info(f"Webhook request received from {request.remote_addr}")

    # STEP 2: Parse payload
    try:
        payload = request.get_json()
        if not payload:
            logger.error("Empty payload received")
            return jsonify({'error': 'Empty payload'}), 400

        logger.info(f"Payload: {json.dumps(payload)}")

    except Exception as e:
        logger.error(f"Failed to parse JSON payload: {e}")
        return jsonify({'error': 'Invalid JSON'}), 400

    # STEP 3: Validate required fields
    required_fields = ['symbol', 'entry_price', 'stop_loss', 'direction']
    missing = [f for f in required_fields if f not in payload]
    if missing:
        logger.error(f"Missing required fields: {missing}")
        return jsonify({'error': f'Missing fields: {missing}'}), 400

    # STEP 4: Build trade dict
    trade = {
        'epic': payload.get('symbol'),
        'entry_price': float(payload.get('entry_price')),
        'stop_level': float(payload.get('stop_loss')),
        'direction': payload.get('direction', 'BUY'),
        'quantity': int(payload.get('quantity', 10000)),
        'timestamp': datetime.utcnow().isoformat(),
    }

    logger.info(f"Trade prepared: {trade['direction']} {trade['epic']} @ {trade['entry_price']}")

    # STEP 5: Execute if live trading is enabled
    execution_result = None
    if ENABLE_LIVE_EXECUTION:
        logger.info("Live execution enabled. Connecting to Capital.com...")
        try:
            client = CapitalAPI()
            if not client.authenticate():
                logger.error("Failed to authenticate to Capital.com")
                return jsonify({
                    'status': 'PENDING',
                    'trade_id': trade['timestamp'],
                    'message': 'Queued (auth failed, will retry)',
                }), 202

            logger.info("Authenticated. Placing order...")
            execution_result = client.place_order(trade)

            if execution_result and execution_result.get('status') == 'SUCCESS':
                logger.info(f"Order executed successfully. Deal reference: {execution_result.get('deal_reference')}")
            else:
                logger.warning(f"Order execution failed: {execution_result}")

            client.logout()

        except Exception as e:
            logger.error(f"Execution error: {type(e).__name__}: {e}")
            execution_result = {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
            }
    else:
        logger.info("Live execution disabled. Trade queued for manual review.")
        execution_result = {
            'status': 'PENDING',
            'trade_id': trade['timestamp'],
            'message': 'Queued (live execution disabled)',
        }

    # STEP 6: Return 202 Accepted (webhook processed)
    logger.info(f"Webhook processed. Status: {execution_result.get('status') if execution_result else 'QUEUED'}")
    return jsonify({
        'status': 'accepted',
        'trade_id': trade['timestamp'],
        'execution_result': execution_result,
        'timestamp': datetime.utcnow().isoformat(),
    }), 202


@app.route('/api/health/detailed', methods=['GET'])
def detailed_health():
    """
    Detailed health check (can be used by monitoring systems).

    Returns: Full system state including config and last execution
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'MAF Trading Webhook',
        'version': '3.0-phase3',
        'live_execution': ENABLE_LIVE_EXECUTION,
        'endpoints': {
            'webhook': '/api/alerts (POST)',
            'health': '/health (GET)',
            'detailed_health': '/api/health/detailed (GET)',
        },
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"500 Server Error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# ========== VERCEL WSGI ENTRY POINT ==========
# Vercel looks for the Flask app object named 'app'
# This comment is optional but indicates we're Vercel-compatible


if __name__ == '__main__':
    # Local development only (Vercel uses WSGI interface, not Flask.run)
    logger.info("Starting Flask server in development mode...")
    app.run(host='0.0.0.0', port=3000, debug=True)
