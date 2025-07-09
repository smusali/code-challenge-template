"""
Documentation and API information endpoints.

Provides dynamic documentation endpoints including:
- API schema information
- Endpoint discovery
- Example requests and responses
- Integration guides
- Status information
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from src.docs.openapi_config import get_openapi_config, get_openapi_tags
from src.docs.swagger_ui import get_custom_swagger_ui_html, get_redoc_html

logger = logging.getLogger(__name__)

router = APIRouter()


class APIInfo(BaseModel):
    """API information model."""

    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="API description")
    docs_url: str = Field(..., description="Swagger UI documentation URL")
    redoc_url: str = Field(..., description="ReDoc documentation URL")
    openapi_url: str = Field(..., description="OpenAPI schema URL")
    contact: dict[str, str] | None = Field(None, description="Contact information")
    license: dict[str, str] | None = Field(None, description="License information")
    servers: list[dict[str, str]] = Field(
        default_factory=list, description="Server information"
    )
    tags: list[dict[str, Any]] = Field(default_factory=list, description="API tags")
    endpoints_count: int = Field(..., description="Total number of endpoints")
    last_updated: str = Field(..., description="Last update timestamp")


class EndpointInfo(BaseModel):
    """Endpoint information model."""

    path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP method")
    summary: str | None = Field(None, description="Endpoint summary")
    description: str | None = Field(None, description="Endpoint description")
    tags: list[str] = Field(default_factory=list, description="Endpoint tags")
    parameters: list[dict[str, Any]] = Field(
        default_factory=list, description="Endpoint parameters"
    )
    responses: dict[str, Any] = Field(
        default_factory=dict, description="Endpoint responses"
    )
    deprecated: bool = Field(False, description="Whether endpoint is deprecated")
    security: list[dict[str, Any]] = Field(
        default_factory=list, description="Security requirements"
    )


class ExampleRequest(BaseModel):
    """Example request model."""

    title: str = Field(..., description="Example title")
    description: str = Field(..., description="Example description")
    method: str = Field(..., description="HTTP method")
    url: str = Field(..., description="Request URL")
    headers: dict[str, str] | None = Field(None, description="Request headers")
    query_params: dict[str, Any] | None = Field(None, description="Query parameters")
    body: dict[str, Any] | None = Field(None, description="Request body")
    curl_example: str = Field(..., description="cURL command example")


class ExampleResponse(BaseModel):
    """Example response model."""

    status_code: int = Field(..., description="HTTP status code")
    headers: dict[str, str] = Field(
        default_factory=dict, description="Response headers"
    )
    body: dict[str, Any] = Field(default_factory=dict, description="Response body")


class IntegrationGuide(BaseModel):
    """Integration guide model."""

    title: str = Field(..., description="Guide title")
    description: str = Field(..., description="Guide description")
    language: str = Field(..., description="Programming language")
    code_example: str = Field(..., description="Code example")
    prerequisites: list[str] = Field(default_factory=list, description="Prerequisites")
    steps: list[str] = Field(default_factory=list, description="Integration steps")


@router.get("/", response_model=APIInfo)
async def get_api_info(request: Request) -> APIInfo:
    """
    Get comprehensive API information.

    Returns detailed information about the API including:
    - Basic API metadata
    - Documentation URLs
    - Available endpoints count
    - Contact and license information
    - Server information
    - API tags and organization
    """
    try:
        config = get_openapi_config()
        tags = get_openapi_tags()

        # Get base URL from request
        base_url = str(request.base_url).rstrip("/")

        # Count endpoints (this is a simple approximation)
        from src.main import app

        endpoints_count = len(
            [route for route in app.routes if hasattr(route, "methods")]
        )

        return APIInfo(
            name=config["title"],
            version=config["version"],
            description=config["description"],
            docs_url=f"{base_url}/docs",
            redoc_url=f"{base_url}/redoc",
            openapi_url=f"{base_url}/openapi.json",
            contact=config.get("contact"),
            license=config.get("license"),
            servers=config.get("servers", []),
            tags=tags,
            endpoints_count=endpoints_count,
            last_updated=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Error getting API info: {e}")
        # Return basic info if detailed info fails
        return APIInfo(
            name="Weather Data Engineering API",
            version="1.0.0",
            description="A comprehensive API for weather data management and analysis",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
            endpoints_count=0,
            last_updated=datetime.now().isoformat(),
        )


@router.get("/endpoints", response_model=list[EndpointInfo])
async def get_endpoints_info() -> list[EndpointInfo]:
    """
    Get detailed information about all API endpoints.

    Returns a list of all endpoints with their:
    - Path and HTTP method
    - Summary and description
    - Parameters and responses
    - Tags and security requirements
    - Deprecation status
    """
    try:
        from src.main import app

        endpoints = []

        # Extract endpoint information from FastAPI routes
        for route in app.routes:
            if hasattr(route, "methods") and hasattr(route, "path"):
                for method in route.methods:
                    if method.upper() not in ["HEAD", "OPTIONS"]:
                        endpoint_info = EndpointInfo(
                            path=route.path,
                            method=method.upper(),
                            summary=getattr(route, "summary", None),
                            description=getattr(route, "description", None),
                            tags=getattr(route, "tags", []),
                            deprecated=getattr(route, "deprecated", False),
                        )
                        endpoints.append(endpoint_info)

        return endpoints

    except Exception as e:
        logger.error(f"Error getting endpoints info: {e}")
        return []


@router.get("/examples", response_model=list[ExampleRequest])
async def get_api_examples(request: Request) -> list[ExampleRequest]:
    """
    Get comprehensive API usage examples.

    Returns examples for common API operations including:
    - Basic weather data queries
    - Advanced filtering and pagination
    - Sorting and search operations
    - Error handling scenarios
    """
    base_url = str(request.base_url).rstrip("/")

    examples = [
        ExampleRequest(
            title="Get Weather Stations",
            description="Retrieve a list of weather stations with basic pagination",
            method="GET",
            url=f"{base_url}/api/v2/weather-stations",
            query_params={
                "page": 1,
                "page_size": 20,
                "sort_by": "name",
                "sort_order": "asc",
            },
            curl_example=f'curl -X GET "{base_url}/api/v2/weather-stations?page=1&page_size=20&sort_by=name&sort_order=asc"',
        ),
        ExampleRequest(
            title="Advanced Weather Data Filtering",
            description="Query daily weather data with multiple filters",
            method="GET",
            url=f"{base_url}/api/v2/daily-weather",
            query_params={
                "start_date": "2010-01-01",
                "end_date": "2010-12-31",
                "states": ["IL", "IA"],
                "min_temp": -10,
                "max_temp": 40,
                "has_temperature": True,
                "sort_by": "date",
                "sort_order": "desc",
                "page": 1,
                "page_size": 50,
            },
            curl_example=f'curl -X GET "{base_url}/api/v2/daily-weather?start_date=2010-01-01&end_date=2010-12-31&states=IL&states=IA&min_temp=-10&max_temp=40&has_temperature=true&sort_by=date&sort_order=desc&page=1&page_size=50"',
        ),
        ExampleRequest(
            title="Search Weather Stations",
            description="Search weather stations by name or ID",
            method="GET",
            url=f"{base_url}/api/v2/weather-stations",
            query_params={
                "search": "Chicago",
                "states": ["IL"],
                "has_recent_data": True,
                "sort_by": "name",
            },
            curl_example=f'curl -X GET "{base_url}/api/v2/weather-stations?search=Chicago&states=IL&has_recent_data=true&sort_by=name"',
        ),
        ExampleRequest(
            title="Get Yearly Statistics",
            description="Retrieve yearly weather statistics with filtering",
            method="GET",
            url=f"{base_url}/api/v2/yearly-stats",
            query_params={
                "start_year": 2000,
                "end_year": 2010,
                "states": ["IL", "IA", "IN"],
                "min_avg_temp": 0,
                "min_data_completeness": 80,
                "sort_by": "year",
                "sort_order": "desc",
            },
            curl_example=f'curl -X GET "{base_url}/api/v2/yearly-stats?start_year=2000&end_year=2010&states=IL&states=IA&states=IN&min_avg_temp=0&min_data_completeness=80&sort_by=year&sort_order=desc"',
        ),
        ExampleRequest(
            title="Health Check",
            description="Check API health and status",
            method="GET",
            url=f"{base_url}/health",
            curl_example=f'curl -X GET "{base_url}/health"',
        ),
        ExampleRequest(
            title="Get Sort Information",
            description="Get available sort fields for a model type",
            method="GET",
            url=f"{base_url}/api/v2/sort-info/daily_weather",
            curl_example=f'curl -X GET "{base_url}/api/v2/sort-info/daily_weather"',
        ),
        ExampleRequest(
            title="Get Filter Information",
            description="Get comprehensive filter documentation",
            method="GET",
            url=f"{base_url}/api/v2/filter-info",
            curl_example=f'curl -X GET "{base_url}/api/v2/filter-info"',
        ),
    ]

    return examples


@router.get("/integration-guides", response_model=list[IntegrationGuide])
async def get_integration_guides() -> list[IntegrationGuide]:
    """
    Get integration guides for different programming languages.

    Returns code examples and guides for:
    - Python integration
    - JavaScript/Node.js integration
    - cURL examples
    - API client libraries
    """
    guides = [
        IntegrationGuide(
            title="Python Integration",
            description="How to integrate with the Weather API using Python",
            language="python",
            code_example="""
import requests
import pandas as pd
from datetime import datetime, timedelta

class WeatherAPIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def get_weather_stations(self, states=None, search=None, page=1, page_size=20):
        \"\"\"Get weather stations with optional filtering.\"\"\"
        params = {
            'page': page,
            'page_size': page_size
        }

        if states:
            for state in states:
                params[f'states'] = state

        if search:
            params['search'] = search

        response = self.session.get(
            f"{self.base_url}/api/v2/weather-stations",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_daily_weather(self, start_date, end_date, states=None,
                         min_temp=None, max_temp=None, page=1, page_size=100):
        \"\"\"Get daily weather data with filtering.\"\"\"
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'page': page,
            'page_size': page_size
        }

        if states:
            for state in states:
                params['states'] = state

        if min_temp is not None:
            params['min_temp'] = min_temp

        if max_temp is not None:
            params['max_temp'] = max_temp

        response = self.session.get(
            f"{self.base_url}/api/v2/daily-weather",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_weather_dataframe(self, start_date, end_date, states=None):
        \"\"\"Get weather data as a pandas DataFrame.\"\"\"
        all_data = []
        page = 1

        while True:
            result = self.get_daily_weather(
                start_date, end_date, states, page=page, page_size=100
            )

            all_data.extend(result['items'])

            if not result['pagination']['has_next']:
                break

            page += 1

        return pd.DataFrame(all_data)

# Usage example
client = WeatherAPIClient()

# Get weather stations in Illinois
stations = client.get_weather_stations(states=['IL'], search='Chicago')
print(f"Found {len(stations['items'])} stations")

# Get weather data for 2010
start_date = datetime(2010, 1, 1)
end_date = datetime(2010, 12, 31)
weather_df = client.get_weather_dataframe(start_date, end_date, states=['IL'])
print(f"Retrieved {len(weather_df)} weather records")
print(weather_df.head())
            """,
            prerequisites=[
                "Python 3.7+",
                "requests library (pip install requests)",
                "pandas library (pip install pandas)",
            ],
            steps=[
                "Install required dependencies",
                "Create a WeatherAPIClient instance",
                "Use the client methods to query data",
                "Handle pagination for large datasets",
                "Convert results to pandas DataFrame for analysis",
            ],
        ),
        IntegrationGuide(
            title="JavaScript Integration",
            description="How to integrate with the Weather API using JavaScript/Node.js",
            language="javascript",
            code_example="""
class WeatherAPIClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, params = {}) {
        const url = new URL(`${this.baseUrl}${endpoint}`);

        // Add query parameters
        Object.entries(params).forEach(([key, value]) => {
            if (Array.isArray(value)) {
                value.forEach(v => url.searchParams.append(key, v));
            } else if (value !== undefined && value !== null) {
                url.searchParams.append(key, value);
            }
        });

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    }

    async getWeatherStations(options = {}) {
        const { states, search, page = 1, pageSize = 20 } = options;

        return this.request('/api/v2/weather-stations', {
            states,
            search,
            page,
            page_size: pageSize
        });
    }

    async getDailyWeather(options = {}) {
        const {
            startDate,
            endDate,
            states,
            minTemp,
            maxTemp,
            page = 1,
            pageSize = 100
        } = options;

        return this.request('/api/v2/daily-weather', {
            start_date: startDate,
            end_date: endDate,
            states,
            min_temp: minTemp,
            max_temp: maxTemp,
            page,
            page_size: pageSize
        });
    }

    async getAllWeatherData(options = {}) {
        const allData = [];
        let page = 1;

        while (true) {
            const result = await this.getDailyWeather({
                ...options,
                page,
                pageSize: 100
            });

            allData.push(...result.items);

            if (!result.pagination.has_next) {
                break;
            }

            page++;
        }

        return allData;
    }
}

// Usage example
const client = new WeatherAPIClient();

async function main() {
    try {
        // Get weather stations in Illinois
        const stations = await client.getWeatherStations({
            states: ['IL'],
            search: 'Chicago'
        });
        console.log(`Found ${stations.items.length} stations`);

        // Get weather data for 2010
        const weatherData = await client.getAllWeatherData({
            startDate: '2010-01-01',
            endDate: '2010-12-31',
            states: ['IL'],
            minTemp: -10,
            maxTemp: 40
        });
        console.log(`Retrieved ${weatherData.length} weather records`);

        // Calculate average temperature
        const avgTemp = weatherData
            .filter(record => record.max_temp !== null)
            .reduce((sum, record) => sum + record.max_temp, 0) / weatherData.length;
        console.log(`Average temperature: ${(avgTemp / 10).toFixed(1)}°C`);

    } catch (error) {
        console.error('Error:', error);
    }
}

main();
            """,
            prerequisites=[
                "Node.js 14+",
                "fetch API or node-fetch library",
                "Modern JavaScript environment (ES6+)",
            ],
            steps=[
                "Create a WeatherAPIClient class",
                "Implement request method with proper error handling",
                "Add methods for specific endpoints",
                "Handle pagination for large datasets",
                "Use async/await for clean asynchronous code",
            ],
        ),
        IntegrationGuide(
            title="cURL Examples",
            description="Command-line examples using cURL",
            language="bash",
            code_example="""
#!/bin/bash

# Set base URL
BASE_URL="http://localhost:8000"

# Get API information
curl -X GET "$BASE_URL/docs/api" | jq '.'

# Get weather stations with pagination
curl -X GET "$BASE_URL/api/v2/weather-stations?page=1&page_size=10" | jq '.'

# Search weather stations
curl -X GET "$BASE_URL/api/v2/weather-stations?search=Chicago&states=IL" | jq '.'

# Get daily weather data with filtering
curl -X GET "$BASE_URL/api/v2/daily-weather?start_date=2010-01-01&end_date=2010-01-31&states=IL&states=IA&min_temp=-10&max_temp=40" | jq '.'

# Get yearly statistics
curl -X GET "$BASE_URL/api/v2/yearly-stats?start_year=2000&end_year=2010&states=IL&min_avg_temp=0" | jq '.'

