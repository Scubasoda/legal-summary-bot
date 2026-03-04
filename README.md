# Legal Summary Bot

Automated case law blog generator for UK legal practices. Fetches latest judgments from the National Archives and generates AI-powered summaries using **Mistral AI**.

## How It Works

1. **Scheduled Runs**: GitHub Actions runs every 21 days
2. **Source Rotation**: Automatically cycles through:
   - Criminal Law cases
   - Family Law cases
   - Housing Law cases
3. **AI Generation**: Uses Mistral AI to create professional blog posts
4. **Auto-Commit**: Generated posts are committed back to the repository

## Setup Instructions

### 1. Get Your Mistral API Key

1. Go to [Mistral AI Console](https://console.mistral.ai/)
2. Sign up or log in
3. Create a new API key
4. Copy the key (starts with `...`)

### 2. Add API Key to GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

- **Name**: `MISTRAL_API_KEY`
- **Value**: Your Mistral API key

### 3. Configure the Workflow (Optional)

Edit `.github/workflows/generate-blog.yml` to customize:
- Schedule frequency (default: every 21 days)
- Case law categories
- Output format

### 4. Manual Trigger

You can manually run the workflow anytime:
1. Go to **Actions → Generate Legal Blog Post**
2. Click **Run workflow**

## Output

Generated blog posts are saved to `src/data/blogPosts.json` in this format:

```json
{
  "id": "blog_1234567890",
  "title": "Case Analysis: Recent Criminal Law Development",
  "slug": "20240304-case-analysis",
  "excerpt": "Brief summary...",
  "content": "<h2>Introduction</h2><p>Full HTML content...</p>",
  "category": "criminal",
  "sourceUrl": "https://caselaw.nationalarchives.gov.uk/...",
  "sourceTitle": "Original case title",
  "publishedAt": "2024-03-04",
  "generatedAt": "2024-03-04T10:00:00Z",
  "readTime": 5
}
```

## File Structure

```
.github/workflows/generate-blog.yml  # GitHub Actions workflow
scripts/generate_blog.py              # Python script for generation
src/data/blogPosts.json               # Generated blog posts (auto-updated)
```

## Customization

### Change Categories

Edit `scripts/generate_blog.py` and modify `CASE_LAW_SOURCES`:

```python
CASE_LAW_SOURCES = [
    {
        "category": "criminal",
        "name": "Criminal Law",
        "feed_url": "https://caselaw.nationalarchives.gov.uk/atom.xml?query=criminal&order=-date",
        "search_url": "https://caselaw.nationalarchives.gov.uk/search?query=criminal&order=-date"
    },
    # Add more categories...
]
```

### Change Schedule

Edit `.github/workflows/generate-blog.yml`:

```yaml
on:
  schedule:
    - cron: '0 9 */21 * *'  # Every 21 days at 9am UTC
```

Cron format: `minute hour day month day-of-week`

### Change AI Model

Edit `scripts/generate_blog.py`:

```python
response = client.chat.complete(
    model="mistral-large-latest",  # Options: mistral-small-latest, mistral-medium-latest, mistral-large-latest
    ...
)
```

## Requirements

- Python 3.11+
- Mistral AI API key
- GitHub repository with Actions enabled

## License

MIT
