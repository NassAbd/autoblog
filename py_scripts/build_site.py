import os
import re
import math
from datetime import datetime
import markdown
from jinja2 import Environment, FileSystemLoader

# --- Configuration ---
CONTENT_DIR = "content"
PUBLIC_DIR = "public"
TEMPLATES_DIR = "templates"
POSTS_PER_PAGE = 5
BASE_URL = os.environ.get("BASE_URL", "")


def parse_front_matter(content):
    """Parses YAML front matter from a Markdown file."""
    front_matter = {}
    match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return None, content

    yaml_content = match.group(1)
    body = content[match.end():]

    for line in yaml_content.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            front_matter[key.strip()] = value.strip().strip('"')

    return front_matter, body


def paginate(posts, per_page=POSTS_PER_PAGE):
    """Split posts into chunks for pagination."""
    total_pages = math.ceil(len(posts) / per_page)
    for page in range(1, total_pages + 1):
        start = (page - 1) * per_page
        end = start + per_page
        yield page, posts[start:end], total_pages


def main():
    print("🚀 Starting site build...")

    # --- Collect posts ---
    posts = []
    if os.path.exists(CONTENT_DIR):
        for filename in os.listdir(CONTENT_DIR):
            if filename.endswith(".md"):
                filepath = os.path.join(CONTENT_DIR, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    file_content = f.read()

                front_matter, md_content = parse_front_matter(file_content)
                if not front_matter:
                    continue

                html_content = markdown.markdown(md_content)
                slug = os.path.splitext(filename)[0]

                posts.append({
                    "title": front_matter.get("title", "Untitled"),
                    "date": front_matter.get("date", ""),
                    "content": html_content,
                    "slug": slug,
                })

    # Sort posts by date (newest first)
    posts.sort(key=lambda p: datetime.strptime(p["date"], "%Y-%m-%d"), reverse=True)
    print(f"✅ Found {len(posts)} posts.")

    # --- Setup Jinja2 environment ---
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    index_template = env.get_template("index.html")
    post_template = env.get_template("post.html")

    # --- Render index pages with pagination ---
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    for page, page_posts, total_pages in paginate(posts):
        html = index_template.render(
            posts=page_posts,
            current_page=page,
            total_pages=total_pages,
            base_url=BASE_URL
        )


        if page == 1:
            output_path = os.path.join(PUBLIC_DIR, "index.html")
        else:
            page_dir = os.path.join(PUBLIC_DIR, "page", str(page))
            os.makedirs(page_dir, exist_ok=True)
            output_path = os.path.join(page_dir, "index.html")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    print(f"✅ Index pages rendered with {POSTS_PER_PAGE} posts per page.")

    # --- Render individual post pages with previous/next navigation ---
    post_output_dir = os.path.join(PUBLIC_DIR, "posts")
    os.makedirs(post_output_dir, exist_ok=True)

    for i, post in enumerate(posts):
        previous_post = posts[i + 1] if i + 1 < len(posts) else None
        next_post = posts[i - 1] if i - 1 >= 0 else None

        post_html = post_template.render(
            post=post,
            previous_post=previous_post,
            next_post=next_post,
            base_url=BASE_URL
        )

        output_path = os.path.join(post_output_dir, f"{post['slug']}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(post_html)

    print(f"✅ All {len(posts)} post pages rendered.")
    print("🎉 Site build complete!")


if __name__ == "__main__":
    main()
