import csv
from pymongo import MongoClient

# Replace the following placeholders with your MongoDB Atlas connection string
# and other credentials
# client = MongoClient('mongodb+srv://gaja:gaja123@cluster0.jdoybcv.mongodb.net/gameproject')

ATLAS_CONNECTION_STRING = "mongodb+srv://gaja:gaja123@cluster0.jdoybcv.mongodb.net/gameproject"
DB_NAME = "gameproject"
COLLECTION_NAME = "winnersdetails"
CSV_FILE_PATH = "exported_collection.csv"

# Connect to MongoDB Atlas cluster
client = MongoClient(ATLAS_CONNECTION_STRING)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Fetch all documents from the collection
cursor = collection.find()

# Get the count of documents in the collection
document_count = collection.count_documents({})

# Export data to CSV file
with open(CSV_FILE_PATH, "w", newline="") as csvfile:
    fieldnames = list(cursor[0].keys()) if document_count > 0 else []
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for document in cursor:
        writer.writerow(document)

print(f"Data from '{COLLECTION_NAME}' collection exported to '{CSV_FILE_PATH}' successfully.")
