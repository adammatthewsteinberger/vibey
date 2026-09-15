# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""
Complete Azure Functions example using Azure Bootstrap library.

This example demonstrates how to use the Azure Bootstrap library
in a production Azure Functions application.

The bootstrap handles:
- Bootstrap logging (works immediately)
- Azure App Configuration loading
- Azure Key Vault secrets resolution
- Application Insights telemetry setup
- Loading all configs to os.environ

Installation:
    pip install vibey-bootstrap

Configuration:
    See local.settings.json.example for required environment variables
"""

import json
import os
from datetime import UTC, datetime

import azure.functions as func

from vibey_bootstrap import get_bootstrap_logger, initialize_application

# Global state for lazy initialization
_bootstrap_initialized = False
_logger = None


def _ensure_bootstrap():
    """
    Ensure application bootstrap has been initialized (lazy initialization).

    This function is called at the start of every function to ensure
    the application bootstrap (logging, config, telemetry) has run.

    The Azure Functions Python worker doesn't execute module-level code
    during indexing, so we must use lazy initialization on first function call.
    """
    global _bootstrap_initialized, _logger

    if _bootstrap_initialized:
        return

    # Get logger that works immediately (before config is loaded)
    _logger = get_bootstrap_logger(__name__)

    _logger.info(
        "Starting Azure Functions application bootstrap",
        extra={"operation": "app_startup", "component": "function_app", "phase": "bootstrap_init"},
    )

    try:
        # Initialize application bootstrap (logging, config, telemetry)
        # This will:
        # 1. Load from Azure App Configuration
        # 2. Resolve Key Vault references automatically
        # 3. Set up Application Insights telemetry
        # 4. Load all configs to os.environ
        config_repository = initialize_application()

        _logger.info(
            "Application bootstrap completed successfully",
            extra={
                "operation": "app_startup",
                "component": "function_app",
                "phase": "bootstrap_complete",
                "config_repository_type": type(config_repository).__name__,
                "database_host": os.getenv("DATABASE_HOST", "NOT SET"),
                "environment": os.getenv("ENVIRONMENT", "dev"),
            },
        )

        _bootstrap_initialized = True

        _logger.info(
            "Azure Functions application ready",
            extra={"operation": "app_startup", "component": "function_app", "phase": "ready"},
        )

    except Exception as e:
        _logger.error(
            "Application bootstrap failed",
            extra={
                "operation": "app_startup",
                "component": "function_app",
                "phase": "bootstrap_failed",
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        raise  # Fail fast - can't continue without bootstrap


# Create Azure Function app
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="hello", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def hello_world(req: func.HttpRequest) -> func.HttpResponse:
    """
    Simple HTTP endpoint demonstrating basic usage.

    GET /api/hello

    Response:
        200 OK: JSON with application info
    """
    _ensure_bootstrap()

    _logger.info(
        "Processing hello request",
        extra={
            "operation": "hello_request",
            "component": "hello_world_function",
        },
    )

    # All configs are now in os.environ
    response_data = {
        "message": "Hello from Azure Functions with Azure Bootstrap!",
        "timestamp": datetime.now(UTC).isoformat(),
        "environment": os.getenv("ENVIRONMENT", "dev"),
        "database_configured": bool(os.getenv("DATABASE_HOST")),
        "app_insights_configured": bool(os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")),
    }

    return func.HttpResponse(
        json.dumps(response_data, indent=2), mimetype="application/json", status_code=200
    )


@app.route(route="config", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def get_config(req: func.HttpRequest) -> func.HttpResponse:
    """
    Config inspection endpoint (protected with function key).

    GET /api/config?key=DATABASE_HOST

    Query Parameters:
        key (optional): Specific config key to retrieve

    Response:
        200 OK: Config value(s)
        404 Not Found: Config key not found
    """
    _ensure_bootstrap()

    config_key = req.params.get("key")

    _logger.info(
        "Processing config request",
        extra={
            "operation": "config_request",
            "component": "get_config_function",
            "config_key": config_key,
        },
    )

    if config_key:
        # Return specific config value
        value = os.getenv(config_key)
        if value is None:
            return func.HttpResponse(
                json.dumps({"error": f"Config key '{config_key}' not found"}),
                mimetype="application/json",
                status_code=404,
            )

        # Mask secrets
        if any(
            secret_word in config_key.upper()
            for secret_word in ["PASSWORD", "SECRET", "KEY", "TOKEN"]
        ):
            value = "***REDACTED***"

        return func.HttpResponse(
            json.dumps({"key": config_key, "value": value}),
            mimetype="application/json",
            status_code=200,
        )
    else:
        # Return list of available config keys (non-sensitive)
        config_keys = [
            k
            for k in os.environ.keys()
            if not any(
                secret_word in k.upper() for secret_word in ["PASSWORD", "SECRET", "KEY", "TOKEN"]
            )
        ]

        return func.HttpResponse(
            json.dumps({"available_keys": sorted(config_keys)}, indent=2),
            mimetype="application/json",
            status_code=200,
        )


@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint for monitoring.

    GET /api/health?detailed=true

    Query Parameters:
        detailed (optional): Include detailed health checks

    Response:
        200 OK: Service is healthy
        503 Service Unavailable: Service has issues
    """
    # Check if detailed health check is requested
    detailed = req.params.get("detailed", "false").lower() == "true"

    # Get current timestamp
    current_time = datetime.now(UTC).isoformat()

    # Basic health response
    health_response = {
        "status": "healthy",
        "service": "Example Azure Function with Azure Bootstrap",
        "timestamp": current_time,
        "version": "1.0.0",
    }

    # If not detailed, return basic health immediately
    if not detailed:
        return func.HttpResponse(
            json.dumps(health_response, indent=2), mimetype="application/json", status_code=200
        )

    # Detailed health checks
    checks = {}
    overall_healthy = True

    # 1. Bootstrap check
    try:
        if _bootstrap_initialized:
            checks["bootstrap"] = "healthy"
        else:
            checks["bootstrap"] = "not_initialized"
            overall_healthy = False
    except Exception as e:
        checks["bootstrap"] = f"error: {str(e)}"
        overall_healthy = False

    # 2. Configuration check
    try:
        required_vars = [
            "DATABASE_HOST",
            "DATABASE_NAME",
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if not missing_vars:
            checks["configuration"] = "healthy"
        else:
            checks["configuration"] = f"missing: {', '.join(missing_vars)}"
            overall_healthy = False
    except Exception as e:
        checks["configuration"] = f"error: {str(e)}"
        overall_healthy = False

    # 3. Telemetry check
    try:
        app_insights_conn = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if app_insights_conn:
            checks["telemetry"] = "configured"
        else:
            checks["telemetry"] = "not_configured"
    except Exception as e:
        checks["telemetry"] = f"error: {str(e)}"

    # Update health response
    health_response["status"] = "healthy" if overall_healthy else "degraded"
    health_response["checks"] = checks

    # Return appropriate status code
    status_code = 200 if overall_healthy else 503

    return func.HttpResponse(
        json.dumps(health_response, indent=2), mimetype="application/json", status_code=status_code
    )


@app.timer_trigger(
    arg_name="timer",
    schedule="0 */5 * * * *",
    run_on_startup=False,  # Every 5 minutes
)
def scheduled_task(timer: func.TimerRequest) -> None:
    """
    Timer triggered function that runs on schedule.

    Schedule: Every 5 minutes
    """
    _ensure_bootstrap()

    _logger.info(
        "Running scheduled task",
        extra={
            "operation": "scheduled_task",
            "component": "scheduled_task_function",
            "is_past_due": timer.past_due,
        },
    )

    # Do your scheduled work here
    # All configs are available in os.environ
    database_host = os.getenv("DATABASE_HOST")

    _logger.info(
        "Scheduled task completed",
        extra={
            "operation": "scheduled_task",
            "component": "scheduled_task_function",
            "database_host": database_host,
        },
    )


@app.queue_trigger(arg_name="msg", queue_name="example-queue", connection="AzureWebJobsStorage")
def queue_processor(msg: func.QueueMessage) -> None:
    """
    Queue triggered function for async processing.

    Queue: example-queue
    """
    _ensure_bootstrap()

    message_body = msg.get_body().decode("utf-8")

    _logger.info(
        "Processing queue message",
        extra={
            "operation": "queue_processing",
            "component": "queue_processor_function",
            "message_id": msg.id,
            "message_length": len(message_body),
        },
    )

    # Process the message
    # All configs are available in os.environ

    _logger.info(
        "Queue message processed successfully",
        extra={
            "operation": "queue_processing",
            "component": "queue_processor_function",
            "message_id": msg.id,
        },
    )
