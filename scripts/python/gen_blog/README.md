# QuizBee Blog Generator

AI-powered CLI tool for generating high-quality, SEO-optimized blog posts for QuizBee.

## Features

- 🤖 **AI-Powered Generation**: Uses OpenAI GPT-5 to generate complete blog posts
- 🌍 **Multi-Language Support**: Generate content in English and Russian
- 📝 **SEO Optimized**: Automatic title, description, keywords, and structured content
- 💾 **Local Storage**: Save generated posts before uploading
- 🔄 **PocketBase Integration**: Direct upload to QuizBee's blog system
- 🎨 **Beautiful CLI**: Modern interface with Typer and Rich
- 📦 **Modular Architecture**: Clean separation of concerns

## Installation

```bash
cd scripts/python/gen_blog
make install
```

Or manually:

```bash
cd scripts/python
uv sync
```

## Quick Start

### Run CLI

```bash
make run
```

Or directly:

```bash
cd scripts/python
uv run python -m gen_blog --help
```

### Available Commands

```
🐝 QuizBee Blog Generator - AI-powered blog post generation

Commands:
  generate    Generate new blog post from raw input
  upload      Upload generated blog post to PocketBase
  update      Update existing blog post in PocketBase
  full        Generate and upload in one go
  list        List generated blog posts
  clean       Remove all generated output files
```

## Usage Examples

### Generate Blog Post

```bash
uv run python -m gen_blog generate
```

Interactively select raw input file, generate blog post, and save to `output/`.

### Upload to PocketBase

```bash
uv run python -m gen_blog upload
```

Select generated file and upload to PocketBase.

### Full Workflow

```bash
uv run python -m gen_blog full
```

Generate and upload in one command.

### Update Existing Post

```bash
uv run python -m gen_blog update <blog-id>
```

Or without blog ID (will prompt):

```bash
uv run python -m gen_blog update
```

### List Generated Posts

```bash
uv run python -m gen_blog list
```

### Clean Output

```bash
uv run python -m gen_blog clean --force
```

## Input Specification

Create JSON files in `raw/` directory:

```json
{
  "topic": "10 Tips for Effective Study Quizzes",
  "target_audience": "students and self-learners",
  "tone": "friendly",
  "length": "medium",
  "category": "quizMaking",
  "languages": ["en"],
  "keywords": ["study tips", "quiz creation"],
  "special_instructions": "Focus on actionable tips"
}
```

### Fields

| Field                  | Type   | Options                                              |
| ---------------------- | ------ | ---------------------------------------------------- |
| `topic`                | string | Main topic of the blog post                          |
| `target_audience`      | string | Who is this post for?                                |
| `tone`                 | enum   | `professional`, `casual`, `educational`, `friendly`  |
| `length`               | enum   | `short` (~500w), `medium` (~1000w), `long` (~1500+w) |
| `category`             | enum   | See [Categories](#categories) below                  |
| `languages`            | array  | `["en"]` or `["en", "ru"]`                           |
| `keywords`             | array  | SEO keywords (optional)                              |
| `special_instructions` | string | Additional requirements (optional)                   |

### Categories

Available categories (matching PocketBase schema):

- `product` - Product announcements, features, updates
- `education` - Educational content, learning theory
- `edtechTrends` - EdTech trends and industry insights
- `quizMaking` - Quiz creation tips and best practices
- `useCases` - Use cases, tutorials, how-tos
- `general` - General blog posts

## Architecture

### Module Structure

```
gen_blog/
├── __init__.py          # Package exports
├── __main__.py          # Entry point for python -m
├── cli.py               # Typer CLI interface (clean!)
├── commands.py          # Command implementations
├── agent.py             # AI agent configuration
├── models.py            # Pydantic models & enums
├── storage.py           # Local file storage
├── uploader.py          # PocketBase uploader
├── utils.py             # UI utilities (Rich)
├── raw/                 # Input templates
│   └── *.json
└── output/              # Generated posts (auto-created)
    └── *.json
```

### Key Improvements

**Before** (monolithic `main.py`):

- 350+ lines in single file
- Manual menu system
- Plain text output
- Mixed concerns

**After** (modular):

- `cli.py` (100 lines) - Clean Typer interface
- `commands.py` (250 lines) - Command logic
- `utils.py` (90 lines) - Rich UI components
- Beautiful colored output
- Type-safe enums
- Separated concerns

## Output Structure

Generated files contain:

```json
{
  "blog": {
    "slug": "effective-study-quizzes",
    "category": "quizMaking",
    "tags": ["study-tips", "education"],
    "published": false,
    "authors": ["QuizBee Team"]
  },
  "i18n_entries": [
    {
      "locale": "en",
      "status": "draft",
      "content": "<p>Full HTML...</p>",
      "data": {
        "title": "10 Tips for Effective Study Quizzes",
        "description": "SEO description..."
      }
    }
  ]
}
```

## Development

### Project Structure

- **CLI Layer** (`cli.py`): Typer commands, argument parsing
- **Command Layer** (`commands.py`): Business logic for each command
- **Agent Layer** (`agent.py`): AI generation with Pydantic-AI
- **Storage Layer** (`storage.py`): File I/O operations
- **Upload Layer** (`uploader.py`): PocketBase integration
- **Utils Layer** (`utils.py`): Rich UI components

### Adding New Commands

1. Add command function in `commands.py`:

```python
async def cmd_my_command():
    console.print("[bold]My Command[/bold]")
    # Implementation
```

2. Register in `cli.py`:

```python
@app.command("my-command", help="Description")
def my_command():
    asyncio.run(commands.cmd_my_command())
```

### Adding New Categories

Update `BlogCategory` enum in `models.py`:

```python
class BlogCategory(StrEnum):
    MY_CATEGORY = "myCategory"
```

Ensure it matches PocketBase schema.

## Environment

Required in `envs/.env`:

```env
PUBLIC_PB_URL=http://localhost:8090
PB_EMAIL=admin@admin.com
PB_PASSWORD=admin
OPENAI_API_KEY=sk-...
```

## Troubleshooting

### Import Errors

```bash
cd scripts/python
uv sync
```

### CLI Not Found

```bash
uv run python -m gen_blog --help
```

### PocketBase Connection

Verify environment variables and PocketBase is running:

```bash
curl http://localhost:8090/api/health
```

## Tips

1. **Start with Examples**: Copy and modify example files
2. **Use `full` Command**: Faster iteration for new posts
3. **Review Before Upload**: Always check generated content
4. **Multi-Language**: Generate English first, then add Russian
5. **Use Correct Categories**: Match PocketBase schema

## See Also

- [USAGE.md](USAGE.md) - Detailed usage guide
- [raw/](raw/) - Example input files
- [../../README.md](../../README.md) - Parent scripts documentation
