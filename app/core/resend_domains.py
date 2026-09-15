import httpx

from app.core.config import settings


RESEND_BASE_URL = "https://api.resend.com"


def _headers() -> dict[str, str]:
    if not settings.RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not configured")

    return {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }


async def create_resend_domain(domain: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{RESEND_BASE_URL}/domains",
            headers=_headers(),
            json={
                "name": domain,
            },
        )

        response.raise_for_status()

        return response.json()


async def get_resend_domain(domain_id: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{RESEND_BASE_URL}/domains/{domain_id}",
            headers=_headers(),
        )

        response.raise_for_status()

        return response.json()


async def verify_resend_domain(domain_id: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{RESEND_BASE_URL}/domains/{domain_id}/verify",
            headers=_headers(),
        )

        response.raise_for_status()

        return response.json()


async def list_resend_domains() -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{RESEND_BASE_URL}/domains",
            headers=_headers(),
        )

        response.raise_for_status()

        return response.json()
