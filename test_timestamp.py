import sys
import logging
from crawler.utils.timestamp_refresher import get_valid_timestamp

# Setup simple logging
logging.basicConfig(level=logging.INFO)

print(">>> Starting Timestamp Refresh Test...")
try:
    ts = get_valid_timestamp()
    if ts:
        print(f">>> SUCCESS! Captured Timestamp: {ts}")
    else:
        print(">>> FAILED. No timestamp captured.")
except Exception as e:
    print(f">>> ERROR: {e}")
