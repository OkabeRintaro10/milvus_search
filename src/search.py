import mysql.connector
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer
import configparser
import os


def get_db_config(config_file="../config.ini"):
    """Retrieves the database configuration from a config.ini file."""
    config = configparser.ConfigParser()
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")
    config.read(config_file)

    if "mysql" not in config:
        raise ValueError("Section 'database' not found in config file.")

    try:
        db_config = {
            "host": config.get("mysql", "host"),
            "user": config.get("mysql", "user"),
            "password": config.get("mysql", "password"),
            "database": config.get("mysql", "database"),  # Added database name
        }
        return db_config
    except configparser.NoOptionError as e:
        raise ValueError(f"Missing option in database config: {e}")


db_config = get_db_config()


def search_articles(query, db_config, milvus_collection="articles", top_k=10):
    """Search for articles based on a query and retrieve details from MySQL."""
    mydb = None
    milvus = None
    try:
        # 1. Embed the query
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        query_embedding = model.encode([query])[0]

        # 2. Search in Milvus (Corrected)
        milvus = MilvusClient("./test.db")  # Or your Milvus connection details
        milvus.load_collection(milvus_collection)
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

        results = milvus.search(
            collection_name=milvus_collection,
            data=[list(query_embedding)],
            anns_field="embedding",
            params=search_params,
            limit=top_k,
        )
        milvus_ids = [item["id"] for item in results[0]]  # Extract IDs correctly

        # 3. Fetch from MySQL (Corrected)
        if milvus_ids:  # Check if milvus_ids is not empty
            mydb = mysql.connector.connect(**db_config)
            cursor = mydb.cursor()
            placeholders = ",".join(["%s"] * len(milvus_ids))
            sql = f"SELECT * FROM articles WHERE milvus_id IN ({placeholders})"
            cursor.execute(sql, milvus_ids)
            articles = cursor.fetchall()
            return articles
        else:
            return []  # Return empty list if no results from milvus
    except Exception as e:
        print(f"Error during search: {e}")
        return []
    finally:
        if milvus:
            milvus.close()
        if mydb and mydb.is_connected():
            cursor.close()
            mydb.close()


# Example usage
query = "cancer research"
results = search_articles(query, db_config)

if results:
    print("Search Results:")
    for article in results:
        print(article)  # Print article details
else:
    print("No matching articles found.")
