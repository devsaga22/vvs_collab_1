import os

import pandas as pd
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from db_config import DatabaseContext as DatabaseManager
# read and dump in db
# 1. get the connection string from .env
DATA_DIR= Path(os.environ.get("DATA_DIR"))
LOG_FILE="pipeline.log"


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

logger=logging.getLogger(__name__)




class DataIngestor:
    def __init__(self, schema_name):
        # We "Autowired" the engine here
        self.engine = DatabaseManager.get_engine()
        self.schema_name = schema_name

        # Immediate connection check (The "Session Started" indicator)
        self._check_connection()

    def _check_connection(self):
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logging.info("--- DATABASE CONNECTION ESTABLISHED ---")
        except Exception as e:
            logging.error(f"--- DATABASE CONNECTION FAILED: {e} ---")
            raise

    def create_schema(self):
        """Ensures the bronze schema exists"""
        with self.engine.connect() as conn:
            conn.execute(text(f"IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{self.schema_name}') "
                              f"EXEC('CREATE SCHEMA {self.schema_name}')"))
            conn.commit()
        logging.info(f"Schema '{self.schema_name}' verified.")

    def load_file(self, file_path, column_names):
        table_name = file_path.stem.lower()
        logging.info(f"Ingesting: {file_path.name} -> {self.schema_name}.{table_name}")
        
        try:
            df = pd.read_csv(file_path, sep=r'\s+', header=None, names=column_names)
            df['ingested_at'] = pd.Timestamp.now()
            with self.engine.begin() as conn:
                # Using the shared engine
                df.to_sql(table_name, 
                        con=conn, 
                        schema=self.schema_name, 
                        if_exists='replace', 
                        chunksize=None,        # <--- The Batch Size, let pandas decide based on the file size method=multi log file explosion
                        index=False)
            
            logging.info(f"Success: {len(df)} rows loaded.")
        except Exception as e:
            logging.error(f"Failed loading {table_name}: {e}")
    

# --- Execution ---
def execute_pipeline():
    # Load Paths from .env
    data_dir_str = os.environ.get("DATA_DIR")
    if not data_dir_str:
        logging.error("DATA_DIR not defined in environment.")
        return
        
    data_dir = Path(data_dir_str)
    
    # Schema Definition
    sensor_cols = ['eng_unit_id', 'cycle', 'op_set1', 'op_set2', 'op_set3'] + [f'sensor_{i}' for i in range(1, 21+1)]
    # 2. Schema for RUL files (Ground Truth)
    rul_cols = ['remaining_cycles']
    # Run Pipeline
    # DEBUG LINE: Let's see if the path is actually valid
    logging.info(f"Searching for files in: {data_dir.absolute()}")
    try:
        ingestor = DataIngestor("bronze")
        ingestor.create_schema()
        
        for filepath in data_dir.glob("*.txt"):
            file_name = filepath.name
            if file_name.startswith(('train', 'test')):
                logger.info(f"Processing file: {file_name}")    
                ingestor.load_file(filepath, sensor_cols)
            elif file_name.startswith("RUL_FD"):
                ingestor.load_file(filepath, rul_cols)
            
        logging.info("--- PIPELINE EXECUTION COMPLETED SUCCESSFULLY ---")
    except Exception as e:
        logging.critical(f"Pipeline crashed: {e}")


if __name__ == "__main__":
    execute_pipeline()