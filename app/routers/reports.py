from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from app.core.security import verify_api_key
from app.models.report import PDFReportRequest, PDFReportData
from app.services.pdf_generator import pdf_generator
from app.core.database import SupabaseClient
from app.models.analytics import RetentionCanvasResponse
from app.models.competitor import GapMatrixResponse
from app.models.report import (
    MechanicCoverageSummary,
    GapAnalysisSummary,
    ROIAnalysisSummary
)
from typing import Optional
import logging
from datetime import datetime
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.post("/pdf")
async def generate_pdf_report(
    request: PDFReportRequest,
    api_key: str = Depends(verify_api_key)
) -> Response:
    """
    Generate a 1-page executive PDF report containing:
    - Brand Name & Audit Date
    - Retention Canvas Summary (Core mechanics coverage score)
    - Competitor Gap Analysis summary
    - ROI Break-Even Analysis table
    - Top 3 Critical Red Flags to fix
    
    Returns PDF file binary stream (application/pdf).
    """
    try:
        logger.info(f"Generating PDF report for brand: {request.brand_name}")
        
        # Initialize report data
        report_data = PDFReportData(
            brand_name=request.brand_name,
            report_date=datetime.utcnow()
        )
        
        # Step 1: Get Retention Canvas Summary if requested
        if request.include_canvas_summary:
            canvas_summary = await _get_canvas_summary(request.brand_name)
            report_data.canvas_summary = canvas_summary
        
        # Step 2: Get Competitor Gap Analysis if requested
        if request.include_gap_analysis:
            gap_analysis = await _get_gap_analysis_summary(request.brand_name)
            report_data.gap_analysis = gap_analysis
        
        # Step 3: Get ROI Analysis if requested
        if request.include_roi_analysis:
            roi_analysis = await _get_roi_analysis_summary()
            report_data.roi_analysis = roi_analysis
        
        # Step 4: Get Top Red Flags if requested
        if request.include_red_flags:
            top_flags = await _get_top_red_flags(request.top_red_flags_count)
            report_data.top_red_flags = top_flags
        
        # Step 5: Generate PDF
        pdf_content = pdf_generator.generate_executive_report(report_data)
        
        # Step 6: Return PDF as streaming response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=retentionops_report_{request.brand_name}_{datetime.now().strftime('%Y%m%d')}.pdf",
                "Content-Length": str(len(pdf_content))
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF report: {str(e)}"
        )


async def _get_canvas_summary(brand_name: str) -> MechanicCoverageSummary:
    """
    Get retention canvas summary for the report.
    """
    try:
        # Get maturity data
        maturity_data = await SupabaseClient.get_mechanic_maturity_levels(brand_name)
        
        total_mechanics = 26
        active_mechanics = sum(1 for m in maturity_data if m.get("maturity_level", 0) > 0)
        
        coverage_percentage = (active_mechanics / total_mechanics) * 100 if total_mechanics > 0 else 0
        
        total_maturity = sum(m.get("maturity_level", 0) for m in maturity_data)
        average_maturity = total_maturity / active_mechanics if active_mechanics > 0 else 0
        
        return MechanicCoverageSummary(
            total_mechanics=total_mechanics,
            active_mechanics=active_mechanics,
            coverage_percentage=round(coverage_percentage, 1),
            average_maturity=round(average_maturity, 1)
        )
        
    except Exception as e:
        logger.error(f"Error getting canvas summary: {e}")
        # Return default values on error
        return MechanicCoverageSummary(
            total_mechanics=26,
            active_mechanics=0,
            coverage_percentage=0.0,
            average_maturity=0.0
        )


