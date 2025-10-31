"""Session and transaction management for TypeDB."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from typedb.driver import (
    Credentials,
    Driver,
    DriverOptions,
    TransactionType,
    TypeDB,
)
from typedb.driver import (
    Transaction as TypeDBTransaction,
)


class Database:
    """Main database connection and session manager."""

    def __init__(
        self,
        address: str = "localhost:1729",
        database: str = "typedb",
        username: str | None = None,
        password: str | None = None,
    ):
        """Initialize database connection.

        Args:
            address: TypeDB server address
            database: Database name
            username: Optional username for authentication
            password: Optional password for authentication
        """
        self.address = address
        self.database_name = database
        self.username = username
        self.password = password
        self._driver: Driver | None = None

    def connect(self) -> None:
        """Connect to TypeDB server."""
        if self._driver is None:
            # Create credentials if username/password provided
            credentials = (
                Credentials(self.username, self.password)
                if self.username and self.password
                else None
            )

            # Create driver options
            # Disable TLS for local connections (non-HTTPS addresses)
            is_tls_enabled = self.address.startswith('https://')
            driver_options = DriverOptions(is_tls_enabled=is_tls_enabled)

            # Connect to TypeDB
            if credentials:
                self._driver = TypeDB.driver(self.address, credentials, driver_options)
            else:
                # For local TypeDB Core without authentication
                self._driver = TypeDB.driver(self.address, Credentials("admin", "password"), driver_options)

    def close(self) -> None:
        """Close connection to TypeDB server."""
        if self._driver:
            self._driver.close()
            self._driver = None

    def __enter__(self) -> "Database":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    @property
    def driver(self) -> Driver:
        """Get the TypeDB driver, connecting if necessary."""
        if self._driver is None:
            self.connect()
        assert self._driver is not None, "Driver should be initialized after connect()"
        return self._driver

    def create_database(self) -> None:
        """Create the database if it doesn't exist."""
        if not self.driver.databases.contains(self.database_name):
            self.driver.databases.create(self.database_name)

    def delete_database(self) -> None:
        """Delete the database."""
        if self.driver.databases.contains(self.database_name):
            self.driver.databases.get(self.database_name).delete()

    def database_exists(self) -> bool:
        """Check if database exists."""
        return self.driver.databases.contains(self.database_name)

    @contextmanager
    def transaction(self, transaction_type: str = "read") -> Iterator["Transaction"]:
        """Create a transaction.

        Args:
            transaction_type: Type of transaction ("read", "write", or "schema")

        Yields:
            Transaction wrapper
        """
        # Map string to TransactionType
        tx_type_map = {
            "read": TransactionType.READ,
            "write": TransactionType.WRITE,
            "schema": TransactionType.SCHEMA,
        }
        tx_type = tx_type_map.get(transaction_type, TransactionType.READ)

        # Create transaction directly on driver
        tx = self.driver.transaction(self.database_name, tx_type)
        try:
            yield Transaction(tx)
        finally:
            if tx.is_open():
                tx.close()

    def execute_query(self, query: str, transaction_type: str = "read") -> list[dict[str, Any]]:
        """Execute a query and return results.

        Args:
            query: TypeQL query string
            transaction_type: Type of transaction ("read", "write", or "schema")

        Returns:
            List of result dictionaries
        """
        with self.transaction(transaction_type) as tx:
            results = tx.execute(query)
            if transaction_type in ("write", "schema"):
                tx.commit()
            return results


class Transaction:
    """Wrapper around TypeDB transaction."""

    def __init__(self, tx: TypeDBTransaction):
        """Initialize transaction wrapper.

        Args:
            tx: TypeDB transaction
        """
        self._tx = tx

    def execute(self, query: str) -> list[dict[str, Any]]:
        """Execute a query.

        Args:
            query: TypeQL query string

        Returns:
            List of result dictionaries
        """
        # Execute query - returns a Promise[QueryAnswer]
        promise = self._tx.query(query)
        answer = promise.resolve()

        # Process based on answer type
        results = []

        # Check if the answer has an iterator (for fetch/get queries)
        if hasattr(answer, "__iter__"):
            for item in answer:
                if hasattr(item, "as_dict"):
                    # ConceptRow with as_dict method
                    results.append(dict(item.as_dict()))
                elif hasattr(item, "as_json"):
                    # Document with as_json method
                    results.append(item.as_json())
                else:
                    # Try to convert to dict
                    results.append(dict(item) if hasattr(item, "__iter__") else {"result": str(item)})

        return results

    def commit(self) -> None:
        """Commit the transaction."""
        self._tx.commit()

    def rollback(self) -> None:
        """Rollback the transaction."""
        self._tx.rollback()

    @property
    def is_open(self) -> bool:
        """Check if transaction is open."""
        return self._tx.is_open()
