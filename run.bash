#!/bin/bash
# Run all components of the project
python3 src\crawl_article.py
python3 src\summarization.py
python3 src\store_in_mysql.py
python3 src\embed_store.py
python3 src\search.py
