import json
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.ai.exceptions import AiProviderError
from apps.ai.gemini import GeminiAiProvider
from apps.ai.providers import AiProviderRequest


class _GeminiResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(
            {
                "candidates": [{"content": {"parts": [{"text": '{"answer":"ok"}'}]}}],
                "usageMetadata": {"promptTokenCount": 2, "candidatesTokenCount": 1},
            }
        ).encode()


class GeminiEnvironmentSeparationTests(SimpleTestCase):
    request = AiProviderRequest(
        model="gemini-test-model",
        system_instructions="Return JSON.",
        user_data={"prompt": "test"},
        output_schema={
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
        },
    )

    @override_settings(PRD_GEMINI_API_KEY="", GEMINI_API_KEY="team-2-key")
    def test_prd_provider_does_not_fall_back_to_team_2_key(self):
        with self.assertRaises(AiProviderError) as raised:
            GeminiAiProvider().generate(
                self.request,
                timeout_seconds=1,
                cancellation_check=lambda: False,
            )

        self.assertEqual(raised.exception.code, "provider_not_configured")

    @override_settings(PRD_GEMINI_API_KEY="team-3-key", GEMINI_API_KEY="team-2-key")
    @patch("apps.ai.gemini.urlopen", return_value=_GeminiResponse())
    def test_prd_provider_sends_only_team_3_key(self, mocked_urlopen):
        result = GeminiAiProvider().generate(
            self.request,
            timeout_seconds=1,
            cancellation_check=lambda: False,
        )

        sent_request = mocked_urlopen.call_args.args[0]
        self.assertEqual(sent_request.get_header("X-goog-api-key"), "team-3-key")
        self.assertNotEqual(sent_request.get_header("X-goog-api-key"), "team-2-key")
        self.assertEqual(result.output, {"answer": "ok"})
