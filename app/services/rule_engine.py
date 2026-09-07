from app.models.capture import MechanicMetadata, RedFlag
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RuleEngine:
    """Service for calculating maturity levels and detecting anomalies."""
    
    # Maturity level definitions
    MATURITY_NONE = 0
    MATURITY_PRIMITIVE = 1
    MATURITY_EXPANDED = 2
    MATURITY_FINALIZED = 3
    
    # Red flag definitions
    TIER_1_FLAGS = [
        "hard_streak_reset",
        "unfair_wagering",
        "hidden_terms",
        "manipulative_timing",
        "impossible_requirements"
    ]
    
    TIER_2_FLAGS = [
        "poor_ui_design",
        "unclear_communication",
        "limited_payment_options",
        "slow_payout_times",
        "missing_responsible_gaming"
    ]
    
    def __init__(self):
        self.mechanic_specific_rules = self._load_mechanic_rules()
    
    def _load_mechanic_rules(self) -> Dict[int, Dict[str, Any]]:
        """
        Load mechanic-specific rules for maturity calculation.
        
        Returns:
            Dict: Mechanic ID to rules mapping
        """
        return {
            # Wheel of Fortune
            1: {
                "name": "Wheel of Fortune",
                "primitive_indicators": ["basic_wheel", "single_prize"],
                "expanded_indicators": ["multiple_prizes", "visual_effects"],
                "finalized_indicators": ["progressive_jackpot", "tiered_rewards", "personalization"]
            },
            # Daily Streak Bonus
            2: {
                "name": "Daily Streak Bonus",
                "primitive_indicators": ["basic_login_reward"],
                "expanded_indicators": ["streak_multiplier", "calendar_view"],
                "finalized_indicators": ["streak_recovery", "milestone_rewards", "social_sharing"]
            },
            # Lootbox
            3: {
                "name": "Lootbox",
                "primitive_indicators": ["random_reward"],
                "expanded_indicators": ["multiple_tiers", "visual_preview"],
                "finalized_indicators": ["pity_system", "guaranteed_drops", "tradeable_items"]
            },
            # Daily Claimer
            4: {
                "name": "Daily Claimer",
                "primitive_indicators": ["daily_button"],
                "expanded_indicators": ["increasing_rewards", "bonus_events"],
                "finalized_indicators": ["missed_day_recovery", "special_events", "achievement_integration"]
            },
            # Achievement System
            5: {
                "name": "Achievement System",
                "primitive_indicators": ["basic_badges"],
                "expanded_indicators": ["progress_tracking", "reward_tiers"],
                "finalized_indicators": ["social_comparison", "seasonal_events", "prestige_levels"]
            },
            # Leaderboard
            6: {
                "name": "Leaderboard",
                "primitive_indicators": ["simple_ranking"],
                "expanded_indicators": ["multiple_categories", "time_filters"],
                "finalized_indicators": ["personal_goals", "social_features", "real_time_updates"]
            },
            # VIP Program
            7: {
                "name": "VIP Program",
                "primitive_indicators": ["basic_tiers"],
                "expanded_indicators": ["tier_benefits", "progression_system"],
                "finalized_indicators": ["personalized_offers", "exclusive_events", "dedicated_support"]
            },
            # Referral Program
            8: {
                "name": "Referral Program",
                "primitive_indicators": ["basic_referral_link"],
                "expanded_indicators": ["multi_tier_rewards", "tracking_dashboard"],
                "finalized_indicators": ["social_sharing", "gamified_referrals", "milestone_bonuses"]
            },
            # Tournament
            9: {
                "name": "Tournament",
                "primitive_indicators": ["basic_competition"],
                "expanded_indicators": ["multiple_formats", "leaderboard"],
                "finalized_indicators": ["live_updates", "social_features", "variable_prizes"]
            },
            # Cashback
            10: {
                "name": "Cashback",
                "primitive_indicators": ["basic_percentage"],
                "expanded_indicators": ["tiered_rates", "calculation_transparency"],
                "finalized_indicators": ["instant_payout", "bonus_boosters", "loss_limits"]
            },
            # Free Spins
            11: {
                "name": "Free Spins",
                "primitive_indicators": ["basic_spins"],
                "expanded_indicators": ["game_selection", "wager_requirements"],
                "finalized_indicators": ["flexible_allocation", "game_unlocking", "spin_accumulation"]
            },
            # Deposit Bonus
            12: {
                "name": "Deposit Bonus",
                "primitive_indicators": ["basic_match"],
                "expanded_indicators": ["tiered_matching", "game_restrictions"],
                "finalized_indicators": ["personalized_offers", "wager_free_bonuses", "bonus_choice"]
            },
            # No Deposit Bonus
            13: {
                "name": "No Deposit Bonus",
                "primitive_indicators": ["free_bonus"],
                "expanded_indicators": ["wager_requirements", "withdrawal_limits"],
                "finalized_indicators": ["risk_free_play", "conversion_tracking", "graduated_rewards"]
            },
            # Loyalty Points
            14: {
                "name": "Loyalty Points",
                "primitive_indicators": ["basic_points"],
                "expanded_indicators": ["point_multiplier", "redemption_options"],
                "finalized_indicators": ["point_expiration_management", "bonus_points", "exclusive_rewards"]
            },
            # Level System
            15: {
                "name": "Level System",
                "primitive_indicators": ["basic_levels"],
                "expanded_indicators": ["level_benefits", "progress_bar"],
                "finalized_indicators": ["prestige_levels", "level_reset_mechanics", "social_comparison"]
            },
            # Mission System
            16: {
                "name": "Mission System",
                "primitive_indicators": ["simple_tasks"],
                "expanded_indicators": ["mission_variety", "reward_scaling"],
                "finalized_indicators": ["dynamic_missions", "story_progression", "collaborative_missions"]
            },
            # Season Pass
            17: {
                "name": "Season Pass",
                "primitive_indicators": ["basic_track"],
                "expanded_indicators": ["free_premium_tracks", "milestone_rewards"],
                "finalized_indicators": ["seasonal_themes", "carryover_mechanics", "exclusive_content"]
            },
            # Challenge System
            18: {
                "name": "Challenge System",
                "primitive_indicators": ["daily_challenges"],
                "expanded_indicators": ["difficulty_tiers", "time_limits"],
                "finalized_indicators": ["adaptive_difficulty", "social_challenges", "reward_optimization"]
            },
            # Bonus Shop
            19: {
                "name": "Bonus Shop",
                "primitive_indicators": ["basic_exchange"],
                "expanded_indicators": ["dynamic_pricing", "limited_offers"],
                "finalized_indicators": ["personalized_recommendations", "shop_events", "exclusive_items"]
            },
            # Prize Drops
            20: {
                "name": "Prize Drops",
                "primitive_indicators": ["random_drops"],
                "expanded_indicators": ["drop_schedules", "prize_variety"],
                "finalized_indicators": ["progressive_drops", "community_events", "guaranteed_prizes"]
            },
            # Live Events
            21: {
                "name": "Live Events",
                "primitive_indicators": ["scheduled_events"],
                "expanded_indicators": ["event_variety", "live_updates"],
                "finalized_indicators": ["interactive_events", "social_integration", "event_archives"]
            },
            # Social Features
            22: {
                "name": "Social Features",
                "primitive_indicators": ["basic_sharing"],
                "expanded_indicators": ["social_feed", "friend_system"],
                "finalized_indicators": ["social_gamification", "community_events", "social_competition"]
            },
            # Personalization
            23: {
                "name": "Personalization",
                "primitive_indicators": ["basic_preferences"],
                "expanded_indicators": ["behavior_tracking", "targeted_offers"],
                "finalized_indicators": ["ai_recommendations", "dynamic_ui", "predictive_offers"]
            },
            # Gamification
            24: {
                "name": "Gamification",
                "primitive_indicators": ["basic_points"],
                "expanded_indicators": ["progress_systems", "achievements"],
                "finalized_indicators": ["narrative_elements", "character_progression", "story_integration"]
            },
            # Responsible Gaming
            25: {
                "name": "Responsible Gaming",
                "primitive_indicators": ["basic_limits"],
                "expanded_indicators": ["self_exclusion", "reality_checks"],
                "finalized_indicators": ["ai_monitoring", "personalized_limits", "support_integration"]
            },
            # Anti-Fraud
            26: {
                "name": "Anti-Fraud",
                "primitive_indicators": ["basic_verification"],
                "expanded_indicators": ["transaction_monitoring", "behavior_analysis"],
                "finalized_indicators": ["ai_detection", "real_time_blocking", "risk_scoring"]
            }
        }
    
    def calculate_maturity_level(
        self,
        mechanic_id: int,
        metadata: MechanicMetadata,
        ui_quality_score: int,
        is_valid_match: bool
    ) -> int:
        """
        Calculate maturity level based on mechanic metadata and UI quality.
        
        Args:
            mechanic_id: ID of the mechanic (1-26)
            metadata: Extracted metadata from vision agent
            ui_quality_score: UI quality score (1-5)
            is_valid_match: Whether the UI element matches the mechanic
            
        Returns:
            int: Maturity level (0=None, 1=Primitive, 2=Expanded, 3=Finalized)
        """
        if not is_valid_match:
            return self.MATURITY_NONE
        
        # Get mechanic rules
        rules = self.mechanic_specific_rules.get(mechanic_id)
        if not rules:
            logger.warning(f"No rules found for mechanic ID: {mechanic_id}")
            return self.MATURITY_PRIMITIVE
        
        # Calculate base maturity from metadata presence
        metadata_score = self._calculate_metadata_score(metadata)
        
        # Adjust based on UI quality
        quality_adjustment = (ui_quality_score - 3) * 0.5
        
        # Calculate final maturity
        final_score = metadata_score + quality_adjustment
        
        # Map to maturity levels
        if final_score < 1.0:
            return self.MATURITY_PRIMITIVE
        elif final_score < 2.0:
            return self.MATURITY_EXPANDED
        else:
            return self.MATURITY_FINALIZED
    
    def _calculate_metadata_score(self, metadata: MechanicMetadata) -> float:
        """
        Calculate a score based on metadata completeness.
        
        Args:
            metadata: Mechanic metadata
            
        Returns:
            float: Metadata score (0-3)
        """
        score = 0.0
        
        # Check for key metadata fields
        if metadata.wager_multiplier is not None:
            score += 0.5
        if metadata.minimum_deposit is not None:
            score += 0.5
        if metadata.expiration_timer is not None:
            score += 0.5
        if metadata.reward_type is not None:
            score += 0.5
        if metadata.additional_params:
            score += 0.5
        
        # Additional complexity from additional_params
        if len(metadata.additional_params) > 2:
            score += 0.5
        
        return min(score, 3.0)
    
    def detect_red_flags(
        self,
        mechanic_id: int,
        metadata: MechanicMetadata,
        ui_quality_score: int,
        is_valid_match: bool
    ) -> List[RedFlag]:
        """
        Detect red flags based on mechanic analysis.
        
        Args:
            mechanic_id: ID of the mechanic (1-26)
            metadata: Extracted metadata from vision agent
            ui_quality_score: UI quality score (1-5)
            is_valid_match: Whether the UI element matches the mechanic
            
        Returns:
            List[RedFlag]: Detected red flags
        """
        red_flags = []
        
        # Check for Tier 1 flags (critical issues)
        red_flags.extend(self._check_tier_1_flags(mechanic_id, metadata))
        
        # Check for Tier 2 flags (important issues)
        red_flags.extend(self._check_tier_2_flags(mechanic_id, ui_quality_score, metadata))
        
        return red_flags
    
    def _check_tier_1_flags(self, mechanic_id: int, metadata: MechanicMetadata) -> List[RedFlag]:
        """
        Check for Tier 1 (critical) red flags.
        
        Args:
            mechanic_id: ID of the mechanic
            metadata: Mechanic metadata
            
        Returns:
            List[RedFlag]: Detected Tier 1 flags
        """
        flags = []
        
        # Check for unfair wagering requirements
        if metadata.wager_multiplier and metadata.wager_multiplier > 50:
            flags.append(RedFlag(
                flag_type="Tier 1",
                severity="Critical",
                description=f"Excessive wagering requirement: {metadata.wager_multiplier}x",
                recommended_action="Reduce wagering requirement to industry standard (35x or lower)"
            ))
        
        # Check for extremely high minimum deposits
        if metadata.minimum_deposit and metadata.minimum_deposit > 100:
            flags.append(RedFlag(
                flag_type="Tier 1",
                severity="High",
                description=f"High minimum deposit requirement: ${metadata.minimum_deposit}",
                recommended_action="Consider lowering minimum deposit to improve accessibility"
            ))
        
        # Mechanic-specific checks
        if mechanic_id == 2:  # Daily Streak Bonus
            # Check for hard streak reset issues
            if metadata.additional_params.get("streak_reset") == "hard":
                flags.append(RedFlag(
                    flag_type="Tier 1",
                    severity="Critical",
                    description="Hard streak reset without recovery path",
                    recommended_action="Implement streak recovery mechanic or soften reset logic"
                ))
        
        if mechanic_id == 3:  # Lootbox
            # Check for missing pity system
            if not metadata.additional_params.get("pity_system"):
                flags.append(RedFlag(
                    flag_type="Tier 1",
                    severity="High",
                    description="Lootbox missing pity system or guaranteed drops",
                    recommended_action="Implement pity system to ensure fair player experience"
                ))
        
        return flags
    
    def _check_tier_2_flags(
        self,
        mechanic_id: int,
        ui_quality_score: int,
        metadata: MechanicMetadata
    ) -> List[RedFlag]:
        """
        Check for Tier 2 (important) red flags.
        
        Args:
            mechanic_id: ID of the mechanic
            ui_quality_score: UI quality score
            metadata: Mechanic metadata
            
        Returns:
            List[RedFlag]: Detected Tier 2 flags
        """
        flags = []
        
        # Check for poor UI design
        if ui_quality_score <= 2:
            flags.append(RedFlag(
                flag_type="Tier 2",
                severity="Medium",
                description=f"Poor UI design quality (score: {ui_quality_score}/5)",
                recommended_action="Improve UI design for better user experience and clarity"
            ))
        
        # Check for missing expiration information
        if not metadata.expiration_timer:
            flags.append(RedFlag(
                flag_type="Tier 2",
                severity="Low",
                description="Missing expiration timer information",
                recommended_action="Clearly display expiration time for rewards"
            ))
        
        # Check for unclear reward type
        if not metadata.reward_type:
            flags.append(RedFlag(
                flag_type="Tier 2",
                severity="Low",
                description="Reward type not clearly specified",
                recommended_action="Clearly specify the type of reward being offered"
            ))
        
        return flags


# Singleton instance
rule_engine = RuleEngine()
