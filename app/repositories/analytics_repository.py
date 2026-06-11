from sqlalchemy import text
from app.db.database import engine

def execute_query(sql_query: str) -> list:
    if "limit" not in sql_query.lower():
        sql_query = sql_query.rstrip(";") + " LIMIT 100;"
    with engine.connect() as connection:
        result = connection.execute(text(sql_query))
        return [dict(row._mapping) for row in result]