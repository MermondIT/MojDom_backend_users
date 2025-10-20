"""
Analog PgDataAccess for PostgreSQL + SQLAlchemy (async)
Simplifies function calls and mapping to ORM models
"""

from typing import Any, List, Optional, Sequence, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.orm import DeclarativeMeta

T = TypeVar("T", bound=DeclarativeMeta)


class PgDataAccess:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Reading lists -----------------------------------
    @staticmethod
    async def read_list(
        db: AsyncSession,
        model: Type[T],
        func_name: str,
        params: Optional[dict[str, Any]] = None,
    ) -> List[T]:
        """
        Calls a stored function that returns SETOF model
        params: {"param1": value, ...}
        """
        sql = PgDataAccess._build_select(func_name, params)
        stmt = select(model).from_statement(text(sql))
        result = await db.execute(stmt, params or {})
        return result.scalars().all()

    # --- Reading one record ------------------------------
    @staticmethod
    async def read_one(
        db: AsyncSession,
        model: Type[T],
        func_name: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Optional[T]:
        sql = PgDataAccess._build_select(func_name, params) 
        stmt = select(model).from_statement(text(sql))
        result = await db.execute(stmt, params or {})
        return result.scalars().first()

    async def read_first_or_default(
        db: AsyncSession,
        model: Type[T],
        func_name: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Optional[T]:
            """
            returns the first row of the result of the function
            or None, if there are no rows.
            """
            sql =    PgDataAccess._build_select(func_name, params)
            stmt = select(model).from_statement(text(sql))
            result = await db.execute(stmt, params or {})
            return result.scalars().first()


    async def read_scalar(
        db: AsyncSession,
        sql: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Any SELECT that returns a single value"""
        res = await db.execute(text(sql), params or {})
        return res.scalar()

    # --- Execution without result ------------------------
    async def execute(
        db: AsyncSession,
        sql: str,
        params: Optional[dict[str, Any]] = None,
    ) -> None:
        await db.execute(text(sql), params or {})
        await db.commit()

    # --- Helper ----------------------------------
    @staticmethod
    def _build_select(func_name: str, params: Optional[dict[str, Any]]) -> str:
        """
        Creates a string of the form:
        SELECT * FROM func_name(:p1, :p2)
        """
        if not params:
            return f"SELECT * FROM {func_name}()"
        placeholders = ", ".join(f":{k}" for k in params.keys())
        return f"SELECT * FROM {func_name}({placeholders})"

    @staticmethod
    async def read_mapping_first_or_default(
        db: AsyncSession,
        func_name: str,
        params: Optional[dict[str, Any]] = None
    ) -> Optional[dict[str, Any]]:
        """
        Calls the PostgreSQL function and returns the first row as a dictionary.
        Does not require ORM and PK.
        """
        sql = PgDataAccess._build_select(func_name, params)
        result = await db.execute(text(sql), params or {})
        row = result.mappings().first()
        return dict(row) if row else None