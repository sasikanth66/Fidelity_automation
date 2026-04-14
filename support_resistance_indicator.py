"""
Support and Resistance Signals MTF Indicator
Translated from Pine Script v5 to Python

This work is licensed under a Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)
https://creativecommons.org/licenses/by-nc-sa/4.0/
© LuxAlgo
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')


@dataclass
class Bar:
    """Bar properties with their values"""
    o: float  # open
    h: float  # high
    l: float  # low
    c: float  # close
    v: float  # volume
    i: int    # index


@dataclass
class PivotPoint:
    """Store pivot high/low and index data"""
    x: int = 0          # last pivot bar index
    x1: int = 0         # previous pivot bar index
    h: float = 0.0      # last pivot high
    h1: float = 0.0     # previous pivot high
    l: float = 0.0      # last pivot low
    l1: float = 0.0     # previous pivot low
    hx: bool = False    # pivot high cross status
    lx: bool = False    # pivot low cross status


@dataclass
class SnR:
    """Stores support and resistance zone data and signals"""
    left: int           # left boundary (start index)
    right: int          # right boundary (end index)
    top: float          # top price
    bottom: float       # bottom price
    level: float        # key level price
    is_resistance: bool # True for resistance, False for support
    b: bool = False     # breakout status
    t: bool = False     # test status
    r: bool = False     # retest status
    l: bool = False     # liquidation status
    m: float = 0.0      # margin
    lq_top: Optional[float] = None      # manipulation zone top
    lq_bottom: Optional[float] = None   # manipulation zone bottom
    lq_left: Optional[int] = None       # manipulation zone left
    lq_right: Optional[int] = None      # manipulation zone right


class SupportResistanceIndicator:
    """
    Support and Resistance Signals Multi-Timeframe Indicator

    Parameters
    ----------
    detection_length : int
        Length for pivot detection (default: 15)
    sr_margin : float
        Support/Resistance margin multiplier (default: 2.0)
    mn_margin : float
        Manipulation zone margin multiplier (default: 1.3)
    avoid_false_breakouts : bool
        Filter false breakouts (default: True)
    check_historical_sr : bool
        Check previous historical S&R zones (default: True)
    show_manipulation : bool
        Show manipulation zones (default: True)
    """

    def __init__(
        self,
        detection_length: int = 15,
        sr_margin: float = 2.0,
        mn_margin: float = 1.3,
        avoid_false_breakouts: bool = True,
        check_historical_sr: bool = True,
        show_manipulation: bool = True
    ):
        self.detection_length = detection_length
        self.sr_margin = sr_margin
        self.mn_margin = mn_margin
        self.avoid_false_breakouts = avoid_false_breakouts
        self.check_historical_sr = check_historical_sr
        self.show_manipulation = show_manipulation

        # Storage for support and resistance zones
        self.resistance_zones: List[SnR] = []
        self.support_zones: List[SnR] = []

        # Market structure shift tracker
        self.mss = 0  # 1 for bullish, -1 for bearish

        # Pivot tracker
        self.pivot = PivotPoint()

        # Signals storage
        self.signals = {
            'breakout_bullish': [],
            'breakout_bearish': [],
            'test_bullish': [],
            'test_bearish': [],
            'retest_bullish': [],
            'retest_bearish': [],
            'rejection_bullish': [],
            'rejection_bearish': [],
            'swing_high': [],
            'swing_low': []
        }

    def calculate_atr(self, df: pd.DataFrame, period: int = 17) -> pd.Series:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def find_pivot_high(self, df: pd.DataFrame, idx: int, left: int, right: int) -> Optional[float]:
        """Find pivot high at given index"""
        if idx < left or idx + right >= len(df):
            return None

        center_high = df['high'].iloc[idx]

        # Check left side
        for i in range(1, left + 1):
            if idx - i < 0 or df['high'].iloc[idx - i] >= center_high:
                return None

        # Check right side
        for i in range(1, right + 1):
            if idx + i >= len(df) or df['high'].iloc[idx + i] >= center_high:
                return None

        return center_high

    def find_pivot_low(self, df: pd.DataFrame, idx: int, left: int, right: int) -> Optional[float]:
        """Find pivot low at given index"""
        if idx < left or idx + right >= len(df):
            return None

        center_low = df['low'].iloc[idx]

        # Check left side
        for i in range(1, left + 1):
            if idx - i < 0 or df['low'].iloc[idx - i] <= center_low:
                return None

        # Check right side
        for i in range(1, right + 1):
            if idx + i >= len(df) or df['low'].iloc[idx + i] <= center_low:
                return None

        return center_low

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate support/resistance zones and signals

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with OHLCV data (columns: open, high, low, close, volume)

        Returns
        -------
        pd.DataFrame
            Original DataFrame with added signal columns
        """
        # Reset state
        self.resistance_zones = []
        self.support_zones = []
        self.mss = 0
        self.pivot = PivotPoint()
        for key in self.signals:
            self.signals[key] = []

        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")

        # Add volume if not present
        if 'volume' not in df.columns:
            df['volume'] = 0

        # Calculate indicators
        df['atr'] = self.calculate_atr(df)
        df['volume_sma'] = df['volume'].rolling(window=17).mean()

        # Calculate highest high and lowest low for range
        df['highest'] = df['high'].rolling(window=self.detection_length).max()
        df['lowest'] = df['low'].rolling(window=self.detection_length).min()

        # Process each bar
        for i in range(self.detection_length, len(df) - self.detection_length):
            self._process_bar(df, i)

        # Convert signals to DataFrame columns
        df = self._add_signal_columns(df)

        return df

    def _process_bar(self, df: pd.DataFrame, idx: int):
        """Process a single bar for pivot detection and signal generation"""

        # Find pivot high
        pp_h = self.find_pivot_high(df, idx, self.detection_length, self.detection_length)

        if pp_h is not None:
            self._handle_pivot_high(df, idx, pp_h)

        # Find pivot low
        pp_l = self.find_pivot_low(df, idx, self.detection_length, self.detection_length)

        if pp_l is not None:
            self._handle_pivot_low(df, idx, pp_l)

        # Check for market structure shifts
        current_idx = idx + self.detection_length
        if current_idx < len(df):
            close = df['close'].iloc[current_idx]
            prev_close = df['close'].iloc[current_idx - 1]

            # Bullish structure shift
            if self.pivot.h > 0 and close > self.pivot.h and prev_close > self.pivot.h and not self.pivot.hx:
                self.pivot.hx = True
                self.mss = 1

            # Bearish structure shift
            if self.pivot.l > 0 and close < self.pivot.l and prev_close < self.pivot.l and not self.pivot.lx:
                self.pivot.lx = True
                self.mss = -1

        # Update existing zones and detect signals
        self._update_zones_and_signals(df, idx + self.detection_length)

    def _handle_pivot_high(self, df: pd.DataFrame, idx: int, pp_h: float):
        """Handle detection of a pivot high"""
        # Update pivot data
        self.pivot.h1 = self.pivot.h
        self.pivot.h = pp_h
        self.pivot.x1 = self.pivot.x
        self.pivot.x = idx
        self.pivot.hx = False

        # Calculate zone boundaries - RESISTANCE extends DOWNWARD from pivot high
        # This matches the Pine Script: top = pp.h, bottom = pp.h * (1 - margin)
        highest = df['highest'].iloc[idx]
        lowest = df['lowest'].iloc[idx]
        margin = (highest - lowest) / highest
        
        # Resistance zone: pivot high is the TOP, zone extends DOWN
        top = pp_h
        bottom = pp_h * (1 - margin * 0.17 * self.sr_margin)

        # Create new resistance zone
        new_zone = SnR(
            left=idx,
            right=idx + self.detection_length,
            top=top,
            bottom=bottom,
            level=pp_h,
            is_resistance=True,
            m=margin
        )

        # Check if we should add this zone
        should_add = True

        if len(self.resistance_zones) > 0:
            last_r = self.resistance_zones[0]

            # Check if price is within existing zone
            if not (pp_h < last_r.bottom * (1 - last_r.m * 0.17 * self.sr_margin) or
                   pp_h > last_r.top * (1 + last_r.m * 0.17 * self.sr_margin)):
                # Extend existing zone
                last_r.right = idx + self.detection_length
                should_add = False

        if should_add:
            self.resistance_zones.insert(0, new_zone)

        # Track swing high
        if self.pivot.h1 > 0:
            swing_type = "Higher High" if pp_h > self.pivot.h1 else "Lower High" if pp_h < self.pivot.h1 else "Equal High"
            self.signals['swing_high'].append({
                'index': idx,
                'price': pp_h,
                'type': swing_type
            })

    def _handle_pivot_low(self, df: pd.DataFrame, idx: int, pp_l: float):
        """Handle detection of a pivot low"""
        # Update pivot data
        self.pivot.l1 = self.pivot.l
        self.pivot.l = pp_l
        self.pivot.x1 = self.pivot.x
        self.pivot.x = idx
        self.pivot.lx = False

        # Calculate zone boundaries - SUPPORT extends UPWARD from pivot low
        # This matches the Pine Script: bottom = pp.l, top = pp.l * (1 + margin)
        highest = df['highest'].iloc[idx]
        lowest = df['lowest'].iloc[idx]
        margin = (highest - lowest) / highest
        
        # Support zone: pivot low is the BOTTOM, zone extends UP
        bottom = pp_l
        top = pp_l * (1 + margin * 0.17 * self.sr_margin)

        # Create new support zone
        new_zone = SnR(
            left=idx,
            right=idx + self.detection_length,
            top=top,
            bottom=bottom,
            level=pp_l,
            is_resistance=False,
            m=margin
        )

        # Check if we should add this zone
        should_add = True

        if len(self.support_zones) > 0:
            last_s = self.support_zones[0]

            # Check if price is within existing zone
            if not (pp_l < last_s.bottom * (1 - last_s.m * 0.17 * self.sr_margin) or
                   pp_l > last_s.top * (1 + last_s.m * 0.17 * self.sr_margin)):
                # Extend existing zone
                last_s.right = idx + self.detection_length
                should_add = False

        if should_add:
            self.support_zones.insert(0, new_zone)

        # Track swing low
        if self.pivot.l1 > 0:
            swing_type = "Lower Low" if pp_l < self.pivot.l1 else "Higher Low" if pp_l > self.pivot.l1 else "Equal Low"
            self.signals['swing_low'].append({
                'index': idx,
                'price': pp_l,
                'type': swing_type
            })

    def _update_zones_and_signals(self, df: pd.DataFrame, idx: int):
        """Update zones and detect trading signals"""
        if idx >= len(df):
            return

        current_bar = {
            'o': df['open'].iloc[idx],
            'h': df['high'].iloc[idx],
            'l': df['low'].iloc[idx],
            'c': df['close'].iloc[idx],
            'v': df['volume'].iloc[idx]
        }

        prev_bar = {
            'o': df['open'].iloc[idx-1] if idx > 0 else current_bar['o'],
            'h': df['high'].iloc[idx-1] if idx > 0 else current_bar['h'],
            'l': df['low'].iloc[idx-1] if idx > 0 else current_bar['l'],
            'c': df['close'].iloc[idx-1] if idx > 0 else current_bar['c']
        }

        # Check resistance zones
        for i, zone in enumerate(self.resistance_zones[:2]):  # Check most recent 2 zones
            self._check_resistance_zone(zone, current_bar, prev_bar, idx, i == 0)

        # Check support zones
        for i, zone in enumerate(self.support_zones[:2]):  # Check most recent 2 zones
            self._check_support_zone(zone, current_bar, prev_bar, idx, i == 0)

        # Check for rejection patterns
        self._check_rejections(df, idx)

    def _check_resistance_zone(self, zone: SnR, current_bar: dict, prev_bar: dict, idx: int, is_latest: bool):
        """Check resistance zone for signals"""

        # Bullish breakout
        if self.avoid_false_breakouts:
            if prev_bar['c'] > zone.top * (1 + zone.m * 0.17) and not zone.b:
                zone.b = True
                zone.right = idx - 1
                self.signals['breakout_bullish'].append({'index': idx - 1, 'price': prev_bar['c']})

                # Flip to support
                new_support = SnR(
                    left=idx - 1,
                    right=idx + 1,
                    top=zone.top,
                    bottom=zone.bottom,
                    level=zone.bottom,
                    is_resistance=False,
                    m=zone.m
                )
                self.support_zones.insert(0, new_support)
        else:
            if prev_bar['c'] > zone.top and not zone.b:
                zone.b = True
                zone.right = idx - 1
                self.signals['breakout_bullish'].append({'index': idx - 1, 'price': prev_bar['c']})

                # Flip to support
                new_support = SnR(
                    left=idx - 1,
                    right=idx + 1,
                    top=zone.top,
                    bottom=zone.bottom,
                    level=zone.bottom,
                    is_resistance=False,
                    m=zone.m
                )
                self.support_zones.insert(0, new_support)

        # Retest after support breakout
        if (len(self.support_zones) > 0 and self.support_zones[0].b and
            prev_bar['o'] < zone.top and prev_bar['h'] > zone.bottom and
            prev_bar['c'] < zone.bottom and not zone.r and idx - 1 != zone.left):
            zone.r = True
            zone.right = idx
            self.signals['retest_bearish'].append({'index': idx - 1, 'price': prev_bar['h']})

        # Test of resistance
        elif (prev_bar['h'] > zone.bottom and prev_bar['c'] < zone.top and
              current_bar['c'] < zone.top and not zone.t and not zone.r and
              not zone.b and idx - 1 != zone.left):
            if len(self.support_zones) == 0 or not self.support_zones[0].b:
                zone.t = True
                zone.right = idx
                self.signals['test_bearish'].append({'index': idx - 1, 'price': prev_bar['h']})

        # Extend zone if price is still respecting it
        elif current_bar['h'] > zone.bottom * (1 - zone.m * 0.17) and not zone.b:
            if current_bar['h'] > zone.bottom:
                zone.right = idx

        # Manipulation zone detection
        if self.show_manipulation and is_latest:
            if (current_bar['h'] > zone.top and
                current_bar['c'] <= zone.top * (1 + zone.m * 0.17 * self.mn_margin) and
                not zone.l and idx == zone.right):

                if zone.lq_right is not None and zone.lq_right + self.detection_length > idx:
                    zone.lq_right = idx + 1
                    zone.lq_top = min(max(current_bar['h'], zone.lq_top), zone.top * (1 + zone.m * 0.17 * self.mn_margin))
                else:
                    zone.lq_left = idx - 1
                    zone.lq_right = idx + 1
                    zone.lq_top = min(current_bar['h'], zone.top * (1 + zone.m * 0.17 * self.mn_margin))
                    zone.lq_bottom = zone.top

                zone.l = True

            elif zone.l and (current_bar['c'] >= zone.top * (1 + zone.m * 0.17 * self.mn_margin) or
                            current_bar['c'] < zone.bottom):
                zone.l = False

    def _check_support_zone(self, zone: SnR, current_bar: dict, prev_bar: dict, idx: int, is_latest: bool):
        """Check support zone for signals"""

        # Bearish breakout
        if self.avoid_false_breakouts:
            if prev_bar['c'] < zone.bottom * (1 - zone.m * 0.17) and not zone.b:
                zone.b = True
                zone.right = idx - 1
                self.signals['breakout_bearish'].append({'index': idx - 1, 'price': prev_bar['c']})

                # Flip to resistance
                new_resistance = SnR(
                    left=idx - 1,
                    right=idx + 1,
                    top=zone.top,
                    bottom=zone.bottom,
                    level=zone.top,
                    is_resistance=True,
                    m=zone.m
                )
                self.resistance_zones.insert(0, new_resistance)
        else:
            if prev_bar['c'] < zone.bottom and not zone.b:
                zone.b = True
                zone.right = idx - 1
                self.signals['breakout_bearish'].append({'index': idx - 1, 'price': prev_bar['c']})

                # Flip to resistance
                new_resistance = SnR(
                    left=idx - 1,
                    right=idx + 1,
                    top=zone.top,
                    bottom=zone.bottom,
                    level=zone.top,
                    is_resistance=True,
                    m=zone.m
                )
                self.resistance_zones.insert(0, new_resistance)

        # Retest after resistance breakout
        if (len(self.resistance_zones) > 0 and self.resistance_zones[0].b and
            prev_bar['o'] > zone.bottom and prev_bar['l'] < zone.top and
            prev_bar['c'] > zone.top and not zone.r and idx - 1 != zone.left):
            zone.r = True
            zone.right = idx
            self.signals['retest_bullish'].append({'index': idx - 1, 'price': prev_bar['l']})

        # Test of support
        elif (prev_bar['l'] < zone.top and prev_bar['c'] > zone.bottom and
              current_bar['c'] > zone.bottom and not zone.t and not zone.b and
              idx - 1 != zone.left):
            if len(self.resistance_zones) == 0 or not self.resistance_zones[0].b:
                zone.t = True
                zone.right = idx
                self.signals['test_bullish'].append({'index': idx - 1, 'price': prev_bar['l']})

        # Extend zone if price is still respecting it
        elif current_bar['l'] < zone.top * (1 + zone.m * 0.17) and not zone.b:
            if current_bar['l'] < zone.top:
                zone.right = idx

        # Manipulation zone detection
        if self.show_manipulation and is_latest:
            if (current_bar['l'] < zone.bottom and
                current_bar['c'] >= zone.bottom * (1 - zone.m * 0.17 * self.mn_margin) and
                not zone.l and idx == zone.right):

                if zone.lq_right is not None and zone.lq_right + self.detection_length > idx:
                    zone.lq_right = idx + 1
                    zone.lq_bottom = max(min(current_bar['l'], zone.lq_bottom), zone.bottom * (1 - zone.m * 0.17 * self.mn_margin))
                else:
                    zone.lq_left = idx - 1
                    zone.lq_right = idx + 1
                    zone.lq_bottom = max(current_bar['l'], zone.bottom * (1 - zone.m * 0.17 * self.mn_margin))
                    zone.lq_top = zone.bottom

                zone.l = True

            elif zone.l and (current_bar['c'] <= zone.bottom * (1 - zone.m * 0.17 * self.mn_margin) or
                            current_bar['c'] > zone.top):
                zone.l = False

    def _check_rejections(self, df: pd.DataFrame, idx: int):
        """Check for price rejection patterns"""
        if idx < 1 or idx >= len(df):
            return

        prev_bar = df.iloc[idx - 1]
        atr = prev_bar['atr']
        volume_sma = prev_bar['volume_sma']

        # Long lower shadow (bullish rejection)
        lower_shadow = abs(prev_bar['low'] - min(prev_bar['open'], prev_bar['close']))
        is_long_lower_shadow = lower_shadow >= 1.618 * atr

        # Long upper shadow (bearish rejection)
        upper_shadow = abs(prev_bar['high'] - max(prev_bar['open'], prev_bar['close']))
        is_long_upper_shadow = upper_shadow >= 1.618 * atr

        # High volume
        is_high_volume = prev_bar['volume'] >= 1.618 * volume_sma

        if is_long_lower_shadow and is_high_volume:
            self.signals['rejection_bullish'].append({
                'index': idx - 1,
                'price': prev_bar['low']
            })

        if is_long_upper_shadow and is_high_volume:
            self.signals['rejection_bearish'].append({
                'index': idx - 1,
                'price': prev_bar['high']
            })

    def _add_signal_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add signal columns to DataFrame"""
        # Initialize all signal columns
        for signal_type in self.signals.keys():
            df[signal_type] = False
            df[f'{signal_type}_price'] = np.nan

        # Populate signal columns
        for signal_type, signal_list in self.signals.items():
            for signal in signal_list:
                idx = signal['index']
                if idx < len(df):
                    df.loc[df.index[idx], signal_type] = True
                    df.loc[df.index[idx], f'{signal_type}_price'] = signal['price']

        return df

    def get_zones(self, current_index: int = None, max_bars_inactive: int = None) -> Dict[str, List[SnR]]:
        """
        Get current support and resistance zones
        
        Note: Unlike our previous implementation, this now matches the Pine Script behavior
        where zones persist indefinitely but stop extending when price no longer touches them.
        This provides better historical context and matches TradingView exactly.
        
        Parameters
        ----------
        current_index : int, optional
            Not used anymore - kept for backward compatibility
        max_bars_inactive : int, optional
            Not used anymore - kept for backward compatibility
            
        Returns
        -------
        Dict[str, List[SnR]]
            Dictionary with 'resistance' and 'support' zone lists
        """
        # Return all zones without time-based filtering (matches Pine Script)
        return {
            'resistance': self.resistance_zones,
            'support': self.support_zones
        }


