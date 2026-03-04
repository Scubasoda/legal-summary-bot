#!/usr/bin/env python3
"""
Ervaid Law Blog Generator
Fetches latest case law from National Archives and generates AI summaries using Mistral AI.
Runs via GitHub Actions on a schedule.
"""

import feedparser
import os
import json
import re
from datetime import datetime
from mistralai import Mistral

# Configuration
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
BLOG_DATA_FILE = "src/data/blogPosts.json"

# Case law sources - rotates through these
CASE_LAW_SOURCES = [
    {
        "category": "criminal",
        "name": "Criminal Law",
        "feed_url": "https://caselaw.nationalarchives.gov.uk/atom.xml?query=criminal&order=-date",
        "search_url": "https://caselaw.nationalarchives.gov.uk/search?query=criminal&order=-date"
    },
    {
        "category": "family",
        "name": "Family Law",
        "feed_url": "https://caselaw.nationalarchives.gov.uk/atom.xml?query=family&order=-date",
        "search_url": "https://caselaw.nationalarchives.gov.uk/search?query=family&order=-date"
    },
    {
        "category": "housing",
        "name": "Housing Law",
        "feed_url": "https://caselaw.nationalarchives.gov.uk/atom.xml?query=housing&order=-date",
        "search_url": "https://caselaw.nationalarchives.gov.uk/search?query=housing&order=-date"
    }
]

def get_week_number(date):
    """Get ISO week number."""
    return date.isocalendar()[1]

def get_this_week_source():
    """Determine which source to use based on current week."""
    week_num = get_week_number(datetime.now())
    index = week_num % len(CASE_LAW_SOURCES)
    return CASE_LAW_SOURCES[index]

