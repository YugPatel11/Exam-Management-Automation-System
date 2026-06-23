"""
Database text content storage service.
Handles saving and retrieving text-based content stored directly in the database.
"""
import logging
from apps.core.models_audit import TextContent

logger = logging.getLogger(__name__)


class TextContentService:
    """
    Service for storing and retrieving all generated content as text in the database.
    Replaces external file storage — everything is stored as text fields.
    """

    @staticmethod
    def save_content(title, content, module, content_type='text',
                     related_object_id='', related_model='', user=None):
        """
        Save text content to the database.

        Args:
            title: Display name for the content
            content: The actual text content (plain text, HTML, CSV, or JSON)
            module: Module type (question_paper, seating_plan, duty_chart, etc.)
            content_type: Format of content (text, html, csv, json)
            related_object_id: ID of the related entity
            related_model: Model name of the related entity
            user: The user who created this content

        Returns:
            TextContent instance or None on failure
        """
        try:
            text_content = TextContent.objects.create(
                title=title,
                content=content,
                content_type=content_type,
                module=module,
                related_object_id=str(related_object_id) if related_object_id else '',
                related_model=related_model,
                created_by=user,
            )
            logger.info(f'Content saved to database: {title} (module: {module})')
            return text_content
        except Exception as e:
            logger.error(f'Failed to save content to database: {e}')
            return None

    @staticmethod
    def get_content(content_id):
        """
        Retrieve a single text content by ID.

        Returns:
            TextContent instance or None
        """
        try:
            return TextContent.objects.get(pk=content_id)
        except TextContent.DoesNotExist:
            return None

    @staticmethod
    def get_by_module(module, related_object_id=None):
        """
        Get all content entries for a given module.

        Args:
            module: Module type to filter by
            related_object_id: Optional filter by related entity

        Returns:
            QuerySet of TextContent
        """
        qs = TextContent.objects.filter(module=module)
        if related_object_id:
            qs = qs.filter(related_object_id=str(related_object_id))
        return qs

    @staticmethod
    def delete_content(content_id):
        """
        Delete a text content record from the database.

        Returns:
            bool: True if deleted successfully
        """
        try:
            TextContent.objects.filter(pk=content_id).delete()
            logger.info(f'Content deleted from database: ID {content_id}')
            return True
        except Exception as e:
            logger.error(f'Failed to delete content: {e}')
            return False


# Singleton instance for convenience
text_content_service = TextContentService()
