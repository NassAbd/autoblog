import os
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Récupérer la clé API Groq depuis les secrets
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_latest_ai_news():
    """Récupère le dernier article du flux RSS TechCrunch AI"""
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
    """Télécharge et extrait le contenu principal d’un article TechCrunch"""
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

    # Charger le prompt de base
    with open("py_scripts/prompt.txt", "r", encoding="utf-8") as f:
        base_prompt = f.read()

    # Récupérer le dernier article IA
    news = get_latest_ai_news()
    news_context = ""

    if news:
        article_text = fetch_article_content(news["link"])
        if article_text:
            # Tronquer si trop long pour éviter dépassement de tokens
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

    # Prompt final
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

    # Nom du fichier = date du jour
    filename = get_unique_filename()

    # Extraire le titre depuis le premier H1
    title_match = re.search(r"^# (.+)", content, re.MULTILINE)
    if not title_match:
        raise ValueError("❌ Impossible de trouver un titre (# ...) dans le contenu généré.")

    title = title_match.group(1).strip()

    # Supprimer le premier H1 du contenu
    content = re.sub(r"^# .+\n+", "", content, count=1, flags=re.MULTILINE)

    # Écrire le fichier Markdown avec front matter correct
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"""---
title: "{title}"
date: {date}
---

{content}
""")

    print(f"✅ Article généré : {filename}")

if __name__ == "__main__":
    generate_post()
