"""
Dukascopy package initialization
"""

from quantix_core.ingestion.dukascopy.client import DukascopyClient
from quantix_core.ingestion.dukascopy.tick_parser import TickParser, Tick
from quantix_core.ingestion.dukascopy.resampler import CandleResampler, Candle
from quantix_core.ingestion.dukascopy.fetcher import DukascopyFetcher, DukascopyFetcherError

__all__ = [
    'DukascopyClient',
    'TickParser',
    'Tick',
    'CandleResampler',
    'Candle',
    'DukascopyFetcher',
    'DukascopyFetcherError'
]
