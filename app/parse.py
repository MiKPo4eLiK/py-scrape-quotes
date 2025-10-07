from dataclasses import dataclass
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
import csv
import time

BASE_URL = "https://quotes.toscrape.com"


@dataclass
class Quote:
    text: str
    author: str
    tags: List[str]


@dataclass
class Author:
    name: str
    birth_date: str
    birth_location: str
    description: str


def get_quotes_from_page(url: str) -> tuple[List[Quote], Optional[str], List[str]]:
    """Gets citations from one page and returns the next link and author links."""
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    quotes_data = []
    author_links = []

    for quote_div in soup.select(".quote"):
        text = quote_div.select_one(".text").get_text(strip=True)
        author = quote_div.select_one(".author").get_text(strip=True)
        tags = [t.get_text(strip=True) for t in quote_div.select(".tag")]
        author_url = BASE_URL + quote_div.select_one("a[href*='/author/']")["href"]
        author_links.append(author_url)

        quotes_data.append(Quote(text=text, author=author, tags=tags))

    next_btn = soup.select_one(".next > a")
    next_url = BASE_URL + next_btn["href"] if next_btn else None

    return quotes_data, next_url, author_links


def get_author_info(url: str) -> Author:
    """Parses the author page and returns data."""
    response = requests.get(url, timeout=5)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    name = soup.select_one(".author-title").get_text(strip=True)
    birth_date = soup.select_one(".author-born-date").get_text(strip=True)
    birth_location = soup.select_one(".author-born-location").get_text(strip=True)
    description = soup.select_one(".author-description").get_text(strip=True)

    return Author(name, birth_date, birth_location, description)


def main(output_csv_path: str) -> None:
    url = BASE_URL
    all_quotes: List[Quote] = []
    authors_cache: dict[str, Author] = {}

    while url:
        quotes, url, author_links = get_quotes_from_page(url)
        all_quotes.extend(quotes)

        # Parse authors if not already in cache
        for author_link in set(author_links):
            if author_link not in authors_cache:
                print(f"Parsing author: {author_link}")
                author = get_author_info(author_link)
                authors_cache[author_link] = author
                time.sleep(0.05)

        time.sleep(0.1)
        print(f"✅ Parsed page: {url}")

    # Write the quotes to quotes.csv
    with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["text", "author", "tags"])
        for q in all_quotes:
            writer.writerow([q.text, q.author, ", ".join(q.tags)])

    # Write authors to authors.csv
    with open("authors.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["name", "birth_date", "birth_location", "description"])
        for author in authors_cache.values():
            writer.writerow([
                author.name,
                author.birth_date,
                author.birth_location,
                author.description
            ])

    print(f"✅ Parsed {len(all_quotes)} quotes and {len(authors_cache)} authors.")


if __name__ == "__main__":
    main("quotes.csv")