# Get sort information
curl -X GET "$BASE_URL/api/v2/sort-info/daily_weather" | jq '.'

# Get filter information
curl -X GET "$BASE_URL/api/v2/filter-info" | jq '.'

# Health check
curl -X GET "$BASE_URL/health" | jq '.'

# Advanced filtering with multiple parameters
curl -X GET "$BASE_URL/api/v2/daily-weather" \\
  -G \\
  -d "start_date=2010-06-01" \\
  -d "end_date=2010-08-31" \\
  -d "states=IL" \\
  -d "states=IA" \\
  -d "min_temp=20" \\
  -d "max_temp=35" \\
  -d "has_temperature=true" \\
  -d "sort_by=date" \\
  -d "sort_order=desc" \\
  -d "page=1" \\
  -d "page_size=50" | jq '.'

# Download data to file
curl -X GET "$BASE_URL/api/v2/daily-weather?start_date=2010-01-01&end_date=2010-01-31&states=IL" \\
  -o weather_data.json

# Check if request was successful
if [ $? -eq 0 ]; then
    echo "Data downloaded successfully"
    jq '.items | length' weather_data.json
else
    echo "Request failed"
fi
            """,
            prerequisites=[
                "cURL command-line tool",
                "jq for JSON parsing (optional)",
                "Basic knowledge of HTTP requests",
            ],
            steps=[
                "Install cURL and jq",
                "Set the base URL variable",
                "Use GET requests with query parameters",
                "Parse JSON responses with jq",
                "Save responses to files for analysis",
            ],
        ),
    ]

    return guides


@router.get("/status", response_model=dict[str, Any])
async def get_documentation_status() -> dict[str, Any]:
    """
    Get documentation system status.

    Returns information about:
    - Documentation availability
    - API schema validation
    - Endpoint coverage
    - Last update times
    """
    try:
        from src.main import app

        # Check if OpenAPI schema is available
        schema_available = app.openapi_schema is not None

        # Count endpoints
        total_endpoints = len(
            [route for route in app.routes if hasattr(route, "methods")]
        )

        # Check documentation URLs
        docs_urls = {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json",
            "api_info": "/docs/api",
            "examples": "/docs/api/examples",
            "integration_guides": "/docs/api/integration-guides",
        }

        return {
            "status": "healthy",
            "schema_available": schema_available,
            "total_endpoints": total_endpoints,
            "documentation_urls": docs_urls,
            "features": {
                "swagger_ui": True,
                "redoc": True,
                "custom_styling": True,
                "examples": True,
                "integration_guides": True,
                "dynamic_schema": True,
            },
            "last_updated": datetime.now().isoformat(),
            "version": "1.0.0",
        }

    except Exception as e:
        logger.error(f"Error getting documentation status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@router.get("/custom-swagger", response_class=HTMLResponse)
async def get_custom_swagger_ui(request: Request) -> HTMLResponse:
    """
    Get custom Swagger UI with enhanced styling and features.

    Returns a custom HTML response with:
    - Weather-themed styling
    - Enhanced UI features
    - Custom branding
    - Improved user experience
    """
    base_url = str(request.base_url).rstrip("/")

    return get_custom_swagger_ui_html(
        openapi_url=f"{base_url}/openapi.json",
        title="Weather Data Engineering API - Enhanced Documentation",
        oauth2_redirect_url=f"{base_url}/docs/oauth2-redirect",
    )


@router.get("/custom-redoc", response_class=HTMLResponse)
async def get_custom_redoc(request: Request) -> HTMLResponse:
    """
    Get custom ReDoc documentation with enhanced styling.

    Returns a custom HTML response with:
    - Weather-themed styling
    - Enhanced readability
    - Custom branding
    - Improved navigation
    """
    base_url = str(request.base_url).rstrip("/")

    return get_redoc_html(
        openapi_url=f"{base_url}/openapi.json",
        title="Weather Data Engineering API - ReDoc Documentation",
    )
