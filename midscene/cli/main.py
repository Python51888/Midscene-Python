"""
Midscene CLI - Command line interface for automation scripts
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, List

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

from .runner import ScriptRunner
from .config import CLIConfig

app = typer.Typer(
    name="midscene",
    help="AI-powered automation framework for Web and Android platforms",
    no_args_is_help=True
)

console = Console()


@app.command()
def run(
    script_path: str = typer.Argument(..., help="Path to YAML script file or directory"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file path"),
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode"),
    device_id: Optional[str] = typer.Option(None, "--device", "-d", help="Android device ID"),
    concurrent: int = typer.Option(1, "--concurrent", help="Number of concurrent executions"),
    continue_on_error: bool = typer.Option(False, "--continue-on-error", help="Continue on script errors"),
    generate_report: bool = typer.Option(True, "--report/--no-report", help="Generate execution report"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Run automation script(s)"""
    
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    logger.remove()
    logger.add(sys.stderr, level=log_level, format="{time} | {level} | {message}")
    
    try:
        # Load configuration
        config = CLIConfig.load(config_file) if config_file else CLIConfig()
        
        # Override config with CLI options
        if headless is not None:
            config.web.headless = headless
        if device_id is not None:
            config.android.device_id = device_id
        if concurrent is not None:
            config.execution.concurrent = concurrent
        if continue_on_error is not None:
            config.execution.continue_on_error = continue_on_error
        if generate_report is not None:
            config.execution.generate_report = generate_report
        
        # Create runner and execute
        runner = ScriptRunner(config)
        
        # Run synchronously
        result = asyncio.run(runner.run(script_path))
        
        if result.success:
            console.print("✅ Execution completed successfully", style="green")
            if result.report_path:
                console.print(f"📊 Report: {result.report_path}")
        else:
            console.print("❌ Execution failed", style="red")
            if result.error:
                console.print(f"Error: {result.error}", style="red")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"❌ CLI Error: {e}", style="red")
        if verbose:
            logger.exception("CLI execution failed")
        sys.exit(1)


@app.command()
def validate(
    script_path: str = typer.Argument(..., help="Path to YAML script file"),
):
    """Validate automation script syntax"""
    
    try:
        from .validator import ScriptValidator
        
        validator = ScriptValidator()
        result = validator.validate_file(script_path)
        
        if result.valid:
            console.print("✅ Script validation passed", style="green")
        else:
            console.print("❌ Script validation failed", style="red")
            for error in result.errors:
                console.print(f"  • {error}", style="red")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"❌ Validation Error: {e}", style="red")
        sys.exit(1)


@app.command()
def devices():
    """List available Android devices"""
    
    try:
        from ..android import AndroidDevice
        
        devices = asyncio.run(AndroidDevice.list_devices())
        
        if not devices:
            console.print("No Android devices found", style="yellow")
            return
        
        table = Table(title="Available Android Devices")
        table.add_column("Device ID", style="cyan")
        table.add_column("Status", style="green")
        
        for device_id in devices:
            table.add_row(device_id, "Connected")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error listing devices: {e}", style="red")
        sys.exit(1)


@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    template: str = typer.Option("basic", "--template", "-t", help="Project template"),
):
    """Initialize new automation project"""
    
    try:
        from .templates import ProjectTemplate
        
        template_manager = ProjectTemplate()
        project_path = template_manager.create_project(name, template)
        
        console.print(f"✅ Created project: {project_path}", style="green")
        console.print(f"📝 Edit {project_path}/scripts/example.yaml to get started")
        
    except Exception as e:
        console.print(f"❌ Initialization Error: {e}", style="red")
        sys.exit(1)


@app.command()
def version():
    """Show version information"""
    
    try:
        from .. import __version__
        console.print(f"Midscene Python v{__version__}")
        
    except Exception as e:
        console.print(f"❌ Error getting version: {e}", style="red")


def main():
    """CLI entry point"""
    app()


if __name__ == "__main__":
    main()