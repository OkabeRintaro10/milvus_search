import mysql.connector
from src.summarization import crawl_data
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


def store_in_mysql(data, db_config):
    """Store article data in MySQL, creating database and table if needed."""
    try:
        mydb = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
        )
        mycursor = mydb.cursor()

        # Create database if it doesn't exist
        mycursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
        mycursor.execute(f"USE {db_config['database']}")

        # Create table if it doesn't exist
        mycursor.execute(
            "CREATE TABLE IF NOT EXISTS articles (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), pub_date VARCHAR(255), abstract TEXT, author VARCHAR(255), summary TEXT)"
        )

        # Insert data into the table
        for article in data:
            sql = "INSERT INTO articles (title, pub_date, abstract, author, summary) VALUES (%s, %s, %s, %s, %s)"
            val = (
                article.get("title"),
                article.get("pub_date"),
                article.get("abstract"),
                article.get("author"),
                article.get("summary"),  # Handle missing 'summary' key
            )
            mycursor.execute(sql, val)

        mydb.commit()
        print(f"{len(data)} articles stored in MySQL.")

    except mysql.connector.Error as err:
        print(f"MySQL error: {err}")

    finally:
        if mydb.is_connected():
            mycursor.close()
            mydb.close()


store_in_mysql(crawl_data, db_config)
