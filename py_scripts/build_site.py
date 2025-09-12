import os
import re
from datetime import datetime
import markdown
from jinja2 import Environment, FileSystemLoader

# --- Configuration ---
CONTENT_DIR = "content"
PUBLIC_DIR = "public"
TEMPLATES_DIR = "templates"

def parse_front_matter(content):
    """Parses YAML front matter from a Markdown file."""
    front_matter = {}
    # The front matter is between the '---' lines
    match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return None, content

    yaml_content = match.group(1)
    body = content[match.end():]

    # Simple key-value parsing
    for line in yaml_content.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            front_matter[key.strip()] = value.strip().strip('"')

    return front_matter, body


def main():
    """Main function to build the static site."""
    print("🚀 Starting site build...")

    # --- 1. Collect and parse all posts ---
    posts = []
    if not os.path.exists(CONTENT_DIR):
        print(f"⚠️ Content directory '{CONTENT_DIR}' not found. No posts to build.")
    else:
        for filename in os.listdir(CONTENT_DIR):
            if filename.endswith(".md"):
                filepath = os.path.join(CONTENT_DIR, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    file_content = f.read()

                front_matter, md_content = parse_front_matter(file_content)
                if not front_matter:
                    print(f"⚠️ Skipping {filename}: no front matter found.")
                    continue

                # Convert Markdown content to HTML
                html_content = markdown.markdown(md_content)

                # Create a slug from the filename
                slug = os.path.splitext(filename)[0]

                post_data = {
                    "title": front_matter.get("title", "Untitled"),
                    "date": front_matter.get("date", ""),
                    "content": html_content,
                    "slug": slug,
                }
                posts.append(post_data)

    # --- 2. Sort posts by date (newest first) ---
    if posts:
        posts.sort(key=lambda p: datetime.strptime(p["date"], "%Y-%m-%d"), reverse=True)
        print(f"✅ Found and processed {len(posts)} posts.")
    else:
        print("ℹ️ No posts found to render.")


    # --- 3. Set up Jinja2 environment ---
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    index_template = env.get_template("index.html")
    post_template = env.get_template("post.html")
    print("✅ Jinja2 environment configured.")

    # --- 4. Render index page ---
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    index_html = index_template.render(posts=posts)
    with open(os.path.join(PUBLIC_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    print("✅ index.html rendered.")


    # --- 5. Render individual post pages ---
    post_output_dir = os.path.join(PUBLIC_DIR, "posts")
    os.makedirs(post_output_dir, exist_ok=True)

    for post in posts:
        post_html = post_template.render(post=post)
        output_path = os.path.join(post_output_dir, f"{post['slug']}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(post_html)

    if posts:
        print(f"✅ All {len(posts)} posts rendered.")

    print("🎉 Site build complete!")


if __name__ == "__main__":
    main()
