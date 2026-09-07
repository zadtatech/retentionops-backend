from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import verify_api_key
from app.models.analytics import (
    RetentionCanvasResponse,
    MechanicStatus,
    ROICalculationRequest,
    ROICalculationResponse,
    RedFlagsResponse,
    RedFlagResponse
)
from app.services.roi_calculator import roi_calculator
from app.core.database import SupabaseClient
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/canvas", response_model=RetentionCanvasResponse)
async def get_retention_canvas(
    api_key: str = Depends(verify_api_key)
) -> RetentionCanvasResponse:
    """
    Return full status of the 26 retention mechanics for the main project.
    """
    try:
        brand_name = "Our Brand"
        
        # Get mechanic audits from database
        maturity_data = await SupabaseClient.get_mechanic_maturity_levels(brand_name)
        
        # Get red flags
        red_flags_data = await SupabaseClient.get_red_flags()
        
        # Build mechanic statuses
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
        
        mechanic_statuses = []
        active_count = 0
        total_maturity = 0
        
        for mechanic_id in range(1, 27):
            # Find maturity data for this mechanic
            maturity_record = next(
                (m for m in maturity_data if m.get("mechanic_id") == mechanic_id),
                None
            )
            
            if maturity_record:
                maturity_level = maturity_record.get("maturity_level", 0)
                is_active = maturity_level > 0
                last_audited = maturity_record.get("updated_at")
                
                # Get UI quality score from metadata if available
                metadata = maturity_record.get("metadata", {})
                ui_quality_score = metadata.get("ui_quality_score")
                
                if is_active:
                    active_count += 1
                    total_maturity += maturity_level
            else:
                maturity_level = 0
                is_active = False
                last_audited = None
                ui_quality_score = None
            
            # Count red flags for this mechanic
            mechanic_flags_count = sum(
                1 for flag in red_flags_data 
                if flag.get("mechanic_id") == mechanic_id and not flag.get("is_resolved", False)
            )
            
            mechanic_statuses.append(MechanicStatus(
                mechanic_id=mechanic_id,
                mechanic_name=mechanic_names.get(mechanic_id, f"Mechanic {mechanic_id}"),
                maturity_level=maturity_level,
                is_active=is_active,
                last_audited=last_audited,
                ui_quality_score=ui_quality_score,
                red_flags_count=mechanic_flags_count
            ))
        
        # Calculate overall maturity score
        overall_maturity_score = 0.0
        if active_count > 0:
            avg_maturity = total_maturity / active_count
            overall_maturity_score = (avg_maturity / 3) * 100  # Convert to percentage
        
        response = RetentionCanvasResponse(
            brand_name=brand_name,
            total_mechanics=26,
            active_mechanics=active_count,
            overall_maturity_score=round(overall_maturity_score, 1),
            mechanic_statuses=mechanic_statuses,
            last_updated=datetime.utcnow()
        )
        
        logger.info(f"Retrieved retention canvas for {brand_name}")
        return response
        
    except Exception as e:
        logger.error(f"Error retrieving retention canvas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving retention canvas: {str(e)}"
        )


@router.post("/calculate-roi", response_model=ROICalculationResponse)
async def calculate_roi(
    request: ROICalculationRequest,
    api_key: str = Depends(verify_api_key)
) -> ROICalculationResponse:
    """
    Calculate ROI metrics based on financial inputs.
    
    Uses the following formulas:
    - break_even_ggr_growth = (vendor_cost / annual_ggr) * 100
    - break_even_bonus_reduction = (vendor_cost / annual_bonus_emission) * 100
    - net_annual_gain = (annual_ggr * (target_uplift_percent / 100)) - vendor_cost
    - roi_percentage = (net_annual_gain / vendor_cost) * 100
    """
    try:
        logger.info(f"Calculating ROI with target uplift: {request.target_uplift_percent}%")
        
        roi_result = roi_calculator.calculate_roi(
            annual_ggr=request.annual_ggr,
            annual_bonus_emission=request.annual_bonus_emission,
            vendor_cost=request.vendor_cost,
            target_uplift_percent=request.target_uplift_percent
        )
        
        logger.info(f"ROI calculation completed: {roi_result.roi_percentage:.2f}%")
        return roi_result
        
    except Exception as e:
        logger.error(f"Error calculating ROI: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating ROI: {str(e)}"
        )


@router.get("/red-flags", response_model=RedFlagsResponse)
async def get_red_flags(
    severity: str = None,
    api_key: str = Depends(verify_api_key)
) -> RedFlagsResponse:
    """
    Return list of active Tier 1 & Tier 2 anomalies with severity badges
    and recommended resolution actions.
    """
    try:
        # Get red flags from database
        red_flags_data = await SupabaseClient.get_red_flags(severity=severity)
        
        # Filter for unresolved flags only
        active_flags = [flag for flag in red_flags_data if not flag.get("is_resolved", False)]
        
        # Count by severity
        critical_count = sum(1 for flag in active_flags if flag.get("severity") == "Critical")
        high_count = sum(1 for flag in active_flags if flag.get("severity") == "High")
        medium_count = sum(1 for flag in active_flags if flag.get("severity") == "Medium")
        low_count = sum(1 for flag in active_flags if flag.get("severity") == "Low")
        
        # Build response objects
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
        
        flag_responses = []
        for flag in active_flags:
            mechanic_id = flag.get("mechanic_id")
            flag_responses.append(RedFlagResponse(
                id=flag.get("id"),
                flag_type=flag.get("flag_type"),
                severity=flag.get("severity"),
                description=flag.get("description"),
                recommended_action=flag.get("recommended_action"),
                mechanic_id=mechanic_id,
                mechanic_name=mechanic_names.get(mechanic_id) if mechanic_id else None,
                created_at=flag.get("created_at"),
                is_resolved=flag.get("is_resolved", False)
            ))
        
        response = RedFlagsResponse(
            total_flags=len(active_flags),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            flags=flag_responses,
            last_updated=datetime.utcnow()
        )
        
        logger.info(f"Retrieved {len(active_flags)} active red flags")
        return response
        
    except Exception as e:
        logger.error(f"Error retrieving red flags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving red flags: {str(e)}"
        )


@router.get("/investment-scenarios")
async def get_investment_scenarios(
    annual_ggr: float,
    annual_bonus_emission: float,
    vendor_cost: float,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Calculate multiple investment scenarios for comparison.
    """
    try:
        logger.info(f"Generating investment scenarios for vendor cost: ${vendor_cost}")
        
        scenarios = roi_calculator.calculate_investment_scenarios(
            annual_ggr=annual_ggr,
            annual_bonus_emission=annual_bonus_emission,
            vendor_cost=vendor_cost
        )
        
        logger.info(f"Generated {len(scenarios)} investment scenarios")
        return scenarios
        
    except Exception as e:
        logger.error(f"Error generating investment scenarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating investment scenarios: {str(e)}"
        )
