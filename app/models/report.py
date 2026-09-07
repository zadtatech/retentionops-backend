from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PDFReportRequest(BaseModel):
    """Request model for PDF report generation."""
    
    brand_name: str = Field(..., description="Brand name for the report")
    include_canvas_summary: bool = Field(default=True, description="Include retention canvas summary")
    include_gap_analysis: bool = Field(default=True, description="Include competitor gap analysis")
    include_roi_analysis: bool = Field(default=True, description="Include ROI break-even analysis")
    include_red_flags: bool = Field(default=True, description="Include top red flags")
    top_red_flags_count: int = Field(default=3, ge=1, le=10, description="Number of top red flags to include")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "Our Brand",
                "include_canvas_summary": True,
                "include_gap_analysis": True,
                "include_roi_analysis": True,
                "include_red_flags": True,
                "top_red_flags_count": 3
            }
        }


class MechanicCoverageSummary(BaseModel):
    """Summary of mechanic coverage."""
    
    total_mechanics: int = Field(..., description="Total number of mechanics")
    active_mechanics: int = Field(..., description="Number of active mechanics")
    coverage_percentage: float = Field(..., description="Coverage percentage")
    average_maturity: float = Field(..., description="Average maturity level")


class GapAnalysisSummary(BaseModel):
    """Summary of gap analysis."""
    
    total_competitors: int = Field(..., description="Total competitors analyzed")
    lagging_mechanics: int = Field(..., description="Number of mechanics where brand is lagging")
    parity_mechanics: int = Field(..., description="Number of mechanics at parity")
    leading_mechanics: int = Field(..., description="Number of mechanics where brand is leading")
    overall_position: str = Field(..., description="Overall market position")


class ROIAnalysisSummary(BaseModel):
    """Summary of ROI analysis."""
    
    break_even_ggr_growth: float = Field(..., description="Break-even GGR growth percentage")
    break_even_bonus_reduction: float = Field(..., description="Break-even bonus reduction percentage")
    recommended_investment: float = Field(..., description="Recommended investment amount")
    expected_roi: float = Field(..., description="Expected ROI percentage")


class PDFReportData(BaseModel):
    """Data for PDF report generation."""
    
    brand_name: str = Field(..., description="Brand name")
    report_date: datetime = Field(default_factory=datetime.utcnow, description="Report generation date")
    canvas_summary: Optional[MechanicCoverageSummary] = Field(None, description="Retention canvas summary")
    gap_analysis: Optional[GapAnalysisSummary] = Field(None, description="Competitor gap analysis")
    roi_analysis: Optional[ROIAnalysisSummary] = Field(None, description="ROI analysis")
    top_red_flags: List[Dict[str, Any]] = Field(default_factory=list, description="Top red flags to address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "Our Brand",
                "report_date": "2024-01-15T10:30:00Z",
                "canvas_summary": {
                    "total_mechanics": 26,
                    "active_mechanics": 20,
                    "coverage_percentage": 76.9,
                    "average_maturity": 2.3
                },
                "gap_analysis": {
                    "total_competitors": 5,
                    "lagging_mechanics": 5,
                    "parity_mechanics": 15,
                    "leading_mechanics": 6,
                    "overall_position": "Competitive"
                },
                "roi_analysis": {
                    "break_even_ggr_growth": 5.0,
                    "break_even_bonus_reduction": 25.0,
                    "recommended_investment": 500000.0,
                    "expected_roi": 150.0
                },
                "top_red_flags": [
                    {
                        "severity": "Critical",
                        "description": "Hard streak reset on Day 2",
                        "mechanic": "Daily Streak Bonus"
                    }
                ]
            }
        }
