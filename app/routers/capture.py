from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import verify_api_key
from app.models.capture import CaptureRequest, CaptureResponse
from app.services.vision_agent import vision_agent
from app.services.rule_engine import rule_engine
from app.core.database import SupabaseClient
from typing import Dict, Any
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/capture", tags=["Capture"])


@router.post("", response_model=CaptureResponse)
async def create_capture(
    request: CaptureRequest,
    api_key: str = Depends(verify_api_key)
) -> CaptureResponse:
    """
    Process screenshot capture from Chrome extension.
    
    This endpoint accepts screenshot data from the Chrome extension,
    analyzes it using AI vision, calculates maturity levels,
    detects red flags, and stores the results in the database.
    """
    try:
        logger.info(f"Processing capture for brand: {request.brand_name}, mechanic: {request.selected_mechanic_name}")
        
        # Step 1: Analyze screenshot with vision agent (Gemini)
        logger.info("Step 1: Running Vision Agent analysis...")
        vision_analysis = await vision_agent.analyze_screenshot(
            mechanic_name=request.selected_mechanic_name,
            screenshot_base64=request.screenshot_base64,
            sanitized_dom_text=request.sanitized_dom_text
        )
        logger.info(f"Vision analysis completed (isValid: {vision_analysis.is_valid_match}, quality: {vision_analysis.ui_quality_score})")
        
        # Step 2: Calculate maturity level using rule engine
        logger.info("Step 2: Calculating maturity level...")
        maturity_level = rule_engine.calculate_maturity_level(
            mechanic_id=request.selected_mechanic_id,
            metadata=vision_analysis.metadata,
            ui_quality_score=vision_analysis.ui_quality_score,
            is_valid_match=vision_analysis.is_valid_match
        )
        
        # Step 3: Detect red flags using rule engine
        logger.info("Step 3: Detecting red flags...")
        red_flags = rule_engine.detect_red_flags(
            mechanic_id=request.selected_mechanic_id,
            metadata=vision_analysis.metadata,
            ui_quality_score=vision_analysis.ui_quality_score,
            is_valid_match=vision_analysis.is_valid_match
        )
        
        # Step 4: Prepare screenshot URL placeholder
        screenshot_url = f"screenshots/{uuid.uuid4()}.jpg"
        
        # Step 5: Prepare metadata for database
        metadata_dict = {
            "wager_multiplier": vision_analysis.metadata.wager_multiplier,
            "minimum_deposit": vision_analysis.metadata.minimum_deposit,
            "expiration_timer": vision_analysis.metadata.expiration_timer,
            "reward_type": vision_analysis.metadata.reward_type,
            "additional_params": vision_analysis.metadata.additional_params,
            "confidence_score": vision_analysis.confidence_score,
            "is_valid_match": vision_analysis.is_valid_match
        }
        
        # Step 6: Save audit log to Supabase
        audit_id = str(uuid.uuid4())
        audit_record = {}
        try:
            logger.info("Step 6: Saving audit log to Supabase...")
            audit_record = await SupabaseClient.insert_mechanic_audit(
                brand_name=request.brand_name,
                scenario=request.scenario,
                mechanic_id=request.selected_mechanic_id,
                mechanic_name=request.selected_mechanic_name,
                screenshot_url=screenshot_url,
                page_url=request.page_url,
                metadata=metadata_dict,
                maturity_level=maturity_level,
                ui_quality_score=vision_analysis.ui_quality_score,
                notes=request.notes
            )
            if isinstance(audit_record, dict) and audit_record.get("id"):
                audit_id = audit_record.get("id")
            logger.info(f"Audit saved to Supabase with ID: {audit_id}")
        except Exception as db_err:
            logger.error(f"Supabase DB insert failed (check SUPABASE_KEY / SUPABASE_URL): {db_err}")
            # Продвигаемся дальше, чтобы клиент получил результат анализа даже при сбое БД

        # Step 7: Save red flags to database
        if audit_record:
            try:
                logger.info("Step 7: Saving red flags to Supabase...")
                for flag in red_flags:
                    await SupabaseClient.insert_red_flag(
                        audit_id=audit_id,
                        flag_type=flag.flag_type,
                        severity=flag.severity,
                        description=flag.description,
                        recommended_action=flag.recommended_action
                    )
            except Exception as flag_err:
                logger.error(f"Failed to insert red flags into Supabase: {flag_err}")

        # Step 8: Build response
        response = CaptureResponse(
            success=True,
            audit_id=audit_id,
            vision_analysis=vision_analysis,
            maturity_level=maturity_level,
            red_flags=red_flags
        )
        
        logger.info(f"Capture processed successfully for {request.brand_name}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing capture: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing capture: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for the capture service."""
    return {
        "status": "healthy",
        "service": "capture"
    }
