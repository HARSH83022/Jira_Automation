"""
AI Provider abstraction.
AI NEVER calculates SP or percentages — it only receives pre-calculated numbers
and generates a natural-language summary.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    @abstractmethod
    async def generate_summary(self, context: dict) -> str:
        ...


class NoAIProvider(AIProvider):
    async def generate_summary(self, context: dict) -> str:
        return ""


class GeminiProvider(AIProvider):
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

    async def generate_summary(self, context: dict) -> str:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured.")

        prompt = _build_prompt(context)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.API_URL}?key={api_key}",
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                )
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc:
            logger.warning("Gemini API failed: %s", exc)
            raise


class DeepSeekProvider(AIProvider):
    API_URL = "https://api.deepseek.com/v1/chat/completions"

    async def generate_summary(self, context: dict) -> str:
        api_key = settings.DEEPSEEK_API_KEY
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not configured.")

        prompt = _build_prompt(context)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    self.API_URL,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.warning("DeepSeek API failed: %s", exc)
            raise


def get_provider(name: Optional[str] = None) -> AIProvider:
    name = (name or settings.DEFAULT_AI_PROVIDER).lower()
    if name == "gemini":
        return GeminiProvider()
    if name == "deepseek":
        return DeepSeekProvider()
    return NoAIProvider()


async def safe_generate_summary(context: dict, provider_name: Optional[str] = None) -> str:
    """
    Always returns a string. If AI fails, returns a fallback message.
    NEVER blocks report generation.
    """
    provider = get_provider(provider_name)
    if isinstance(provider, NoAIProvider):
        return ""
    try:
        return await provider.generate_summary(context)
    except Exception as exc:
        logger.warning("AI summary unavailable: %s", exc)
        return "AI summary unavailable — report generated without AI."


def _build_prompt(context: dict) -> str:
    devs = context.get("developers", [])
    dev_lines = "\n".join(
        f"  - {d['name']}: Assigned {d['assigned_sp']} SP, "
        f"Completed {d['completed_sp']} SP ({d['completion_pct']}%)"
        for d in devs
    )
    return f"""You are a sprint reporting assistant. Based on the following pre-calculated sprint data, write a concise professional summary (3-5 sentences) for a management audience.

Sprint: {context.get('sprint', 'N/A')}
Date: {context.get('report_date', 'N/A')}
Total Scope: {context.get('total_scope', 0)} SP
Completed SP: {context.get('completed_sp', 0)} SP
Remaining SP: {context.get('remaining_sp', 0)} SP
Overall Completion: {context.get('completion_pct', 0)}%

Developer breakdown:
{dev_lines}

Instructions:
- Do NOT recalculate any numbers.
- Use the numbers as given.
- Highlight the highest and lowest performing developers.
- Note any risks if completion is below 30%.
- Keep tone professional and concise.
"""
