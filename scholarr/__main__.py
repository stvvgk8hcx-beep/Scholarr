"""Entry point for running Scholarr as a module."""

import logging
from pathlib import Path

import typer
import uvicorn

from scholarr.core.config import settings

app = typer.Typer(help="Scholarr - Self-hosted Academic File Management System")

logger = logging.getLogger(__name__)


@app.command()
def main(
    port: int = typer.Option(settings.port, "--port", "-p", help="Port to run the server on"),
    host: str = typer.Option(settings.host, "--host", "-h", help="Host to bind to"),
    config: str = typer.Option(None, "--config", "-c", help="Path to config file"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode"),
):
    """Run the Scholarr application."""

    # Set up logging
    log_level = "DEBUG" if debug else "INFO"
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load config if provided
    if config:
        config_path = Path(config)
        if not config_path.exists():
            typer.echo(f"Error: Config file not found: {config}", err=True)
            raise typer.Exit(1)
        # You could implement custom config loading here
        logger.info(f"Loading config from: {config}")

    logger.info(f"Starting Scholarr on {host}:{port}")

    # Run uvicorn
    uvicorn.run(
        "scholarr.app:app",
        host=host,
        port=port,
        reload=debug,
        log_level=log_level.lower(),
    )


if __name__ == "__main__":
    app()
