"""
Report generation and visualization
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Template
from loguru import logger


class ExecutionReport:
    """Execution report data model"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.success = True
        self.error: Optional[str] = None
        self.tasks: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.screenshots: List[str] = []
        self.ai_usage: Dict[str, Any] = {}
    
    def add_task(self, task_data: Dict[str, Any]) -> None:
        """Add task execution data"""
        self.tasks.append({
            **task_data,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_screenshot(self, screenshot_base64: str, description: str = "") -> None:
        """Add screenshot to report"""
        self.screenshots.append({
            "image": screenshot_base64,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
    
    def update_ai_usage(self, usage_data: Dict[str, Any]) -> None:
        """Update AI usage statistics"""
        for key, value in usage_data.items():
            if key in self.ai_usage:
                if isinstance(value, (int, float)):
                    self.ai_usage[key] += value
                else:
                    self.ai_usage[key] = value
            else:
                self.ai_usage[key] = value
    
    def finalize(self, success: bool = True, error: Optional[str] = None) -> None:
        """Finalize report"""
        self.end_time = datetime.now()
        self.success = success
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        duration = None
        if self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": duration,
            "success": self.success,
            "error": self.error,
            "tasks": self.tasks,
            "metadata": self.metadata,
            "screenshots": self.screenshots,
            "ai_usage": self.ai_usage,
            "summary": {
                "total_tasks": len(self.tasks),
                "successful_tasks": len([t for t in self.tasks if t.get("success", True)]),
                "failed_tasks": len([t for t in self.tasks if not t.get("success", True)]),
                "total_screenshots": len(self.screenshots)
            }
        }


class ReportGenerator:
    """Generate execution reports in various formats"""
    
    def __init__(self, output_dir: str = "./reports"):
        """Initialize report generator
        
        Args:
            output_dir: Output directory for reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_report(
        self, 
        report: ExecutionReport, 
        template_path: Optional[str] = None
    ) -> str:
        """Generate HTML report
        
        Args:
            report: Execution report data
            template_path: Custom template path
            
        Returns:
            Path to generated HTML file
        """
        if template_path:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        else:
            template_content = self._get_default_html_template()
        
        template = Template(template_content)
        
        # Generate report
        html_content = template.render(
            report=report.to_dict(),
            generated_at=datetime.now().isoformat()
        )
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"midscene_report_{timestamp}.html"
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {file_path}")
        return str(file_path)
    
    def generate_json_report(self, report: ExecutionReport) -> str:
        """Generate JSON report
        
        Args:
            report: Execution report data
            
        Returns:
            Path to generated JSON file
        """
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"midscene_report_{timestamp}.json"
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON report generated: {file_path}")
        return str(file_path)
    
    def _get_default_html_template(self) -> str:
        """Get default HTML template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Midscene Execution Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }
        .header {
            border-bottom: 2px solid #e1e5e9;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            color: #2c3e50;
            font-size: 2.5em;
        }
        .status {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 10px;
        }
        .status.success {
            background-color: #d4edda;
            color: #155724;
        }
        .status.failure {
            background-color: #f8d7da;
            color: #721c24;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .summary-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }
        .tasks {
            margin-bottom: 30px;
        }
        .task {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            margin-bottom: 15px;
            padding: 20px;
        }
        .task.success {
            border-left: 4px solid #28a745;
        }
        .task.failure {
            border-left: 4px solid #dc3545;
        }
        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .task-title {
            font-weight: bold;
            font-size: 1.1em;
            color: #2c3e50;
        }
        .task-status {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .task-status.success {
            background-color: #d4edda;
            color: #155724;
        }
        .task-status.failure {
            background-color: #f8d7da;
            color: #721c24;
        }
        .screenshots {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .screenshot {
            border: 1px solid #dee2e6;
            border-radius: 6px;
            overflow: hidden;
        }
        .screenshot img {
            width: 100%;
            height: auto;
            display: block;
        }
        .screenshot-caption {
            padding: 10px;
            background: #f8f9fa;
            font-size: 0.9em;
            color: #6c757d;
        }
        .ai-usage {
            background: #e3f2fd;
            border-radius: 6px;
            padding: 20px;
            margin-top: 30px;
        }
        .ai-usage h3 {
            margin-top: 0;
            color: #1976d2;
        }
        .usage-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .usage-item {
            text-align: center;
        }
        .usage-item .label {
            font-size: 0.8em;
            color: #666;
            text-transform: uppercase;
        }
        .usage-item .value {
            font-size: 1.5em;
            font-weight: bold;
            color: #1976d2;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e1e5e9;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Midscene Execution Report</h1>
            <div class="status {{ 'success' if report.success else 'failure' }}">
                {{ '✅ Success' if report.success else '❌ Failed' }}
            </div>
            {% if report.error %}
            <div style="margin-top: 15px; padding: 15px; background: #f8d7da; color: #721c24; border-radius: 4px;">
                <strong>Error:</strong> {{ report.error }}
            </div>
            {% endif %}
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>Duration</h3>
                <div class="value">
                    {% if report.duration_seconds %}
                        {{ "%.1f"|format(report.duration_seconds) }}s
                    {% else %}
                        -
                    {% endif %}
                </div>
            </div>
            <div class="summary-card">
                <h3>Total Tasks</h3>
                <div class="value">{{ report.summary.total_tasks }}</div>
            </div>
            <div class="summary-card">
                <h3>Successful</h3>
                <div class="value">{{ report.summary.successful_tasks }}</div>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <div class="value">{{ report.summary.failed_tasks }}</div>
            </div>
        </div>

        {% if report.tasks %}
        <div class="tasks">
            <h2>📋 Task Execution</h2>
            {% for task in report.tasks %}
            <div class="task {{ 'success' if task.get('success', True) else 'failure' }}">
                <div class="task-header">
                    <div class="task-title">{{ task.get('type', 'Task') }}: {{ task.get('description', 'Unknown') }}</div>
                    <div class="task-status {{ 'success' if task.get('success', True) else 'failure' }}">
                        {{ 'Success' if task.get('success', True) else 'Failed' }}
                    </div>
                </div>
                {% if task.get('error') %}
                <div style="color: #dc3545; margin-top: 10px;">
                    <strong>Error:</strong> {{ task.error }}
                </div>
                {% endif %}
                {% if task.get('result') %}
                <div style="margin-top: 10px;">
                    <strong>Result:</strong> {{ task.result }}
                </div>
                {% endif %}
                <div style="margin-top: 10px; font-size: 0.9em; color: #6c757d;">
                    {{ task.timestamp }}
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if report.ai_usage %}
        <div class="ai-usage">
            <h3>🧠 AI Usage Statistics</h3>
            <div class="usage-grid">
                {% for key, value in report.ai_usage.items() %}
                <div class="usage-item">
                    <div class="label">{{ key.replace('_', ' ').title() }}</div>
                    <div class="value">{{ value }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        {% if report.screenshots %}
        <div class="screenshots">
            <h2>📸 Screenshots</h2>
            {% for screenshot in report.screenshots %}
            <div class="screenshot">
                <img src="data:image/png;base64,{{ screenshot.image }}" alt="Screenshot">
                {% if screenshot.description %}
                <div class="screenshot-caption">{{ screenshot.description }}</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="footer">
            Generated by Midscene Python at {{ generated_at }}
        </div>
    </div>
</body>
</html>
        """.strip()


def create_report() -> ExecutionReport:
    """Create new execution report
    
    Returns:
        ExecutionReport instance
    """
    return ExecutionReport()