def load_existing_posts():
    """Load existing blog posts from JSON file."""
    try:
        with open(BLOG_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_posts(posts):
    """Save blog posts to JSON file."""
    with open(BLOG_DATA_FILE, 'w') as f:
        json.dump(posts, f, indent=2)

def generate_slug(title, date_str):
    """Generate URL-friendly slug from title and date."""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    date_part = date_str.replace('-', '')
    return f"{date_part}-{slug[:50]}"

def fetch_latest_case(source):
    """Fetch the latest case from the National Archives feed."""
    print(f"Fetching cases from: {source['name']}")
    print(f"Feed URL: {source['feed_url']}")
    
    feed = feedparser.parse(source['feed_url'])
    
    if not feed.entries:
        print("No cases found in feed.")
        return None
    
    latest = feed.entries[0]
    
    case = {
        'title': latest.get('title', 'Untitled Case'),
        'link': latest.get('link', ''),
        'published': latest.get('published', ''),
        'summary': latest.get('summary', ''),
        'content': latest.get('content', [{}])[0].get('value', '') if latest.get('content') else latest.get('summary', ''),
        'court': latest.get('author', 'Unknown Court') if latest.get('author') else 'UK Court'
    }
    
    print(f"Found case: {case['title']}")
    return case

def generate_blog_post(case, source):
    """Generate a blog post using Mistral AI."""
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY environment variable not set")
    
    client = Mistral(api_key=MISTRAL_API_KEY)
    
    prompt = f"""You are a legal content writer for Ervaid Law Solicitors, a UK law firm.

Write a professional blog post summarizing and analyzing this recent case law:

Case Title: {case['title']}
Court: {case['court']}
Date: {case['published']}
Summary: {case['summary'][:2000] if case['summary'] else 'See full judgment'}

Your blog post should:
1. Have a compelling, professional title (different from the case title)
2. Include an engaging introduction explaining the case's significance
3. Summarize the key facts and legal issues
4. Explain the court's decision and reasoning
5. Discuss the practical implications for clients and legal practitioners
6. Be written in a clear, accessible style suitable for both legal professionals and informed lay clients
7. Be approximately 500-800 words
8. Use HTML formatting with <h2> for headings and <p> for paragraphs

Format your response as JSON with these fields:
- title: The blog post title (string)
- excerpt: A 2-3 sentence summary for the blog listing (string)
- content: The full HTML content (string with HTML tags)
- readTime: Estimated reading time in minutes (number)

Return ONLY the JSON object, no markdown formatting."""
    
    print("Generating blog post with Mistral AI...")
    
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": "You are a professional legal content writer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2048
    )
    
    generated_text = response.choices[0].message.content
    
    # Parse the JSON response
    try:
        # Extract JSON from response (Mistral might wrap it in markdown)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', generated_text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        else:
            json_match = re.search(r'(\{.*\})', generated_text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            else:
                text = generated_text
        
        result = json.loads(text)
        return result
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        print(f"Response text: {generated_text[:500]}")
        return generate_fallback_post(case, source)

def generate_fallback_post(case, source):
    """Generate a fallback blog post if AI generation fails."""
    now = datetime.now()
    return {
        'title': f"Recent Developments in {source['name']}: {case['title']}",
        'excerpt': f"An analysis of {case['title']}, a significant recent decision with important implications for {source['name']} practitioners.",
        'content': f"""<h2>Introduction</h2>
<p>The courts recently handed down judgment in <em>{case['title']}</em>, a case that raises important issues for {source['name']} practitioners and their clients.</p>

<h2>Background</h2>
<p>{case['summary'][:500] if case['summary'] else 'The case involves significant legal issues requiring careful analysis.'}</p>

<h2>The Court's Decision</h2>
<p>The court carefully considered the evidence and legal arguments presented by both parties before reaching its conclusion. The judgment provides valuable guidance on the proper approach to similar cases.</p>

<h2>Practical Implications</h2>
<p>This decision has significant practical implications for legal practitioners advising clients in {source['name']} matters, parties involved in ongoing or prospective litigation, and the development of case law in this area.</p>

<h2>Conclusion</h2>
<p>The judgment in <em>{case['title']}</em> represents an important development in {source['name']}. Practitioners should carefully consider its implications when advising clients and preparing cases.</p>

<p><em>For advice on how this case may affect your situation, please contact Ervaid Law Solicitors on 020 4513 6001.</em></p>""",
        'readTime': 5
    }

def create_blog_post(case, generated, source):
    """Create a complete blog post object."""
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    
    return {
        'id': f"blog_{int(now.timestamp())}",
        'title': generated['title'],
        'slug': generate_slug(generated['title'], date_str),
        'excerpt': generated['excerpt'],
        'content': generated['content'],
        'category': source['category'],
        'sourceUrl': case['link'],
        'sourceTitle': case['title'],
        'publishedAt': date_str,
        'generatedAt': now.isoformat(),
        'readTime': generated.get('readTime', 5)
    }

def should_generate_new_post(existing_posts):
    """Check if we should generate a new post (every 21 days)."""
    if not existing_posts:
        return True
    
    latest = max(existing_posts, key=lambda p: p.get('publishedAt', ''))
    latest_date = datetime.strptime(latest['publishedAt'], '%Y-%m-%d')
    
    days_since = (datetime.now() - latest_date).days
    return days_since >= 21

def main():
    """Main workflow."""
    print("=" * 60)
    print("Ervaid Law Blog Generator - Mistral AI")
    print("=" * 60)
    
    existing_posts = load_existing_posts()
    print(f"Loaded {len(existing_posts)} existing posts")
    
    if not should_generate_new_post(existing_posts):
        latest = max(existing_posts, key=lambda p: p.get('publishedAt', ''))
        print(f"Latest post is from {latest['publishedAt']}. Skipping generation (runs every 21 days).")
        return
    
    source = get_this_week_source()
    print(f"\nThis week's source: {source['name']}")
    
    case = fetch_latest_case(source)
    if not case:
        print("No case found. Exiting.")
        return
    
    try:
        generated = generate_blog_post(case, source)
    except Exception as e:
        print(f"Error generating post: {e}")
        generated = generate_fallback_post(case, source)
    
    post = create_blog_post(case, generated, source)
    
    existing_posts.insert(0, post)
    existing_posts = existing_posts[:20]
    
    save_posts(existing_posts)
    
    print(f"\n✓ Generated blog post: {post['title']}")
    print(f"✓ Saved to {BLOG_DATA_FILE}")
    print(f"✓ Total posts: {len(existing_posts)}")

if __name__ == "__main__":
    main()
