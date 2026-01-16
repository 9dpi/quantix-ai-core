import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

print("Importing health...")
from quantix_core.api.routes import health
print("Importing structure...")
from quantix_core.api.routes import structure
print("Importing features...")
from quantix_core.api.routes import features
print("Importing signals...")
from quantix_core.api.routes import signals
print("Importing ingestion...")
from quantix_core.api.routes import ingestion
print("Importing csv_ingestion...")
from quantix_core.api.routes import csv_ingestion
print("Importing admin...")
from quantix_core.api.routes import admin
print("Importing lab...")
from quantix_core.api.routes import lab
print("Importing public...")
from quantix_core.api.routes import public
print("Importing reference...")
from quantix_core.api.routes import reference
print("Importing lab_reference...")
from quantix_core.api.routes import lab_reference
print("All imports successful!")
