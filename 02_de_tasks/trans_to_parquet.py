from sqlalchemy import inspect, text
from db_config import DatabaseContext as DatabaseManager
from simp_etl_1 import logger
from pandas import pandas as pd
import os

class SilverToParquetTransformer:
    def __init__(self):
        # Use the same Singleton engine your Ingestor uses
        self.engine = DatabaseManager.get_engine()
        self.schema_name="silver"
        self._ensure_schema()

    def _ensure_schema(self):
        """Creates the silver schema if it doesn't exist"""
        with self.engine.connect() as conn:
            conn.execute(text(f"IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{self.schema_name}') " 
                              f"EXEC('CREATE SCHEMA {self.schema_name}')"))
            conn.commit()
            logger.info(f"Schema '{self.schema_name}' verified and its in the db.")
    def get_schema_tables(self):
        # This reaches into the DB and looks at the structure
        inspector = inspect(self.engine)
        
        # Get all tables in the silver schema
        all_tables = inspector.get_table_names(schema=self.schema_name)
        
        # Filter to only get train and test (ignoring RUL tables)
        target_tables = [t for t in all_tables if t.startswith(('silver'))]
        return target_tables
    
    def parq_generator(self):
        tables=self.get_schema_tables()
        output_dir="./parquet_output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")
        for table in tables:
            print(f"Reading {table} from SQL Server...")
            # Read from Silver Schema
            df = pd.read_sql(f"SELECT * FROM silver.{table}", self.engine)
            
            # Save to Parquet (using fastparquet or pyarrow)
            file_path = f"{output_dir}/{table}.parquet"
            df.to_parquet(file_path, index=False)
            print(f"✅ Created: {file_path}")
            logger.info(f"Parquet file created for {table} at {file_path}")

if __name__=="__main__":
    parqGen = SilverToParquetTransformer()
    parqGen.parq_generator()

    