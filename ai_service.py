import os
import json
import re
import httpx
from typing import Any, Dict, List

DO_INFERENCE_URL = "https://inference.do-ai.run/v1/chat/completions"
DEFAULT_MODEL = os.getenv("DO_INFERENCE_MODEL", "openai-gpt-oss-120b")
API_KEY = os.getenv("DIGITALOCEAN_INFERENCE_KEY")

def _extract_json(text: str) -> str:
    """Extract JSON string from LLM response possibly wrapped in markdown fences."""
    m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()

async def _call_inference(messages: List[Dict[str, str]], max_tokens: int = 512) -> Dict[str, Any]:
    """Common helper that talks to DO inference API and returns parsed JSON.
    On any error it returns a fallback dictionary with a helpful note.
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}" if API_KEY else "",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "max_completion_tokens": max_tokens,
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(DO_INFERENCE_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # The content is usually under choices[0].message.content
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            json_str = _extract_json(content)
            return json.loads(json_str)
    except Exception as e:
        return {"note": f"AI service unavailable: {str(e)}"}

async def get_recommendations(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """Return habit recommendations from the AI model.
    Expected to return a dict with a 'recommendations' key.
    """
    result = await _call_inference(messages, max_tokens=512)
    if "recommendations" not in result:
        # Normalise fallback structure
        result = {"recommendations": [], "note": result.get("note", "No recommendations returned.")}
    return result

async def analyze_streak_pattern(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """Return streak analysis data from the AI model.
    Expected to return a dict with an 'analysis' key.
    """
    result = await _call_inference(messages, max_tokens=512)
    if "analysis" not in result:
        result = {"analysis": {}, "note": result.get("note", "No analysis returned.")}
    return result
