import { MONGO_JMDICT_URL } from '$env/static/private';
import { MongoClient } from 'mongodb';

console.log("Mongo JMDICT URL:" + MONGO_JMDICT_URL);

if (!MONGO_JMDICT_URL) {
    throw new Error('Invalid/Missing environment variable: "MONGO_JMDICT_URL"');
  }

const jmdict_client = new MongoClient(MONGO_JMDICT_URL);

// connect to the database
export async function connect() {
    await jmdict_client.connect();
}

// disconnect from the database
export async function disconnect() {
    await jmdict_client.close();
}

// get the database
export function getJmdictClientDB() {
    return jmdict_client.db();
}