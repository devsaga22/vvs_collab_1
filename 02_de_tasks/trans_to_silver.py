import pandas as pd
from sqlalchemy import create_engine, inspect, text
from db_config import DatabaseContext as DatabaseManager
from simp_etl_1 import logger
"""
this is like writing store proc for silver layer. We will read from bronze, do the transformations and write to silver.
"""


class SilverTransformer:
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
    def get_bronze_tables(self):
        # This reaches into the DB and looks at the structure
        inspector = inspect(self.engine)
        
        # Get all tables in the bronze schema
        all_tables = inspector.get_table_names(schema='bronze')
        
        # Filter to only get train and test (ignoring RUL tables)
        target_tables = [t for t in all_tables if t.startswith(('train', 'test'))]
        return target_tables

    def rul_process(self, table_name,df):
        if("train" in table_name):
        # Train is self-contained: Max cycle is the failure point
            max_cycles= df.groupby('eng_unit_id')['cycle'].transform('max')
            df['target_rul'] = max_cycles - df['cycle']
        else:
        # Test needs to be merged with RUL to get the failure point
            rul_table_name = table_name.replace("test", "rul")
            df_rul = pd.read_sql(f"SELECT * FROM bronze.{rul_table_name}", self.engine)
            df_rul['eng_unit_id'] = df_rul.index + 1 # Assigning IDs based on row index to serve as fk
            df = df.merge(df_rul, on='eng_unit_id', how='left')
            total_life= df.groupby('eng_unit_id')['cycle'].transform('max')+df['remaining_cycles']
            df['target_rul'] = total_life- df['cycle']
        return df

    def transform_load_b2s(self,unit_table):
            df_raw = pd.read_sql(f"SELECT * FROM bronze.{unit_table}", self.engine)
            # --- STEP 1: CALCULATE RUL ---
            # Find the max cycle for each engine
            dfb=self.rul_process(unit_table, df_raw)
            
            # --- STEP 2: DROP DEAD SENSORS ---
            # Find columns where all values are the same (variance = 0)
            # We only check sensor columns
            sensor_cols = [c for c in dfb.columns if 'sensor' in c]
            active_sensors = []
            
            for col in sensor_cols:
                if dfb[col].std() > 0: # If it actually moves
                    active_sensors.append(col)
                else:
                    print(f"Dropping Dead Sensor: {col}")
                    
            # Keep only useful columns
            final_cols = ['eng_unit_id', 'cycle', 'op_set1', 'op_set2', 'op_set3'] + active_sensors + ['target_rul']
            silver_df = dfb[final_cols]
            
            # --- STEP 3: PUSH TO SILVER ---
            
            with self.engine.begin() as conn:
                silver_df.to_sql(f"silver_{unit_table}", 
                                con=conn, 
                                schema='silver', 
                                if_exists='replace', 
                                index=False)
                logger.info(f"Silver Table Created: silver_{unit_table} with {len(active_sensors)} active sensors.")

# Run it
if __name__ == "__main__":

    # 1. Initialize the Transformer
    transformer = SilverTransformer()
    
    # 2. Automatically find what needs to be worked on
    tables_to_process = transformer.get_bronze_tables()
    
    print(f"Found {len(tables_to_process)} tables to transform: {tables_to_process}")
    
    # 3. Loop and execute
    for table in tables_to_process:
        if table.startswith("rul"):
            print(f"Skipping RUL table: {table} (processed together with train/test)")
            continue
        try:
            transformer.transform_load_b2s(table)
        except Exception as e:
            print(f"FAILED to transform {table}: {e}")