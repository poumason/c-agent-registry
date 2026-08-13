import io
import json
import zipfile

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.crud import agent_dependency as dependency_crud
from app.crud import agent_fab as agent_fab_crud
from app.crud import agent_version as version_crud
from app.crud import mcp as mcp_crud
from app.crud import skill as skill_crud
from app.models.agent import Agent
from app.models.agent_version import AgentVersion
from app.models.enums import DependencyType
from app.services.agent_card import build_agent_card
from app.services.storage import ensure_buckets, get_bytes, put_bytes

settings = get_settings()


def _build_install_manifest(skills: list[dict], mcps: list[dict]) -> dict:
    return {"skills": skills, "mcp": mcps}


async def generate_package_for_version(
    db: AsyncSession, *, agent: Agent, agent_version: AgentVersion
) -> str:
    """Build agent_card.json + install.yaml + skills/ and upload the zip to MinIO.

    Sets and persists AgentVersion.package_path. Returns the MinIO object key.
    """
    ensure_buckets()

    dependencies = await dependency_crud.list_by_version(db, agent_version.slug)

    skill_entries: list[dict] = []
    mcp_entries: list[dict] = []
    skill_files: list[tuple[str, bytes]] = []

    for dependency in dependencies:
        if dependency.type == DependencyType.skill:
            skill = await skill_crud.get_by_id(db, dependency.dependency_id)
            if skill is None:
                continue
            skill_entries.append(
                {
                    "id": str(skill.id),
                    "name": skill.name,
                    "version": skill.version,
                    "category": skill.category,
                }
            )
            filename = skill.bucket_path.rsplit("/", 1)[-1]
            content = get_bytes(settings.minio_skills_bucket, skill.bucket_path)
            skill_files.append((f"skills/{skill.name}/{filename}", content))
        else:
            mcp = await mcp_crud.get_by_id(db, dependency.dependency_id)
            if mcp is None:
                continue
            # No single "host" anymore — an MCP's host is per-fab now (see MCPFab).
            # Which fab's host applies depends on where this agent version itself
            # gets deployed (see AgentFab), a decision this packaging step doesn't
            # make; install.yaml lists the MCP identity only.
            mcp_entries.append(
                {
                    "id": str(mcp.id),
                    "name": mcp.name,
                    "version": mcp.version,
                }
            )

    fabs = await agent_fab_crud.list_for_version(db, agent_version.slug)
    agent_card = build_agent_card(agent, agent_version, fabs).model_dump()
    install_manifest = _build_install_manifest(skill_entries, mcp_entries)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("agent_card.json", json.dumps(agent_card, indent=2))
        zf.writestr("install.yaml", yaml.safe_dump(install_manifest, sort_keys=False))
        for path, content in skill_files:
            zf.writestr(path, content)
        if not skill_files:
            zf.writestr("skills/.gitkeep", b"")

    # bucket/{agent_id}/{version_slug}.zip - the version slug (not a fixed literal name)
    # keeps multiple versions of the same agent from colliding in the same folder.
    object_name = f"{agent.id}/{agent_version.slug}.zip"
    put_bytes(
        settings.minio_packages_bucket, object_name, buffer.getvalue(), "application/zip"
    )

    agent_version.package_path = object_name
    await version_crud.save(db, agent_version)
    return object_name
