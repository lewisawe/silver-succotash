"""
AWS Operations Command Center - Configuration Management
Centralized configuration with environment variable support and validation.
"""

from dataclasses import dataclass, field
import os
from typing import Dict, List, Optional

@dataclass
class Settings:
    """Application settings with environment variable defaults"""
    
    # AWS Configuration
    aws_region: str = field(default_factory=lambda: os.getenv('AWS_REGION', 'us-east-1'))
    aws_profiles: Dict[str, str] = field(default_factory=lambda: {
        'management': os.getenv('AWS_PROFILE_MANAGEMENT', 'default'),
        'crummyfun': os.getenv('AWS_PROFILE_CRUMMYFUN', 'simi-ops'),
        'achamin': os.getenv('AWS_PROFILE_ACHAMIN', 'achamin-profile')
    })
    
    # Agent Configuration
    max_retries: int = field(default_factory=lambda: int(os.getenv('MAX_RETRIES', '3')))
    cache_ttl: int = field(default_factory=lambda: int(os.getenv('CACHE_TTL', '300')))
    parallel_workers: int = field(default_factory=lambda: int(os.getenv('PARALLEL_WORKERS', '5')))
    request_timeout: int = field(default_factory=lambda: int(os.getenv('REQUEST_TIMEOUT', '30')))
    
    # API Configuration
    api_host: str = field(default_factory=lambda: os.getenv('API_HOST', 'localhost'))
    api_port: int = field(default_factory=lambda: int(os.getenv('API_PORT', '8000')))
    debug_mode: bool = field(default_factory=lambda: os.getenv('DEBUG', 'false').lower() == 'true')
    
    # Logging Configuration
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    log_format: str = field(default_factory=lambda: os.getenv('LOG_FORMAT', 'json'))
    
    # Cost Analysis Configuration
    cost_analysis_days: int = field(default_factory=lambda: int(os.getenv('COST_ANALYSIS_DAYS', '30')))
    forecast_days: int = field(default_factory=lambda: int(os.getenv('FORECAST_DAYS', '90')))
    
    # Operations Configuration
    resource_scan_timeout: int = field(default_factory=lambda: int(os.getenv('RESOURCE_SCAN_TIMEOUT', '60')))
    max_resources_per_service: int = field(default_factory=lambda: int(os.getenv('MAX_RESOURCES_PER_SERVICE', '1000')))
    
    def validate(self) -> None:
        """Validate configuration settings"""
        errors = []
        
        # AWS Region validation
        if not self.aws_region:
            errors.append("AWS_REGION is required")
        
        # Numeric validations
        if self.max_retries < 1:
            errors.append("MAX_RETRIES must be >= 1")
        
        if self.cache_ttl < 0:
            errors.append("CACHE_TTL must be >= 0")
        
        if self.parallel_workers < 1:
            errors.append("PARALLEL_WORKERS must be >= 1")
        
        if self.api_port < 1 or self.api_port > 65535:
            errors.append("API_PORT must be between 1 and 65535")
        
        if self.request_timeout < 1:
            errors.append("REQUEST_TIMEOUT must be >= 1")
        
        # Log level validation
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of {valid_log_levels}")
        
        # Date range validations
        if self.cost_analysis_days < 1:
            errors.append("COST_ANALYSIS_DAYS must be >= 1")
        
        if self.forecast_days < 1:
            errors.append("FORECAST_DAYS must be >= 1")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def get_aws_profile(self, account_type: str) -> Optional[str]:
        """Get AWS profile for account type"""
        return self.aws_profiles.get(account_type)
    
    def get_enabled_profiles(self) -> List[str]:
        """Get list of enabled AWS profiles"""
        return [profile for profile in self.aws_profiles.values() if profile]

# Global settings instance
try:
    settings = Settings()
    settings.validate()
except Exception as e:
    print(f"Configuration error: {e}")
    # Use default settings if validation fails
    settings = Settings()
    print("Using default configuration settings")

# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    debug_mode: bool = True
    log_level: str = 'DEBUG'
    cache_ttl: int = 60  # Shorter cache for development

class ProductionSettings(Settings):
    """Production environment settings"""
    debug_mode: bool = False
    log_level: str = 'INFO'
    max_retries: int = 5
    cache_ttl: int = 600  # Longer cache for production

def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    if env == 'production':
        return ProductionSettings()
    else:
        return DevelopmentSettings()
