import mysql.connector  # Import mysql.connector for MySQL database interaction
from pymilvus import (
    MilvusClient,
    CollectionSchema,
    FieldSchema,
    DataType,
)  # Import MilvusClient and related classes
import json  # Import json for working with JSON data

from sentence_transformers import (
    SentenceTransformer,
)  # Import SentenceTransformer for text embeddings
from crawl_article import crawl_data
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

def embed_and_store(data, db_config):
    """Embed titles and store them in Milvus."""
    # Initialize Milvus client and embed titles
    milvus = MilvusClient("./test.db")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embeddings = model.encode([d["title"] for d in data])
    name = "articles"
    # Define Milvus schema
    schema = CollectionSchema(
        fields=[
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(
                name="title",
                dtype=DataType.VARCHAR,
                max_length=1000,
                enable_analyzer=True,  # Whether to enable text analysis for this field
                enable_match=True,
            ),  # Whether to enable text match),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        ],
        auto_id=True,
        enable_dynamic_field=False,
    )
    # Create or use existing Milvus collection
    try:
        if name not in milvus.list_collections():
            milvus.create_collection(collection_name=name, schema=schema)
            print("Schema Created")
        # Load the collection
        milvus.load_collection(name)
        # Insert data into Milvus
        insert_data = [
            {"title": d["title"], "embedding": list(embedding)}
            for d, embedding in zip(data, embeddings)
        ]
        ids = milvus.insert(collection_name=name, data=insert_data)
        index_params = MilvusClient.prepare_index_params()

        # 4.2. Add an index on the vector field.
        index_params.add_index(
            field_name="embedding",
            metric_type="L2",
            index_type="IVF_FLAT",
            index_name="vector_index",
            params={"nlist": 128},
        )
        milvus.create_index(name, index_params=index_params, sync=False)
        milvus.load_collection(name)
        print(f"Data inserted into Milvus with IDs: {ids}")

        # Establish MySQL connection
        mydb = mysql.connector.connect(**db_config)
        cursor = mydb.cursor()

        # Add 'milvus_id' column if it doesn't exist
        cursor.execute("SHOW COLUMNS FROM articles LIKE 'milvus_id'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE articles ADD COLUMN milvus_id BIGINT")
            mydb.commit()
            print("Column 'milvus_id' added to table 'articles'.")

        # Update MySQL with Milvus IDs based on titles
        for i, article in enumerate(data):
            sql = "UPDATE articles SET milvus_id = %s WHERE title = %s"
            val = (ids["ids"][i], article["title"])
            cursor.execute(sql, val)

        mydb.commit()
        print("MySQL updated with IDs.")

    except Exception as e:
        print(f"Error in Milvus operations: {e}")
        print(
            "Schema (for detailed debugging):", json.dumps(schema.to_dict(), indent=4)
        )
    finally:
        milvus.close()
        if mydb.is_connected():
            cursor.close()
            mydb.close()


embed_and_store(crawl_data, db_config = get_db_config())
