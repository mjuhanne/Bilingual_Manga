from pymongo.mongo_client import MongoClient
# Create a new client and connect to the server
client = MongoClient()

# Send a ping to confirm a successful connection
if __name__ == '__main__':
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)