import os
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_latest_ai_news():
    """Retrieve the latest article from TechCrunch's AI RSS feed"""
    rss_url = "https://techcrunch.com/category/artificial-intelligence/feed/"
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        return None

    latest = feed.entries[0]
    return {
        "title": latest.title,
        "summary": getattr(latest, "summary", ""),
        "link": latest.link
    }

def fetch_article_content(url):
    """Download and extract the main content of a TechCrunch article"""
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    content_div = soup.find("div", class_="article-content")
    if not content_div:
        return None

    paragraphs = [p.get_text() for p in content_div.find_all("p")]
    return "\n\n".join(paragraphs)

def generate_post():
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    with open("py_scripts/prompt.txt", "r", encoding="utf-8") as f:
        base_prompt = f.read()

    news = get_latest_ai_news()
    news_context = ""

    if news:
        article_text = fetch_article_content(news["link"])
        if article_text:
            article_excerpt = article_text[:3000]

            news_context = f"""
Today's blog post should be inspired by the latest TechCrunch AI article:

Title: {news['title']}
Summary: {news['summary']}
Link: {news['link']}

Here is the main article content to analyze:
{article_excerpt}

Write a full blog post that expands on this news, providing analysis, implications, and future perspectives.
"""
        else:
            news_context = f"""
Today's blog post should be inspired by this TechCrunch AI headline:
{news['title']} ({news['link']}).

Write an analysis that goes beyond the news itself.
"""
    else:
        news_context = "Today's blog post should cover a recent AI or technology trend with fresh insights."

    # Final prompt
    user_prompt = base_prompt + "\n\n" + news_context

    json_data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a helpful AI that writes blog posts."},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 1500,
        "temperature": 0.7,
    }

    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]

    date = datetime.now().strftime("%Y-%m-%d")

    def get_unique_filename(base_dir="content"):
        counter = 0
        while True:
            suffix = f"-{counter}" if counter > 0 else ""
            filename = f"{base_dir}/{date}-auto-post{suffix}.md"
            if not os.path.exists(filename):
                return filename
            counter += 1

    # File name = today's date
    filename = get_unique_filename()

    title_match = re.search(r"^# (.+)", content, re.MULTILINE)
    if not title_match:
        raise ValueError("Cannot find title in generated content")

    title = title_match.group(1).strip()

    # Remove the first H1 from the content
    content = re.sub(r"^# .+\n+", "", content, count=1, flags=re.MULTILINE)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"""---
title: "{title}"
date: {date}
---

{content}
""")

    print(f"✅ Generated article : {filename}")

if __name__ == "__main__":
    generate_post()
