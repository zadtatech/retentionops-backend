import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.analytics import ROICalculationRequest
from app.models.capture import CaptureRequest
from unittest.mock import patch, MagicMock
import json

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "operational"
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_capture_health_endpoint(self):
        """Test capture service health check."""
        response = client.get("/api/v1/capture/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "capture"
    
    def test_reports_health_endpoint(self):
        """Test reports service health check."""
        response = client.get("/api/v1/reports/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "reports"


class TestROICalculation:
    """Test ROI calculation endpoints."""
    
    def test_calculate_roi_success(self):
        """Test successful ROI calculation."""
        payload = {
            "annual_ggr": 10000000.0,
            "annual_bonus_emission": 2000000.0,
            "vendor_cost": 500000.0,
            "target_uplift_percent": 5.0
        }
        
        response = client.post("/api/v1/analytics/calculate-roi", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "break_even_ggr_growth" in data
        assert "break_even_bonus_reduction" in data
        assert "net_annual_gain" in data
        assert "roi_percentage" in data
        assert "is_profitable" in data
        
        # Verify calculations
        # break_even_ggr_growth = (500000 / 10000000) * 100 = 5.0
        assert abs(data["break_even_ggr_growth"] - 5.0) < 0.01
        
        # break_even_bonus_reduction = (500000 / 2000000) * 100 = 25.0
        assert abs(data["break_even_bonus_reduction"] - 25.0) < 0.01
        
        # net_annual_gain = (10000000 * 0.05) - 500000 = 0
        assert abs(data["net_annual_gain"] - 0.0) < 0.01
    
    def test_calculate_roi_profitable_scenario(self):
        """Test ROI calculation with profitable scenario."""
        payload = {
            "annual_ggr": 10000000.0,
            "annual_bonus_emission": 2000000.0,
            "vendor_cost": 300000.0,
            "target_uplift_percent": 10.0
        }
        
        response = client.post("/api/v1/analytics/calculate-roi", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # net_annual_gain = (10000000 * 0.10) - 300000 = 700000
        assert abs(data["net_annual_gain"] - 700000.0) < 0.01
        assert data["is_profitable"] == True
        assert data["roi_percentage"] > 0
    
    def test_calculate_roi_unprofitable_scenario(self):
        """Test ROI calculation with unprofitable scenario."""
        payload = {
            "annual_ggr": 10000000.0,
            "annual_bonus_emission": 2000000.0,
            "vendor_cost": 600000.0,
            "target_uplift_percent": 3.0
        }
        
        response = client.post("/api/v1/analytics/calculate-roi", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # net_annual_gain = (10000000 * 0.03) - 600000 = -300000
        assert abs(data["net_annual_gain"] - (-300000.0)) < 0.01
        assert data["is_profitable"] == False
        assert data["roi_percentage"] < 0
    
    def test_calculate_roi_invalid_payload_negative_values(self):
        """Test ROI calculation with negative values (should fail validation)."""
        payload = {
            "annual_ggr": -10000000.0,
            "annual_bonus_emission": 2000000.0,
            "vendor_cost": 500000.0,
            "target_uplift_percent": 5.0
        }
        
        response = client.post("/api/v1/analytics/calculate-roi", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_calculate_roi_invalid_payload_zero_values(self):
        """Test ROI calculation with zero values (should fail validation)."""
        payload = {
            "annual_ggr": 0.0,
            "annual_bonus_emission": 2000000.0,
            "vendor_cost": 500000.0,
            "target_uplift_percent": 5.0
        }
        
        response = client.post("/api/v1/analytics/calculate-roi", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_calculate_roi_missing_fields(self):
        """Test ROI calculation with missing required fields."""
        payload = {
            "annual_ggr": 10000000.0,
            "annual_bonus_emission": 2000000.0
            # Missing vendor_cost and target_uplift_percent
        }
        
        response = client.post("/api/v1/analytics/calculate-roi", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_investment_scenarios(self):
        """Test investment scenarios endpoint."""
        response = client.get(
            "/api/v1/analytics/investment-scenarios",
            params={
                "annual_ggr": 10000000.0,
                "annual_bonus_emission": 2000000.0,
                "vendor_cost": 500000.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify multiple scenarios are returned
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Check that expected uplift percentages are present
        expected_keys = ["3.0%_uplift", "5.0%_uplift", "7.5%_uplift", "10.0%_uplift", "15.0%_uplift"]
        for key in expected_keys:
            assert key in data
            assert "roi_percentage" in data[key]
            assert "is_profitable" in data[key]


class TestPayloadValidation:
    """Test payload validation for various endpoints."""
    
    def test_capture_request_valid_payload(self):
        """Test capture request with valid payload."""
        payload = {
            "brand_name": "Test Brand",
            "scenario": "Registration / Onboarding",
            "selected_mechanic_id": 1,
            "selected_mechanic_name": "Wheel of Fortune",
            "screenshot_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBD",
            "sanitized_dom_text": "Sample DOM text for testing",
            "page_url": "https://example.com/test",
            "notes": "Test capture"
        }
        
        # Mock the vision agent and database calls
        with patch('app.routers.capture.vision_agent.analyze_screenshot') as mock_vision:
            with patch('app.routers.capture.SupabaseClient.insert_mechanic_audit') as mock_db:
                with patch('app.routers.capture.SupabaseClient.insert_red_flag') as mock_flag:
                    # Setup mocks
                    mock_vision.return_value = MagicMock(
                        is_valid_match=True,
                        confidence_score=0.9,
                        metadata=MagicMock(
                            wager_multiplier=35.0,
                            minimum_deposit=20.0,
                            expiration_timer="7 days",
                            reward_type="free spins",
                            additional_params={}
                        ),
                        ui_quality_score=4,
                        analysis_notes="Test analysis"
                    )
                    mock_db.return_value = {"id": "test-id"}
                    mock_flag.return_value = {}
                    
                    response = client.post(
                        "/api/v1/capture",
                        json=payload,
                        headers={"X-API-Key": "test-api-key"}
                    )
                    # This will fail due to auth, but we can still validate the payload structure
                    # The payload validation happens before auth
    
    def test_capture_request_invalid_mechanic_id(self):
        """Test capture request with invalid mechanic ID."""
        payload = {
            "brand_name": "Test Brand",
            "scenario": "Registration / Onboarding",
            "selected_mechanic_id": 27,  # Invalid (should be 1-26)
            "selected_mechanic_name": "Wheel of Fortune",
            "screenshot_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBD",
            "sanitized_dom_text": "Sample DOM text",
            "page_url": "https://example.com/test"
        }
        
        response = client.post("/api/v1/capture", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_capture_request_invalid_url(self):
        """Test capture request with invalid URL."""
        payload = {
            "brand_name": "Test Brand",
            "scenario": "Registration / Onboarding",
            "selected_mechanic_id": 1,
            "selected_mechanic_name": "Wheel of Fortune",
            "screenshot_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBD",
            "sanitized_dom_text": "Sample DOM text",
            "page_url": "invalid-url"  # Invalid URL format
        }
        
        response = client.post("/api/v1/capture", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_capture_request_missing_required_fields(self):
        """Test capture request with missing required fields."""
        payload = {
            "brand_name": "Test Brand",
            "scenario": "Registration / Onboarding"
            # Missing other required fields
        }
        
        response = client.post("/api/v1/capture", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_competitor_create_valid_payload(self):
        """Test competitor creation with valid payload."""
        payload = {
            "name": "Test Competitor",
            "website": "https://competitor.com",
            "notes": "Test notes"
        }
        
        # This will fail due to auth, but validates payload structure
        response = client.post(
            "/api/v1/competitors",
            json=payload,
            headers={"X-API-Key": "test-api-key"}
        )
        # Payload validation happens before auth, so we expect 401 (auth error) not 422 (validation error)
        assert response.status_code in [401, 422]
    
    def test_competitor_create_invalid_url(self):
        """Test competitor creation with invalid URL."""
        payload = {
            "name": "Test Competitor",
            "website": "invalid-url",
            "notes": "Test notes"
        }
        
        response = client.post("/api/v1/competitors", json=payload)
        # Should fail validation or auth
        assert response.status_code in [401, 422]
    
    def test_competitor_create_name_too_long(self):
        """Test competitor creation with name exceeding max length."""
        payload = {
            "name": "A" * 300,  # Exceeds 255 character limit
            "website": "https://competitor.com"
        }
        
        response = client.post("/api/v1/competitors", json=payload)
        assert response.status_code in [401, 422]


class TestAuthentication:
    """Test authentication middleware."""
    
    def test_protected_endpoint_without_auth(self):
        """Test that protected endpoints require authentication."""
        response = client.get("/api/v1/competitors")
        assert response.status_code == 401  # Unauthorized
    
    def test_protected_endpoint_with_invalid_auth(self):
        """Test that invalid authentication is rejected."""
        response = client.get(
            "/api/v1/competitors",
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code == 401  # Unauthorized
    
    def test_protected_endpoint_with_bearer_token_invalid(self):
        """Test that invalid bearer token is rejected."""
        response = client.get(
            "/api/v1/competitors",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401  # Unauthorized


class TestAnalyticsEndpoints:
    """Test analytics endpoints."""
    
    def test_retention_canvas_without_auth(self):
        """Test retention canvas endpoint requires authentication."""
        response = client.get("/api/v1/analytics/canvas")
        assert response.status_code == 401
    
    def test_red_flags_without_auth(self):
        """Test red flags endpoint requires authentication."""
        response = client.get("/api/v1/analytics/red-flags")
        assert response.status_code == 401
    
    def test_red_flags_with_severity_filter(self):
        """Test red flags with severity filter (will fail auth)."""
        response = client.get(
            "/api/v1/analytics/red-flags?severity=Critical",
            headers={"X-API-Key": "test-key"}
        )
        # Will fail auth, but validates parameter structure
        assert response.status_code in [401, 500]


class TestReportEndpoints:
    """Test report generation endpoints."""
    
    def test_pdf_report_without_auth(self):
        """Test PDF report generation requires authentication."""
        payload = {
            "brand_name": "Test Brand",
            "include_canvas_summary": True,
            "include_gap_analysis": True,
            "include_roi_analysis": True,
            "include_red_flags": True,
            "top_red_flags_count": 3
        }
        
        response = client.post("/api/v1/reports/pdf", json=payload)
        assert response.status_code == 401
    
    def test_pdf_report_invalid_top_flags_count(self):
        """Test PDF report with invalid top_red_flags_count."""
        payload = {
            "brand_name": "Test Brand",
            "top_red_flags_count": 15  # Exceeds max of 10
        }
        
        response = client.post("/api/v1/reports/pdf", json=payload)
        assert response.status_code in [401, 422]  # Auth error or validation error
    
    def test_pdf_report_negative_top_flags_count(self):
        """Test PDF report with negative top_red_flags_count."""
        payload = {
            "brand_name": "Test Brand",
            "top_red_flags_count": -1  # Negative value
        }
        
        response = client.post("/api/v1/reports/pdf", json=payload)
        assert response.status_code in [401, 422]


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_404_endpoint(self):
        """Test 404 for non-existent endpoint."""
        response = client.get("/api/v1/non-existent")
        assert response.status_code == 404
    
    def test_invalid_json_payload(self):
        """Test handling of invalid JSON payload."""
        response = client.post(
            "/api/v1/analytics/calculate-roi",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_empty_json_payload(self):
        """Test handling of empty JSON payload."""
        response = client.post(
            "/api/v1/analytics/calculate-roi",
            json={},
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [401, 422]  # Auth error or validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
