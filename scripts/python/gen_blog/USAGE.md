# QuizBee Blog Generator - Usage Guide

## Quick Start

### Option 1: Using Makefile (Recommended)

```bash
cd scripts/python/gen_blog
make run
```

### Option 2: Direct Python

```bash
cd scripts/python
uv run python -m gen_blog.main
```

## Step-by-Step Workflow

### 1. Prepare Your Input

Create a JSON file in the `raw/` directory with your blog specifications. You can copy and modify one of the examples:

```bash
cp raw/example-quiz-tips.json raw/my-blog-post.json
```

Edit `my-blog-post.json`:

```json
{
  "topic": "Your Blog Topic Here",
  "target_audience": "students preparing for exams",
  "tone": "friendly",
  "length": "medium",
  "category": "tips",
  "languages": ["en"],
  "keywords": ["study", "quizzes", "learning"],
  "special_instructions": "Include practical examples"
}
```

### 2. Generate Blog Post

Run the CLI:

```bash
make run
```

Select **1 (generate)** and choose your input file.

The AI will:

- Generate complete blog post(s) in requested language(s)
- Create SEO-optimized titles and descriptions
- Generate proper HTML structure with headings
- Save output to `output/` directory

**Expected time**: 30-60 seconds for single language, 60-90 seconds for multiple languages.

### 3. Review Generated Content

The output file contains:

```json
{
  "blog": {
    "slug": "your-blog-slug",
    "category": "tips",
    "tags": ["study", "quizzes"],
    "published": false
  },
  "i18n_entries": [
    {
      "locale": "en",
      "status": "draft",
      "content": "<p>Full HTML content...</p>",
      "data": {
        "title": "Your Blog Title",
        "description": "SEO description..."
      }
    }
  ]
}
```

Review the content in your favorite editor. Check:

- Title and description are compelling
- HTML is well-structured
- Content matches your requirements
- Keywords are naturally integrated

### 4. Upload to PocketBase

Once satisfied, upload to PocketBase:

```bash
make run
```

Select **2 (upload)** and choose the generated file.

The script will:

- Show you a preview
- Ask for confirmation
- Upload to PocketBase (blog + blogI18n records)
- Display record IDs

### 5. Publish on Website

1. Go to PocketBase admin: `http://localhost:8090/_/`
2. Navigate to `blog` collection
3. Find your post by slug
4. Set `published = true`
5. Your blog post is now live!

## Advanced Workflows

### Full Workflow (Generate + Upload)

For faster iteration:

```bash
make run
# Select: 4 (full)
# Choose input file
# Review output
# Confirm upload
```

### Update Existing Post

To update an already published post:

1. Generate new version (or use existing output file)
2. Run CLI: `make run`
3. Select **3 (update)**
4. Enter existing blog post ID
5. Choose output file
6. Confirm update

### Multi-Language Posts

Set languages in your input:

```json
{
  "topic": "How to Study Effectively",
  "languages": ["en", "ru"],
  ...
}
```

The AI will generate:

- Complete, original content for each language
- Not just translations - culturally adapted content
- Same structure and key points across languages

## Tips & Best Practices

### Content Quality

- **Be Specific**: More detailed `special_instructions` = better output
- **Iterate**: Generate multiple versions, pick the best
- **Review Before Publishing**: Always check generated content
- **Edit if Needed**: Feel free to manually edit JSON before uploading

### SEO Optimization

- Use 3-5 targeted keywords
- Check title length (50-80 chars)
- Verify description is compelling (120-160 chars)
- Ensure headings are descriptive and keyword-rich

### Writing Tone

- `professional` - For technical guides, whitepapers
- `casual` - For tips, tricks, lifestyle content
- `educational` - For tutorials, how-tos
- `friendly` - For community posts, announcements

### Content Length

- `short` (~500 words) - Quick tips, announcements, updates
- `medium` (~1000 words) - Standard blog posts, guides
- `long` (~1500+ words) - In-depth tutorials, comprehensive guides

## Troubleshooting

### "Failed to load .env file"

**Solution**: Ensure `envs/.env` exists at repository root

```bash
ls ../../envs/.env
```

### "No raw input files found"

**Solution**: Create JSON files in `raw/` directory

```bash
ls raw/*.json
# If empty, copy examples:
cp raw/example-quiz-tips.json raw/my-first-post.json
```

### PocketBase Connection Error

**Solution**: Verify PocketBase is running and credentials are correct

```bash
# Check PocketBase is running
curl http://localhost:8090/api/health

# Verify env vars
grep PB_ ../../envs/.env
```

### AI Generation Takes Too Long

**Solutions**:

- Check OpenAI API key is valid
- Verify internet connection
- Try shorter `length` setting
- Reduce number of languages

### Generated Content is Off-Topic

**Solutions**:

- Be more specific in `topic` field
- Add detailed `special_instructions`
- Include more relevant `keywords`
- Try different `tone` setting

## Examples

### Example 1: Quick Study Tips

```json
{
  "topic": "5 Quick Study Tips for Busy Students",
  "target_audience": "high school and college students",
  "tone": "friendly",
  "length": "short",
  "category": "tips",
  "languages": ["en"],
  "keywords": ["study tips", "productivity", "time management"],
  "special_instructions": "Keep it concise, use numbered list format, include QuizBee mention at the end"
}
```

### Example 2: Comprehensive Guide

```json
{
  "topic": "The Complete Guide to Active Learning Techniques",
  "target_audience": "educators and serious learners",
  "tone": "professional",
  "length": "long",
  "category": "guides",
  "languages": ["en", "ru"],
  "keywords": ["active learning", "teaching methods", "educational psychology"],
  "special_instructions": "Include research citations, practical exercises, real-world examples from classrooms"
}
```

### Example 3: Product Announcement

```json
{
  "topic": "Announcing QuizBee Mobile App - Learn Anywhere, Anytime",
  "target_audience": "QuizBee users and potential customers",
  "tone": "casual",
  "length": "medium",
  "category": "news",
  "languages": ["en"],
  "keywords": ["mobile app", "QuizBee", "learning on the go"],
  "special_instructions": "Highlight key features: offline mode, push notifications, cloud sync. Include download links and CTA"
}
```

## Output Management

### List Generated Posts

```bash
make run
# Select: 5 (list)
```

### Clean Output Directory

```bash
make clean
```

## Support

For issues or questions:

1. Check this guide first
2. Review `README.md` for technical details
3. Check example files in `raw/`
4. Review generated output structure

## Next Steps

Once comfortable with basic usage:

- Experiment with different tones and lengths
- Try multi-language generation
- Integrate into your content workflow
- Automate with CI/CD (future enhancement)
