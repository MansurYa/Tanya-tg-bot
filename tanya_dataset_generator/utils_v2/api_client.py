"""Opus 4.6 API client"""

import aiohttp
import asyncio
from typing import Dict, Optional


class OpusClient:
    def __init__(self):
        self.base_url = "https://dev.aiprime.store/api"
        self.api_key = "cr_dfb54972ac4679d2d916c2af15d50cbd8a62bb51cfd9d18f61034ca462a2ef08"
        self.model = "claude-opus-4-20250514"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": self.api_key,
        }

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.8,
        max_tokens: int = 4096
    ) -> Dict:
        """Send request to Opus 4.6"""

        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": temperature,
        }

        if system:
            body["system"] = [{"type": "text", "text": system}]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/messages",
                headers=self.headers,
                json=body,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")

                data = await response.json()
                text = "".join(
                    block["text"]
                    for block in data["content"]
                    if block["type"] == "text"
                )

                return {
                    "text": text,
                    "usage": data["usage"],
                    "stop_reason": data["stop_reason"]
                }
