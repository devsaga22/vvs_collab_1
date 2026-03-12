import pandas as pd
import logging
import pathlib

# 1. Read the file using this schema
DATA_DIR= pathlib.Path(r'..\01_proj_design\sim-1_2007\6. Turbofan Engine Degradation Simulation Data Set')
LOG_FILE="pipeline.log"

# df = pd.read_csv('..\\01_proj_design\\sim-1_2007\\6. Turbofan Engine Degradation Simulation Data Set\\train_FD001.txt')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

# 2. Define the names based on your README
# We use a list to map the index to a name
column_names = [
    'eng_unit_id',      # Engine ID (1 to 100)
    'cycle',        # Time (1 to failure)
    'op_set1',      # Altitude (Boundary Condition)
    'op_set2',      # Mach Number (Boundary Condition)
    'op_set3'       # Throttle (Boundary Condition)
]

# 3. Add the 21 Sensors (6 to 26 in your README)
# We use a loop to quickly generate 's1', 's2' ... 's21'
sensor_names = [f'sensor_{i}' for i in range(1, 22)]
FULL_SCHEMA = column_names + sensor_names
# df = pd.read_csv(DATA_DIR+r'\train_FD001.txt', sep=r'\s+', header=None, names=FULL_SCHEMA)
def data_ingest():
    if not DATA_DIR.exists():
        logging.error(f"Data directory does not exist: {DATA_DIR}")
        return None
    for file_path in DATA_DIR.glob("*.txt"):
        file_name = file_path.name
        
        try:
            # STRATEGY: Handle files based on their prefix
            if file_name.startswith(('train', 'test')):
                logging.info(f"Processing Telemetry: {file_name}")
                df = pd.read_csv(file_path, sep=r'\s+', header=None, names=FULL_SCHEMA)
                
            elif file_name.startswith('RUL'):
                logging.info(f"Processing Ground Truth: {file_name}")
                df = pd.read_csv(file_path, header=None, names=['actual_rul'])
                df['eng_unit_id'] = df.index + 1 # Align with engine IDs
            
            else:
                logging.warning(f"Skipping unknown file format: {file_name}")
                continue

            # PREVIEW (Optional logging of data quality)
            logging.info(f"Successfully read {len(df)} rows from {file_name}")
            
            # TODO: Add your df.to_sql() logic here later
            
        except Exception as e:
            logging.error(f"Failed to process {file_name}: {str(e)}")


if __name__ == "__main__":
    data_ingest()