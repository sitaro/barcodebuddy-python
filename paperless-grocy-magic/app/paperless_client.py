"""Paperless-ngx API client for document management."""
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class PaperlessDocument:
    """Represents a Paperless document."""

    def __init__(self, data: Dict):
        self.id = data.get('id')
        self.title = data.get('title', '')
        self.content = data.get('content', '')
        self.tags = data.get('tags', [])
        self.custom_fields = data.get('custom_fields', [])
        self.created = data.get('created')
        self.added = data.get('added')
        self.download_url = data.get('download_url')

    def __repr__(self):
        return f"PaperlessDocument(id={self.id}, title={self.title})"

    def get_custom_field_value(self, field_id: int):
        """Get value of a custom field by ID."""
        for field in self.custom_fields:
            if field.get('field') == field_id:
                return field.get('value')
        return None


class PaperlessClient:
    """Client for interacting with Paperless-ngx API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {api_key}',
            'Content-Type': 'application/json'
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make API request to Paperless."""
        url = f"{self.base_url}/api{endpoint}"

        try:
            logger.debug(f"Paperless API: {method} {url}")
            if 'json' in kwargs:
                logger.debug(f"Request data: {kwargs['json']}")

            response = self.session.request(method, url, timeout=30, **kwargs)

            logger.debug(f"Response status: {response.status_code}")

            response.raise_for_status()

            if response.status_code == 204:  # No content
                logger.debug("Got 204 No Content, returning empty dict")
                return {}

            return response.json()

        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"Paperless API JSON decode error ({method} {endpoint}): {e}")
            logger.error(f"Response was: {response.text[:1000]}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Paperless API request error ({method} {endpoint}): {e}")
            logger.error(f"Full URL: {url}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:1000]}")
            return None

    def test_connection(self) -> bool:
        """Test connection to Paperless API."""
        result = self._request('GET', '/ui_settings/')
        if result is not None:
            logger.info("Connected to Paperless-ngx")
            return True
        logger.error("Paperless connection test failed")
        return False

    def get_custom_field_id(self, field_name: str) -> Optional[int]:
        """Get custom field ID by name."""
        result = self._request('GET', '/custom_fields/')
        if result and 'results' in result:
            for field in result['results']:
                if field.get('name') == field_name:
                    logger.info(f"Found custom field '{field_name}' with ID {field.get('id')}")
                    return field.get('id')
        logger.warning(f"Custom field '{field_name}' not found")
        return None

    def get_tag_id(self, tag_name: str) -> Optional[int]:
        """Get tag ID by name."""
        result = self._request('GET', '/tags/')
        if result and 'results' in result:
            for tag in result['results']:
                if tag.get('name') == tag_name:
                    logger.info(f"Found tag '{tag_name}' with ID {tag.get('id')}")
                    return tag.get('id')
        logger.warning(f"Tag '{tag_name}' not found")
        return None

    def get_documents_by_tag(self, tag_name: str, processed_field_name: str = None) -> List[PaperlessDocument]:
        """
        Get documents with specific tag.
        Optionally filter by custom field (unprocessed only).
        """
        # Get tag ID
        tag_id = self.get_tag_id(tag_name)
        if tag_id is None:
            logger.error(f"Cannot query documents: tag '{tag_name}' not found")
            return []

        # Query documents with tag
        params = {
            'tags__id__all': tag_id,
            'page_size': 100  # Adjust as needed
        }

        result = self._request('GET', '/documents/', params=params)
        if not result or 'results' not in result:
            logger.error("Failed to get documents")
            return []

        documents = [PaperlessDocument(doc) for doc in result['results']]
        logger.info(f"Found {len(documents)} documents with tag '{tag_name}'")

        # Filter by custom field if specified
        if processed_field_name:
            field_id = self.get_custom_field_id(processed_field_name)
            if field_id:
                # Filter: field is None (not set) or False
                unprocessed = []
                for doc in documents:
                    value = doc.get_custom_field_value(field_id)
                    if value is None or value is False:
                        unprocessed.append(doc)

                logger.info(f"Filtered to {len(unprocessed)} unprocessed documents")
                return unprocessed

        return documents

    def download_document(self, document_id: int) -> Optional[bytes]:
        """Download document PDF as bytes."""
        try:
            url = f"{self.base_url}/api/documents/{document_id}/download/"
            logger.debug(f"Downloading document {document_id} from {url}")

            response = self.session.get(url, timeout=60)
            response.raise_for_status()

            logger.info(f"Downloaded document {document_id} ({len(response.content)} bytes)")
            return response.content

        except Exception as e:
            logger.error(f"Error downloading document {document_id}: {e}")
            return None

    def update_custom_field(self, document_id: int, field_name: str, value: bool) -> bool:
        """Update custom field value for a document."""
        field_id = self.get_custom_field_id(field_name)
        if field_id is None:
            logger.error(f"Cannot update field: '{field_name}' not found")
            return False

        # Get current document to preserve other fields
        doc_data = self._request('GET', f'/documents/{document_id}/')
        if not doc_data:
            logger.error(f"Failed to get document {document_id}")
            return False

        # Update custom_fields array
        custom_fields = doc_data.get('custom_fields', [])

        # Find and update the field, or add it
        field_found = False
        for field in custom_fields:
            if field.get('field') == field_id:
                field['value'] = value
                field_found = True
                break

        if not field_found:
            custom_fields.append({'field': field_id, 'value': value})

        # Update document
        update_data = {'custom_fields': custom_fields}
        result = self._request('PATCH', f'/documents/{document_id}/', json=update_data)

        if result is not None:
            logger.info(f"Updated custom field '{field_name}' = {value} for document {document_id}")
            return True

        logger.error(f"Failed to update custom field for document {document_id}")
        return False
