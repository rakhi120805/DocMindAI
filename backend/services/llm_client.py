"""
LLM Client — a single, provider-agnostic interface every agent calls.

WHY THIS EXISTS (important interview point):
None of the agent code (classification_agent.py, qa_agent.py, etc.)
should ever import `openai` or `anthropic` directly. If it did,
switching providers would mean editing every agent file. Instead,
every agent depends on THIS class's `.complete()` method, and only
this file knows which actual API is being called underneath.

This is the Adapter pattern: different LLM providers have different
SDKs and response shapes, but every agent sees the same simple
interface.
"""

import json
import requests
from backend.config.settings import settings


class LLMClient:
    def __init__(self):
        self.provider = settings.llm_provider
        self.model_name = settings.llm_model_name

    def complete(self, prompt: str, json_mode: bool = False) -> str:
        if self.provider == "openai":
            return self._complete_openai_compatible(prompt, json_mode)
        elif self.provider == "groq":
            return self._complete_openai_compatible(
                prompt, json_mode, base_url="https://api.groq.com/openai/v1", provider_label="Groq"
            )
        elif self.provider == "anthropic":
            return self._complete_anthropic(prompt, json_mode)
        elif self.provider == "ollama":
            return self._complete_ollama(prompt, json_mode)
        else:
            raise NotImplementedError(
                f"LLM provider '{self.provider}' not configured. "
                "Set llm_provider in backend/config/settings.py "
                "(or LLM_PROVIDER env var) to one of: openai, groq, anthropic, ollama."
            )

    def _complete_openai_compatible(
        self, prompt: str, json_mode: bool, base_url: str = None, provider_label: str = "OpenAI"
    ) -> str:
        """
        Shared implementation for any provider that speaks the same API
        shape as OpenAI's chat completions endpoint - which includes
        Groq, since Groq deliberately built their API to be a drop-in
        match for OpenAI's client. This is exactly why the provider
        list only needed one new branch (routing + a base_url), not a
        whole new method: the WIRE FORMAT is identical, only the
        server behind the URL differs (Groq runs open models like
        Llama/Mixtral on custom LPU hardware, dramatically faster than
        typical GPU inference - useful to know if asked why Groq feels
        near-instant compared to Ollama's ~30s local CPU generation).

        NOTE on json_mode with Groq specifically: only some models
        support forced JSON output (e.g. llama-3.3-70b-versatile does,
        smaller/older ones may not) - check Groq's current model docs
        if complete_json() starts failing after a model change.
        """
        from openai import OpenAI

        client = OpenAI(api_key=settings.llm_api_key, base_url=base_url)
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"} if json_mode else None,
            )
        except Exception as e:
            # Both providers' SDKs raise their own exception types
            # (AuthenticationError, RateLimitError, APIConnectionError,
            # etc.) - wrapping in a RuntimeError with the original
            # message keeps this function's error type consistent with
            # _complete_ollama's, so callers (agents) don't need to
            # know which provider they're talking to.
            raise RuntimeError(f"{provider_label} API error: {e}") from e

        return response.choices[0].message.content

    def _complete_anthropic(self, prompt: str, json_mode: bool) -> str:
        # from anthropic import Anthropic
        # client = Anthropic(api_key=settings.llm_api_key)
        # response = client.messages.create(
        #     model=self.model_name,
        #     max_tokens=1024,
        #     messages=[{"role": "user", "content": prompt}],
        # )
        # return response.content[0].text
        raise NotImplementedError("pip install anthropic, then uncomment above")

    def _complete_ollama(self, prompt: str, json_mode: bool) -> str:
        """
        Calls a locally-running Ollama server.

        stream=False: we want the whole response back in one go, not
        token-by-token streaming — simpler to handle for now, at the
        cost of waiting for the full generation before getting anything.

        format="json": Ollama supports forcing valid JSON output at the
        model level (not just prompting "please return JSON" and hoping).
        This is a big reliability win for agents like ClassificationAgent
        and SummaryAgent that need to parse the response as structured data.
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }
        if json_mode:
            payload["format"] = "json"

        try:
            response = requests.post(
                f"{settings.ollama_base_url}/api/generate",
                json=payload,
                timeout=120,  # local LLM generation can be slow on CPU
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Could not reach Ollama. Is it running? Start it with `ollama serve` "
                f"and make sure the model is pulled: `ollama pull {self.model_name}`"
            )
        except requests.exceptions.HTTPError as e:
            # Ollama's actual error message lives in the response body,
            # not the status code - e.g. "model not found" vs "out of
            # memory" vs a malformed request all return 500, but with
            # very different body text. Surfacing it here turns a dead
            # end into an actionable error.
            raise RuntimeError(
                f"Ollama returned an error (status {response.status_code}): "
                f"{response.text.strip()}. Common causes: the model name in "
                f"your .env (currently '{self.model_name}') doesn't exactly "
                f"match what you pulled - run `ollama list` to check - or "
                f"Ollama ran out of memory loading the model."
            ) from e

        return response.json()["response"]

    def complete_json(self, prompt: str) -> dict:
        """
        Convenience wrapper used by agents that expect structured JSON
        back (Classification, Summary). Centralizing the "strip stray
        text and parse JSON" logic here means each agent doesn't need
        its own error-handling for slightly malformed model output.
        """
        raw = self.complete(prompt, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Even with format="json", weaker models occasionally wrap
            # the JSON in markdown code fences - strip and retry once.
            cleaned = raw.strip().strip("`").replace("json\n", "", 1)
            return json.loads(cleaned)