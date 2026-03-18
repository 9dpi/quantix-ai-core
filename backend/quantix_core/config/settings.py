"""
Configuration settings for Quantix AI Core
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Signal Genius AI Core - Forex Signal Intelligence Engine"
    APP_VERSION: str = "4.7.2.5"
    MODEL_VERSION: str = "signal_genius_fx_v1.0"
    DEBUG: bool = False
    INSTANCE_NAME: str = "LOCAL-MACHINE"  # Override via Railway env var INSTANCE_NAME
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    TWELVE_DATA_API_KEY: Optional[str] = None
    
    # Heartbeat [T0+Δ] - v4.7.2.9: Responsive Mode
    MONITOR_INTERVAL_SECONDS: int = 60   # 1m interval (was 300s)
    WATCHER_CHECK_INTERVAL: int = 60    # 1m interval (was 30s)
    
    # Supabase Database
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # Telegram [T1]
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_ADMIN_CHAT_ID: Optional[str] = None
    
    # Database Tables
    TABLE_SIGNALS: str = "fx_signals"
    TABLE_VALIDATION: str = "fx_signal_validation"
    TABLE_LIFECYCLE: str = "fx_signal_lifecycle"
    TABLE_BACKTEST: str = "fx_backtest_patterns"
    TABLE_ANALYSIS_LOG: str = "fx_analysis_log"
    
    # Trading Rules
    TP_PIPS: float = 12.0                   # v4.7.2.9: 12 pips
    SL_PIPS: float = 10.0                   # v4.7.2.9: 10 pips (Relaxed for noise)
    MIN_RR: float = 1.2  # v4.7.2.9: Relaxed RR for hit rate
    MIN_CONFIDENCE: float = 0.70  # v4.6.3: Lowered to 70% for aggressive M5 scalping
    MAX_SIGNALS_PER_ASSET: int = 9999
    MAX_PENDING_DURATION_MINUTES: int = 35  # Entry window before auto-cancel
    MAX_TRADE_DURATION_MINUTES: int = 150   # v3.8: Adjusted from 180m to 150m per institutional audit
    MAX_LOT_SIZE_CAP: float = 0.20          # 🛡️ Safety Cap for 1:30 leverage accounts (£1000 balance)
    RISK_PERCENT: float = 2.0               # v4.6.2: Fixed 2% Risk Ratio per trade
    RISK_USD_PER_TRADE: float = 50.0        # Institutional Risk Model base per signal
    
    # 🔒 ANTI-BURST RULES
    MIN_RELEASE_INTERVAL_MINUTES: int = 5  # v4.7.2.9: Reduced to 5m for M5 Scalper responsiveness
    MAX_SIGNALS_PER_DAY: int = 50           # v4.7.2.9: Increased cap for scalper mode
    MAX_CONSECUTIVE_LOSSES: int = 5  # v4.7.2.9: Increased tolerance for choppy markets
    CIRCUIT_BREAKER_COOLDOWN_HOURS: float = 0.25 # v4.7.2.9: 15 min cooldown (was 1h)
    
    # 📈 v4.7.0: Stepped Trailing TP (Irfan Request)
    ENABLE_TRAILING_TP: bool = True
    TRAILING_TP_STEPS: list[float] = [5.0, 6.0, 7.0, 8.0, 9.0] # Pips
    TRAILING_TP_REVERSAL: float = 0.5                            # Pips reversal to close trade
    
    HEALTH_REPORT_INTERVAL_MINUTES: int = 480 # 8 hours (was 2 hours)
    
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
    ENABLE_LIVE_SIGNAL: bool = True
    ENABLE_BACKTEST: bool = True
    ENABLE_LEARNING: bool = True
    ENABLE_LAB_SIGNALS: bool = True
    WATCHER_OBSERVE_MODE: bool = False
    QUANTIX_PUBLIC_API_KEY: Optional[str] = None
    RAILWAY_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# Global settings instance
settings = Settings()
