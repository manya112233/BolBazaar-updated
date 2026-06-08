from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
MAX_LIST_ROWS = 10
MAX_LIST_ROW_TITLE_CHARS = 24
MAX_LIST_ROW_DESCRIPTION_CHARS = 72
MAX_LIST_SECTION_TITLE_CHARS = 24
MAX_LIST_ROW_ID_CHARS = 200


class WhatsAppService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def missing_outbound_config(self) -> list[str]:
        missing: list[str] = []
        if not self.settings.whatsapp_access_token:
            missing.append('WHATSAPP_ACCESS_TOKEN')
        if not self.settings.whatsapp_phone_number_id:
            missing.append('WHATSAPP_PHONE_NUMBER_ID')
        return missing

    def is_configured(self) -> bool:
        return not self.missing_outbound_config()

    def delivery_status(self, result: dict[str, Any]) -> str:
        if result.get('sent'):
            return 'sent'
        if result.get('reason') == 'whatsapp_not_configured':
            return 'not_configured'
        return 'failed'

    def verify_webhook(self, mode: str | None, token: str | None, challenge: str | None) -> str:
        if not self.settings.whatsapp_verify_token:
            raise ValueError('WHATSAPP_VERIFY_TOKEN is not configured')
        if mode != 'subscribe' or token != self.settings.whatsapp_verify_token or challenge is None:
            raise ValueError('Webhook verification failed')
        return challenge

    def _auth_headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self.settings.whatsapp_access_token}',
            'Content-Type': 'application/json',
        }

    def graph_url(self, suffix: str) -> str:
        version = self.settings.whatsapp_graph_version.strip('/')
        base = self.settings.whatsapp_graph_base_url.rstrip('/')
        return f'{base}/{version}/{suffix.lstrip("/")}'

    def _post_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        missing = self.missing_outbound_config()
        if missing:
            logger.warning('WhatsApp outbound is not configured. Missing: %s', ', '.join(missing))
            return {'sent': False, 'reason': 'whatsapp_not_configured', 'missing': missing}

        try:
            response = httpx.post(
                self.graph_url(f'{self.settings.whatsapp_phone_number_id}/messages'),
                headers=self._auth_headers(),
                json=payload,
                timeout=20.0,
                trust_env=False,
            )
            response.raise_for_status()
            return {'sent': True, 'payload': response.json()}
        except httpx.HTTPStatusError as exc:
            logger.warning(
                'WhatsApp send failed: %s %s',
                exc.response.status_code,
                exc.response.text,
            )
            return {
                'sent': False,
                'reason': 'send_failed',
                'status_code': exc.response.status_code,
                'error': exc.response.text,
            }
        except httpx.HTTPError as exc:
            logger.warning('WhatsApp send failed: %s', exc)
            return {'sent': False, 'reason': 'send_failed', 'error': str(exc)}

    def send_text_message(self, to: str, body: str) -> dict[str, Any]:
        payload = {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'text',
            'text': {'preview_url': False, 'body': body},
        }
        return self._post_message(payload)

    def send_reply_buttons(
        self,
        *,
        to: str,
        body: str,
        buttons: list[dict[str, str]],
    ) -> dict[str, Any]:
        payload = {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'interactive',
            'interactive': {
                'type': 'button',
                'body': {'text': body},
                'action': {
                    'buttons': [
                        {
                            'type': 'reply',
                            'reply': {
                                'id': button['id'],
                                'title': button['title'][:20],
                            },
                        }
                        for button in buttons[:3]
                    ],
                },
            },
        }
        return self._post_message(payload)

    def send_list_message(
        self,
        *,
        to: str,
        body: str,
        button_text: str,
        sections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        sanitized_sections = self._sanitize_list_sections(sections)
        if not sanitized_sections:
            logger.warning('WhatsApp list message was not sent because it has no rows.')
            return {'sent': False, 'reason': 'invalid_list_message'}

        payload = {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'interactive',
            'interactive': {
                'type': 'list',
                'body': {'text': body},
                'action': {
                    'button': button_text[:20],
                    'sections': sanitized_sections,
                },
            },
        }
        return self._post_message(payload)

    def _sanitize_list_sections(self, sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        sanitized: list[dict[str, Any]] = []
        rows_seen = 0
        rows_kept = 0

        for section in sections:
            rows = section.get('rows') or []
            rows_seen += len(rows)
            if rows_kept >= MAX_LIST_ROWS:
                continue

            sanitized_rows: list[dict[str, str]] = []
            for row in rows:
                if rows_kept >= MAX_LIST_ROWS:
                    break
                row_id = str(row.get('id') or '').strip()
                row_title = str(row.get('title') or '').strip()
                if not row_id or not row_title:
                    continue

                sanitized_row = {
                    'id': row_id[:MAX_LIST_ROW_ID_CHARS],
                    'title': row_title[:MAX_LIST_ROW_TITLE_CHARS],
                }
                description = str(row.get('description') or '').strip()
                if description:
                    sanitized_row['description'] = description[:MAX_LIST_ROW_DESCRIPTION_CHARS]
                sanitized_rows.append(sanitized_row)
                rows_kept += 1

            if sanitized_rows:
                section_title = str(section.get('title') or 'Menu').strip() or 'Menu'
                sanitized.append(
                    {
                        'title': section_title[:MAX_LIST_SECTION_TITLE_CHARS],
                        'rows': sanitized_rows,
                    }
                )

        if rows_seen > MAX_LIST_ROWS:
            logger.warning(
                'WhatsApp list rows exceeded %s; truncated from %s rows.',
                MAX_LIST_ROWS,
                rows_seen,
            )

        return sanitized

    def fetch_media_bytes(self, media_id: str) -> tuple[bytes | None, str | None]:
        if not self.settings.whatsapp_access_token:
            return None, None

        headers = {'Authorization': f'Bearer {self.settings.whatsapp_access_token}'}

        try:
            media_meta = httpx.get(self.graph_url(media_id), headers=headers, timeout=20.0, trust_env=False)
            media_meta.raise_for_status()
            media_payload = media_meta.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                'WhatsApp media metadata fetch failed for %s: %s %s',
                media_id,
                exc.response.status_code,
                exc.response.text,
            )
            return None, None
        except httpx.HTTPError as exc:
            logger.warning('WhatsApp media metadata fetch failed for %s: %s', media_id, exc)
            return None, None

        download_url = media_payload.get('url')
        mime_type = media_payload.get('mime_type')
        if not download_url:
            logger.warning('WhatsApp media metadata for %s did not include a download URL.', media_id)
            return None, mime_type

        try:
            media_response = httpx.get(download_url, headers=headers, timeout=30.0, trust_env=False)
            media_response.raise_for_status()
            return media_response.content, mime_type
        except httpx.HTTPStatusError as exc:
            logger.warning(
                'WhatsApp media download failed for %s: %s %s',
                media_id,
                exc.response.status_code,
                exc.response.text,
            )
            return None, mime_type
        except httpx.HTTPError as exc:
            logger.warning('WhatsApp media download failed for %s: %s', media_id, exc)
            return None, mime_type

    def extract_incoming_message(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        for entry in payload.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                messages = value.get('messages', [])
                contacts = value.get('contacts', [])
                if not messages:
                    continue
                profile_name = None
                if contacts:
                    profile_name = contacts[0].get('profile', {}).get('name')
                return {
                    'value': value,
                    'message': messages[0],
                    'profile_name': profile_name,
                }
        return None
