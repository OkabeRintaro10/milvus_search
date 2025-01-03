from transformers import pipeline  # Import the summarization pipeline from transformers
from crawl_article import (
    crawl_data,
)  # Import the crawled data from the crawl_article module

summarizer = pipeline("summarization")


def summarize_text(text):
    """Summarize the given text."""
    # Generate a summary using the summarization pipeline
    return summarizer(text, max_length=50, min_length=20, do_sample=False)[0][
        "summary_text"
    ]


# Summarize abstracts
for article in crawl_data:
    if len(article["abstract"]) >= 50:
        article["summary"] = summarize_text(article["abstract"])
    else:
        article["summary"] = "N/A"
