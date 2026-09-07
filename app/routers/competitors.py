from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import verify_api_key
from app.models.competitor import (
    Competitor, 
    CompetitorCreate, 
    CompetitorMaturityProfile,
    GapMatrixResponse,
    GapScore
)
from app.core.database import SupabaseClient
from typing import List, Dict, Any
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/competitors", tags=["Competitors"])


@router.get("", response_model=List[Competitor])
async def get_competitors(
    api_key: str = Depends(verify_api_key)
) -> List[Competitor]:
    """
    Retrieve list of all tracked competitors.
    """
    try:
        competitors_data = await SupabaseClient.get_competitors()
        
        competitors = [
            Competitor(
                id=comp.get("id"),
                name=comp.get("name"),
                website=comp.get("website"),
                notes=comp.get("notes"),
                created_at=comp.get("created_at"),
                updated_at=comp.get("updated_at")
            )
            for comp in competitors_data
        ]
        
        logger.info(f"Retrieved {len(competitors)} competitors")
        return competitors
        
    except Exception as e:
        logger.error(f"Error retrieving competitors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving competitors: {str(e)}"
        )


@router.post("", response_model=Competitor)
async def create_competitor(
    competitor: CompetitorCreate,
    api_key: str = Depends(verify_api_key)
) -> Competitor:
    """
    Add a new competitor to track.
    """
    try:
        competitor_data = await SupabaseClient.insert_competitor(
            name=competitor.name,
            website=competitor.website,
            notes=competitor.notes
        )
        
        logger.info(f"Created competitor: {competitor.name}")
        
        return Competitor(
            id=competitor_data.get("id"),
            name=competitor_data.get("name"),
            website=competitor_data.get("website"),
            notes=competitor_data.get("notes"),
            created_at=competitor_data.get("created_at"),
            updated_at=competitor_data.get("updated_at")
        )
        
    except Exception as e:
        logger.error(f"Error creating competitor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating competitor: {str(e)}"
        )


@router.delete("/{competitor_id}")
async def delete_competitor(
    competitor_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, str]:
    """
    Remove a competitor from tracking.
    """
    try:
        success = await SupabaseClient.delete_competitor(competitor_id)
        
        if success:
            logger.info(f"Deleted competitor: {competitor_id}")
            return {"message": "Competitor deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Competitor not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting competitor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting competitor: {str(e)}"
        )


@router.get("/gap-matrix", response_model=GapMatrixResponse)
async def get_gap_matrix(
    competitor_id: str,
    api_key: str = Depends(verify_api_key)
) -> GapMatrixResponse:
    """
    Calculate the comparative Gap Matrix between "Our Brand" and a specific competitor.
    
    Returns Gap score for each mechanic:
    - [-1] (Lagging)
    - [0] (Parity)
    - [+1] (Market Leader)
    """
    try:
        # Get competitor information
        competitors = await SupabaseClient.get_competitors()
        competitor = next((c for c in competitors if c.get("id") == competitor_id), None)
        
        if not competitor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Competitor not found"
            )
        
        # Get maturity levels for our brand (default brand name)
        our_maturity_data = await SupabaseClient.get_mechanic_maturity_levels("Our Brand")
        
        # Get maturity levels for the competitor
        competitor_maturity_data = await SupabaseClient.get_mechanic_maturity_levels(competitor.get("name"))
        
        # Build maturity dictionaries
        our_maturity = {m.get("mechanic_id"): m.get("maturity_level", 0) for m in our_maturity_data}
        competitor_maturity = {m.get("mechanic_id"): m.get("maturity_level", 0) for m in competitor_maturity_data}
        
        # Calculate gap scores for all 26 mechanics
        gap_scores = []
        lagging_count = 0
        parity_count = 0
        leading_count = 0
        
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
        
        for mechanic_id in range(1, 27):
            our_level = our_maturity.get(mechanic_id, 0)
            competitor_level = competitor_maturity.get(mechanic_id, 0)
            
            # Calculate gap score
            if our_level > competitor_level:
                gap_score = 1
                leading_count += 1
            elif our_level < competitor_level:
                gap_score = -1
                lagging_count += 1
            else:
                gap_score = 0
                parity_count += 1
            
            gap_scores.append(GapScore(
                mechanic_id=mechanic_id,
                mechanic_name=mechanic_names.get(mechanic_id, f"Mechanic {mechanic_id}"),
                gap_score=gap_score,
                our_maturity=our_level,
                competitor_maturity=competitor_level
            ))
        
        # Calculate overall gap score
        total_mechanics = len(gap_scores)
        overall_gap_score = (leading_count - lagging_count) / total_mechanics if total_mechanics > 0 else 0
        
        # Determine overall position
        if overall_gap_score > 0.2:
            overall_position = "Market Leader"
        elif overall_gap_score < -0.2:
            overall_position = "Lagging"
        else:
            overall_position = "Competitive"
        
        response = GapMatrixResponse(
            brand_name="Our Brand",
            competitor_name=competitor.get("name"),
            gap_scores=gap_scores,
            summary={
                "lagging_count": lagging_count,
                "parity_count": parity_count,
                "leading_count": leading_count,
                "overall_gap_score": round(overall_gap_score, 3),
                "overall_position": overall_position
            }
        )
        
        logger.info(f"Generated gap matrix for competitor: {competitor.get('name')}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating gap matrix: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating gap matrix: {str(e)}"
        )


@router.get("/maturity-profiles", response_model=List[CompetitorMaturityProfile])
async def get_maturity_profiles(
    api_key: str = Depends(verify_api_key)
) -> List[CompetitorMaturityProfile]:
    """
    Retrieve maturity profiles for all competitors.
    """
    try:
        competitors = await SupabaseClient.get_competitors()
        profiles = []
        
        for competitor in competitors:
            maturity_data = await SupabaseClient.get_mechanic_maturity_levels(competitor.get("name"))
            
            # Calculate overall score
            if maturity_data:
                avg_maturity = sum(m.get("maturity_level", 0) for m in maturity_data) / len(maturity_data)
                overall_score = (avg_maturity / 3) * 100  # Convert to percentage
            else:
                overall_score = 0.0
            
            profiles.append(CompetitorMaturityProfile(
                competitor_id=competitor.get("id"),
                competitor_name=competitor.get("name"),
                maturity_levels=maturity_data,
                overall_score=round(overall_score, 1)
            ))
        
        logger.info(f"Retrieved maturity profiles for {len(profiles)} competitors")
        return profiles
        
    except Exception as e:
        logger.error(f"Error retrieving maturity profiles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving maturity profiles: {str(e)}"
        )
