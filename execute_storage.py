import subprocess
import sys

# Install TinyDB if not already installed
try:
    from tinydb import TinyDB, Query
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'tinydb'])
    from tinydb import TinyDB, Query

# Execute the storage script
exec(open('./store_trade_data.py').read())
