"""
Configuration for Cassandra integration in different environments.

Supports: development (local), staging, and production deployments.
"""

from dataclasses import dataclass
from typing import List, Optional
import os


@dataclass
class CassandraConfig:
    """Cassandra configuration."""
    hosts: List[str]
    port: int
    keyspace: str
    username: Optional[str]
    password: Optional[str]
    max_pool_size: int
    min_pool_size: int
    session_timeout: int
    ssl_enabled: bool = False
    ssl_ca_cert: Optional[str] = None
    ssl_client_cert: Optional[str] = None
    ssl_client_key: Optional[str] = None
    metrics_enabled: bool = True

    def to_dict(self):
        """Export as dictionary."""
        return {
            'hosts': self.hosts,
            'port': self.port,
            'keyspace': self.keyspace,
            'username': self.username,
            'password': self.password,
            'max_pool_size': self.max_pool_size,
            'min_pool_size': self.min_pool_size,
            'session_timeout': self.session_timeout,
            'ssl_enabled': self.ssl_enabled,
        }


# ============= DEVELOPMENT CONFIG =============

DEVELOPMENT = CassandraConfig(
    hosts=['127.0.0.1'],
    port=9042,
    keyspace='herrrickshaw',
    username=None,
    password=None,
    max_pool_size=10,
    min_pool_size=2,
    session_timeout=30,
    ssl_enabled=False,
    metrics_enabled=True,
)

# ============= STAGING CONFIG =============

STAGING = CassandraConfig(
    hosts=[
        'cassandra-1.staging.internal',
        'cassandra-2.staging.internal',
        'cassandra-3.staging.internal',
    ],
    port=9042,
    keyspace='herrrickshaw',
    username=os.getenv('CASSANDRA_USER', 'cassandra'),
    password=os.getenv('CASSANDRA_PASSWORD', 'cassandra'),
    max_pool_size=20,
    min_pool_size=5,
    session_timeout=30,
    ssl_enabled=True,
    ssl_ca_cert='/etc/cassandra/ssl/ca.pem',
    ssl_client_cert='/etc/cassandra/ssl/client.pem',
    ssl_client_key='/etc/cassandra/ssl/client-key.pem',
    metrics_enabled=True,
)

# ============= PRODUCTION CONFIG =============

PRODUCTION = CassandraConfig(
    hosts=[
        'cassandra-1.prod.us-east-1.internal',
        'cassandra-2.prod.us-east-1.internal',
        'cassandra-3.prod.us-east-1.internal',
        'cassandra-4.prod.us-west-2.internal',
        'cassandra-5.prod.us-west-2.internal',
        'cassandra-6.prod.eu-west-1.internal',
    ],
    port=9042,
    keyspace='herrrickshaw',
    username=os.getenv('CASSANDRA_USER', 'cassandra'),
    password=os.getenv('CASSANDRA_PASSWORD'),  # MUST be set via env
    max_pool_size=50,
    min_pool_size=10,
    session_timeout=60,
    ssl_enabled=True,
    ssl_ca_cert='/etc/cassandra/ssl/ca.pem',
    ssl_client_cert='/etc/cassandra/ssl/client.pem',
    ssl_client_key='/etc/cassandra/ssl/client-key.pem',
    metrics_enabled=True,
)

# ============= AWS PRODUCTION CONFIG =============

AWS_PRODUCTION = CassandraConfig(
    hosts=[
        'cassandra-cluster.us-east-1.cassandra.amazonaws.com',
    ],
    port=9042,
    keyspace='herrrickshaw',
    username='cassandra',
    password=os.getenv('CASSANDRA_PASSWORD'),
    max_pool_size=50,
    min_pool_size=10,
    session_timeout=60,
    ssl_enabled=True,
    metrics_enabled=True,
)

# ============= GCP PRODUCTION CONFIG =============

GCP_PRODUCTION = CassandraConfig(
    hosts=[
        'cassandra-1.c.project-id.internal',
        'cassandra-2.c.project-id.internal',
        'cassandra-3.c.project-id.internal',
    ],
    port=9042,
    keyspace='herrrickshaw',
    username='cassandra',
    password=os.getenv('CASSANDRA_PASSWORD'),
    max_pool_size=50,
    min_pool_size=10,
    session_timeout=60,
    ssl_enabled=True,
    ssl_ca_cert='/etc/cassandra/ssl/ca.pem',
    metrics_enabled=True,
)

# ============= ENVIRONMENT SELECTION =============

def get_config(environment: str = None) -> CassandraConfig:
    """
    Get configuration for environment.

    Args:
        environment: 'development', 'staging', 'production', 'aws', 'gcp'
                    Defaults to CASSANDRA_ENV env var or 'development'

    Returns:
        CassandraConfig instance
    """
    env = environment or os.getenv('CASSANDRA_ENV', 'development').lower()

    configs = {
        'development': DEVELOPMENT,
        'staging': STAGING,
        'production': PRODUCTION,
        'aws': AWS_PRODUCTION,
        'gcp': GCP_PRODUCTION,
    }

    if env not in configs:
        raise ValueError(
            f"Unknown environment: {env}. "
            f"Must be one of: {', '.join(configs.keys())}"
        )

    return configs[env]


# ============= MARKET-SPECIFIC DEFAULTS =============

MARKET_SETTINGS = {
    'india': {
        'ticker_prefix': '',           # Bare NSE symbols
        'ticker_suffix': '.NS',        # For yfinance queries
        'data_source': 'yfinance',
        'update_interval': 300,        # 5 min
    },
    'us': {
        'ticker_prefix': '',
        'ticker_suffix': '',
        'data_source': 'yfinance',
        'update_interval': 300,
    },
    'europe': {
        'ticker_prefix': '',
        'ticker_suffix': '',           # Pre-suffixed (.DE, .L, .PA, etc.)
        'data_source': 'yfinance',
        'update_interval': 300,
    },
    'japan': {
        'ticker_prefix': '',
        'ticker_suffix': '',           # Pre-suffixed (.T)
        'data_source': 'yfinance',
        'update_interval': 300,
    },
    'korea': {
        'ticker_prefix': '',
        'ticker_suffix': '',           # Pre-suffixed (.KS, .KQ)
        'data_source': 'yfinance',
        'update_interval': 300,
    },
    'china': {
        'ticker_prefix': '',
        'ticker_suffix': '',           # Pre-suffixed (.SS, .SZ)
        'data_source': 'yfinance',
        'update_interval': 600,        # 10 min (due to data delays)
    },
}

if __name__ == '__main__':
    # Print configuration info
    import sys

    env = sys.argv[1] if len(sys.argv) > 1 else 'development'

    try:
        config = get_config(env)
        print(f"Configuration for {env}:")
        print(f"  Hosts: {', '.join(config.hosts)}")
        print(f"  Port: {config.port}")
        print(f"  Keyspace: {config.keyspace}")
        print(f"  Max pool size: {config.max_pool_size}")
        print(f"  SSL enabled: {config.ssl_enabled}")

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
