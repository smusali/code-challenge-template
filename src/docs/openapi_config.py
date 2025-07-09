"""
OpenAPI configuration for the Weather Data Engineering API.

Provides comprehensive OpenAPI schema configuration including:
- API metadata and contact information
- Security schemes and authentication
- Tag organization and descriptions
- Server configuration
- Response examples and schemas
"""

from typing import Any


def get_openapi_config() -> dict[str, Any]:
    """
    Get comprehensive OpenAPI configuration.

    Returns:
        OpenAPI configuration dictionary with metadata, servers, and security
    """
    return {
        "title": "Weather Data Engineering API",
        "version": "1.0.0",
        "description": """
# Weather Data Engineering API

A comprehensive data engineering solution for weather data management and analysis.

## 🌤️ Overview

This API provides comprehensive endpoints for:
- **Weather Station Management**: Station metadata and geographic information
- **Daily Weather Data**: Historical weather observations with temperature and precipitation
- **Yearly Statistics**: Pre-calculated yearly weather statistics and aggregates
- **Crop Yield Data**: Agricultural data for correlation analysis
- **Data Filtering & Pagination**: Advanced query capabilities with filtering and pagination
- **Analytics & Reporting**: Statistical analysis and data insights

## 📊 Data Coverage

- **Time Period**: 1985-2014 (30 years of historical data)
- **Geographic Coverage**: Nebraska, Iowa, Illinois, Indiana, and Ohio
- **Data Points**: Temperature, precipitation, and weather station metadata
- **Stations**: 200+ weather stations across the Midwest United States

## 🔍 Key Features

### Advanced Filtering
- **Date Range Filtering**: Filter by specific date ranges, years, or months
- **Temperature Filtering**: Filter by temperature ranges in Celsius
- **Precipitation Filtering**: Filter by precipitation ranges in millimeters
- **Geographic Filtering**: Filter by state or specific weather stations
- **Data Availability Filtering**: Filter by data completeness and availability

### Flexible Pagination
- **Page-based Pagination**: Traditional page/offset pagination
- **Cursor-based Pagination**: Efficient pagination for large datasets
- **Configurable Page Sizes**: Customizable result set sizes
- **Navigation Links**: Automatic generation of next/previous page links

### Multi-field Sorting
- **Flexible Sorting**: Sort by multiple fields with ascending/descending order
- **Context-aware Fields**: Different sort fields available for different endpoints
- **Performance Optimized**: Database-level sorting for optimal performance

### Data Quality
- **Input Validation**: Comprehensive validation using Pydantic models
- **Error Handling**: Detailed error responses with helpful messages
- **Data Integrity**: Consistent data formats and validation rules

## 🚀 Getting Started

1. **Explore the Documentation**: Use the interactive Swagger UI below
2. **Try the Examples**: Use the provided example requests
3. **Check Response Schemas**: Review the detailed response models
4. **Use Filtering**: Combine filters for specific data queries

## 📝 API Versions

- **v1**: Basic CRUD operations and simple queries
- **v2**: Enhanced endpoints with advanced filtering, pagination, and sorting

## 🔧 Technical Details

- **Framework**: FastAPI with automatic OpenAPI generation
- **Database**: PostgreSQL with Django ORM integration
- **Authentication**: API key authentication (when enabled)
- **Rate Limiting**: Request rate limiting for API stability
- **Caching**: Redis caching for improved performance

## 📖 Usage Examples

### Basic Weather Station Query
```bash
GET /api/v2/weather-stations?page=1&page_size=10
```

### Advanced Filtering
```bash
GET /api/v2/daily-weather?start_date=2010-01-01&end_date=2010-12-31&states=IL&states=IA&min_temp=-10&max_temp=40
```

### Sorting and Pagination
```bash
GET /api/v2/yearly-stats?sort_by=year&sort_order=desc&page=1&page_size=50
```

## 🛡️ Security

- **HTTPS**: All endpoints support HTTPS encryption
- **Input Validation**: Comprehensive input validation and sanitization
- **Rate Limiting**: API rate limiting to prevent abuse
- **Error Handling**: Secure error responses without sensitive information exposure

## 📞 Support

For questions, issues, or contributions:
- **Documentation**: Comprehensive API documentation with examples
- **Error Messages**: Detailed error responses with troubleshooting guidance
- **Response Codes**: Standard HTTP status codes with clear meanings
        """,
        "contact": {
            "name": "Weather Data Engineering Team",
            "email": "support@weatherapi.com",
            "url": "https://github.com/smusali/weather-data-engineering-api",
        },
        "license": {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        "servers": [
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://api.weatherdata.com", "description": "Production server"},
        ],
        "external_docs": {
            "description": "GitHub Repository",
            "url": "https://github.com/smusali/weather-data-engineering-api",
        },
    }


def get_openapi_tags() -> list[dict[str, Any]]:
    """
    Get organized API tags with descriptions.

    Returns:
        List of OpenAPI tags with names, descriptions, and external documentation
    """
    return [
        {
            "name": "Health & Status",
            "description": """
**System Health and Status Monitoring**

Endpoints for monitoring API health, system status, and diagnostic information.

**Use Cases:**
- Load balancer health checks
- System monitoring and alerting
- API status verification
- Performance monitoring
            """,
            "externalDocs": {
                "description": "Health Check Best Practices",
                "url": "https://docs.github.com/en/rest/guides/best-practices-for-integrators#dealing-with-rate-limits",
            },
        },
        {
            "name": "Weather Data",
            "description": """
**Weather Data Management (API v1)**

Core weather data operations including stations, daily observations, and basic queries.

**Features:**
- Weather station CRUD operations
- Daily weather record management
- Basic filtering and search
- Standard pagination

**Data Coverage:**
- 30 years of historical data (1985-2014)
- 200+ weather stations across Midwest US
- Temperature and precipitation observations
            """,
            "externalDocs": {
                "description": "Weather Data Documentation",
                "url": "https://github.com/smusali/weather-data-engineering-api/blob/main/docs/weather-data.md",
            },
        },
        {
            "name": "Enhanced API with Filtering & Pagination",
            "description": """
**Advanced Weather Data API (API v2)**

Enhanced endpoints with comprehensive filtering, sorting, and pagination capabilities.

**Advanced Features:**
- Multi-field filtering (date, temperature, precipitation, location)
- Flexible sorting with multiple fields
- Page-based and cursor-based pagination
- Data availability filtering
- Performance optimized queries

**Query Capabilities:**
- Complex date range queries
- Temperature and precipitation thresholds
- Geographic filtering by state or station
- Data completeness filtering
- Combined filter operations
            """,
            "externalDocs": {
                "description": "Advanced Filtering Guide",
                "url": "https://github.com/smusali/weather-data-engineering-api/blob/main/docs/filtering.md",
            },
        },
        {
            "name": "Statistics & Analytics",
            "description": """
**Weather Statistics and Analytics**

Pre-calculated statistics, aggregations, and analytical insights from weather data.

**Statistical Features:**
- Yearly weather statistics
- Temperature and precipitation aggregates
- Data completeness analysis
- Trend analysis capabilities

**Analytics Capabilities:**
- Historical trend analysis
- Statistical summaries
- Data quality metrics
- Performance statistics
            """,
            "externalDocs": {
                "description": "Statistics Documentation",
                "url": "https://github.com/smusali/weather-data-engineering-api/blob/main/docs/statistics.md",
            },
        },
        {
            "name": "Crop Data",
            "description": """
**Agricultural Crop Data**

Crop yield data for agricultural analysis and correlation with weather patterns.

**Crop Data Features:**
- Historical crop yield records
- Agricultural correlation analysis
- Yield prediction support
- Regional crop statistics

**Analysis Capabilities:**
- Weather-crop correlation analysis
- Yield trend analysis
- Regional agricultural insights
- Historical crop performance
            """,
            "externalDocs": {
                "description": "Crop Data Documentation",
                "url": "https://github.com/smusali/weather-data-engineering-api/blob/main/docs/crop-data.md",
            },
        },
        {
            "name": "Simple Weather API",
            "description": """
**Simplified Weather API**

Simplified endpoints for quick weather data access with minimal configuration.

**Simple Features:**
- Easy-to-use endpoints
- Minimal query parameters
- Quick data access
- Basic response formats

**Use Cases:**
- Quick prototyping
- Simple integrations
- Basic weather queries
- Mobile applications
            """,
            "externalDocs": {
                "description": "Simple API Guide",
                "url": "https://github.com/smusali/weather-data-engineering-api/blob/main/docs/simple-api.md",
            },
        },
    ]


def get_security_schemes() -> dict[str, Any]:
    """
    Get security schemes configuration.

    Returns:
        OpenAPI security schemes configuration
    """
    return {
        "security": [{"APIKeyAuth": []}, {"BearerAuth": []}],
        "components": {
            "securitySchemes": {
                "APIKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for authentication. Contact support to obtain an API key.",
                },
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT token authentication. Use /auth/token endpoint to obtain a token.",
                },
            }
        },
    }


