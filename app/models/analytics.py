from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MechanicStatus(BaseModel):
    """Status of a single retention mechanic."""
    
    mechanic_id: int = Field(..., ge=1, le=26, description="Mechanic ID (1-26)")
    mechanic_name: str = Field(..., description="Mechanic name")
    maturity_level: int = Field(..., ge=0, le=3, description="Maturity level (0=None, 1=Primitive, 2=Expanded, 3=Finalized)")
    is_active: bool = Field(..., description="Whether the mechanic is currently active")
    last_audited: Optional[datetime] = Field(None, description="Last audit timestamp")
    ui_quality_score: Optional[int] = Field(None, ge=1, le=5, description="UI quality score (1-5)")
    red_flags_count: int = Field(default=0, description="Number of active red flags")


class RetentionCanvasResponse(BaseModel):
    """Response model for retention canvas endpoint."""
    
    brand_name: str = Field(..., description="Brand name")
    total_mechanics: int = Field(..., description="Total number of mechanics (26)")
    active_mechanics: int = Field(..., description="Number of active mechanics")
    overall_maturity_score: float = Field(..., ge=0.0, le=100.0, description="Overall maturity score (0-100)")
    mechanic_statuses: List[MechanicStatus] = Field(default_factory=list, description="Status of all mechanics")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "Our Brand",
                "total_mechanics": 26,
                "active_mechanics": 20,
                "overall_maturity_score": 73.5,
                "mechanic_statuses": [
                    {
                        "mechanic_id": 1,
                        "mechanic_name": "Wheel of Fortune",
                        "maturity_level": 3,
                        "is_active": True,
                        "last_audited": "2024-01-15T10:30:00Z",
                        "ui_quality_score": 4,
                        "red_flags_count": 0
                    }
                ],
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }


class ROICalculationRequest(BaseModel):
    """Request model for ROI calculation."""
    
    annual_ggr: float = Field(..., gt=0, description="Annual Gross Gaming Revenue")
    annual_bonus_emission: float = Field(..., gt=0, description="Annual bonus emission amount")
    vendor_cost: float = Field(..., gt=0, description="Vendor/implementation cost")
    target_uplift_percent: float = Field(..., ge=0, description="Target percentage uplift in GGR")
    
    class Config:
        json_schema_extra = {
            "example": {
                "annual_ggr": 10000000.0,
                "annual_bonus_emission": 2000000.0,
                "vendor_cost": 500000.0,
                "target_uplift_percent": 5.0
            }
        }


class ROICalculationResponse(BaseModel):
    """Response model for ROI calculation."""
    
    break_even_ggr_growth: float = Field(..., description="Break-even GGR growth percentage")
    break_even_bonus_reduction: float = Field(..., description="Break-even bonus reduction percentage")
    net_annual_gain: float = Field(..., description="Net annual gain after costs")
    roi_percentage: float = Field(..., description="Return on Investment percentage")
    is_profitable: bool = Field(..., description="Whether the investment is profitable")
    payback_period_months: Optional[float] = Field(None, description="Payback period in months")
    
    class Config:
        json_schema_extra = {
            "example": {
                "break_even_ggr_growth": 5.0,
                "break_even_bonus_reduction": 25.0,
                "net_annual_gain": 0.0,
                "roi_percentage": 0.0,
                "is_profitable": True,
                "payback_period_months": 12.0
            }
        }


class RedFlagResponse(BaseModel):
    """Response model for red flag."""
    
    id: str = Field(..., description="Red flag ID")
    flag_type: str = Field(..., description="Type of flag (Tier 1 or Tier 2)")
    severity: str = Field(..., description="Severity level (Critical, High, Medium, Low)")
    description: str = Field(..., description="Description of the flag")
    recommended_action: str = Field(..., description="Recommended action to resolve")
    mechanic_id: Optional[int] = Field(None, description="Associated mechanic ID")
    mechanic_name: Optional[str] = Field(None, description="Associated mechanic name")
    created_at: datetime = Field(..., description="Creation timestamp")
    is_resolved: bool = Field(default=False, description="Whether the flag has been resolved")


class RedFlagsResponse(BaseModel):
    """Response model for red flags endpoint."""
    
    total_flags: int = Field(..., description="Total number of red flags")
    critical_count: int = Field(..., description="Number of critical flags")
    high_count: int = Field(..., description="Number of high severity flags")
    medium_count: int = Field(..., description="Number of medium severity flags")
    low_count: int = Field(..., description="Number of low severity flags")
    flags: List[RedFlagResponse] = Field(default_factory=list, description="List of red flags")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_flags": 15,
                "critical_count": 3,
                "high_count": 5,
                "medium_count": 5,
                "low_count": 2,
                "flags": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "flag_type": "Tier 1",
                        "severity": "Critical",
                        "description": "Hard streak reset on Day 2 without recovery path",
                        "recommended_action": "Implement streak recovery mechanic or soften reset logic",
                        "mechanic_id": 5,
                        "mechanic_name": "Daily Streak Bonus",
                        "created_at": "2024-01-15T10:30:00Z",
                        "is_resolved": False
                    }
                ],
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }
