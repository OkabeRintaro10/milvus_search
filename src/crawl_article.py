import requests  # Import the requests library for making HTTP requests
from bs4 import BeautifulSoup  # Import BeautifulSoup for parsing HTML


def extract_authors(article):
    """Extract authors from the <ul> tag."""
    # Find the authors tag and extract author names
    authors_tag = article.find("ul", class_="c-author-list")
    if authors_tag:
        authors = [li.text.strip() for li in authors_tag.find_all("li")]
        return ", ".join(authors)
    return "N/A"


def crawl_articles(base_url):
    """Crawl articles from the given base URL."""
    # Fetch the webpage content
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    # Extract article information
    for article in soup.find_all("article"):
        title = article.find("h3").text.strip()
        pub_date = (
            article.find("time", class_="c-meta__item").text.strip()
            if article.find("time", class_="c-meta__item")
            else "N/A"
        )
        abstract = (
            article.find("div", class_="c-card__summary").text.strip()
            if article.find("div", class_="c-card__summary")
            else "N/A"
        )
        author = extract_authors(article)
        articles.append(
            {
                "title": title,
                "pub_date": pub_date,
                "abstract": abstract,
                "author": author,
            }
        )
    return articles


# Configuration setup
base_url = "https://www.nature.com/subjects/oncology"
# Crawl articles
crawl_data = crawl_articles(base_url)