async def _get_gap_analysis_summary(brand_name: str) -> GapAnalysisSummary:
    """
    Get gap analysis summary for the report.
    """
    try:
        # Get competitors
        competitors = await SupabaseClient.get_competitors()
        
        if not competitors:
            return GapAnalysisSummary(
                total_competitors=0,
                lagging_mechanics=0,
                parity_mechanics=0,
                leading_mechanics=0,
                overall_position="No competitors"
            )
        
        # Get our maturity data
        our_maturity_data = await SupabaseClient.get_mechanic_maturity_levels(brand_name)
        our_maturity = {m.get("mechanic_id"): m.get("maturity_level", 0) for m in our_maturity_data}
        
        # Aggregate across all competitors
        total_lagging = 0
        total_parity = 0
        total_leading = 0
        total_comparisons = 0
        
        for competitor in competitors:
            competitor_maturity_data = await SupabaseClient.get_mechanic_maturity_levels(competitor.get("name"))
            competitor_maturity = {m.get("mechanic_id"): m.get("maturity_level", 0) for m in competitor_maturity_data}
            
            for mechanic_id in range(1, 27):
                our_level = our_maturity.get(mechanic_id, 0)
                competitor_level = competitor_maturity.get(mechanic_id, 0)
                
                if our_level > competitor_level:
                    total_leading += 1
                elif our_level < competitor_level:
                    total_lagging += 1
                else:
                    total_parity += 1
                
                total_comparisons += 1
        
        # Calculate averages per mechanic
        if total_comparisons > 0:
            avg_lagging = total_lagging / len(competitors)
            avg_parity = total_parity / len(competitors)
            avg_leading = total_leading / len(competitors)
        else:
            avg_lagging = avg_parity = avg_leading = 0
        
        # Determine overall position
        if avg_leading > avg_lagging:
            overall_position = "Market Leader"
        elif avg_lagging > avg_leading:
            overall_position = "Lagging"
        else:
            overall_position = "Competitive"
        
        return GapAnalysisSummary(
            total_competitors=len(competitors),
            lagging_mechanics=int(avg_lagging),
            parity_mechanics=int(avg_parity),
            leading_mechanics=int(avg_leading),
            overall_position=overall_position
        )
        
    except Exception as e:
        logger.error(f"Error getting gap analysis summary: {e}")
        # Return default values on error
        return GapAnalysisSummary(
            total_competitors=0,
            lagging_mechanics=0,
            parity_mechanics=0,
            leading_mechanics=0,
            overall_position="Unknown"
        )


async def _get_roi_analysis_summary() -> ROIAnalysisSummary:
    """
    Get ROI analysis summary for the report.
    """
    try:
        # Use default values for demonstration
        # In production, these would come from actual calculations or user inputs
        return ROIAnalysisSummary(
            break_even_ggr_growth=5.0,
            break_even_bonus_reduction=25.0,
            recommended_investment=500000.0,
            expected_roi=150.0
        )
        
    except Exception as e:
        logger.error(f"Error getting ROI analysis summary: {e}")
        # Return default values on error
        return ROIAnalysisSummary(
            break_even_ggr_growth=0.0,
            break_even_bonus_reduction=0.0,
            recommended_investment=0.0,
            expected_roi=0.0
        )


async def _get_top_red_flags(count: int) -> list:
    """
    Get top red flags for the report.
    """
    try:
        # Get red flags from database
        red_flags_data = await SupabaseClient.get_red_flags()
        
        # Filter for unresolved flags and sort by severity
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        
        active_flags = [
            flag for flag in red_flags_data 
            if not flag.get("is_resolved", False)
        ]
        
        sorted_flags = sorted(
            active_flags,
            key=lambda x: severity_order.get(x.get("severity", "Low"), 99)
        )
        
        # Get top N flags
        top_flags = sorted_flags[:count]
        
        # Format for report
        mechanic_names = {
            1: "Wheel of Fortune",
            2: "Daily Streak Bonus",
            3: "Lootbox",
            4: "Daily Claimer",
            5: "Achievement System",
            6: "Leaderboard",
            7: "VIP Program",
            8: "Referral Program",
            9: "Tournament",
            10: "Cashback",
            11: "Free Spins",
            12: "Deposit Bonus",
            13: "No Deposit Bonus",
            14: "Loyalty Points",
            15: "Level System",
            16: "Mission System",
            17: "Season Pass",
            18: "Challenge System",
            19: "Bonus Shop",
            20: "Prize Drops",
            21: "Live Events",
            22: "Social Features",
            23: "Personalization",
            24: "Gamification",
            25: "Responsible Gaming",
            26: "Anti-Fraud"
        }
        
        formatted_flags = []
        for flag in top_flags:
            mechanic_id = flag.get("mechanic_id")
            formatted_flags.append({
                "severity": flag.get("severity"),
                "description": flag.get("description"),
                "mechanic": mechanic_names.get(mechanic_id) if mechanic_id else "Unknown"
            })
        
        return formatted_flags
        
    except Exception as e:
        logger.error(f"Error getting top red flags: {e}")
        return []


@router.get("/health")
async def health_check():
    """Health check endpoint for the reports service."""
    return {
        "status": "healthy",
        "service": "reports",
        "timestamp": datetime.utcnow().isoformat()
    }
