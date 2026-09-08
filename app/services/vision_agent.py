import base64
import json
import logging
import os
import google.generativeai as genai
from app.config import settings
from app.models.capture import VisionAnalysisResult, MechanicMetadata

logger = logging.getLogger(__name__)


class VisionAgent:
    """Service for analyzing screenshots using Google Gemini Vision."""

    def _get_clean_api_key(self) -> str | None:
        """Retrieve and sanitize Gemini API key from settings or environment."""
        raw_key = getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
        if raw_key:
            # Очищаем от случайных пробелов, переносов строк и кавычек
            cleaned_key = str(raw_key).strip().strip("'\"")
            return cleaned_key if cleaned_key else None
        return None

    def _prepare_image_bytes(self, screenshot_base64: str) -> bytes:
        """Extract raw bytes from base64 screenshot."""
        if "," in screenshot_base64:
            base64_data = screenshot_base64.split(",")[1]
        else:
            base64_data = screenshot_base64
        return base64.b64decode(base64_data)

    def _build_analysis_prompt(
        self,
        mechanic_name: str,
        sanitized_dom_text: str
    ) -> str:
        """Build the analysis prompt for Gemini API."""
        return f"""You are an expert iGaming retention mechanic analyst. Analyze the provided screenshot and DOM text to determine if it matches the expected mechanic: "{mechanic_name}".

Your task:
1. Validate if the UI element matches the selected mechanic
2. Extract key metadata if present:
   - Wager multiplier (e.g., 35, 40)
   - Minimum deposit requirement (e.g., 20, 10)
   - Expiration timer (e.g., 24h, 7 days, 30 days)
   - Reward type (e.g., free spins, bonus cash, cashback, loyalty points)
3. Rate the UI presentation quality (1-5 scale):
   - 1: Poor design, confusing, hard to understand
   - 2: Below average, some clarity issues
   - 3: Average, functional but not engaging
   - 4: Good design, clear and engaging
   - 5: Excellent, visually appealing and very clear

DOM Text Context:
{sanitized_dom_text[:2000]}

Provide your analysis in the following JSON format:
{{
    "is_valid_match": true,
    "confidence_score": 0.95,
    "metadata": {{
        "wager_multiplier": 35.0,
        "minimum_deposit": 20.0,
        "expiration_timer": "7 days",
        "reward_type": "Free Spins",
        "additional_params": {{}}
    }},
    "ui_quality_score": 4,
    "analysis_notes": "Brief explanation of your analysis"
}}"""

    async def analyze_screenshot(
        self,
        mechanic_name: str,
        screenshot_base64: str,
        sanitized_dom_text: str
    ) -> VisionAnalysisResult:
        """
        Analyze a screenshot using Gemini Flash.
        Matches exact arguments of previous OpenAI implementation.
        """
        api_key = self._get_clean_api_key()

        if not api_key:
            logger.warning("GEMINI_API_KEY is missing or empty. Returning default analysis.")
            return self._get_default_analysis(mechanic_name)

        # Маскированное логгирование ключа для отладки
        masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "INVALID_SHORT_KEY"
        logger.info(f"Configuring Gemini Vision API with key: {masked_key}")

        try:
            # Всегда конфигурируем перед запросом свежим ключом
            genai.configure(api_key=api_key)

            image_bytes = self._prepare_image_bytes(screenshot_base64)
            prompt = self._build_analysis_prompt(mechanic_name, sanitized_dom_text)

            model_name = getattr(settings, "GEMINI_MODEL", "gemini-flash-latest")
            model = genai.GenerativeModel(model_name)

            response = await model.generate_content_async(
                [
                    {"mime_type": "image/jpeg", "data": image_bytes},
                    prompt
                ],
                generation_config={"response_mime_type": "application/json"}
            )

            raw_text = response.text.strip()
            analysis_data = json.loads(raw_text)

            metadata_dict = analysis_data.get("metadata", {})
            metadata = MechanicMetadata(
                wager_multiplier=metadata_dict.get("wager_multiplier"),
                minimum_deposit=metadata_dict.get("minimum_deposit"),
                expiration_timer=metadata_dict.get("expiration_timer"),
                reward_type=metadata_dict.get("reward_type"),
                additional_params=metadata_dict.get("additional_params", {})
            )

            return VisionAnalysisResult(
                is_valid_match=analysis_data.get("is_valid_match", True),
                confidence_score=analysis_data.get("confidence_score", 0.9),
                metadata=metadata,
                ui_quality_score=analysis_data.get("ui_quality_score", 4),
                analysis_notes=analysis_data.get("analysis_notes", "Analyzed successfully with Gemini")
            )

        except Exception as e:
            logger.error(f"Error analyzing screenshot with Gemini Vision: {e}", exc_info=True)
            return self._get_default_analysis(mechanic_name)

    def _get_default_analysis(self, mechanic_name: str) -> VisionAnalysisResult:
        """Get a default analysis result when API fails or key is missing."""
        return VisionAnalysisResult(
            is_valid_match=True,
            confidence_score=0.5,
            metadata=MechanicMetadata(),
            ui_quality_score=3,
            analysis_notes=f"API error or missing GEMINI_API_KEY - using fallback analysis for {mechanic_name}"
        )


# Singleton instance
vision_agent = VisionAgent()
