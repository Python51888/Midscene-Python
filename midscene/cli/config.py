"""
CLI configuration management
"""

from pathlib import Path
from typing import Optional, Dict, Any

import yaml
from pydantic import BaseModel, Field


class WebConfig(BaseModel):
    """Web automation configuration"""
    browser: str = "chrome"
    headless: bool = False
    window_size: tuple[int, int] = (1920, 1080)
    user_data_dir: Optional[str] = None
    timeout: int = 30


class AndroidConfig(BaseModel):
    """Android automation configuration"""
    device_id: Optional[str] = None
    adb_path: str = "adb"
    auto_dismiss_keyboard: bool = True
    timeout: int = 30


class AIConfig(BaseModel):
    """AI model configuration"""
    provider: str = "openai"
    model: str = "gpt-4-vision-preview"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.1


class ExecutionConfig(BaseModel):
    """Execution configuration"""
    concurrent: int = 1
    continue_on_error: bool = False
    generate_report: bool = True
    report_format: str = "html"
    output_dir: str = "./reports"


class CLIConfig(BaseModel):
    """CLI configuration"""
    web: WebConfig = Field(default_factory=WebConfig)
    android: AndroidConfig = Field(default_factory=AndroidConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'CLIConfig':
        """Load configuration from file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            CLIConfig instance
        """
        if not config_path:
            # Look for default config files
            for default_path in ["midscene.yml", "midscene.yaml", ".midscene.yml"]:
                if Path(default_path).exists():
                    config_path = default_path
                    break
        
        if not config_path or not Path(config_path).exists():
            # Return default configuration
            return cls()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        return cls(**config_data)
    
    def save(self, config_path: str) -> None:
        """Save configuration to file
        
        Args:
            config_path: Path to save configuration
        """
        config_data = self.model_dump()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
    
    def to_env_vars(self) -> Dict[str, str]:
        """Convert configuration to environment variables
        
        Returns:
            Dictionary of environment variables
        """
        env_vars = {}
        
        # AI configuration
        if self.ai.api_key:
            env_vars['MIDSCENE_AI_API_KEY'] = self.ai.api_key
        env_vars['MIDSCENE_AI_PROVIDER'] = self.ai.provider
        env_vars['MIDSCENE_AI_MODEL'] = self.ai.model
        if self.ai.base_url:
            env_vars['MIDSCENE_AI_BASE_URL'] = self.ai.base_url
        
        # Execution configuration
        env_vars['MIDSCENE_CONCURRENT'] = str(self.execution.concurrent)
        env_vars['MIDSCENE_CONTINUE_ON_ERROR'] = str(self.execution.continue_on_error).lower()
        env_vars['MIDSCENE_GENERATE_REPORT'] = str(self.execution.generate_report).lower()
        
        return env_vars