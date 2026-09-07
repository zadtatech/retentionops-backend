from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Competitor(BaseModel):
    """Competitor model."""
    
    id: Optional[str] = Field(None, description="Competitor ID")
    name: str = Field(..., description="Competitor name")
    website: str = Field(..., description="Competitor website URL")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Competitor Brand",
                "website": "https://competitor.com",
                "notes": "Focus on sports betting",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class CompetitorCreate(BaseModel):
    """Request model for creating a competitor."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Competitor name")
    website: str = Field(..., description="Competitor website URL")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Competitor Brand",
                "website": "https://competitor.com",
                "notes": "Focus on sports betting"
            }
        }


class MechanicMaturity(BaseModel):
    """Maturity level for a specific mechanic."""
    
    mechanic_id: int = Field(..., ge=1, le=26, description="Mechanic ID (1-26)")
    mechanic_name: str = Field(..., description="Mechanic name")
    maturity_level: int = Field(..., ge=0, le=3, description="Maturity level (0=None, 1=Primitive, 2=Expanded, 3=Finalized)")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")


class CompetitorMaturityProfile(BaseModel):
    """Full maturity profile for a competitor."""
    
    competitor_id: str = Field(..., description="Competitor ID")
    competitor_name: str = Field(..., description="Competitor name")
    maturity_levels: List[MechanicMaturity] = Field(default_factory=list, description="Maturity levels for all mechanics")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall maturity score (0-100)")


class GapScore(BaseModel):
    """Gap score for a specific mechanic."""
    
    mechanic_id: int = Field(..., ge=1, le=26, description="Mechanic ID (1-26)")
    mechanic_name: str = Field(..., description="Mechanic name")
    gap_score: int = Field(..., ge=-1, le=1, description="Gap score (-1=Lagging, 0=Parity, +1=Market Leader)")
    our_maturity: int = Field(..., ge=0, le=3, description="Our brand's maturity level")
    competitor_maturity: int = Field(..., ge=0, le=3, description="Competitor's maturity level")


class GapMatrixResponse(BaseModel):
    """Response model for gap matrix analysis."""
    
    brand_name: str = Field(..., description="Our brand name")
    competitor_name: str = Field(..., description="Competitor name")
    gap_scores: List[GapScore] = Field(default_factory=list, description="Gap scores for all mechanics")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "Our Brand",
                "competitor_name": "Competitor Brand",
                "gap_scores": [
                    {
                        "mechanic_id": 1,
                        "mechanic_name": "Wheel of Fortune",
                        "gap_score": 1,
                        "our_maturity": 3,
                        "competitor_maturity": 2
                    }
                ],
                "summary": {
                    "lagging_count": 5,
                    "parity_count": 15,
                    "leading_count": 6,
                    "overall_gap_score": 0.04
                }
            }
        }
