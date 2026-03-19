"""
Configuration settings for Quantix AI Core
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Signal Genius AI Core - Forex Signal Intelligence Engine"
    APP_VERSION: str = "4.7.3"
    MODEL_VERSION: str = "signal_genius_fx_v1.0"
    DEBUG: bool = False
    INSTANCE_NAME: str = "LOCAL-MACHINE"  # Override via Railway env var INSTANCE_NAME
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    TWELVE_DATA_API_KEY: Optional[str] = None
    
    # Heartbeat [T0+Δ] - v4.7.3: Quality Mode
    MONITOR_INTERVAL_SECONDS: int = 60   # 1m interval
    WATCHER_CHECK_INTERVAL: int = 60    # 1m interval
    
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
    TP_PIPS: float = 10.0                   # v4.7.3: RESTORED 10 pips (was 12)
    SL_PIPS: float = 5.0                    # v4.7.3: RESTORED 5 pips (was 10) -> RR = 2:1
    MIN_RR: float = 2.0  # v4.7.3: Strict 2:1 minimum
    MIN_CONFIDENCE: float = 0.70  # v4.6.3: Lowered to 70% for aggressive M5 scalping
    MAX_SIGNALS_PER_ASSET: int = 9999
    MAX_PENDING_DURATION_MINUTES: int = 35  # Entry window before auto-cancel
    MAX_TRADE_DURATION_MINUTES: int = 150   # v3.8: Adjusted from 180m to 150m per institutional audit
    MAX_LOT_SIZE_CAP: float = 0.20          # 🛡️ Safety Cap for 1:30 leverage accounts (£1000 balance)
    RISK_PERCENT: float = 2.0               # v4.6.2: Fixed 2% Risk Ratio per trade
    RISK_USD_PER_TRADE: float = 50.0        # Institutional Risk Model base per signal
    
    # 🔒 ANTI-BURST RULES
    MIN_RELEASE_INTERVAL_MINUTES: int = 15  # v4.7.3: Increased from 5 to 15m to prevent duplicate clusters
    MAX_SIGNALS_PER_DAY: int = 20           # v4.7.3: Reduced for quality over quantity
    MAX_CONSECUTIVE_LOSSES: int = 3  # v4.7.3: Tighter circuit breaker
    CIRCUIT_BREAKER_COOLDOWN_HOURS: float = 1.0 # v4.7.3: 1 hour cooldown (was 15 min)
    
    # 📈 v4.7.0: Stepped Trailing TP (Irfan Request)
    ENABLE_TRAILING_TP: bool = True
    TRAILING_TP_STEPS: list[float] = [5.0, 6.0, 7.0, 8.0, 9.0] # Pips
    TRAILING_TP_REVERSAL: float = 1.0                            # v4.7.3: Relaxed from 0.5 to 1.0 pips to reduce false closes
    
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
