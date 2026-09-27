"""Farm-aware AI helpers for AgroIntel (Gemini first, Groq optional fallback)."""
import os
import requests


class FarmAIService:
    """Calls the Gemini generateContent API, with optional Groq compatibility."""

    def __init__(self, gemini_api_key=None, groq_api_key=None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        # Google restricts the older 2.5 models for new API users; use the current GA lite model.
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    @property
    def provider(self):
        if self.gemini_api_key:
            return "Gemini"
        if self.groq_api_key:
            return "Groq"
        return None

    def get_farm_analysis(self, question, farm_data, history=None, focus=""):
        """Answer a question with only the supplied user's farm context."""
        if not self.provider:
            return {"success": False, "error": "Add a Gemini API key to enable live AI.",
                    "response": self._offline_summary(question, farm_data), "source": "Local farm analysis"}
        prompt = self._build_prompt(question, farm_data, focus)
        try:
            if self.gemini_api_key:
                answer = self._call_gemini(prompt, history or [])
                source = f"Google Gemini ({self.gemini_model})"
            else:
                answer = self._call_groq(prompt, history or [])
                source = f"Groq ({self.groq_model})"
            return {"success": True, "response": answer, "source": source}
        except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
            return {"success": False, "error": self._friendly_error(exc),
                    "response": self._offline_summary(question, farm_data), "source": "Local farm analysis"}

    def generate_suggestions(self, farm_data):
        """Generate a prioritized, evidence-aware farm action plan."""
        question = ("Create a prioritized farm action plan for the next 7–14 days. Format it with "
                    "these exact Markdown sections: 'Priority actions', 'Hold off for now', and 'Data "
                    "to collect'. Under Priority actions, give 3–6 numbered actions. Start each action "
                    "with a short bold title and priority label, then include concise Evidence, Next step, "
                    "and Monitor details. Include a 'Hold off for now' section "
                    "for actions that need more evidence. Never invent weather forecasts, prices, "
                    "soil tests, diagnoses, legal deadlines, yield gains, or ROI. If data is missing, "
                    "say what measurement or local expert should be consulted first. For chemical, "
                    "fertilizer, irrigation, or disease decisions, avoid unsupported precise rates and "
                    "tell the farmer to follow product labels and local agronomic guidance.")
        return self.get_farm_analysis(question, farm_data, focus="AI Suggestions page")

    def _build_prompt(self, question, data, focus):
        # Explicit whitelist prevents profile credentials or unrelated data entering the AI request.
        context = {
            "farm_summary": {k: data.get(k) for k in (
                "total_acres", "avg_yield", "active_machinery", "total_machinery", "compliance_score")},
            "fields": data.get("fields", []),
            "soil_tests": data.get("soil", []),
            "recent_recorded_weather": data.get("weather", []),
            "machinery": data.get("machinery", []),
            "compliance_records": data.get("compliance", []),
            "existing_recommendations": data.get("ai_recommendations", []),
            "field_intelligence": data.get("field_intelligence", {}),
        }
        import json
        return ("You are AgroIntel, a careful agricultural decision-support assistant. Use the farm data "
                "below as the only source for claims about this farm. Distinguish measured facts from "
                "general guidance, identify missing or stale data, and ask a focused follow-up if needed. "
                "Give practical, prioritized steps and explain the evidence. Never claim to have taken "
                "actions or accessed external/current conditions. Do not provide precise pesticide or "
                "fertilizer rates without adequate local context; advise label and local expert guidance. "
                "Respect user privacy and do not request secrets.\n\n"
                f"Page focus: {focus or 'Farm copilot'}\n"
                f"Farm data (JSON):\n{json.dumps(context, ensure_ascii=False, default=str)}\n\n"
                f"Farmer's question: {question}")

    def _call_gemini(self, prompt, history):
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.gemini_model}:generateContent")
        contents = []
        for item in history[-12:]:
            role = "model" if item.get("role") == "assistant" else "user"
            if item.get("content"):
                contents.append({"role": role, "parts": [{"text": str(item["content"])}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        response = requests.post(url, headers={"x-goog-api-key": self.gemini_api_key}, json={
            "systemInstruction": {"parts": [{"text": "You are a trustworthy, concise farm decision-support copilot."}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.35, "maxOutputTokens": 1400},
        }, timeout=45)
        self._raise_for_response(response)
        data = response.json()
        return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"]).strip()

    def _call_groq(self, prompt, history):
        messages = [{"role": "system", "content": "You are a careful agricultural decision-support assistant. "
                    "Do not invent farm data; identify uncertainty and advise local expert guidance for "
                    "high-impact chemical or nutrient decisions."}]
        messages.extend({"role": m.get("role", "user"), "content": str(m.get("content", ""))}
                        for m in history[-12:] if m.get("role") in ("user", "assistant"))
        messages.append({"role": "user", "content": prompt})
        response = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.groq_api_key}"},
            json={"model": self.groq_model, "messages": messages, "temperature": 0.35, "max_tokens": 1400},
            timeout=45)
        self._raise_for_response(response)
        return response.json()["choices"][0]["message"]["content"].strip()

    @staticmethod
    def _raise_for_response(response):
        if response.ok:
            return
        try:
            message = response.json().get("error", {}).get("message", response.text[:300])
        except ValueError:
            message = response.text[:300]
        raise ValueError(f"AI provider returned HTTP {response.status_code}: {message}")

    @staticmethod
    def _friendly_error(exc):
        message = str(exc)
        if "API_KEY_INVALID" in message or "invalid api key" in message.lower() or "HTTP 401" in message:
            return "The API key was rejected. Check your Gemini key in Google AI Studio."
        if "HTTP 429" in message or "RESOURCE_EXHAUSTED" in message:
            return "The free API quota or rate limit was reached. Try again later or check your AI Studio limits."
        return f"AI request failed: {message}"

    @staticmethod
    def _offline_summary(question, data):
        fields = data.get("fields", [])
        machinery = data.get("machinery", [])
        soil = data.get("soil", [])
        lines = ["### Local farm snapshot", f"- Fields recorded: {len(fields)}",
                 f"- Total recorded area: {data.get('total_acres', 0):,.1f} acres",
                 f"- Average recorded yield: {data.get('avg_yield', 0)} t/ha",
                 f"- Equipment operational: {data.get('active_machinery', 0)}/{data.get('total_machinery', 0)}"]
        if soil:
            lines.append(f"- Soil test records available: {len(soil)}. Compare each result with crop and local recommendations.")
        if not fields:
            lines.append("Add fields to get tailored crop suggestions.")
        lines.append("I couldn't reach the AI provider, so this is a data summary rather than a generated recommendation.")
        return "\n".join(lines)


# Backwards-compatible name for existing imports.
GroqAIService = FarmAIService