def get_response_examples() -> dict[str, Any]:
    """
    Get common response examples for documentation.

    Returns:
        Common response examples for different HTTP status codes
    """
    return {
        "responses": {
            "400": {
                "description": "Bad Request",
                "content": {
                    "application/json": {
                        "example": {
                            "error": "Bad Request",
                            "message": "Invalid query parameters",
                            "details": {
                                "field": "start_date",
                                "error": "Invalid date format. Use YYYY-MM-DD",
                            },
                            "timestamp": "2024-01-01T12:00:00Z",
                        }
                    }
                },
            },
            "401": {
                "description": "Unauthorized",
                "content": {
                    "application/json": {
                        "example": {
                            "error": "Unauthorized",
                            "message": "Invalid or missing API key",
                            "timestamp": "2024-01-01T12:00:00Z",
                        }
                    }
                },
            },
            "403": {
                "description": "Forbidden",
                "content": {
                    "application/json": {
                        "example": {
                            "error": "Forbidden",
                            "message": "Insufficient permissions for this resource",
                            "timestamp": "2024-01-01T12:00:00Z",
                        }
                    }
                },
            },
            "404": {
                "description": "Not Found",
                "content": {
                    "application/json": {
                        "example": {
                            "error": "Not Found",
                            "message": "The requested resource was not found",
                            "timestamp": "2024-01-01T12:00:00Z",
                        }
                    }
                },
            },
            "422": {
                "description": "Validation Error",
                "content": {
                    "application/json": {
                        "example": {
                            "error": "Validation Error",
                            "message": "Request validation failed",
                            "details": [
                                {
                                    "field": "page",
                                    "error": "ensure this value is greater than or equal to 1",
                                }
                            ],
                            "timestamp": "2024-01-01T12:00:00Z",
                        }
                    }
                },
            },
            "429": {
                "description": "Too Many Requests",
                "content": {
                    "application/json": {
                        "example": {
                            "error": "Too Many Requests",
                            "message": "Rate limit exceeded. Please slow down your requests",
                            "retry_after": 60,
                            "timestamp": "2024-01-01T12:00:00Z",
                        }
                    }
                },
            },
            "500": {
                "description": "Internal Server Error",
                "content": {
                    "application/json": {
                        "example": {
                            "error": "Internal Server Error",
                            "message": "An unexpected error occurred. Please try again later",
                            "request_id": "req-123456789",
                            "timestamp": "2024-01-01T12:00:00Z",
                        }
                    }
                },
            },
        }
    }


