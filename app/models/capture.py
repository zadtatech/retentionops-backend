from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime


class CaptureRequest(BaseModel):
    """Request model for screenshot capture from Chrome extension."""
    
    brand_name: str = Field(..., description="Name of the brand being analyzed")
    scenario: str = Field(..., description="User scenario (e.g., 'Registration / Onboarding', 'Withdrawal Request')")
    selected_mechanic_id: int = Field(..., ge=1, le=26, description="Mechanic ID (1-26)")
    selected_mechanic_name: str = Field(..., description="Name of the selected mechanic")
    screenshot_base64: str = Field(..., description="Base64 encoded screenshot (JPEG data URI or raw base64)")
    sanitized_dom_text: str = Field(..., description="Sanitized DOM text from the page")
    page_url: str = Field(..., description="URL of the captured page")
    notes: Optional[str] = Field(None, description="Optional notes about the capture")
    
    @validator('screenshot_base64')
    def validate_screenshot(cls, v):
        """Validate screenshot base64 string."""
        if not v:
            raise ValueError('Screenshot cannot be empty')
        
        # Handle data URI format
        if v.startswith('data:image/'):
            return v
        
        # If raw base64, it should be reasonably long
        if len(v) < 100:
            raise ValueError('Invalid base64 screenshot data')
        
        return v
    
    @validator('page_url')
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
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
    maturity_level: int = Field(..., ge=0, le=3, description="Calculated maturity level (0=None, 1=Primitive, 2=Expanded, 3=Finalized)")
    red_flags: list[RedFlag] = Field(default_factory=list, description="Detected red flags")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the capture")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "audit_id": "123e4567-e89b-12d3-a456-426614174000",
                "vision_analysis": {
                    "is_valid_match": True,
                    "confidence_score": 0.95,
                    "metadata": {
                        "wager_multiplier": 35.0,
                        "minimum_deposit": 20.0,
                        "expiration_timer": "7 days",
                        "reward_type": "free spins"
                    },
                    "ui_quality_score": 4,
                    "analysis_notes": "Well-designed wheel of fortune with clear terms"
                },
                "maturity_level": 3,
                "red_flags": [],
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
