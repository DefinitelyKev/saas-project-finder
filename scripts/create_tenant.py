#!/usr/bin/env python3
"""
Script to create a new tenant for testing purposes.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories.tenant_repository import TenantRepository
from src.services.tenant_service import TenantService
from src.config.constants import TenantTier


async def create_test_tenant():
    """Create a test tenant."""

    async with get_db_session() as session:
        tenant_repository = TenantRepository(session)
        tenant_service = TenantService(tenant_repository)

        # Create tenant
        tenant, api_key = await tenant_service.create_tenant(
            name="Test SaaS Project",
            tier=TenantTier.PRO,
            allowed_agents=["customer-support", "data-analyst", "content-writer"]
        )

        print(f"✅ Tenant created successfully!")
        print(f"   Tenant ID: {tenant.id}")
        print(f"   Name: {tenant.name}")
        print(f"   Tier: {tenant.tier.value}")
        print(f"   API Key: {api_key}")
        print(f"   Allowed Agents: {', '.join(tenant.allowed_agents)}")
        print()
        print(f"🔗 Use this API key in your Next.js apps:")
        print(f"   X-API-Key: {api_key}")


if __name__ == "__main__":
    asyncio.run(create_test_tenant())