"""API-key header verification helper.

Re-exported from :mod:`vibey_bootstrap.security` for ergonomic import. The
canonical pattern for non-webhook FastAPI routes is::

    from vibey_bootstrap.auth.api_key import verify_api_key_header
    from fastapi import Depends

    @app.get('/api/private', dependencies=[Depends(verify_api_key_header)])
    async def private(): ...

Webhook routes use :func:`vibey_bootstrap.auth.webhook.verify_webhook_client_state`
instead.
"""

from vibey_bootstrap.security import verify_api_key_header

__all__ = ["verify_api_key_header"]
