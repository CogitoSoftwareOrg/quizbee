# QuizBee Blog Generator

AI-powered CLI tool for generating high-quality, SEO-optimized blog posts for QuizBee.

## Features

- 🤖 **AI-Powered Generation**: Uses OpenAI GPT-4o-mini to generate complete blog posts
- 🌍 **Multi-Language Support**: Generate content in English and Russian
- 📝 **SEO Optimized**: Automatic title, description, keywords, and structured content
- 💾 **Local Storage**: Save generated posts before uploading
- 🔄 **PocketBase Integration**: Direct upload to QuizBee's blog system
- 🎯 **Template-Based**: Use JSON templates for consistent blog specifications

## Installation

Dependencies are already included in the parent `pyproject.toml`:

```bash
cd scripts/python
uv sync
```

## Quick Start

### 1. Create Raw Input

Create a JSON file in `raw/` directory with your blog specifications:

```json
{
  "topic": "10 Tips for Effective Study Quizzes",
  "target_audience": "students and self-learners",
  "tone": "friendly",
  "length": "medium",
  "category": "tips",
  "languages": ["en"],
  "keywords": ["study tips", "quiz creation", "exam preparation"],
  "special_instructions": "Focus on actionable tips with examples"
}
```

See `raw/example-*.json` for more examples.

### 2. Run CLI

```bash
cd scripts/python
uv run python -m gen_blog.main
```

### 3. Select Action

The CLI provides several commands:

- **generate** - Generate blog post from raw input
- **upload** - Upload generated post to PocketBase
- **update** - Update existing blog post
- **full** - Generate and upload in one go
- **list** - List generated blog posts

## Input Specification

### RawBlogInput Fields

| Field                  | Type   | Description                                             |
| ---------------------- | ------ | ------------------------------------------------------- |
| `topic`                | string | Main topic of the blog post                             |
| `target_audience`      | string | Who is this post for?                                   |
| `tone`                 | enum   | `professional`, `casual`, `educational`, `friendly`     |
| `length`               | enum   | `short` (~500 words), `medium` (~1000), `long` (~1500+) |
| `category`             | string | Blog category (e.g., tips, guides, news, features)      |
| `languages`            | array  | List of languages: `["en"]` or `["en", "ru"]`           |
| `keywords`             | array  | SEO keywords (optional)                                 |
| `special_instructions` | string | Additional requirements (optional)                      |

## Output Structure

Generated blog posts consist of two parts:

### 1. Blog Record (blog collection)

```json
{
  "slug": "how-to-create-effective-quizzes",
  "category": "tips",
  "published": false,
  "tags": ["study-tips", "quiz-creation", "education"],
  "authors": ["QuizBee Team"],
  "cover": null
}
```

### 2. I18n Records (blogI18n collection)

```json
{
  "locale": "en",
  "status": "draft",
  "content": "<p>Full HTML content...</p>",
  "data": {
    "title": "10 Tips for Creating Effective Study Quizzes",
    "description": "Learn proven techniques...",
    "image": null,
    "ogTitle": null,
    "ogDescription": null
  }
}
```

## Directory Structure

```
gen_blog/
├── main.py              # CLI entry point
├── models.py            # Pydantic models
├── agent.py             # AI agent configuration
├── storage.py           # Local file storage
├── uploader.py          # PocketBase uploader
├── raw/                 # Input templates
│   ├── example-quiz-tips.json
│   ├── example-ai-education.json
│   └── example-feature-announcement.json
└── output/              # Generated blog posts (auto-created)
    └── *.json
```

## Workflow Examples

### Generate Only

```bash
# Run CLI
uv run python -m gen_blog.main

# Select: 1 (generate)
# Choose raw input file
# Review generated content
# Output saved to output/
```

### Full Workflow (Generate + Upload)

```bash
# Run CLI
uv run python -m gen_blog.main

# Select: 4 (full)
# Choose raw input file
# Review generated content
# Confirm upload
# Blog post live in PocketBase!
```

### Update Existing Post

```bash
# Generate new version first
# Then run CLI
uv run python -m gen_blog.main

# Select: 3 (update)
# Enter blog post ID
# Choose generated file
# Confirm update
```

## Content Guidelines

The AI agent follows these guidelines:

### HTML Structure

- Semantic HTML with `<h2>` and `<h3>` headings
- All headings have unique `id` attributes for TOC
- Use `<p>`, `<ul>`, `<ol>`, `<strong>`, `<em>`, `<blockquote>`
- Code blocks with `<pre><code>`

### SEO Optimization

- Title: 50-80 characters
- Description: 120-160 characters
- Natural keyword integration
- Descriptive headings
- Comprehensive content

### QuizBee Context

- Platform: AI-powered quiz generation
- Features: Quiz from any material, adaptive learning, mobile apps
- Target: Students, teachers, corporate trainers
- USP: Generate quizzes in seconds from PDFs, videos, text

## Environment Variables

Required in `envs/.env`:

```env
PUBLIC_PB_URL=http://localhost:8090
PB_EMAIL=admin@admin.com
PB_PASSWORD=admin
OPENAI_API_KEY=sk-...
```

## Troubleshooting

### "Failed to load .env file"

- Ensure `envs/.env` exists at repository root
- Check file permissions

### "No raw input files found"

- Create JSON files in `raw/` directory
- Use examples as templates

### PocketBase Upload Errors

- Verify PB_URL, PB_EMAIL, PB_PASSWORD
- Ensure PocketBase is running
- Check blog/blogI18n collections exist

### AI Generation Timeouts

- Increase timeout for longer content
- Check OpenAI API key and quota
- Try shorter `length` setting

## Tips

1. **Start with Examples**: Copy and modify example files
2. **Test Locally First**: Always review generated content before uploading
3. **Iterative Improvement**: Generate multiple versions, pick the best
4. **Multi-Language**: Generate English first, then add Russian
5. **Draft First**: Keep `published: false` until content is reviewed

## Future Enhancements

- [ ] Cover image upload support
- [ ] Image generation for blog posts
- [ ] Batch generation from multiple inputs
- [ ] Content preview in terminal (HTML rendering)
- [ ] Automated SEO scoring
- [ ] Integration with CMS workflow
