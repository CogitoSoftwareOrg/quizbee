"""PocketBase uploader for blog posts."""

from datetime import datetime
import logging
from pocketbase import PocketBase

from .models import BlogGenerationOutput

logger = logging.getLogger(__name__)


class BlogUploader:
    """Handles uploading blog posts to PocketBase."""

    def __init__(self, pb: PocketBase):
        self.pb = pb

    async def upload_blog_post(self, output: BlogGenerationOutput) -> dict[str, str]:
        """
        Upload blog post to PocketBase.

        Args:
            output: Generated blog data

        Returns:
            Dict with created record IDs: {"blog_id": "...", "i18n_ids": [...]}
        """
        logger.info(f"Uploading blog post: {output.blog.slug}")

        # 1. Create main blog record
        blog_data = {
            "slug": output.blog.slug,
            "category": output.blog.category,
            "published": output.blog.published,
            "tags": output.blog.tags,
            "authors": output.blog.authors,
        }

        # Handle cover image if provided
        # Note: For now, cover is optional. In future, implement image upload
        if output.blog.cover:
            logger.warning(
                f"Cover image '{output.blog.cover}' specified but upload not implemented"
            )

        blog_record = await self.pb.collection("blog").create(blog_data)
        blog_id = blog_record.get("id", "")

        logger.info(f"Created blog record: {blog_id}")

        # 2. Create i18n records
        i18n_ids: list[str] = []
        for i18n_entry in output.i18n_entries:
            i18n_data = {
                "post": blog_id,  # Relation to blog record
                "locale": i18n_entry.locale,
                "content": i18n_entry.content,
                "status": i18n_entry.status,
                "data": i18n_entry.data.model_dump(mode="json"),
            }

            i18n_record = await self.pb.collection("blogI18n").create(i18n_data)
            i18n_ids.append(i18n_record.get("id", ""))

            logger.info(
                f"Created i18n record ({i18n_entry.locale}): {i18n_record.get('id')}"
            )

        logger.info(
            f"Successfully uploaded blog post with {len(i18n_ids)} translation(s)"
        )

        return {"blog_id": blog_id, "i18n_ids": ", ".join(i18n_ids)}

    async def update_blog_post(
        self, blog_id: str, output: BlogGenerationOutput
    ) -> dict[str, str]:
        """
        Update existing blog post in PocketBase.

        Args:
            blog_id: Existing blog record ID
            output: Updated blog data

        Returns:
            Dict with updated record IDs
        """
        logger.info(f"Updating blog post: {blog_id}")

        # 1. Update main blog record
        blog_data = {
            "slug": f"{output.blog.slug}",
            "category": output.blog.category,
            "published": output.blog.published,
            "tags": output.blog.tags,
            "authors": output.blog.authors,
        }

        await self.pb.collection("blog").update(blog_id, blog_data)
        logger.info(f"Updated blog record: {blog_id}")

        # 2. Get existing i18n records
        existing_i18n = await self.pb.collection("blogI18n").get_full_list(
            options={
                "params": {
                    "filter": f'post = "{blog_id}"',
                }
            }
        )

        existing_by_locale = {
            record.get("locale", ""): record for record in existing_i18n
        }

        i18n_ids = []
        for i18n_entry in output.i18n_entries:
            i18n_data = {
                "post": blog_id,
                "locale": i18n_entry.locale,
                "content": i18n_entry.content,
                "status": i18n_entry.status,
                "data": i18n_entry.data.model_dump(mode="json"),
            }

            if i18n_entry.locale in existing_by_locale:
                # Update existing
                record = existing_by_locale[i18n_entry.locale]
                await self.pb.collection("blogI18n").update(
                    record.get("id", ""), i18n_data
                )
                i18n_ids.append(record.get("id", ""))
                logger.info(
                    f"Updated i18n record ({i18n_entry.locale}): {record.get('id', '')}"
                )
            else:
                # Create new
                new_record = await self.pb.collection("blogI18n").create(i18n_data)
                i18n_ids.append(new_record.get("id", ""))
                logger.info(
                    f"Created new i18n record ({i18n_entry.locale}): {new_record.get('id', '')}"
                )

        logger.info(f"Successfully updated blog post with {len(i18n_ids)} translations")

        return {"blog_id": blog_id, "i18n_ids": ", ".join(i18n_ids)}
