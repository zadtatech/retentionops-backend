from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any
from datetime import datetime


class CaptureRequest(BaseModel):
    """Request model for screenshot capture from Chrome extension (Pydantic V2 Compatible)."""
    
    brand_name: str = Field(default="Unknown Brand", description="Name of the brand being analyzed")
    scenario: str = Field(default="Registration", description="User scenario")
    selected_mechanic_id: int = Field(default=1, description="Mechanic ID (1-26)")
    selected_mechanic_name: str = Field(default="Welcome Bonus", description="Name of the selected mechanic")
    screenshot_base64: str = Field(..., description="Base64 encoded screenshot")
    sanitized_dom_text: str = Field(default="", description="Sanitized DOM text from the page")
    page_url: str = Field(default="https://example.com", description="URL of the captured page")
    notes: Optional[str] = Field(None, description="Optional notes about the capture")

    @model_validator(mode='before')
    @classmethod
    def map_extension_payload(cls, data: Any) -> Any:
        """Map payload fields sent by Chrome extension to match CaptureRequest model in Pydantic v2."""
        if not isinstance(data, dict):
            return data

        values = dict(data)

        # 1. competitorBrand -> brand_name
        if not values.get('brand_name') and values.get('competitorBrand'):
            values['brand_name'] = str(values.get('competitorBrand'))

        # 2. auditScenario -> scenario
        if not values.get('scenario') and values.get('auditScenario'):
            values['scenario'] = str(values.get('auditScenario'))

        # 3. targetMechanic -> selected_mechanic_name & selected_mechanic_id
        target_mechanic = values.get('targetMechanic')
        if not values.get('selected_mechanic_name') and target_mechanic:
            values['selected_mechanic_name'] = str(target_mechanic)
        
        if 'selected_mechanic_id' not in values:
            if isinstance(target_mechanic, int):
                values['selected_mechanic_id'] = target_mechanic
            elif isinstance(target_mechanic, str) and target_mechanic.isdigit():
                values['selected_mechanic_id'] = int(target_mechanic)
            else:
                values['selected_mechanic_id'] = 1

        # 4. screenshot -> screenshot_base64
        if not values.get('screenshot_base64') and values.get('screenshot'):
            values['screenshot_base64'] = values.get('screenshot')

        # 5. pageData -> page_url & sanitized_dom_text
        page_data = values.get('pageData', {})
        if isinstance(page_data, dict):
            if not values.get('page_url') and page_data.get('url'):
                values['page_url'] = page_data.get('url')
            if not values.get('sanitized_dom_text') and page_data.get('bodyText'):
                values['sanitized_dom_text'] = page_data.get('bodyText')

        return values

    @field_validator('screenshot_base64')
    @classmethod
    def validate_screenshot(cls, v: str) -> str:
        """Validate screenshot base64 string."""
        if not v:
            raise ValueError('Screenshot cannot be empty')
        return v
    
    @field_validator('page_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v or not v.startswith(('http://', 'https://')):
            return 'https://example.com'
        return v


class MechanicMetadata(BaseModel):
    """Metadata extracted from vision agent analysis."""
    
    wager_multiplier: Optional[float] = Field(None, description="Wager multiplier requirement")
    minimum_deposit: Optional[float] = Field(None, description="Minimum deposit requirement")
    expiration_timer: Optional[str] = Field(None, description="Expiration timer (e.g., '24h', '7 days')")
    reward_type: Optional[str] = Field(None, description="Type of reward (e.g., 'free spins', 'bonus cash')")
    additional_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional extracted parameters")


class VisionAnalysisResult(BaseModel):
    """Result from vision agent analysis."""
    
    is_valid_match: bool = Field(..., description="Whether UI element matches the selected mechanic")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the match")
    metadata: MechanicMetadata = Field(..., description="Extracted mechanic metadata")
    ui_quality_score: int = Field(..., ge=1, le=5, description="UI presentation quality score (1-5)")
    analysis_notes: Optional[str] = Field(None, description="Additional analysis notes")


class RedFlag(BaseModel):
    """Red flag detected by rule engine."""
    
    flag_type: str = Field(..., description="Type of flag (Tier 1 or Tier 2)")
    severity: str = Field(..., description="Severity level (Critical, High, Medium, Low)")
    description: str = Field(..., description="Description of the flag")
    recommended_action: str = Field(..., description="Recommended action to resolve")


class CaptureResponse(BaseModel):
    """Response model for capture endpoint."""
    
    success: bool = Field(..., description="Whether the capture was successful")
    audit_id: Optional[str] = Field(None, description="ID of the created audit record")
    vision_analysis: VisionAnalysisResult = Field(..., description="Results from vision agent")
    maturity_level: int = Field(..., ge=0, le=3, description="Calculated maturity level")
    red_flags: list[RedFlag] = Field(default_factory=list, description="Detected red flags")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the capture")
