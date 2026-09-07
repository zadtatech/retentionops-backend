from openai import AsyncOpenAI
from app.config import settings
from app.models.capture import VisionAnalysisResult, MechanicMetadata
from typing import Dict, Any, Optional
import logging
import re
import base64

logger = logging.getLogger(__name__)


class VisionAgent:
    """Service for analyzing screenshots using OpenAI GPT-4o-mini Vision."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
    
    def _prepare_image_url(self, screenshot_base64: str) -> str:
        """
        Prepare the image URL for OpenAI API.
        
        Args:
            screenshot_base64: Base64 encoded screenshot (data URI or raw base64)
            
        Returns:
            str: Data URL format for OpenAI API
        """
        # If already a data URI, return as-is
        if screenshot_base64.startswith('data:image/'):
            return screenshot_base64
        
        # Otherwise, wrap in data URI
        return f"data:image/jpeg;base64,{screenshot_base64}"
    
    def _build_analysis_prompt(
        self,
        mechanic_name: str,
        sanitized_dom_text: str
    ) -> str:
        """
        Build the analysis prompt for OpenAI Vision API.
        
        Args:
            mechanic_name: Name of the mechanic to validate
            sanitized_dom_text: Sanitized DOM text from the page
            
        Returns:
            str: The analysis prompt
        """
        prompt = f"""You are an expert iGaming retention mechanic analyst. Analyze the provided screenshot and DOM text to determine if it matches the expected mechanic: "{mechanic_name}".

Your task:
1. Validate if the UI element matches the selected mechanic
2. Extract key metadata if present:
   - Wager multiplier (e.g., 35x, 40x)
   - Minimum deposit requirement (e.g., $20, €10)
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
    "is_valid_match": true/false,
    "confidence_score": 0.0-1.0,
    "metadata": {{
        "wager_multiplier": float or null,
        "minimum_deposit": float or null,
        "expiration_timer": string or null,
        "reward_type": string or null,
        "additional_params": {{}}
    }},
    "ui_quality_score": 1-5,
    "analysis_notes": "Brief explanation of your analysis"
}}"""
        
        return prompt
    
    def _extract_number_from_text(self, text: str) -> Optional[float]:
        """
        Extract a number from text.
        
        Args:
            text: Text containing a number
            
        Returns:
            Optional[float]: Extracted number or None
        """
        if not text:
            return None
        
        # Try to extract a number (integer or float)
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        
        return None
    
    async def analyze_screenshot(
        self,
        mechanic_name: str,
        screenshot_base64: str,
        sanitized_dom_text: str
    ) -> VisionAnalysisResult:
        """
        Analyze a screenshot using OpenAI GPT-4o-mini Vision.
        
        Args:
            mechanic_name: Name of the mechanic to validate
            screenshot_base64: Base64 encoded screenshot
            sanitized_dom_text: Sanitized DOM text from the page
            
        Returns:
            VisionAnalysisResult: Analysis results
        """
        try:
            # Prepare image URL
            image_url = self._prepare_image_url(screenshot_base64)
            
            # Build prompt
            prompt = self._build_analysis_prompt(mechanic_name, sanitized_dom_text)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            logger.info(f"OpenAI Vision response received for mechanic: {mechanic_name}")
            
            # Parse JSON response
            import json
            try:
                analysis_data = json.loads(content)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse OpenAI response as JSON: {content}")
                # Return default analysis on parse error
                return self._get_default_analysis(mechanic_name)
            
            # Extract metadata
            metadata = MechanicMetadata(
                wager_multiplier=analysis_data.get("metadata", {}).get("wager_multiplier"),
                minimum_deposit=analysis_data.get("metadata", {}).get("minimum_deposit"),
                expiration_timer=analysis_data.get("metadata", {}).get("expiration_timer"),
                reward_type=analysis_data.get("metadata", {}).get("reward_type"),
                additional_params=analysis_data.get("metadata", {}).get("additional_params", {})
            )
            
            # Build result
            result = VisionAnalysisResult(
                is_valid_match=analysis_data.get("is_valid_match", False),
                confidence_score=analysis_data.get("confidence_score", 0.5),
                metadata=metadata,
                ui_quality_score=analysis_data.get("ui_quality_score", 3),
                analysis_notes=analysis_data.get("analysis_notes")
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing screenshot with OpenAI Vision: {e}")
            # Return default analysis on error
            return self._get_default_analysis(mechanic_name)
    
    def _get_default_analysis(self, mechanic_name: str) -> VisionAnalysisResult:
        """
        Get a default analysis result when API fails.
        
        Args:
            mechanic_name: Name of the mechanic
            
        Returns:
            VisionAnalysisResult: Default analysis result
        """
        return VisionAnalysisResult(
            is_valid_match=True,
            confidence_score=0.5,
            metadata=MechanicMetadata(),
            ui_quality_score=3,
            analysis_notes=f"API error - using default analysis for {mechanic_name}"
        )


# Singleton instance
vision_agent = VisionAgent()
