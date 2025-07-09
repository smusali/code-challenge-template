"""
Swagger UI configuration for enhanced API documentation.

Provides custom Swagger UI configuration including:
- Custom styling and themes
- Enhanced features and plugins
- Documentation customization
- Interactive examples
"""

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse


def get_swagger_ui_config() -> dict[str, Any]:
    """
    Get custom Swagger UI configuration.

    Returns:
        Swagger UI configuration with custom styling and features
    """
    return {
        "swagger_ui_parameters": {
            "deepLinking": True,
            "displayOperationId": True,
            "defaultModelsExpandDepth": 2,
            "defaultModelExpandDepth": 2,
            "defaultModelRendering": "model",
            "displayRequestDuration": True,
            "docExpansion": "list",
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
            "tryItOutEnabled": True,
            "supportedSubmitMethods": ["get", "post", "put", "delete", "patch"],
            "validatorUrl": None,
            "withCredentials": True,
            "persistAuthorization": True,
            "layout": "BaseLayout",
            "plugins": ["TopbarPlugin"],
            "presets": ["apis", "standalone"],
        }
    }


def get_custom_swagger_ui_html(
    openapi_url: str,
    title: str,
    swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
    swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    swagger_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
    oauth2_redirect_url: str | None = None,
) -> HTMLResponse:
    """
    Generate custom Swagger UI HTML with enhanced styling and features.

    Args:
        openapi_url: URL to the OpenAPI schema
        title: API title
        swagger_js_url: URL to Swagger UI JavaScript
        swagger_css_url: URL to Swagger UI CSS
        swagger_favicon_url: URL to favicon
        oauth2_redirect_url: OAuth2 redirect URL

    Returns:
        HTMLResponse with custom Swagger UI
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <link rel="stylesheet" type="text/css" href="{swagger_css_url}">
        <link rel="icon" type="image/png" href="{swagger_favicon_url}">
        <style>
            /* Custom Weather API Theme */
            .swagger-ui .topbar {{
                background-color: #2c3e50;
                background-image: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                border-bottom: 3px solid #3498db;
            }}

            .swagger-ui .topbar .download-url-wrapper {{
                display: none;
            }}

            .swagger-ui .info {{
                margin: 50px 0;
                padding: 20px;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 8px;
                border-left: 4px solid #3498db;
            }}

            .swagger-ui .info .title {{
                color: #2c3e50;
                font-size: 36px;
                font-weight: 700;
                margin-bottom: 10px;
            }}

            .swagger-ui .info .description {{
                color: #495057;
                font-size: 14px;
                line-height: 1.6;
            }}

            .swagger-ui .info .description h1 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }}

            .swagger-ui .info .description h2 {{
                color: #34495e;
                margin-top: 30px;
                margin-bottom: 15px;
            }}

            .swagger-ui .info .description h3 {{
                color: #3498db;
                margin-top: 25px;
                margin-bottom: 10px;
            }}

            .swagger-ui .info .description code {{
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 2px 6px;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                color: #e74c3c;
            }}

            .swagger-ui .info .description pre {{
                background-color: #2c3e50;
                border: 1px solid #34495e;
                border-radius: 6px;
                padding: 15px;
                overflow-x: auto;
                color: #ecf0f1;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            }}

            .swagger-ui .info .description pre code {{
                background: none;
                border: none;
                color: #ecf0f1;
                padding: 0;
            }}

            .swagger-ui .scheme-container {{
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 15px;
                margin-bottom: 20px;
            }}

            .swagger-ui .opblock {{
                border: 1px solid #e9ecef;
                border-radius: 6px;
                margin-bottom: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            .swagger-ui .opblock.opblock-get {{
                border-color: #27ae60;
            }}

            .swagger-ui .opblock.opblock-post {{
                border-color: #3498db;
            }}

            .swagger-ui .opblock.opblock-put {{
                border-color: #f39c12;
            }}

            .swagger-ui .opblock.opblock-delete {{
                border-color: #e74c3c;
            }}

            .swagger-ui .opblock-summary {{
                border-radius: 6px 6px 0 0;
            }}

            .swagger-ui .opblock-summary-method {{
                font-weight: 700;
                min-width: 80px;
                border-radius: 4px;
                margin-right: 10px;
            }}

            .swagger-ui .opblock-summary-description {{
                font-weight: 600;
                color: #2c3e50;
            }}

            .swagger-ui .opblock-description-wrapper {{
                padding: 20px;
                background-color: #f8f9fa;
                border-top: 1px solid #e9ecef;
            }}

            .swagger-ui .response-col_status {{
                font-weight: 700;
                color: #27ae60;
            }}

            .swagger-ui .response-col_description {{
                color: #495057;
            }}

            .swagger-ui .btn {{
                border-radius: 4px;
                font-weight: 600;
                transition: all 0.3s ease;
            }}

            .swagger-ui .btn.execute {{
                background-color: #3498db;
                border-color: #3498db;
                color: white;
            }}

            .swagger-ui .btn.execute:hover {{
                background-color: #2980b9;
                border-color: #2980b9;
                transform: translateY(-1px);
            }}

            .swagger-ui .btn.cancel {{
                background-color: #95a5a6;
                border-color: #95a5a6;
                color: white;
            }}

            .swagger-ui .btn.cancel:hover {{
                background-color: #7f8c8d;
                border-color: #7f8c8d;
            }}

            .swagger-ui .parameters-col_description {{
                color: #495057;
            }}

            .swagger-ui .parameter__name {{
                color: #2c3e50;
                font-weight: 600;
            }}

            .swagger-ui .parameter__type {{
                color: #8e44ad;
                font-weight: 600;
            }}

            .swagger-ui .response-content-type {{
                color: #27ae60;
                font-weight: 600;
            }}

            .swagger-ui .model-title {{
                color: #2c3e50;
                font-weight: 700;
            }}

            .swagger-ui .model {{
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 15px;
            }}

            .swagger-ui .model-toggle {{
                color: #3498db;
                font-weight: 600;
            }}

            .swagger-ui .model-toggle:hover {{
                color: #2980b9;
            }}

            .swagger-ui .tab li {{
                color: #495057;
                font-weight: 600;
            }}

            .swagger-ui .tab li.active {{
                color: #3498db;
                border-bottom: 2px solid #3498db;
            }}

            .swagger-ui .loading-container {{
                background-color: #3498db;
            }}

            .swagger-ui .loading-container .loading {{
                border-color: #ecf0f1;
                border-top-color: #3498db;
            }}

            /* Custom scrollbar */
            .swagger-ui ::-webkit-scrollbar {{
                width: 8px;
                height: 8px;
            }}

            .swagger-ui ::-webkit-scrollbar-track {{
                background: #f1f1f1;
                border-radius: 4px;
            }}

            .swagger-ui ::-webkit-scrollbar-thumb {{
                background: #3498db;
                border-radius: 4px;
            }}

            .swagger-ui ::-webkit-scrollbar-thumb:hover {{
                background: #2980b9;
            }}

            /* Weather-specific styling */
            .swagger-ui .opblock-tag {{
                color: #2c3e50;
                font-weight: 700;
                font-size: 18px;
                margin-bottom: 10px;
                padding: 10px 0;
                border-bottom: 2px solid #3498db;
            }}

            .swagger-ui .opblock-tag:hover {{
                color: #3498db;
            }}

            .swagger-ui .opblock-tag small {{
                color: #7f8c8d;
                font-weight: 400;
                font-size: 14px;
            }}

            /* Status badges */
            .swagger-ui .response-col_status.response-200 {{
                color: #27ae60;
                font-weight: 700;
            }}

            .swagger-ui .response-col_status.response-400 {{
                color: #e74c3c;
                font-weight: 700;
            }}

            .swagger-ui .response-col_status.response-500 {{
                color: #c0392b;
                font-weight: 700;
            }}

            /* Custom header */
            .swagger-ui::before {{
                content: "🌤️ Weather Data Engineering API";
                display: block;
                text-align: center;
                font-size: 24px;
                font-weight: 700;
                color: #2c3e50;
                margin: 20px 0;
                padding: 20px;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 8px;
                border-left: 4px solid #3498db;
            }}

            /* Footer */
            .swagger-ui::after {{
                content: "Built with FastAPI and Django ORM • Weather Data Engineering Team";
                display: block;
                text-align: center;
                font-size: 14px;
                color: #7f8c8d;
                margin-top: 40px;
                padding: 20px;
                border-top: 1px solid #e9ecef;
            }}

            /* Animation for loading */
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
                100% {{ opacity: 1; }}
            }}

            .swagger-ui .loading {{
                animation: pulse 2s infinite;
            }}

            /* Responsive design */
            @media (max-width: 768px) {{
                .swagger-ui .info .title {{
                    font-size: 28px;
                }}

                .swagger-ui .info .description {{
                    font-size: 13px;
                }}

                .swagger-ui .opblock-summary {{
                    padding: 10px;
                }}

                .swagger-ui .opblock-summary-method {{
                    min-width: 60px;
                    font-size: 12px;
                }}
            }}
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="{swagger_js_url}"></script>
        <script>
            const ui = SwaggerUIBundle({{
                url: '{openapi_url}',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "BaseLayout",
                deepLinking: true,
                displayOperationId: true,
                defaultModelsExpandDepth: 2,
                defaultModelExpandDepth: 2,
                defaultModelRendering: 'model',
                displayRequestDuration: true,
                docExpansion: 'list',
                filter: true,
                showExtensions: true,
                showCommonExtensions: true,
                tryItOutEnabled: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                validatorUrl: null,
                withCredentials: true,
                persistAuthorization: true,
                onComplete: function() {{
                    // Add custom JavaScript after initialization
                    console.log('Weather Data Engineering API Documentation Loaded');

                    // Add weather-themed favicon
                    const favicon = document.createElement('link');
                    favicon.rel = 'icon';
                    favicon.href = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzM0OThkYiI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iNSIvPjxsaW5lIHgxPSIxMiIgeTE9IjEiIHgyPSIxMiIgeTI9IjMiLz48bGluZSB4MT0iMTIiIHkxPSIyMSIgeDI9IjEyIiB5Mj0iMjMiLz48bGluZSB4MT0iNC4yMiIgeTE9IjQuMjIiIHgyPSI1LjY0IiB5Mj0iNS42NCIvPjxsaW5lIHgxPSIxOC4zNiIgeTE9IjE4LjM2IiB4Mj0iMTkuNzgiIHkyPSIxOS43OCIvPjxsaW5lIHgxPSIxIiB5MT0iMTIiIHgyPSIzIiB5Mj0iMTIiLz48bGluZSB4MT0iMjEiIHkxPSIxMiIgeDI9IjIzIiB5Mj0iMTIiLz48bGluZSB4MT0iNC4yMiIgeTE9IjE5Ljc4IiB4Mj0iNS42NCIgeTI9IjE4LjM2Ii8+PGxpbmUgeDE9IjE4LjM2IiB5MT0iNS42NCIgeDI9IjE5Ljc4IiB5Mj0iNC4yMiIvPjwvc3ZnPg==';
                    document.head.appendChild(favicon);

                    // Add keyboard shortcuts
                    document.addEventListener('keydown', function(e) {{
                        if (e.ctrlKey && e.key === '/') {{
                            e.preventDefault();
                            const filterInput = document.querySelector('.filter-container input');
                            if (filterInput) {{
                                filterInput.focus();
                            }}
                        }}
                    }});

                    // Add tooltips for better UX
                    const tooltips = document.querySelectorAll('[title]');
                    tooltips.forEach(function(element) {{
                        element.addEventListener('mouseenter', function() {{
                            const tooltip = document.createElement('div');
                            tooltip.className = 'custom-tooltip';
                            tooltip.textContent = element.getAttribute('title');
                            document.body.appendChild(tooltip);

                            const rect = element.getBoundingClientRect();
                            tooltip.style.position = 'absolute';
                            tooltip.style.top = rect.bottom + 5 + 'px';
                            tooltip.style.left = rect.left + 'px';
                            tooltip.style.backgroundColor = '#2c3e50';
                            tooltip.style.color = 'white';
                            tooltip.style.padding = '5px 10px';
                            tooltip.style.borderRadius = '4px';
                            tooltip.style.fontSize = '12px';
                            tooltip.style.zIndex = '10000';
                        }});

                        element.addEventListener('mouseleave', function() {{
                            const tooltip = document.querySelector('.custom-tooltip');
                            if (tooltip) {{
                                tooltip.remove();
                            }}
                        }});
                    }});
                }},
                oauth2RedirectUrl: '{oauth2_redirect_url}' if '{oauth2_redirect_url}' !== 'None' else null
            }});
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html, status_code=200)


def get_redoc_html(
    openapi_url: str,
    title: str,
    redoc_js_url: str = "https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
    redoc_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
) -> HTMLResponse:
    """
    Generate custom ReDoc HTML with enhanced styling.

    Args:
        openapi_url: URL to the OpenAPI schema
        title: API title
        redoc_js_url: URL to ReDoc JavaScript
        redoc_favicon_url: URL to favicon

    Returns:
        HTMLResponse with custom ReDoc
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="icon" type="image/png" href="{redoc_favicon_url}">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
                background-color: #fafafa;
            }}

            .redoc-container {{
                background-color: #fafafa;
            }}

            .redoc-wrap {{
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin: 20px;
                overflow: hidden;
            }}

            /* Custom ReDoc theme */
            .redoc-json {{
                border: 1px solid #e9ecef;
                border-radius: 6px;
                background-color: #f8f9fa;
            }}

            .redoc-json .key {{
                color: #e74c3c;
            }}

            .redoc-json .string {{
                color: #27ae60;
            }}

            .redoc-json .number {{
                color: #3498db;
            }}

            .redoc-json .boolean {{
                color: #9b59b6;
            }}

            .redoc-json .null {{
                color: #95a5a6;
            }}
        </style>
    </head>
    <body>
        <div class="redoc-container">
            <div class="redoc-wrap">
                <redoc spec-url="{openapi_url}"></redoc>
            </div>
        </div>
        <script src="{redoc_js_url}"></script>
        <script>
            // Initialize ReDoc with custom configuration
            Redoc.init(
                '{openapi_url}',
                {{
                    theme: {{
                        colors: {{
                            primary: {{
                                main: '#3498db'
                            }},
                            success: {{
                                main: '#27ae60'
                            }},
                            warning: {{
                                main: '#f39c12'
                            }},
                            error: {{
                                main: '#e74c3c'
                            }}
                        }},
                        typography: {{
                            fontSize: '14px',
                            lineHeight: '1.5',
                            code: {{
                                fontSize: '13px',
                                fontFamily: 'Monaco, Consolas, "Lucida Console", monospace'
                            }}
                        }},
                        sidebar: {{
                            backgroundColor: '#f8f9fa',
                            width: '300px'
                        }},
                        rightPanel: {{
                            backgroundColor: '#2c3e50',
                            width: '40%'
                        }}
                    }},
                    scrollYOffset: 60,
                    hideDownloadButton: false,
                    disableSearch: false,
                    expandResponses: "200,201",
                    requiredPropsFirst: true,
                    sortPropsAlphabetically: true,
                    showExtensions: true,
                    nativeScrollbars: false,
                    pathInMiddlePanel: false,
                    untrustedSpec: false,
                    expandSingleSchemaField: false,
                    menuToggle: true,
                    jsonSampleExpandLevel: 2
                }},
                document.querySelector('.redoc-wrap')
            );
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html, status_code=200)


def create_custom_openapi_schema(app: FastAPI) -> None:
    """
    Create custom OpenAPI schema with enhanced documentation.

    Args:
        app: FastAPI application instance
    """
    from .openapi_config import (
        get_openapi_config,
        get_openapi_parameters,
        get_openapi_tags,
        get_response_examples,
        get_security_schemes,
    )

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        # Get base OpenAPI schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Apply custom configuration
        config = get_openapi_config()
        openapi_schema.update(config)

        # Add custom tags
        openapi_schema["tags"] = get_openapi_tags()

        # Add security schemes
        security_config = get_security_schemes()
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        openapi_schema["components"].update(security_config["components"])

        # Add common parameters
        parameters_config = get_openapi_parameters()
        openapi_schema["components"].update(parameters_config["components"])

        # Add response examples
        response_config = get_response_examples()
        openapi_schema["components"].update(response_config)

        # Cache the schema
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
