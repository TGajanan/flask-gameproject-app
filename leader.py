import csv
from pymongo import MongoClient
import pandas as pd

# Your existing MongoDB Atlas and collection information
ATLAS_CONNECTION_STRING = "mongodb+srv://gaja:gaja123@cluster0.jdoybcv.mongodb.net/gameproject"
# ATLAS_CONNECTION_STRING = "YOUR_ATLAS_CONNECTION_STRING"
DB_NAME = "gameproject"
COLLECTION_NAME = "winnersdetails"

# Path to the CSV file
CSV_FILE_PATH = "exported_collection.csv"

def get_winner_details():
    # Connect to MongoDB Atlas cluster
    client = MongoClient(ATLAS_CONNECTION_STRING)
    db = client[DB_NAME]
    collection2 = db[COLLECTION_NAME]

    # Perform MongoDB aggregation to get winners details
    pipeline = [
        {
            "$match": {"winner": True}
        },
        {
            "$group": {
                "_id": "$user_id",
                "winner_count": {"$sum": 1},
                "profileImage": {"$first": "$profileImage"},
                "email": {"$first": "$email"},
                "fname": {"$first": "$fname"},
                "mobile_number": {"$first": "$mobile_number"},
                "state": {"$first": "$state"},
                "address": {"$first": "$address"},
                "timestamp": {"$first": "$timestamp"}
            }
        },
        {
            "$sort": {
                "winner_count": -1,  # DESCENDING order for winner_count
                "timestamp": 1       # ASCENDING order for timestamp
            }
        }
    ]

    # Execute the aggregation pipeline
    result = collection2.aggregate(pipeline)

    # Convert the aggregation result to a list of dictionaries
    winners_list = list(result)

    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(winners_list)

    # Sort the DataFrame by winner_count and timestamp
    df_sorted = df.sort_values(by=["winner_count", "timestamp"], ascending=[False, True])

    # Convert the DataFrame back to a list of dictionaries and return
    return df_sorted.to_dict(orient="records")


# Call the function to get the sorted winners details
sorted_winners = get_winner_details()
print(sorted_winners)
