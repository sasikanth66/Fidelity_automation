"""
Visualization module for Support and Resistance Indicator
Uses Plotly for interactive charts
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from support_resistance_indicator import SupportResistanceIndicator, SnR
from typing import List, Optional


class SRVisualizer:
    """Visualizer for Support and Resistance Indicator"""

    def __init__(self, indicator: SupportResistanceIndicator):
        self.indicator = indicator

    def plot(
        self,
        df: pd.DataFrame,
        title: str = "Support and Resistance Analysis",
        show_volume: bool = True,
        show_signals: bool = True,
        show_zones: bool = True,
        show_manipulation: bool = True,
        show_swings: bool = True,
        width: int = 1400,
        height: int = 800
    ):
        """
        Create interactive plot with support/resistance zones and signals

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with OHLCV data and calculated signals
        title : str
            Chart title
        show_volume : bool
            Show volume subplot
        show_signals : bool
            Show trading signals
        show_zones : bool
            Show support/resistance zones
        show_manipulation : bool
            Show manipulation zones
        show_swings : bool
            Show swing highs/lows
        width : int
            Chart width in pixels
        height : int
            Chart height in pixels
        """

        # Create subplots
        if show_volume:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=(title, 'Volume')
            )
        else:
            fig = make_subplots(rows=1, cols=1)
            fig.update_layout(title=title)

        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Price',
                increasing_line_color='#089981',
                decreasing_line_color='#f23645'
            ),
            row=1, col=1
        )

        # Add support/resistance zones
        if show_zones:
            self._add_zones(fig, df)

        # Add manipulation zones
        if show_manipulation:
            self._add_manipulation_zones(fig, df)

        # Add signals
        if show_signals:
            self._add_signals(fig, df)

        # Add swing highs/lows
        if show_swings:
            self._add_swings(fig, df)

        # Add volume
        if show_volume:
            colors = ['#089981' if df['close'].iloc[i] >= df['open'].iloc[i]
                     else '#f23645' for i in range(len(df))]

            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['volume'],
                    name='Volume',
                    marker_color=colors,
                    opacity=0.5
                ),
                row=2, col=1
            )

        # Update layout
        fig.update_layout(
            width=width,
            height=height,
            xaxis_rangeslider_visible=False,
            template='plotly_dark',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        fig.update_xaxes(title_text="Date", row=2 if show_volume else 1, col=1)
        fig.update_yaxes(title_text="Price", row=1, col=1)
        if show_volume:
            fig.update_yaxes(title_text="Volume", row=2, col=1)

        return fig

    def _add_zones(self, fig, df: pd.DataFrame):
        """Add support and resistance zones to chart"""
        zones = self.indicator.get_zones()

        # Add resistance zones
        for zone in zones['resistance']:
            if zone.right < len(df):
                x0 = df.index[zone.left]
                x1 = df.index[min(zone.right, len(df) - 1)]

                # Zone box
                fig.add_shape(
                    type="rect",
                    x0=x0, x1=x1,
                    y0=zone.bottom, y1=zone.top,
                    fillcolor="rgba(242, 54, 69, 0.15)",
                    line=dict(width=0),
                    layer="below",
                    row=1, col=1
                )

                # Level line
                fig.add_shape(
                    type="line",
                    x0=x0, x1=x1,
                    y0=zone.level, y1=zone.level,
                    line=dict(color="rgba(242, 54, 69, 0.5)", width=2),
                    row=1, col=1
                )

        # Add support zones
        for zone in zones['support']:
            if zone.right < len(df):
                x0 = df.index[zone.left]
                x1 = df.index[min(zone.right, len(df) - 1)]

                # Zone box
                fig.add_shape(
                    type="rect",
                    x0=x0, x1=x1,
                    y0=zone.bottom, y1=zone.top,
                    fillcolor="rgba(8, 153, 129, 0.15)",
                    line=dict(width=0),
                    layer="below",
                    row=1, col=1
                )

                # Level line
                fig.add_shape(
                    type="line",
                    x0=x0, x1=x1,
                    y0=zone.level, y1=zone.level,
                    line=dict(color="rgba(8, 153, 129, 0.5)", width=2),
                    row=1, col=1
                )

    def _add_manipulation_zones(self, fig, df: pd.DataFrame):
        """Add manipulation zones to chart"""
        zones = self.indicator.get_zones()

        # Check resistance zones for manipulation
        for zone in zones['resistance']:
            if zone.lq_left is not None and zone.lq_right is not None:
                if zone.lq_right < len(df):
                    x0 = df.index[zone.lq_left]
                    x1 = df.index[min(zone.lq_right, len(df) - 1)]

                    fig.add_shape(
                        type="rect",
                        x0=x0, x1=x1,
                        y0=zone.lq_bottom, y1=zone.lq_top,
                        fillcolor="rgba(255, 152, 0, 0.25)",
                        line=dict(color="rgba(255, 152, 0, 0.5)", width=1),
                        layer="below",
                        row=1, col=1
                    )

        # Check support zones for manipulation
        for zone in zones['support']:
            if zone.lq_left is not None and zone.lq_right is not None:
                if zone.lq_right < len(df):
                    x0 = df.index[zone.lq_left]
                    x1 = df.index[min(zone.lq_right, len(df) - 1)]

                    fig.add_shape(
                        type="rect",
                        x0=x0, x1=x1,
                        y0=zone.lq_bottom, y1=zone.lq_top,
                        fillcolor="rgba(41, 98, 255, 0.25)",
                        line=dict(color="rgba(41, 98, 255, 0.5)", width=1),
                        layer="below",
                        row=1, col=1
                    )

    def _add_signals(self, fig, df: pd.DataFrame):
        """Add trading signals to chart"""

        # Bullish breakouts
        breakout_bull = df[df['breakout_bullish']]
        if not breakout_bull.empty:
            fig.add_trace(
                go.Scatter(
                    x=breakout_bull.index,
                    y=breakout_bull['low'] * 0.998,
                    mode='markers+text',
                    name='Breakout (Bull)',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color='rgba(8, 153, 129, 0.8)',
                        line=dict(color='white', width=1)
                    ),
                    text=['▲B'] * len(breakout_bull),
                    textposition='bottom center',
                    textfont=dict(size=8, color='white'),
                    hovertemplate='Bullish Breakout<br>Price: %{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

        # Bearish breakouts
        breakout_bear = df[df['breakout_bearish']]
        if not breakout_bear.empty:
            fig.add_trace(
                go.Scatter(
                    x=breakout_bear.index,
                    y=breakout_bear['high'] * 1.002,
                    mode='markers+text',
                    name='Breakout (Bear)',
                    marker=dict(
                        symbol='triangle-down',
                        size=12,
                        color='rgba(242, 54, 69, 0.8)',
                        line=dict(color='white', width=1)
                    ),
                    text=['▼B'] * len(breakout_bear),
                    textposition='top center',
                    textfont=dict(size=8, color='white'),
                    hovertemplate='Bearish Breakout<br>Price: %{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

        # Bullish tests
        test_bull = df[df['test_bullish']]
        if not test_bull.empty:
            fig.add_trace(
                go.Scatter(
                    x=test_bull.index,
                    y=test_bull['low'] * 0.999,
                    mode='markers+text',
                    name='Test (Bull)',
                    marker=dict(
                        symbol='circle',
                        size=10,
                        color='rgba(41, 98, 255, 0.8)',
                        line=dict(color='white', width=1)
                    ),
                    text=['T'] * len(test_bull),
                    textposition='middle center',
                    textfont=dict(size=8, color='white'),
                    hovertemplate='Test of Support<br>Price: %{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

        # Bearish tests
        test_bear = df[df['test_bearish']]
        if not test_bear.empty:
            fig.add_trace(
                go.Scatter(
                    x=test_bear.index,
                    y=test_bear['high'] * 1.001,
                    mode='markers+text',
                    name='Test (Bear)',
                    marker=dict(
                        symbol='circle',
                        size=10,
                        color='rgba(224, 64, 251, 0.8)',
                        line=dict(color='white', width=1)
                    ),
                    text=['T'] * len(test_bear),
                    textposition='middle center',
                    textfont=dict(size=8, color='white'),
                    hovertemplate='Test of Resistance<br>Price: %{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

        # Bullish retests
        retest_bull = df[df['retest_bullish']]
        if not retest_bull.empty:
            fig.add_trace(
                go.Scatter(
                    x=retest_bull.index,
                    y=retest_bull['low'] * 0.999,
                    mode='markers+text',
                    name='Retest (Bull)',
                    marker=dict(
                        symbol='diamond',
                        size=10,
                        color='rgba(8, 153, 129, 0.8)',
                        line=dict(color='white', width=1)
                    ),
                    text=['R'] * len(retest_bull),
                    textposition='middle center',
                    textfont=dict(size=8, color='white'),
                    hovertemplate='Retest of Support<br>Price: %{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

        # Bearish retests
        retest_bear = df[df['retest_bearish']]
        if not retest_bear.empty:
            fig.add_trace(
                go.Scatter(
                    x=retest_bear.index,
                    y=retest_bear['high'] * 1.001,
                    mode='markers+text',
                    name='Retest (Bear)',
                    marker=dict(
                        symbol='diamond',
                        size=10,
                        color='rgba(242, 54, 69, 0.8)',
                        line=dict(color='white', width=1)
                    ),
                    text=['R'] * len(retest_bear),
                    textposition='middle center',
                    textfont=dict(size=8, color='white'),
                    hovertemplate='Retest of Resistance<br>Price: %{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

        # Bullish rejections
        reject_bull = df[df['rejection_bullish']]
        if not reject_bull.empty:
            fig.add_trace(
                go.Scatter(
                    x=reject_bull.index,
                    y=reject_bull['low'] * 0.998,
                    mode='markers',
                    name='Rejection (Bull)',
                    marker=dict(
                        symbol='star',
                        size=10,
                        color='rgba(8, 153, 129, 0.8)',
                        line=dict(color='white', width=1)
                    ),
                    hovertemplate='Rejection of Lower Prices<br>Price: %{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

        # Bearish rejections
        reject_bear = df[df['rejection_bearish']]
        if not reject_bear.empty:
            fig.add_trace(
                go.Scatter(
                    x=reject_bear.index,
                    y=reject_bear['high'] * 1.002,
                    mode='markers',
                    name='Rejection (Bear)',
                    marker=dict(
                        symbol='star',
                        size=10,
                        color='rgba(242, 54, 69, 0.8)',
                        line=dict(color='white', width=1)
                    ),
                    hovertemplate='Rejection of Higher Prices<br>Price: %{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

    def _add_swings(self, fig, df: pd.DataFrame):
        """Add swing high/low markers"""

        # Swing highs
        swing_high = df[df['swing_high']]
        if not swing_high.empty:
            fig.add_trace(
                go.Scatter(
                    x=swing_high.index,
                    y=swing_high['high'] * 1.003,
                    mode='markers',
                    name='Swing High',
                    marker=dict(
                        symbol='diamond',
                        size=8,
                        color='rgba(242, 54, 69, 0.6)',
                        line=dict(color='rgba(242, 54, 69, 0.8)', width=1)
                    ),
                    hovertemplate='Swing High<br>Price: %{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

        # Swing lows
        swing_low = df[df['swing_low']]
        if not swing_low.empty:
            fig.add_trace(
                go.Scatter(
                    x=swing_low.index,
                    y=swing_low['low'] * 0.997,
                    mode='markers',
                    name='Swing Low',
                    marker=dict(
                        symbol='diamond',
                        size=8,
                        color='rgba(8, 153, 129, 0.6)',
                        line=dict(color='rgba(8, 153, 129, 0.8)', width=1)
                    ),
                    hovertemplate='Swing Low<br>Price: %{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

    def save_html(self, fig, filename: str = "sr_analysis.html"):
        """Save interactive chart to HTML file"""
        fig.write_html(filename)
        print(f"Chart saved to {filename}")

    def show(self, fig):
        """Display interactive chart"""
        fig.show()
