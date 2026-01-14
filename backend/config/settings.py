"""
Configuration settings for Quantix AI Core
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Quantix AI Core - Forex Signal Intelligence Engine"
    APP_VERSION: str = "1.0.0"
    MODEL_VERSION: str = "quantix_fx_v1.0"
    DEBUG: bool = False
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # Supabase Database
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # Database Tables
    TABLE_SIGNALS: str = "fx_signals"
    TABLE_VALIDATION: str = "fx_signal_validation"
    TABLE_LIFECYCLE: str = "fx_signal_lifecycle"
    TABLE_BACKTEST: str = "fx_backtest_patterns"
    
    # Trading Rules
    MIN_RISK_REWARD: float = 1.2
    MIN_CONFIDENCE: float = 0.75
    MAX_SIGNALS_PER_ASSET: int = 3
    
    # Session Times (UTC)
    TOKYO_OPEN: str = "00:00"
    TOKYO_CLOSE: str = "09:00"
    LONDON_OPEN: str = "08:00"
    LONDON_CLOSE: str = "17:00"
    NY_OPEN: str = "13:00"
    NY_CLOSE: str = "22:00"
    
    # Confidence Grading Thresholds
    CONFIDENCE_A_PLUS: float = 0.95
    CONFIDENCE_A: float = 0.90
    CONFIDENCE_B_PLUS: float = 0.85
    CONFIDENCE_B: float = 0.80
    
    # Agent Weights (for probability calculation)
    WEIGHT_STRUCTURE: float = 0.30
    WEIGHT_SESSION: float = 0.25
    WEIGHT_VOLATILITY: float = 0.20
    WEIGHT_HISTORICAL: float = 0.25
    
    # Invalidation Rules
    VOLATILITY_SPIKE_THRESHOLD: float = 2.0  # 2x normal ATR
    NEWS_PROXIMITY_MINUTES: int = 30
    
    # Feature Flags
    QUANTIX_MODE: str = "INTERNAL"
    ENABLE_LIVE_SIGNAL: bool = False
    ENABLE_BACKTEST: bool = True
    ENABLE_LEARNING: bool = True
    ENABLE_LAB_SIGNALS: bool = True
    QUANTIX_PUBLIC_API_KEY: str = "quantix_dev_beta_2026"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
