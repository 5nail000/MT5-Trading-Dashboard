"""
Reusable UI components for MT5 Trading Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, Any, List, Optional
from ...config.settings import Config, UIConfig
from ...utils.helpers import performance_utils, data_utils


class ChartComponent:
    """Chart component for displaying trading data"""
    
    @staticmethod
    def create_bar_chart(data: pd.DataFrame, x_col: str, y_col: str, 
                         color_col: str, title: str = "", 
                         orientation: str = 'h') -> px.bar:
        """Create a bar chart"""
        fig = px.bar(
            data, 
            x=x_col, 
            y=y_col, 
            orientation=orientation,
            color=color_col, 
            color_continuous_scale=Config.COLOR_SCHEMES["profit_loss"],
            color_continuous_midpoint=0,
            title=title
        )
        fig.update_yaxes(type='category')
        return fig
    
    @staticmethod
    def create_pie_chart(data: pd.DataFrame, values_col: str, 
                         names_col: str, title: str = "") -> px.pie:
        """Create a pie chart"""
        return px.pie(data, values=values_col, names=names_col, title=title)
    
    @staticmethod
    def add_annotation(fig, text: str, x: float = 0.5, y: float = 1.15, 
                      color: str = "black", font_size: int = 14):
        """Add annotation to chart"""
        fig.add_annotation(
            text=text,
            xref="paper",
            yref="paper",
            x=x,
            y=y,
            showarrow=False,
            font=dict(size=font_size, color=color, family="Arial"),
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="rgba(255,255,255,0.5)",
            borderwidth=1,
            borderpad=5
        )
    
    @staticmethod
    def update_layout(fig, height: int = None, show_legend: bool = False, 
                     margins: Dict[str, int] = None):
        """Update chart layout"""
        if height is None:
            height = Config.MIN_CHART_HEIGHT
        
        if margins is None:
            margins = Config.CHART_MARGINS
        
        fig.update_layout(
            height=height,
            showlegend=show_legend,
            margin=margins
        )


class DataTableComponent:
    """Data table component"""
    
    @staticmethod
    def create_results_table(magics: List[int], magic_total_sums: Dict[int, float], 
                           labels: Dict[int, str]) -> pd.DataFrame:
        """Create results table"""
        return pd.DataFrame({
            'Magic': magics,
            'Label': [f"${magic_total_sums[m]:.2f}  -  {labels[m]}" for m in magics],
            'Result': [round(magic_total_sums[m], 2) for m in magics]
        })
    
    @staticmethod
    def create_open_positions_table(magics_open: List[int], by_magic: Dict[int, float], 
                                  labels_open: Dict[int, str], 
                                  current_balance: float) -> pd.DataFrame:
        """Create open positions table"""
        percentages = [(by_magic[m] / current_balance * 100) if current_balance != 0 else 0 
                      for m in magics_open]
        
        return pd.DataFrame({
            'Magic': magics_open,
            'Label': [f"${by_magic[m]:.2f} ({percentages[i]:+.2f}%) - {labels_open[m]}" 
                     for i, m in enumerate(magics_open)],
            'Floating': [round(by_magic[m], 2) for m in magics_open]
        })
    
    @staticmethod
    def sort_table(df: pd.DataFrame, sort_option: str) -> pd.DataFrame:
        """Sort table based on option"""
        if sort_option == "Magics ↓":
            return df.sort_values('Magic')
        elif sort_option == "Magics ↑":
            return df.sort_values('Magic', ascending=False)
        elif sort_option in ["Results ↓", "Floating ↓"]:
            return df.sort_values(df.columns[2])  # Result or Floating column
        elif sort_option in ["Results ↑", "Floating ↑"]:
            return df.sort_values(df.columns[2], ascending=False)
        return df


class DateRangeComponent:
    """Date range selection component"""
    
    @staticmethod
    def render_date_inputs(session_state: Any):
        """Render date input controls"""
        col1, col2 = st.columns(2)
        
        with col1:
            pending_from = st.date_input(
                "From Date", 
                value=session_state.pending_from_date.date()
            )
        
        with col2:
            pending_to = st.date_input(
                "To Date", 
                value=session_state.pending_to_date.date()
            )
        
        return pending_from, pending_to
    
    @staticmethod
    def render_preset_buttons(session_state: Any, date_presets: Dict[str, Dict]):
        """Render preset date range buttons"""
        col_btn1, col2, col3, col4 = st.columns(4)
        
        with col_btn1:
            if st.button("Today"):
                preset = date_presets["today"]
                session_state.pending_from_date = preset["from"]
                session_state.pending_to_date = preset["to"]
                st.rerun()
        
        with col2:
            if st.button("This Week"):
                preset = date_presets["this_week"]
                session_state.pending_from_date = preset["from"]
                session_state.pending_to_date = preset["to"]
                st.rerun()
        
        with col3:
            if st.button("This Month"):
                preset = date_presets["this_month"]
                session_state.pending_from_date = preset["from"]
                session_state.pending_to_date = preset["to"]
                st.rerun()
        
        with col4:
            if st.button("This Year"):
                preset = date_presets["this_year"]
                session_state.pending_from_date = preset["from"]
                session_state.pending_to_date = preset["to"]
                st.rerun()


class MagicDescriptionComponent:
    """Magic description management component"""
    
    @staticmethod
    def render_magic_descriptions(magics: List[int], account_id: str, 
                                db_manager: Any):
        """Render magic description management interface"""
        with st.expander("Manage Magic Descriptions"):
            for magic in magics:
                col1, col2, col3 = st.columns([2, 3, 1])
                
                with col1:
                    st.write(f"Magic {magic}:")
                
                with col2:
                    desc = db_manager.get_magic_description(account_id, magic)
                    new_desc = st.text_input(
                        "", 
                        value=desc or "", 
                        key=f"desc_{magic}_{account_id}"
                    )
                
                with col3:
                    if st.button("Save", key=f"save_{magic}_{account_id}"):
                        db_manager.set_magic_description(account_id, magic, new_desc)
                        st.success(f"Description for Magic {magic} saved.")


class StatusComponent:
    """Status and notification components"""
    
    @staticmethod
    def show_performance_summary(total_summ: float, balance_start: float, 
                               custom_text: str):
        """Show performance summary"""
        percent_change = performance_utils.calculate_percentage_change(total_summ, balance_start)
        color = performance_utils.get_performance_color(percent_change)
        
        summary_text = (
            f"{custom_text}<br><br>"
            f"Total Result: {performance_utils.format_currency(total_summ)} "
            f"({performance_utils.format_percentage(percent_change)})<br>"
            f"Start Balance: {performance_utils.format_currency(balance_start)}"
        )
        
        return summary_text, color
    
    @staticmethod
    def show_floating_summary(total_floating: float, current_balance: float):
        """Show floating P/L summary"""
        percent_floating = performance_utils.calculate_percentage_change(total_floating, current_balance)
        color = performance_utils.get_performance_color(percent_floating)
        
        summary_text = (
            f"Current Floating P/L: {performance_utils.format_currency(total_floating)} "
            f"({performance_utils.format_percentage(percent_floating)})<br>"
            f"Current Balance: {performance_utils.format_currency(current_balance)}"
        )
        
        return summary_text, color


# Global component instances
chart_component = ChartComponent()
data_table_component = DataTableComponent()
date_range_component = DateRangeComponent()
magic_description_component = MagicDescriptionComponent()
status_component = StatusComponent()