def get_openapi_parameters() -> dict[str, Any]:
    """
    Get common OpenAPI parameters for reuse.

    Returns:
        Common parameter definitions for OpenAPI documentation
    """
    return {
        "components": {
            "parameters": {
                "PageParam": {
                    "name": "page",
                    "in": "query",
                    "description": "Page number for pagination (1-based)",
                    "required": False,
                    "schema": {"type": "integer", "minimum": 1, "default": 1},
                    "example": 1,
                },
                "PageSizeParam": {
                    "name": "page_size",
                    "in": "query",
                    "description": "Number of items per page (max 100)",
                    "required": False,
                    "schema": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 20,
                    },
                    "example": 20,
                },
                "SortByParam": {
                    "name": "sort_by",
                    "in": "query",
                    "description": "Field to sort by",
                    "required": False,
                    "schema": {"type": "string"},
                    "example": "date",
                },
                "SortOrderParam": {
                    "name": "sort_order",
                    "in": "query",
                    "description": "Sort order (asc or desc)",
                    "required": False,
                    "schema": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "default": "asc",
                    },
                    "example": "desc",
                },
                "StartDateParam": {
                    "name": "start_date",
                    "in": "query",
                    "description": "Start date for filtering (YYYY-MM-DD)",
                    "required": False,
                    "schema": {"type": "string", "format": "date"},
                    "example": "2010-01-01",
                },
                "EndDateParam": {
                    "name": "end_date",
                    "in": "query",
                    "description": "End date for filtering (YYYY-MM-DD)",
                    "required": False,
                    "schema": {"type": "string", "format": "date"},
                    "example": "2010-12-31",
                },
                "StatesParam": {
                    "name": "states",
                    "in": "query",
                    "description": "State codes to filter by (can be repeated)",
                    "required": False,
                    "schema": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["IL", "IA", "IN", "NE", "OH"],
                        },
                    },
                    "example": ["IL", "IA"],
                },
            }
        }
    }
