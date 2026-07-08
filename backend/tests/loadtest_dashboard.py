"""
Load tests for stock analysis dashboard.

Simulates 1000 concurrent users performing realistic operations:
- Portfolio uploads and P&L calculations
- Watchlist management
- Real-time alert streaming
- Market data queries

Run with:
  locust -f loadtest_dashboard.py --users 1000 --spawn-rate 50 --run-time 5m --host http://localhost:8000
"""
from __future__ import annotations

import json
import random
from io import BytesIO

from locust import HttpUser, task, between, events
from faker import Faker

fake = Faker()


# ──────────────────────────────────────────────────────────────────────────────
# Load Test Constants
# ──────────────────────────────────────────────────────────────────────────────

SAMPLE_HOLDINGS = {
    'india': [
        {'symbol': 'RELIANCE', 'yf_ticker': 'RELIANCE.NS', 'name': 'Reliance Industries'},
        {'symbol': 'HDFCBANK', 'yf_ticker': 'HDFCBANK.NS', 'name': 'HDFC Bank'},
        {'symbol': 'INFY', 'yf_ticker': 'INFY.NS', 'name': 'Infosys'},
        {'symbol': 'TCS', 'yf_ticker': 'TCS.NS', 'name': 'Tata Consultancy Services'},
        {'symbol': 'LT', 'yf_ticker': 'LT.NS', 'name': 'Larsen & Toubro'},
    ],
    'us': [
        {'symbol': 'AAPL', 'yf_ticker': 'AAPL', 'name': 'Apple Inc'},
        {'symbol': 'MSFT', 'yf_ticker': 'MSFT', 'name': 'Microsoft'},
        {'symbol': 'GOOGL', 'yf_ticker': 'GOOGL', 'name': 'Alphabet Inc'},
        {'symbol': 'AMZN', 'yf_ticker': 'AMZN', 'name': 'Amazon'},
        {'symbol': 'TSLA', 'yf_ticker': 'TSLA', 'name': 'Tesla'},
    ],
    'europe': [
        {'symbol': 'ADS', 'yf_ticker': 'ADS.DE', 'name': 'Adidas AG'},
        {'symbol': 'SAP', 'yf_ticker': 'SAP.DE', 'name': 'SAP SE'},
        {'symbol': 'RIO', 'yf_ticker': 'RIO.L', 'name': 'Rio Tinto'},
    ],
}

ALERTS_TRIGGER_RATE = 10  # Percentage of users checking alerts


# ──────────────────────────────────────────────────────────────────────────────
# Locust User Classes
# ──────────────────────────────────────────────────────────────────────────────

