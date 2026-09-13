"""
Fetches a webpage and breaks it into small chunks (a few sentences each).
Chunking matters because embeddings work best on small, focused pieces
of text — one giant blob loses precision when you search/compare it.
"""
import requests
from bs4 import BeautifulSoup


def fetch_page_text(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (AgentHub Competitor Watcher)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    return text


def chunk_text(text: str, chunk_size: int = 300) -> list[str]:
    words = text.split()
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return [c for c in chunks if c.strip()]
