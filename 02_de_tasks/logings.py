import logging
import os

# logging.disable(logging.CRITICAL)
# To disable all logging messages, uncomment the above line."Ignore every log message at this level OR LOWER."
"""
basicConfig() parameters of interest:
level= (The Floor): Sets the minimum severity allowed.

Set to INFO: Shows INFO, WARNING, ERROR, CRITICAL. (DEBUG is blocked).

disable() (The Ceiling): Sets the maximum level to be silenced.

Disable INFO: Hides INFO and DEBUG. (WARNING, ERROR, CRITICAL still show thats why we disable critical if every log needed to be ignored
"""
# Create a 'logs' directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO, # Change this to DEBUG when you are stuck
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/pipeline.log"), # Writes to a file
        logging.StreamHandler() # Also prints to your terminal
    ]
)

# Example usage:
logging.info("ETL Pipeline started.")
try:
    # Your SQL/Python logic here
    logging.debug("Attempting to connect to ODBC...")
except Exception as e:
    logging.error(f"Pipeline failed: {e}")