class DashboardUser(HttpUser):
    """
    Simulates a user interacting with the stock analysis dashboard.

    Performs realistic user behaviors:
    1. View supported markets (10% of requests)
    2. Upload portfolio (15% of requests)
    3. Fetch portfolio P&L (30% of requests)
    4. Manage watchlist (25% of requests)
    5. Poll alerts (20% of requests)
    """

    wait_time = between(1, 5)  # Wait 1-5 seconds between requests

    def on_start(self):
        """Initialize user session."""
        self.market = random.choice(list(SAMPLE_HOLDINGS.keys()))
        self.watchlist = []

    # ──────────────────────────────────────────────────────────────────────────
    # Task: View Markets
    # ──────────────────────────────────────────────────────────────────────────

    @task(10)
    def view_markets(self):
        """
        View supported markets and their info.
        Weight: 10 (10% of user operations)
        """
        with self.client.get(
            '/api/portfolio/markets',
            catch_response=True,
            name='/api/portfolio/markets',
        ) as response:
            if response.status_code == 200:
                markets = response.json()
                assert len(markets) >= 6, "Should return all 6+ markets"
                response.success()
            else:
                response.failure(f"Expected 200, got {response.status_code}")

    # ──────────────────────────────────────────────────────────────────────────
    # Task: Upload Portfolio (Simulated)
    # ──────────────────────────────────────────────────────────────────────────

    @task(15)
    def upload_portfolio(self):
        """
        Upload a portfolio file (simulated Excel).
        Weight: 15 (15% of user operations)
        """
        try:
            import openpyxl
            from openpyxl import Workbook
        except ImportError:
            # Fallback: create raw Excel-like bytes
            excel_data = b'PK\x03\x04'  # ZIP header (Excel is ZIP)
            self.client.post(
                '/api/portfolio/parse',
                files={'file': ('portfolio.xlsx', excel_data)},
                params={'market': self.market},
                catch_response=True,
                name='/api/portfolio/parse',
            ).close()
            return

        # Create minimal valid Excel
        wb = Workbook()
        ws = wb.active
        ws['A1'] = 'Symbol'
        ws['B1'] = 'Quantity'
        ws['C1'] = 'Purchase Price'

        # Add sample holdings
        for i, holding in enumerate(SAMPLE_HOLDINGS[self.market][:3], start=2):
            ws[f'A{i}'] = holding['symbol']
            ws[f'B{i}'] = random.randint(10, 1000)
            ws[f'C{i}'] = random.uniform(50, 5000)

        # Write to bytes
        excel_bytes = BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)

        with self.client.post(
            '/api/portfolio/parse',
            files={'file': ('portfolio.xlsx', excel_bytes.getvalue())},
            params={'market': self.market},
            catch_response=True,
            name='/api/portfolio/parse',
        ) as response:
            if response.status_code == 200:
                data = response.json()
                assert 'stocks' in data, "Response should contain stocks"
                response.success()
            else:
                response.failure(f"Expected 200, got {response.status_code}")

    # ──────────────────────────────────────────────────────────────────────────
    # Task: Fetch Portfolio P&L
    # ──────────────────────────────────────────────────────────────────────────

    @task(30)
    def fetch_portfolio_pnl(self):
        """
        Fetch portfolio history and P&L calculations.
        Weight: 30 (30% of user operations — most common dashboard view)
        """
        holdings = random.sample(SAMPLE_HOLDINGS[self.market], k=min(3, len(SAMPLE_HOLDINGS[self.market])))

        payload = {
            'market': self.market,
            'holdings': [
                {
                    'yf_ticker': h['yf_ticker'],
                    'quantity': random.randint(10, 1000),
                    'purchase_price': random.uniform(50, 5000),
                    'purchase_date': '2023-01-15',
                }
                for h in holdings
            ],
        }

        with self.client.post(
            '/api/portfolio/history',
            json=payload,
            catch_response=True,
            name='/api/portfolio/history',
        ) as response:
            if response.status_code == 200:
                data = response.json()
                assert data['market'] == self.market, "Market mismatch"
                response.success()
            elif response.status_code == 422:
                # Validation error — acceptable in load test
                response.success()
            else:
                response.failure(f"Expected 200 or 422, got {response.status_code}")

    # ──────────────────────────────────────────────────────────────────────────
    # Task: Manage Watchlist
    # ──────────────────────────────────────────────────────────────────────────

    @task(25)
    def manage_watchlist(self):
        """
        Add/remove tickers from watchlist.
        Weight: 25 (25% of user operations)
        """
        operation = random.choice(['add', 'view', 'remove'])

        if operation == 'add':
            tickers = [h['symbol'] for h in random.sample(SAMPLE_HOLDINGS[self.market], k=2)]
            payload = {'tickers': tickers, 'market': self.market}

            with self.client.post(
                '/api/alerts/portfolio',
                json=payload,
                catch_response=True,
                name='/api/alerts/portfolio [POST]',
            ) as response:
                if response.status_code == 200:
                    self.watchlist.extend(tickers)
                    response.success()
                else:
                    response.failure(f"Expected 200, got {response.status_code}")

        elif operation == 'view':
            with self.client.get(
                '/api/alerts/portfolio',
                catch_response=True,
                name='/api/alerts/portfolio [GET]',
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Expected 200, got {response.status_code}")

        elif operation == 'remove' and self.watchlist:
            ticker = random.choice(self.watchlist)
            with self.client.delete(
                f'/api/alerts/portfolio/{ticker}',
                catch_response=True,
                name='/api/alerts/portfolio/{ticker} [DELETE]',
            ) as response:
                if response.status_code == 200:
                    self.watchlist.remove(ticker)
                    response.success()
                else:
                    response.failure(f"Expected 200, got {response.status_code}")

    # ──────────────────────────────────────────────────────────────────────────
    # Task: Poll Alerts
    # ──────────────────────────────────────────────────────────────────────────

    @task(20)
    def poll_alerts(self):
        """
        Poll for recent alerts.
        Weight: 20 (20% of user operations)
        """
        limit = random.randint(5, 50)

        with self.client.get(
            f'/api/alerts/latest?limit={limit}',
            catch_response=True,
            name='/api/alerts/latest',
        ) as response:
            if response.status_code == 200:
                data = response.json()
                assert 'alerts' in data, "Response should contain alerts"
                response.success()
            else:
                response.failure(f"Expected 200, got {response.status_code}")

    # ──────────────────────────────────────────────────────────────────────────
    # Task: Trigger Manual Alert (Optional)
    # ──────────────────────────────────────────────────────────────────────────

    @task(5)
    def trigger_manual_alert(self):
        """
        Manually trigger an alert for testing.
        Weight: 5 (5% of user operations)
        """
        ticker = random.choice([h['symbol'] for h in SAMPLE_HOLDINGS[self.market]])

        with self.client.post(
            f'/api/alerts/trigger/{ticker}?market={self.market}',
            catch_response=True,
            name='/api/alerts/trigger/{ticker}',
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Expected 200, got {response.status_code}")


class StressTestUser(HttpUser):
    """
    Simulates stress testing with rapid-fire requests.
    Used to test API under extreme load.
    """

    wait_time = between(0.1, 0.5)  # Very short wait — aggressive load

    @task
    def rapid_market_queries(self):
        """Rapidly query markets endpoint."""
        self.client.get('/api/portfolio/markets')

    @task
    def rapid_alert_checks(self):
        """Rapidly check alerts."""
        self.client.get('/api/alerts/latest?limit=10')


# ──────────────────────────────────────────────────────────────────────────────
# Locust Event Listeners (Reporting & Monitoring)
# ──────────────────────────────────────────────────────────────────────────────

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("\n" + "=" * 80)
    print("LOAD TEST STARTED")
    print("=" * 80)
    print(f"Target Host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test finishes."""
    print("\n" + "=" * 80)
    print("LOAD TEST SUMMARY")
    print("=" * 80)

    stats = environment.stats
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    success_rate = (
        ((total_requests - total_failures) / total_requests * 100)
        if total_requests > 0
        else 0
    )

    print(f"Total Requests: {total_requests}")
    print(f"Total Failures: {total_failures}")
    print(f"Success Rate: {success_rate:.2f}%")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min Response Time: {stats.total.min_response_time:.2f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th Percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")

    print("\nEndpoint Performance:")
    print("-" * 80)
    print(f"{'Endpoint':<40} {'Count':<10} {'Avg (ms)':<15} {'Failure %':<10}")
    print("-" * 80)

    for endpoint in sorted(stats.entries.keys()):
        entry = stats.entries[endpoint]
        avg_time = entry.avg_response_time
        failure_rate = (entry.num_failures / entry.num_requests * 100) if entry.num_requests > 0 else 0
        print(f"{endpoint:<40} {entry.num_requests:<10} {avg_time:<15.2f} {failure_rate:<10.2f}%")


# ──────────────────────────────────────────────────────────────────────────────
# CLI Instructions
# ──────────────────────────────────────────────────────────────────────────────

"""
QUICK START:

1. Run with default settings (1000 users, 5 minute test):
   locust -f loadtest_dashboard.py --users 1000 --spawn-rate 50 --run-time 5m

2. Run with web UI (interactive):
   locust -f loadtest_dashboard.py

3. Run stress test variant:
   locust -f loadtest_dashboard.py::StressTestUser --users 5000 --spawn-rate 200 --run-time 3m

4. Run with custom host:
   locust -f loadtest_dashboard.py --host http://your-domain.com:8000 --users 500

5. Export results to CSV:
   locust -f loadtest_dashboard.py --csv=results --headless --users 1000 --run-time 5m

EXPECTED RESULTS:

- Baseline (500 users): 95%+ success rate, <100ms avg response time
- High Load (1000 users): 90%+ success rate, <200ms avg response time
- Stress (5000 users): 70-85% success rate, <500ms avg response time

PERFORMANCE TARGETS:

- P95 Response Time: <250ms (normal load)
- P99 Response Time: <500ms (normal load)
- Error Rate: <5% (normal load)
- Throughput: 100+ requests/second at peak
"""
