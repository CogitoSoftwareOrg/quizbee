"""AI agent for blog post generation."""

import logging
from pydantic_ai import Agent

from .models import BlogGenerationOutput, RawBlogInput

logger = logging.getLogger(__name__)

# System prompt for blog generation
SYSTEM_PROMPT = """You are an expert blog post writer for QuizBee, an AI-powered quiz generation platform.

Your task is to generate high-quality, SEO-optimized blog posts based on the provided input.

## Content Guidelines

1. **Structure**: Use semantic HTML with proper heading hierarchy
   - Use <h2> for main sections
   - Use <h3> for subsections
   - Each heading MUST have a unique id attribute for TOC navigation (use lowercase-with-hyphens format)
   - Example: <h2 id="introduction">Introduction</h2>

2. **HTML Format**: 
   - Use semantic HTML tags: <p>, <ul>, <ol>, <strong>, <em>, <a>, <blockquote>
   - Use <code> for inline code and <pre><code> for code blocks
   - Add appropriate classes for styling (e.g., "text-center" for centered text)
   - Include images with <img> tags where relevant (use descriptive alt text)
   
3. **Content Quality**:
   - Write engaging, informative content
   - Use natural language and include keywords organically
   - Break long paragraphs into digestible chunks
   - Use bullet points and numbered lists for clarity
   - Include practical examples and actionable tips
   - Add relevant internal/external links where appropriate

4. **SEO Optimization**:
   - Title: 50-80 characters, include main keyword
   - Description: 120-160 characters, compelling and descriptive
   - Use keywords naturally throughout the content
   - Create descriptive, keyword-rich headings
   - Write comprehensive content (aim for target length)

5. **QuizBee Context**:
   - QuizBee is an AI-powered quiz generation platform for education
   - Features: AI quiz generation, adaptive learning, progress tracking, mobile apps
   - Target users: students, teachers, corporate trainers, self-learners
   - USP: Generate quizzes from any material (PDFs, videos, text) in seconds

6. **Slug Format**:
   - Use lowercase with hyphens
   - Keep it short and descriptive (3-6 words)
   - Include main keyword
   - Example: "how-to-create-effective-quizzes"

7. **Tags**:
   - Use 3-5 relevant tags maximum
   - All lowercase, single words or hyphenated phrases
   - Example: ["quiz-tips", "education", "ai", "study-hacks"]

8. **Multiple Languages**:
   - If multiple languages requested, generate COMPLETE, ORIGINAL content for each
   - Do NOT simply translate - adapt to cultural context and idioms
   - Maintain same structure and key points across languages
   - Each version should feel native to that language

## Output Format

Return a structured JSON with:
- `blog`: Main blog data (slug, category, tags, etc.)
- `i18n_entries`: Array of language-specific content with HTML and metadata

Example HTML structure:
```html
<p>Introduction paragraph with <strong>important concepts</strong>.</p>

<h2 id="main-section">Main Section Title</h2>
<p>Content for this section...</p>

<h3 id="subsection">Subsection Title</h3>
<ul>
  <li>Point one with details</li>
  <li>Point two with examples</li>
</ul>

<blockquote>
  <p>An insightful quote or key takeaway.</p>
</blockquote>

<h2 id="conclusion">Conclusion</h2>
<p>Wrap up with actionable advice...</p>
```

Generate comprehensive, professional content that provides real value to readers.
"""


def create_blog_agent() -> Agent[None, BlogGenerationOutput]:
    """Create and configure the blog generation agent."""
    agent = Agent(
        model="openai:gpt-5",
        output_type=BlogGenerationOutput,
        system_prompt=SYSTEM_PROMPT,
        history_processors=[],
    )

    return agent


async def generate_blog_post(
    raw_input: RawBlogInput,
) -> BlogGenerationOutput:
    """
    Generate blog post using AI agent.

    Args:
        raw_input: Raw blog input specification

    Returns:
        BlogGenerationOutput with blog data and i18n entries
    """
    agent = create_blog_agent()

    # Build user prompt from input
    user_prompt = f"""Generate a blog post with the following specifications:

**Topic**: {raw_input.topic}

**Target Audience**: {raw_input.target_audience}

**Tone**: {raw_input.tone}

**Length**: {raw_input.length}

**Category**: {raw_input.category}

**Languages**: {', '.join(raw_input.languages)}

**Keywords**: {', '.join(raw_input.keywords) if raw_input.keywords else 'None specified'}

**Special Instructions**: {raw_input.special_instructions or 'None'}

Please generate a complete, high-quality blog post following all content guidelines.
"""

    logger.info(f"Generating blog post for topic: {raw_input.topic}")

    result = await agent.run(user_prompt)
    data = result.output

    logger.info(
        f"Blog post generated successfully: {data.blog.slug} "
        f"with {len(data.i18n_entries)} language(s)"
    )

    return data
