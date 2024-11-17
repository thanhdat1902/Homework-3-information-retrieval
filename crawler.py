import urllib.request
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pymongo import MongoClient

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["crawlerDB"]
collection = db["pages"]

# Starting URL and stop criteria
START_URL = "https://www.cpp.edu/sci/computer-science/"
TARGET_TEXT = "Permanent Faculty"

class Frontier:
    def __init__(self):
        self.frontier = [START_URL]  # Use a list as a frontier
        self.visited = set()

    def nextURL(self):
        if self.frontier:
            url = self.frontier.pop()
            self.visited.add(url)
            return url
        return None

    def addURL(self, url):
        if url not in self.visited and url not in self.frontier:
            self.frontier.append(url)  # Enfrontier

    def done(self):
        return len(self.frontier) == 0

def retrieveHTML(url):
    try:
        response = urllib.request.urlopen(url)
        if "text/html" in response.getheader("Content-Type"):
            return response.read()
    except Exception as e:
        print(f"Error retrieving {url}: {e}")
    return None

def storePage(url, html):
    if html:
        collection.insert_one({"url": url, "html": html.decode("utf-8")})

def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        # Handle relative URLs and absolute URLs, if href is different domain than START_URL then ignore
        full_url = urljoin(START_URL, href)
        if full_url.startswith(START_URL):  # Restrict to subdomain
            links.append(full_url)
    return links

def target_page(html):
    soup = BeautifulSoup(html, "html.parser")
    h1_tag = soup.find("h1", class_="cpp-h1")
    return h1_tag and h1_tag.get_text() == "Permanent Faculty"

def crawler(frontier):
    while not frontier.done():
        url = frontier.nextURL()
        if not url:
            break

        print(f"Crawling: {url}")
        html = retrieveHTML(url)
        if html:
            storePage(url, html)
            if target_page(html):
                print(f"Target page found: {url}")
                return
            for link in parse(html):
                frontier.addURL(link)

if __name__ == "__main__":
    # Create frontier
    frontier = Frontier()

    # Start crawling
    crawler(frontier)

    print("Crawling completed.")
