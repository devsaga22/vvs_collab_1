import pandas as pd
from db_config import DatabaseContext as DatabaseManager
"""
 a code to explore the data in the bronze layer and do some basic transformations.
"""
# Get our connection
engine = DatabaseManager.get_engine()

# Load just one table to play with
df = pd.read_sql("SELECT * FROM bronze.train_fd001", engine)

# 1. The 'Head': Show me the first 5 rows (Like SELECT TOP 5)
print(df.head())
print ("below is info:")
# 2. The 'Info': What are the data types and are there NULLs?
print(df.info())

# 3. The 'Describe': Show me the stats
print(" data description : ")
stats = df.describe()
print(type(stats))
print(stats)

# 4. How many unique engines?
num_engines = df['eng_unit_id'].nunique()
print(f"Total Engines: {num_engines}")

# 5. What is the max cycle for each engine? (The 'Failure' point)
max_cycles = df.groupby('eng_unit_id')['cycle'].max()
print(max_cycles.head())

# 6. Check the range of a sensor
print(f"Sensor 2 range: {df['sensor_2'].min()} to {df['sensor_2'].max()}")

# Transformation and cleaning 
# identify dead sensors (zero variance)
# Look at the 'std' row. Find column names where the value is 0.0

dead_cols = stats.columns[stats.loc['std'] == 0].tolist()

print(f"Sensors with zero variance (Dead): {dead_cols}")
# 1.drop dead sensors
df_clean = df.drop(columns=dead_cols)
print(f"Dropped: {dead_cols}")

# 2. Downcast to float32 (save memory)
float_cols = df_clean.select_dtypes(include=['float64']).columns
df_clean[float_cols] = df_clean[float_cols].astype('float32')
print("Data types after downcasting:")
print(df_clean.dtypes)

# 3 add new column RUL
max_cycle = df_clean.groupby('eng_unit_id')['cycle'].transform('max')

df_clean['target_rul'] = max_cycle - df_clean['cycle']
print(df_clean.info())

# 3.1 Rename the RUL file column to match for the merge
df_rul = pd.read_sql("SELECT * FROM bronze.rul_fd001", engine)
df_rul['eng_unit_id'] = df_rul.index + 1 # Assigning IDs based on row index to serve as fk