# RetentionOps API

A production-ready, fully asynchronous FastAPI backend service for analyzing iGaming retention mechanics. This service provides AI-powered screenshot analysis, competitor gap analysis, ROI calculations, and executive PDF reporting for B2B SaaS platforms in the iGaming industry.

## Features

- **AI-Powered Vision Analysis**: Uses OpenAI GPT-4o-mini Vision to analyze screenshots and extract retention mechanic metadata
- **Maturity Level Calculation**: Automated assessment of retention mechanic maturity (0-3 scale)
- **Anomaly Detection**: Tier 1 and Tier 2 red flag detection for UX issues and unfair practices
- **Competitor Analysis**: Gap matrix analysis comparing your brand against competitors
- **ROI Calculator**: Financial analysis for retention investments with break-even calculations
- **PDF Reports**: Executive summary reports with canvas, gap analysis, and ROI metrics
- **Secure API**: API key authentication for Chrome extension and web frontend integration
- **Fully Async**: Built with FastAPI and async/await for optimal performance

## Tech Stack

- **Python 3.11+**
- **FastAPI** with Pydantic v2 for API and data validation
- **Uvicorn** as ASGI server
- **OpenAI API** (GPT-4o-mini) for Vision and text analysis
- **Supabase** for PostgreSQL database integration
- **Jinja2 & WeasyPrint** for PDF generation
- **Docker** for containerized deployment

## Project Structure

```
retentionops-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI entry point, CORS, Middlewares
│   ├── config.py                   # Pydantic BaseSettings (.env loading)
│   ├── core/
│   │   ├── security.py             # API Key validation middleware
│   │   └── database.py             # Supabase client initialization
│   ├── models/                     # Pydantic request/response schemas
│   │   ├── capture.py
│   │   ├── competitor.py
│   │   ├── analytics.py
│   │   └── report.py
│   ├── services/                   # Business logic
│   │   ├── vision_agent.py         # OpenAI GPT-4o-mini screenshot analysis
│   │   ├── rule_engine.py          # Maturity levels & Anomaly detection
│   │   ├── roi_calculator.py       # Financial threshold math
│   │   └── pdf_generator.py        # Executive PDF summary exporter
│   ├── routers/                    # API Endpoints
│   │   ├── capture.py              # /api/v1/capture (From Chrome Extension)
│   │   ├── competitors.py          # /api/v1/competitors (CRUD & Gap matrix)
│   │   ├── analytics.py            # /api/v1/analytics (Canvas & ROI math)
│   │   └── reports.py              # /api/v1/reports/pdf (PDF exporter)
│   └── templates/                  # Jinja2 templates for PDF generation
├── tests/
│   ├── __init__.py
│   └── test_api.py                 # Pytest test suites
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized deployment)
- Supabase account and project
- OpenAI API key

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd retentionops-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration values
   ```

5. **Set up Supabase database tables**
   
   Create the following tables in your Supabase project:
   
   ```sql
   -- Mechanic audits table
   CREATE TABLE mechanic_audits (
       id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
       brand_name VARCHAR(255) NOT NULL,
       scenario VARCHAR(255) NOT NULL,
       mechanic_id INTEGER NOT NULL,
       mechanic_name VARCHAR(255) NOT NULL,
       screenshot_url TEXT NOT NULL,
       page_url TEXT NOT NULL,
       metadata JSONB NOT NULL,
       maturity_level INTEGER NOT NULL,
       ui_quality_score INTEGER NOT NULL,
       notes TEXT,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Red flags table
   CREATE TABLE red_flags (
       id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
       audit_id UUID REFERENCES mechanic_audits(id),
       flag_type VARCHAR(50) NOT NULL,
       severity VARCHAR(50) NOT NULL,
       description TEXT NOT NULL,
       recommended_action TEXT NOT NULL,
       mechanic_id INTEGER,
       is_resolved BOOLEAN DEFAULT FALSE,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Competitors table
   CREATE TABLE competitors (
       id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
       name VARCHAR(255) NOT NULL,
       website TEXT NOT NULL,
       notes TEXT,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Mechanic maturity table
   CREATE TABLE mechanic_maturity (
       id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
       brand_name VARCHAR(255) NOT NULL,
       mechanic_id INTEGER NOT NULL,
       mechanic_name VARCHAR(255) NOT NULL,
       maturity_level INTEGER NOT NULL,
       last_audited TIMESTAMP WITH TIME ZONE,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       UNIQUE(brand_name, mechanic_id)
   );
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t retentionops-api .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     -p 8000:8000 \
     --env-file .env \
     --name retentionops-api \
     retentionops-api
   ```

3. **Or use Docker Compose**
   ```bash
   docker-compose up -d
   ```

## API Documentation

Once the server is running, access the interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs` (debug mode only)
- **ReDoc**: `http://localhost:8000/redoc` (debug mode only)

### Authentication

All API endpoints require authentication via API key. Include one of the following headers:

- `X-API-Key: your_api_token`
- `Authorization: Bearer your_api_token`

### Core Endpoints

#### Health Check
```http
GET /health
```

