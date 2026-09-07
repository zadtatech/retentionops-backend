from app.models.analytics import ROICalculationResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ROICalculator:
    """Service for calculating ROI and break-even analysis."""
    
    def calculate_roi(
        self,
        annual_ggr: float,
        annual_bonus_emission: float,
        vendor_cost: float,
        target_uplift_percent: float
    ) -> ROICalculationResponse:
        """
        Calculate ROI metrics based on financial inputs.
        
        Args:
            annual_ggr: Annual Gross Gaming Revenue
            annual_bonus_emission: Annual bonus emission amount
            vendor_cost: Vendor/implementation cost
            target_uplift_percent: Target percentage uplift in GGR
            
        Returns:
            ROICalculationResponse: Calculated ROI metrics
        """
        try:
            # Calculate break-even metrics
            break_even_ggr_growth = self._calculate_break_even_ggr_growth(
                vendor_cost, annual_ggr
            )
            
            break_even_bonus_reduction = self._calculate_break_even_bonus_reduction(
                vendor_cost, annual_bonus_emission
            )
            
            # Calculate net annual gain
            net_annual_gain = self._calculate_net_annual_gain(
                annual_ggr, target_uplift_percent, vendor_cost
            )
            
            # Calculate ROI percentage
            roi_percentage = self._calculate_roi_percentage(
                net_annual_gain, vendor_cost
            )
            
            # Determine if profitable
            is_profitable = net_annual_gain > 0
            
            # Calculate payback period if profitable
            payback_period_months = None
            if is_profitable and vendor_cost > 0:
                monthly_gain = net_annual_gain / 12
                if monthly_gain > 0:
                    payback_period_months = vendor_cost / monthly_gain
            
            response = ROICalculationResponse(
                break_even_ggr_growth=break_even_ggr_growth,
                break_even_bonus_reduction=break_even_bonus_reduction,
                net_annual_gain=net_annual_gain,
                roi_percentage=roi_percentage,
                is_profitable=is_profitable,
                payback_period_months=payback_period_months
            )
            
            logger.info(f"ROI calculation completed: ROI={roi_percentage:.2f}%, Profitable={is_profitable}")
            return response
            
        except Exception as e:
            logger.error(f"Error calculating ROI: {e}")
            raise
    
    def _calculate_break_even_ggr_growth(
        self,
        vendor_cost: float,
        annual_ggr: float
    ) -> float:
        """
        Calculate break-even GGR growth percentage.
        
        Formula: (vendor_cost / annual_ggr) * 100
        
        Args:
            vendor_cost: Vendor/implementation cost
            annual_ggr: Annual Gross Gaming Revenue
            
        Returns:
            float: Break-even GGR growth percentage
        """
        if annual_ggr <= 0:
            return 0.0
        
        return (vendor_cost / annual_ggr) * 100
    
    def _calculate_break_even_bonus_reduction(
        self,
        vendor_cost: float,
        annual_bonus_emission: float
    ) -> float:
        """
        Calculate break-even bonus reduction percentage.
        
        Formula: (vendor_cost / annual_bonus_emission) * 100
        
        Args:
            vendor_cost: Vendor/implementation cost
            annual_bonus_emission: Annual bonus emission amount
            
        Returns:
            float: Break-even bonus reduction percentage
        """
        if annual_bonus_emission <= 0:
            return 0.0
        
        return (vendor_cost / annual_bonus_emission) * 100
    
    def _calculate_net_annual_gain(
        self,
        annual_ggr: float,
        target_uplift_percent: float,
        vendor_cost: float
    ) -> float:
        """
        Calculate net annual gain after costs.
        
        Formula: (annual_ggr * (target_uplift_percent / 100)) - vendor_cost
        
        Args:
            annual_ggr: Annual Gross Gaming Revenue
            target_uplift_percent: Target percentage uplift in GGR
            vendor_cost: Vendor/implementation cost
            
        Returns:
            float: Net annual gain
        """
        uplift_amount = annual_ggr * (target_uplift_percent / 100)
        return uplift_amount - vendor_cost
    
    def _calculate_roi_percentage(
        self,
        net_annual_gain: float,
        vendor_cost: float
    ) -> float:
        """
        Calculate ROI percentage.
        
        Formula: (net_annual_gain / vendor_cost) * 100
        
        Args:
            net_annual_gain: Net annual gain after costs
            vendor_cost: Vendor/implementation cost
            
        Returns:
            float: ROI percentage
        """
        if vendor_cost <= 0:
            return 0.0
        
        return (net_annual_gain / vendor_cost) * 100
    
    def calculate_investment_scenarios(
        self,
        annual_ggr: float,
        annual_bonus_emission: float,
        vendor_cost: float
    ) -> dict:
        """
        Calculate multiple investment scenarios for comparison.
        
        Args:
            annual_ggr: Annual Gross Gaming Revenue
            annual_bonus_emission: Annual bonus emission amount
            vendor_cost: Vendor/implementation cost
            
        Returns:
            dict: Multiple ROI scenarios
        """
        scenarios = {}
        
        # Calculate scenarios for different uplift percentages
        uplift_percentages = [3.0, 5.0, 7.5, 10.0, 15.0]
        
        for uplift in uplift_percentages:
            scenario = self.calculate_roi(
                annual_ggr=annual_ggr,
                annual_bonus_emission=annual_bonus_emission,
                vendor_cost=vendor_cost,
                target_uplift_percent=uplift
            )
            scenarios[f"{uplift}%_uplift"] = {
                "break_even_ggr_growth": scenario.break_even_ggr_growth,
                "break_even_bonus_reduction": scenario.break_even_bonus_reduction,
                "net_annual_gain": scenario.net_annual_gain,
                "roi_percentage": scenario.roi_percentage,
                "is_profitable": scenario.is_profitable,
                "payback_period_months": scenario.payback_period_months
            }
        
        logger.info(f"Generated {len(scenarios)} investment scenarios")
        return scenarios


# Singleton instance
roi_calculator = ROICalculator()
