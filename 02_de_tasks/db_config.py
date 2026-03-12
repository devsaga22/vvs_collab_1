
import urllib.parse
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

class DatabaseContext:
    _engine = None
    _SessionLocal = None

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            # 1. Get raw strings from .env
            server = os.environ.get("SERVER_NAME", ".")
            db = os.environ.get("DATABASE_NAME", "master")
            print(f"DEBUG: Connecting to Server={server}, Database={db}")
            # 2. Build the connection string
            # We use urllib to handle the special characters in the driver name
            params = urllib.parse.quote_plus(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={db};"
                f"Trusted_Connection=yes;"
            )
            
            # 3. Construct the SQLAlchemy-friendly URL
            url = f"mssql+pyodbc:///?odbc_connect={params}"
            cls._engine = create_engine(url, fast_executemany=True)
        return cls._engine

    @classmethod
    def get_session(cls):
        if cls._SessionLocal is None:
            cls._SessionLocal = sessionmaker(bind=cls.get_engine())
        return cls._SessionLocal()