#### Capture Analysis (Chrome Extension)
```http
POST /api/v1/capture
Content-Type: application/json
X-API-Key: your_api_token

{
  "brand_name": "Brand Name",
  "scenario": "Registration / Onboarding",
  "selected_mechanic_id": 1,
  "selected_mechanic_name": "Wheel of Fortune",
  "screenshot_base64": "data:image/jpeg;base64,...",
  "sanitized_dom_text": "DOM text content",
  "page_url": "https://example.com",
  "notes": "Optional notes"
}
```

#### Competitors Management
```http
GET /api/v1/competitors
POST /api/v1/competitors
DELETE /api/v1/competitors/{id}
GET /api/v1/competitors/gap-matrix?competitor_id={id}
```

#### Analytics
```http
GET /api/v1/analytics/canvas
POST /api/v1/analytics/calculate-roi
GET /api/v1/analytics/red-flags
GET /api/v1/analytics/investment-scenarios
```

#### Reports
```http
POST /api/v1/reports/pdf
Content-Type: application/json
X-API-Key: your_api_token

{
  "brand_name": "Brand Name",
  "include_canvas_summary": true,
  "include_gap_analysis": true,
  "include_roi_analysis": true,
  "include_red_flags": true,
  "top_red_flags_count": 3
}
```

## Retention Mechanics

The system analyzes 26 key retention mechanics:

1. Wheel of Fortune
2. Daily Streak Bonus
3. Lootbox
4. Daily Claimer
5. Achievement System
6. Leaderboard
7. VIP Program
8. Referral Program
9. Tournament
10. Cashback
11. Free Spins
12. Deposit Bonus
13. No Deposit Bonus
14. Loyalty Points
15. Level System
16. Mission System
17. Season Pass
18. Challenge System
19. Bonus Shop
20. Prize Drops
21. Live Events
22. Social Features
23. Personalization
24. Gamification
25. Responsible Gaming
26. Anti-Fraud

## Maturity Levels

- **0 (None)**: Mechanic not implemented
- **1 (Primitive)**: Basic implementation with core functionality
- **2 (Expanded)**: Enhanced features and better UX
- **3 (Finalized)**: Complete implementation with advanced features

## Red Flag Detection

### Tier 1 Flags (Critical)
- Excessive wagering requirements (>50x)
- Hard streak reset without recovery path
- Missing pity system in lootboxes
- Unfair minimum deposit requirements

### Tier 2 Flags (Important)
- Poor UI design quality
- Missing expiration information
- Unclear reward specifications
- Limited payment options

## ROI Calculation Formulas

- **Break-even GGR Growth**: `(vendor_cost / annual_ggr) * 100`
- **Break-even Bonus Reduction**: `(vendor_cost / annual_bonus_emission) * 100`
- **Net Annual Gain**: `(annual_ggr * (target_uplift_percent / 100)) - vendor_cost`
- **ROI Percentage**: `(net_annual_gain / vendor_cost) * 100`

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/test_api.py -v

# Run specific test class
pytest tests/test_api.py::TestROICalculation -v

# Run with coverage
pytest tests/test_api.py --cov=app --cov-report=html
```

## Development

### Code Style

The project follows Python best practices with:
- Type hints for better code clarity
- Async/await for I/O operations
- Comprehensive error handling
- Detailed logging

### Adding New Mechanics

To add a new retention mechanic:

1. Update the mechanic name mapping in `app/routers/analytics.py`
2. Add specific rules in `app/services/rule_engine.py`
3. Update the maturity indicators in the rule engine
4. Add tests for the new mechanic

### Database Migrations

For database schema changes:
1. Create a migration script
2. Test in development environment
3. Apply to production during maintenance window
4. Update the README with new schema

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase anon key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `API_AUTH_TOKEN` | API authentication token | Yes |
| `DEBUG` | Enable debug mode | No |
| `ALLOWED_ORIGINS` | CORS allowed origins | No |

### OpenAI Settings

- `OPENAI_MODEL`: Default is `gpt-4o-mini`
- `OPENAI_MAX_TOKENS`: Default is `1000`
- `OPENAI_TEMPERATURE`: Default is `0.3`

## Deployment

### Production Considerations

1. **Security**: 
   - Use strong API tokens
   - Enable HTTPS
   - Implement rate limiting
   - Keep dependencies updated

2. **Performance**:
   - Use caching for frequently accessed data
   - Implement connection pooling
   - Monitor API response times
   - Set up proper logging

3. **Monitoring**:
   - Set up health checks
   - Monitor error rates
   - Track API usage metrics
   - Set up alerts for critical issues

4. **Database**:
   - Use connection pooling
   - Implement proper indexing
   - Set up regular backups
   - Monitor query performance

## Troubleshooting

### Common Issues

**CORS Errors**: Ensure your frontend URL is in `ALLOWED_ORIGINS`

**Database Connection**: Verify Supabase credentials and network connectivity

**OpenAI API Errors**: Check API key quota and rate limits

**PDF Generation Issues**: Ensure WeasyPrint system dependencies are installed

### Logging

Logs are configured to output to console with different levels:
- `INFO`: Normal operations
- `WARNING`: Potential issues
- `ERROR`: Failed operations
- `DEBUG`: Detailed information (debug mode only)

## License

Proprietary - All rights reserved

## Support

For support and issues, please contact the development team.

## Changelog

### Version 1.0.0
- Initial release
- Core API endpoints
- AI vision analysis
- ROI calculator
- PDF generation
- Competitor analysis
- Red flag detection
