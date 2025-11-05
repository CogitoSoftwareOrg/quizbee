"""Data models for blog generation."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class BlogMetadata(BaseModel):
    """Blog post metadata (for blogI18n.data field)."""

    title: str = Field(description="Blog post title (max 80 chars)")
    description: str = Field(
        description="Blog post description/excerpt (max 160 chars)"
    )
    image: str | None = Field(default=None, description="Optional OG image URL or path")
    ogTitle: str | None = Field(
        default=None, description="Optional OG title override (max 60 chars)"
    )
    ogDescription: str | None = Field(
        default=None, description="Optional OG description override (max 160 chars)"
    )


class BlogI18nData(BaseModel):
    """Blog post content in specific language."""

    locale: Literal["en", "ru"] = Field(description="Language code (en or ru)")
    content: str = Field(
        description="Full HTML content of the blog post. Must include semantic HTML with h2/h3 headings for TOC."
    )
    status: Literal["draft", "published"] = Field(
        default="draft", description="Publication status"
    )
    data: BlogMetadata = Field(description="Metadata for SEO and OG tags")


class BlogPostData(BaseModel):
    """Main blog post data (for 'blog' collection)."""

    slug: str = Field(
        description="URL-friendly slug (lowercase, hyphens, no special chars)"
    )
    category: str = Field(description="Blog category (e.g., tips, guides, news)")
    published: bool = Field(default=False, description="Whether post is published")
    tags: list[str] = Field(
        default_factory=list,
        description="List of tags for the post (lowercase, max 5 tags)",
    )
    authors: list[str] = Field(
        default_factory=lambda: ["QuizBee Team"],
        description="List of author names",
    )
    cover: str | None = Field(
        default=None,
        description="Cover image filename (will be uploaded to PocketBase)",
    )


class BlogGenerationOutput(BaseModel):
    """Complete output from AI agent - contains both blog and i18n data."""

    blog: BlogPostData = Field(description="Main blog post data")
    i18n_entries: list[BlogI18nData] = Field(
        description="List of translations (at least one language required)",
        min_length=1,
    )


class RawBlogInput(BaseModel):
    """Input specification for blog generation."""

    topic: str = Field(description="Main topic of the blog post")
    target_audience: str = Field(
        description="Who is this post for? (e.g., students, teachers, parents)"
    )
    tone: Literal["professional", "casual", "educational", "friendly"] = Field(
        default="professional"
    )
    length: Literal["short", "medium", "long"] = Field(
        default="medium",
        description="short: ~500 words, medium: ~1000 words, long: ~1500+ words",
    )
    category: str = Field(
        description="Category for the post (e.g., tips, guides, news, features)"
    )
    languages: list[Literal["en", "ru"]] = Field(
        default=["en"], description="Languages to generate content in"
    )
    keywords: list[str] = Field(
        default_factory=list, description="SEO keywords to include naturally"
    )
    special_instructions: str | None = Field(
        default=None, description="Any specific requirements or focus areas"
    )
