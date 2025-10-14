"""
Application pages for MT5 Trading Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, Any, List
from ...ui.components.ui_components import (
    chart_component, data_table_component, 
    magic_description_component, status_component
)
from ...utils.helpers import data_utils
from ...config.settings import Config, UIConfig


class OpenPositionsPage:
    """Open Positions page"""
    
    @staticmethod
    def render(open_profits: Dict[str, Any], account_id: str, 
              db_manager: Any, balance_start: float, 
              account_info_open: Any = None):
        """Render open positions page"""
        st.subheader("Open Positions")
        
        if not open_profits:
            st.info("No open positions data available.")
            return
        
        detailed = open_profits["detailed"]
        by_magic = open_profits["by_magic"]
        total_floating = open_profits["total_floating"]
        
        current_balance = account_info_open.balance if account_info_open else balance_start
        
        magics_open = list(by_magic.keys()) if by_magic else []
        descriptions = db_manager.get_all_magic_descriptions(account_id)
        labels_open = data_utils.create_labels_dict(magics_open, descriptions, account_id)
        
        st.write(f"Current Floating P/L: {total_floating:.2f}")
        
        # Create and display table
        df_open_results = data_table_component.create_open_positions_table(
            magics_open, by_magic, labels_open, current_balance
        )
        
        # Sort options
        sort_options = UIConfig.SORT_OPTIONS["open_positions"]
        sort_option_open = st.selectbox("Sort by", sort_options, index=0)
        df_open_results = data_table_component.sort_table(df_open_results, sort_option_open)
        
        # Create chart
        fig_open = chart_component.create_bar_chart(
            df_open_results, 'Floating', 'Label', 'Floating'
        )
        
        # Add summary annotation
        summary_text, color = status_component.show_floating_summary(
            total_floating, current_balance
        )
        chart_component.add_annotation(fig_open, summary_text, color=color, y=1)
        
        # Update layout
        height = max(Config.MIN_CHART_HEIGHT, len(df_open_results) * Config.CHART_HEIGHT_MULTIPLIER)
        chart_component.update_layout(fig_open, height=height)
        
        st.plotly_chart(fig_open, use_container_width=True)
        
        # Drill-down section
        selected_magic_open = st.selectbox(
            "Select Magic for Details (None for Overview)", 
            [None] + magics_open
        )
        
        if selected_magic_open is not None and selected_magic_open in detailed:
            OpenPositionsPage._render_magic_breakdown(
                selected_magic_open, detailed, labels_open
            )
    
    @staticmethod
    def _render_magic_breakdown(selected_magic: int, detailed: Dict, labels_open: Dict):
        """Render breakdown for selected magic"""
        symbols_for_magic = detailed[selected_magic]
        st.subheader(f"Breakdown for Magic {selected_magic} ({labels_open[selected_magic]})")
        
        # Flatten data for display
        breakdown_data = []
        for symbol, types in symbols_for_magic.items():
            for type_str, profit in types.items():
                breakdown_data.append({
                    'Symbol': symbol,
                    'Type': type_str,
                    'Floating': profit
                })
        
        if breakdown_data:
            df_breakdown = pd.DataFrame(breakdown_data)
            df_breakdown['Label'] = df_breakdown['Symbol'] + " - " + df_breakdown['Type']
            
            # Create breakdown chart
            fig_breakdown = chart_component.create_bar_chart(
                df_breakdown, 'Floating', 'Label', 'Floating'
            )
            
            height = max(Config.MIN_CHART_HEIGHT, len(df_breakdown) * Config.CHART_HEIGHT_MULTIPLIER)
            chart_component.update_layout(fig_breakdown, height=height)
            
            st.plotly_chart(fig_breakdown, use_container_width=True)
            
            # Display table
            st.dataframe(df_breakdown[['Symbol', 'Type', 'Floating']].round(2))


class ResultsPage:
    """Results page"""
    
    @staticmethod
    def render(magic_profits: Dict[str, Any], account_id: str, 
              db_manager: Any, balance_start: float, custom_text: str,
              display_time_in: Any, display_time_out: Any):
        """Render results page"""
        st.subheader("Results")
        
        st.write("Period:")
        st.write(f"From {display_time_in} to {display_time_out}")
        
        magic_total_sums = magic_profits["Total by Magic"]
        total_summ = magic_profits["Summ"]
        
        st.write(f"Total Result: {total_summ:.2f}")
        
        magics = list(magic_total_sums.keys())
        descriptions = db_manager.get_all_magic_descriptions(account_id)
        labels_tab1 = data_utils.create_labels_dict(magics, descriptions, account_id, reverse_order=True)
        
        # Create results table
        df_results = data_table_component.create_results_table(
            magics, magic_total_sums, labels_tab1
        )
        
        # Sort options
        sort_options = UIConfig.SORT_OPTIONS["results"]
        sort_option = st.selectbox("Sort by", sort_options, index=0)
        df_results = data_table_component.sort_table(df_results, sort_option)
        
        # Create chart
        fig_results = chart_component.create_bar_chart(
            df_results, 'Result', 'Label', 'Result'
        )
        
        # Add summary annotation
        summary_text, color = status_component.show_performance_summary(
            total_summ, balance_start, custom_text
        )
        chart_component.add_annotation(fig_results, summary_text, color=color)
        
        # Update layout
        height = max(Config.MIN_CHART_HEIGHT, len(df_results) * Config.CHART_HEIGHT_MULTIPLIER)
        chart_component.update_layout(fig_results, height=height)
        
        st.plotly_chart(fig_results, use_container_width=True)


class DistributionPage:
    """Distribution page"""
    
    @staticmethod
    def render(magic_profits: Dict[str, Any], account_id: str, db_manager: Any):
        """Render distribution page"""
        st.subheader("Distribution of Profits / Losses")
        
        magic_total_sums = magic_profits["Total by Magic"]
        magics = list(magic_total_sums.keys())
        descriptions = db_manager.get_all_magic_descriptions(account_id)
        labels = data_utils.create_labels_dict(magics, descriptions, account_id)
        
        selected_magic = st.selectbox(
            "Select Magic for Symbol Details (None for Overall)", 
            [None] + magics
        )
        
        if selected_magic is None:
            DistributionPage._render_overall_distribution(magic_total_sums, labels)
        else:
            DistributionPage._render_magic_distribution(magic_profits, selected_magic)
    
    @staticmethod
    def _render_overall_distribution(magic_total_sums: Dict[int, float], labels: Dict[int, str]):
        """Render overall profit/loss distribution"""
        # Profit distribution
        df_pos = pd.DataFrame({
            'Label': [f"{labels[m]}  -  ${magic_total_sums[m]:.2f}" 
                     for m in magic_total_sums.keys() if magic_total_sums[m] > 0],
            'Profit': [v for v in magic_total_sums.values() if v > 0]
        })
        
        # Loss distribution
        df_neg = pd.DataFrame({
            'Label': [f"{labels[m]}  -  ${magic_total_sums[m]:.2f}" 
                     for m in magic_total_sums.keys() if magic_total_sums[m] < 0],
            'Loss': [abs(v) for v in magic_total_sums.values() if v < 0]
        })
        
        if not df_pos.empty:
            fig_pos = chart_component.create_pie_chart(df_pos, 'Profit', 'Label', "Profit Distribution")
            st.plotly_chart(fig_pos)
        
        if not df_neg.empty:
            fig_neg = chart_component.create_pie_chart(df_neg, 'Loss', 'Label', "Loss Distribution")
            st.plotly_chart(fig_neg)
    
    @staticmethod
    def _render_magic_distribution(magic_profits: Dict[str, Any], selected_magic: int):
        """Render distribution for specific magic"""
        per_symbol = {key[1]: val for key, val in magic_profits.items()
                     if isinstance(key, tuple) and len(key) == 2 
                     and isinstance(key[0], (int, float)) and isinstance(key[1], str) 
                     and key[0] == selected_magic}
        
        # Profit distribution by symbol
        df_pos_sym = pd.DataFrame({
            'Symbol': [s for s, v in per_symbol.items() if v > 0],
            'Profit': [v for v in per_symbol.values() if v > 0]
        })
        
        # Loss distribution by symbol
        df_neg_sym = pd.DataFrame({
            'Symbol': [s for s, v in per_symbol.items() if v < 0],
            'Loss': [abs(v) for v in per_symbol.values() if v < 0]
        })
        
        if not df_pos_sym.empty:
            fig_pos_sym = chart_component.create_pie_chart(
                df_pos_sym, 'Profit', 'Symbol', 
                f"Profit Distribution for Magic {selected_magic}"
            )
            st.plotly_chart(fig_pos_sym)
        
        if not df_neg_sym.empty:
            fig_neg_sym = chart_component.create_pie_chart(
                df_neg_sym, 'Loss', 'Symbol', 
                f"Loss Distribution for Magic {selected_magic}"
            )
            st.plotly_chart(fig_neg_sym)


class DealsByHourPage:
    """Deals by Hour page"""
    
    @staticmethod
    def render(trade_history: List):
        """Render deals by hour page"""
        st.subheader("Deals by Hour")
        
        if not trade_history or len(trade_history) == 0:
            st.info("No deals in the selected period.")
            return
        
        df_deals = pd.DataFrame([d._asdict() for d in trade_history])
        if df_deals.empty:
            st.info("No deals to display.")
            return
        
        # Filter out balance changes
        df_deals = df_deals[df_deals['type'] != 2]
        df_deals['time_dt'] = pd.to_datetime(df_deals['time'], unit='s')
        df_deals['hour'] = df_deals['time_dt'].dt.hour
        
        # Count deals by hour
        counts = df_deals.groupby('hour').size().reset_index(name='count')
        counts = counts.sort_values('hour')
        counts['hour'] = counts['hour'].astype(str)
        
        # Create chart
        fig_hours = px.bar(
            counts, 
            x='hour', 
            y='count',
            labels={'count': 'Number of Deals', 'hour': 'Hour'}
        )
        
        st.plotly_chart(fig_hours, use_container_width=True)


# Global page instances
open_positions_page = OpenPositionsPage()
results_page = ResultsPage()
distribution_page = DistributionPage()
deals_by_hour_page = DealsByHourPage()
