"""Custom universal column types for database compatibility (PostgreSQL + pgvector with SQLite fallback)."""

import json
from pgvector.sqlalchemy import Vector
from sqlalchemy import types
from sqlalchemy.types import TypeDecorator


class UniversalVector(TypeDecorator):
    """
    Universal vector column type.
    Uses native pgvector Vector(1536) on PostgreSQL,
    and JSON array on SQLite / fallback dialects.
    """

    impl = types.TypeEngine
    cache_ok = True

    def __init__(self, dim: int = 1536, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(types.JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                pass
        return list(value)
