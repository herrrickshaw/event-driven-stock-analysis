#!/usr/bin/env python3
"""
Cassandra cluster initialization script.

Reads CQL schema from herrrickshaw_schema.cql and applies it to a Cassandra cluster.
Supports both local development and distributed production clusters.

Usage:
    python init_cassandra.py --hosts localhost --port 9042
    python init_cassandra.py --hosts cassandra-1,cassandra-2,cassandra-3 --port 9042 --username cassandra --password cassandra
"""

import argparse
import logging
import sys
from pathlib import Path

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra import ConsistencyLevel
import cassandra.cluster

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_schema(schema_file: str) -> str:
    """Read CQL schema from file."""
    path = Path(schema_file)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    with open(path, 'r') as f:
        return f.read()


def parse_statements(schema_content: str) -> list[str]:
    """Parse CQL statements from schema content."""
    statements = []
    current = []

    for line in schema_content.split('\n'):
        # Skip comments and empty lines
        if line.strip().startswith('--') or not line.strip():
            continue

        current.append(line)

        # Check if statement is complete (ends with semicolon)
        if line.strip().endswith(';'):
            statement = '\n'.join(current).strip()
            if statement:
                statements.append(statement)
            current = []

    return statements


def create_cluster(
    hosts: list[str],
    port: int,
    username: str = None,
    password: str = None,
) -> Cluster:
    """Create Cassandra cluster connection."""
    auth_provider = None
    if username and password:
        auth_provider = PlainTextAuthProvider(username, password)

    cluster = Cluster(
        contact_points=hosts,
        port=port,
        auth_provider=auth_provider,
        control_connection_timeout=10,
        connect_timeout=10,
    )

    return cluster


def apply_schema(
    hosts: list[str],
    port: int,
    schema_file: str,
    username: str = None,
    password: str = None,
    dry_run: bool = False,
) -> bool:
    """Apply CQL schema to cluster."""
    try:
        # Read schema
        logger.info(f"Reading schema from {schema_file}")
        schema_content = read_schema(schema_file)

        # Parse statements
        statements = parse_statements(schema_content)
        logger.info(f"Parsed {len(statements)} CQL statements")

        if dry_run:
            logger.info("=== DRY RUN MODE ===")
            for i, stmt in enumerate(statements, 1):
                print(f"\n--- Statement {i} ---")
                print(stmt)
            return True

        # Connect to cluster
        logger.info(f"Connecting to cluster at {hosts}:{port}")
        cluster = create_cluster(hosts, port, username, password)

        try:
            # Use system session initially (no keyspace)
            session = cluster.connect()
            session.default_consistency_level = ConsistencyLevel.QUORUM

            # Execute statements
            for i, statement in enumerate(statements, 1):
                try:
                    logger.info(f"Executing statement {i}/{len(statements)}")
                    session.execute(statement)
                    logger.info(f"Statement {i} completed successfully")

                except Exception as e:
                    logger.warning(f"Statement {i} failed: {e}")
                    # Continue with next statement (allow idempotent operations)

            logger.info("Schema applied successfully")
            session.shutdown()
            return True

        finally:
            cluster.shutdown()

    except Exception as e:
        logger.error(f"Failed to apply schema: {e}")
        return False


def verify_schema(
    hosts: list[str],
    port: int,
    username: str = None,
    password: str = None,
) -> bool:
    """Verify that schema was applied correctly."""
    try:
        logger.info("Verifying schema...")

        cluster = create_cluster(hosts, port, username, password)

        try:
            session = cluster.connect('herrrickshaw')

            # Check keyspace exists
            metadata = cluster.metadata
            if 'herrrickshaw' not in metadata.keyspaces:
                logger.error("Keyspace 'herrrickshaw' not found")
                return False

            keyspace = metadata.keyspaces['herrrickshaw']

            # Check tables
            expected_tables = {
                'instruments',
                'instruments_by_symbol',
                'instruments_by_name',
                'stock_quotes',
                'price_history',
                'seed_status',
            }

            actual_tables = set(keyspace.tables.keys())
            missing = expected_tables - actual_tables
            extra = actual_tables - expected_tables

            if missing:
                logger.error(f"Missing tables: {missing}")
                return False

            if extra:
                logger.warning(f"Extra tables: {extra}")

            logger.info(f"Found all {len(expected_tables)} expected tables:")
            for table in sorted(expected_tables):
                col_count = len(keyspace.tables[table].columns)
                logger.info(f"  - {table} ({col_count} columns)")

            # Test basic connectivity
            session.execute("SELECT * FROM seed_status LIMIT 1")
            logger.info("Schema verification passed")

            session.shutdown()
            return True

        finally:
            cluster.shutdown()

    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return False


def cluster_info(
    hosts: list[str],
    port: int,
    username: str = None,
    password: str = None,
) -> bool:
    """Display cluster information."""
    try:
        cluster = create_cluster(hosts, port, username, password)

        try:
            session = cluster.connect()

            # Get cluster info
            logger.info("=== Cluster Information ===")
            metadata = cluster.metadata
            logger.info(f"Cluster name: {metadata.cluster_name}")
            logger.info(f"Cassandra version: {metadata.cassandra_version}")

            # List nodes
            logger.info("\nNodes:")
            for node in metadata.all_hosts():
                logger.info(f"  - {node.address}:{port}")
                logger.info(f"    Datacenter: {node.datacenter}")
                logger.info(f"    Rack: {node.rack}")
                logger.info(f"    Up: {node.is_up}")

            # List keyspaces
            logger.info("\nKeyspaces:")
            for ks_name in sorted(metadata.keyspaces.keys()):
                ks = metadata.keyspaces[ks_name]
                logger.info(f"  - {ks_name}")
                logger.info(f"    Replication: {ks.replication_map}")

            session.shutdown()
            return True

        finally:
            cluster.shutdown()

    except Exception as e:
        logger.error(f"Failed to get cluster info: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Initialize Cassandra cluster with herrrickshaw schema'
    )

    parser.add_argument(
        '--hosts',
        default='localhost',
        help='Comma-separated list of Cassandra hosts (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=9042,
        help='Cassandra port (default: 9042)'
    )
    parser.add_argument(
        '--username',
        help='Cassandra username (optional)'
    )
    parser.add_argument(
        '--password',
        help='Cassandra password (optional)'
    )
    parser.add_argument(
        '--schema-file',
        default='herrrickshaw_schema.cql',
        help='Path to CQL schema file (default: herrrickshaw_schema.cql)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print schema without applying'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing schema'
    )
    parser.add_argument(
        '--info-only',
        action='store_true',
        help='Only display cluster information'
    )

    args = parser.parse_args()

    # Parse hosts
    hosts = [h.strip() for h in args.hosts.split(',')]

    logger.info(f"Cassandra cluster initialization")
    logger.info(f"Hosts: {', '.join(hosts)}")
    logger.info(f"Port: {args.port}")

    try:
        if args.info_only:
            # Display cluster info
            success = cluster_info(hosts, args.port, args.username, args.password)
            return 0 if success else 1

        if args.verify_only:
            # Verify schema only
            success = verify_schema(hosts, args.port, args.username, args.password)
            return 0 if success else 1

        # Apply schema
        success = apply_schema(
            hosts,
            args.port,
            args.schema_file,
            args.username,
            args.password,
            args.dry_run,
        )

        if not success:
            return 1

        # Verify schema
        logger.info("\nVerifying schema...")
        success = verify_schema(hosts, args.port, args.username, args.password)
        return 0 if success else 1

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
