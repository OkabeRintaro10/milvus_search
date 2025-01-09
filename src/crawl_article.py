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


def extract_article_data(article_links, baseurl="https://www.nature.com"):
    """Fetch information from the article such as title, pub_date, abstract etc """
    try:
        articles = []
        for link in article_links:
            response = requests.get(baseurl + link)
            # print(f"Processing: {baseurl + link}")
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            # Extract article information
            for article in soup.find_all("article"):
                title = article.find("h1").text.strip() if article.find("h1") else "N/A"

                pub_date = (
                    article.find("time").text.strip() if article.find("time") else "N/A"
                )
                abstract = (
                    article.find("div", class_="c-article-section__content").text.strip()
                    if article.find("div", class_="c-article-section__content")
                    else "N/A"
                )
                authors = extract_authors(article)
                articles.append(
                    {"title": title, "pub_date": pub_date, "abstract": abstract, "authors": authors}
                )
            
        return [item for item in articles if item.get('title') != 'N/A']

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def extract_article_links(all_articles_url):
    try:
        response = requests.get(all_articles_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        article_links = []
        """Finding all the articles in the website
        soup.find_all("article"): This syntax fetches all the HTLM5 tag <article> which is SEO optimized
        Ref: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/article
        
        for article in soup.find_all("article"): ... finds all the <a> tags present in each <article> tag and appends the href to a seperate list """
        for article in soup.find_all("article"):
            link = article.find("a")
            if link:
                article_links.append(link["href"])

        print(f"Found {len(article_links)} article links.")
        article = extract_article_data(article_links)

        return article

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Configuration setup
base_url = "https://www.nature.com/subjects/oncology"
# Crawl articles
crawl_data = extract_article_links(base_url)
