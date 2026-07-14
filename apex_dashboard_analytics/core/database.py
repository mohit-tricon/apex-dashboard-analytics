"""Database connection management (PostgreSQL, sync SQLAlchemy 2.0 + psycopg).

Exposes:
    * ``Base``     - declarative base every ORM model inherits from.
    * ``Database`` - a singleton wrapping the engine + session factory.
    * ``db``       - the shared ``Database`` instance used across the app.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class Database:
    """Singleton owning the SQLAlchemy engine and session factory.

    Only one instance ever exists per process. Call :meth:`init` once at
    startup (e.g. in the app lifespan) before using :meth:`session`.
    """

    _instance: "Database | None" = None

    def __new__(cls) -> "Database":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._engine = None
            instance._sessionmaker = None
            cls._instance = instance
        return cls._instance

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def init(
        self,
        dsn: str,
        *,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_pre_ping: bool = True,
    ) -> None:
        """Create the engine and session factory (idempotent)."""
        if self._engine is not None:
            return
        self._engine = create_engine(
            dsn,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            future=True,
        )
        self._sessionmaker = sessionmaker(
            bind=self._engine,
            class_=Session,
            expire_on_commit=False,
            autoflush=False,
        )

    def dispose(self) -> None:
        """Dispose of the engine's connection pool."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._sessionmaker = None

    @property
    def is_initialized(self) -> bool:
        return self._engine is not None

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call db.init(...) first.")
        return self._engine

    # ------------------------------------------------------------------ #
    # Sessions & schema
    # ------------------------------------------------------------------ #
    @contextmanager
    def session(self) -> Iterator[Session]:
        """Transactional session scope: commits on success, rolls back on error."""
        if self._sessionmaker is None:
            raise RuntimeError("Database not initialized. Call db.init(...) first.")
        session = self._sessionmaker()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_all(self) -> None:
        """Create all tables registered on ``Base.metadata``."""
        # Import models so they register on the metadata before create_all.
        from apex_dashboard_analytics import models  # noqa: F401

        Base.metadata.create_all(self.engine)


# Shared singleton instance.
db = Database()
