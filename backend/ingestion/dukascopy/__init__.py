"""
Dukascopy package initialization
"""

from ingestion.dukascopy.client import DukascopyClient
from ingestion.dukascopy.tick_parser import TickParser, Tick
from ingestion.dukascopy.resampler import CandleResampler, Candle

__all__ = [
    'DukascopyClient',
    'TickParser',
    'Tick',
    'CandleResampler',
    'Candle'
]
