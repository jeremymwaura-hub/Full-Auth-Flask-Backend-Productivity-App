"""Shared helpers used by the API resources."""

from __future__ import annotations

from marshmallow import ValidationError


def flatten_marshmallow_errors(error: ValidationError) -> list[str]:
    """Turn a marshmallow ValidationError into a flat list of readable strings.

    The provided JWT frontend client renders error responses as
    ``{"errors": ["message one", "message two"]}``, so every error response
    in this API follows that same convention.
    """
    messages = error.messages

    if isinstance(messages, dict):
        errors = []
        for field, field_messages in messages.items():
            if isinstance(field_messages, (list, tuple)):
                errors.extend(f"{field}: {msg}" for msg in field_messages)
            else:
                errors.append(f"{field}: {field_messages}")
        return errors

    if isinstance(messages, (list, tuple)):
        return [str(message) for message in messages]

    return [str(messages)]
