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
            if 'Magic' in df.columns:
                return df.sort_values('Magic')
            return df
        elif sort_option == "Magics ↑":
            if 'Magic' in df.columns:
                return df.sort_values('Magic', ascending=False)
            return df
        elif sort_option in ["Results ↓", "Floating ↓"]:
            # Try to find the appropriate column by name
            if 'Result' in df.columns:
                return df.sort_values('Result')
            elif 'Floating' in df.columns:
                return df.sort_values('Floating')
            # Fallback to last numeric column if neither found
            elif len(df.columns) > 0:
                return df.sort_values(df.columns[-1])
            return df
        elif sort_option in ["Results ↑", "Floating ↑"]:
            # Try to find the appropriate column by name
            if 'Result' in df.columns:
                return df.sort_values('Result', ascending=False)
            elif 'Floating' in df.columns:
                return df.sort_values('Floating', ascending=False)
            # Fallback to last numeric column if neither found
            elif len(df.columns) > 0:
                return df.sort_values(df.columns[-1], ascending=False)
            return df
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
                        f"Описание Magic {magic}", 
                        value=desc or "", 
                        key=f"desc_{magic}_{account_id}",
                        label_visibility="collapsed"
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
        percent_change = performance_utils.calculate_percentage_change(total_summ + balance_start, balance_start)
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
        percent_floating = performance_utils.calculate_percentage_change(total_floating + current_balance, current_balance)
        color = performance_utils.get_performance_color(percent_floating)
        
        summary_text = (
            f"Current Floating P/L: {performance_utils.format_currency(total_floating)} "
            f"({performance_utils.format_percentage(percent_floating)})<br>"
            f"Current Balance: {performance_utils.format_currency(current_balance)}"
        )
        
        return summary_text, color


class AccountInfoComponent:
    """Account information display component"""
    
    @staticmethod
    def render(account_info: Any, account_id: str, db_manager: Any):
        """Render account number, title, leverage and server"""
        account_number = account_info.login if account_info else account_id
        account_title = db_manager.get_account_title(account_id) or "No Title"
        
        # Получаем leverage и server из БД или из account_info
        leverage = db_manager.get_account_leverage(account_id)
        server = db_manager.get_account_server(account_id)
        
        # Если есть account_info, обновляем данные в БД
        if account_info:
            # Получаем leverage и server из MT5
            mt5_leverage = getattr(account_info, 'leverage', None)
            mt5_server = getattr(account_info, 'server', None)
            
            # Сохраняем в БД, если они есть и отличаются от сохраненных
            if mt5_leverage is not None and mt5_leverage != leverage:
                db_manager.set_account_leverage(account_id, mt5_leverage)
                leverage = mt5_leverage
            
            if mt5_server is not None and mt5_server != server:
                db_manager.set_account_server(account_id, mt5_server)
                server = mt5_server
        
        # Display Account Title large at the top (centered)
        st.markdown(f"<h1 style='text-align: center;'>{account_title}</h1><br>", unsafe_allow_html=True)
        
        # Display other account info below
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Account Number:** {account_number}")
        with col2:
            leverage_str = f"1:{leverage}" if leverage else "N/A"
            st.write(f"**Leverage:** {leverage_str}")
        with col3:
            st.write(f"**Server:** {server or 'N/A'}")


class OpenPositionsDashboardComponent:
    """Open positions dashboard component"""
    
    @staticmethod
    def render(open_profits: Dict[str, Any], account_id: str, db_manager: Any,
              balance_start: float, account_info_open: Any = None,
              on_refresh: callable = None):
        """Render open positions dashboard in collapsible expander"""
        with st.expander("📊 Open Positions Dashboard", expanded=True):
            if not open_profits:
                st.info("No open positions data available.")
                return
            
            # Auto-refresh toggle
            auto_refresh = st.checkbox("Enable Auto-Refresh", value=False, key="open_pos_auto_refresh")
            
            # Manual refresh button
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🔄 Refresh", key="open_pos_manual_refresh"):
                    if on_refresh:
                        on_refresh()
                    st.rerun()
            
            detailed = open_profits.get("detailed", {})
            by_magic = open_profits.get("by_magic", {})
            total_floating = open_profits.get("total_floating", 0.0)
            
            current_balance = account_info_open.balance if account_info_open else balance_start
            
            magics_open = list(by_magic.keys()) if by_magic else []
            descriptions = db_manager.get_all_magic_descriptions(account_id)
            labels_open = data_utils.create_labels_dict(magics_open, descriptions, account_id)
            
            st.write(f"**Current Floating P/L:** {total_floating:.2f}")
            
            # Create and display table
            df_open_results = data_table_component.create_open_positions_table(
                magics_open, by_magic, labels_open, current_balance
            )
            
            # Sort options
            sort_options = UIConfig.SORT_OPTIONS["open_positions"]
            sort_option_open = st.selectbox("Sort by", sort_options, index=0, key="open_pos_sort")
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
            
            st.plotly_chart(fig_open)


class DateSelectorComponent:
    """Date selector with quick filters and recalculate button"""
    
    @staticmethod
    def render(session_state: Any, date_presets: Dict[str, Dict]):
        """Render date selector component"""
        st.subheader("📅 Date Selector and Quick Filters")
        # Date range inputs
        pending_from, pending_to = date_range_component.render_date_inputs(session_state)
        
        # Update pending values
        from datetime import datetime, time
        session_state.pending_from_date = datetime.combine(pending_from, time(0, 0))
        session_state.pending_to_date = datetime.combine(pending_to, time(23, 59, 59))
        
        # Preset buttons
        st.write("**Quick Filters:**")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
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
        
        with col5:
            return st.button("🔄 Recalculate", key="recalculate_main")


class MagicGroupingComponent:
    """Magic grouping selection component"""
    
    @staticmethod
    def render(account_id: str, db_manager: Any):
        """Render magic grouping selection"""
        with st.expander("🔢 Magic Number Selection", expanded=False):
            current_mode = db_manager.get_view_mode(account_id)
            
            view_mode = st.radio(
                "View Mode:",
                ["Individual Magics", "Grouped Magics"],
                index=0 if current_mode == "individual" else 1,
                key="magic_view_mode"
            )
            
            mode_value = "individual" if view_mode == "Individual Magics" else "grouped"
            
            if mode_value != current_mode:
                db_manager.set_view_mode(account_id, mode_value)
                # Don't rerun here - let app.py handle recalculation and rerun
            
            return mode_value


class SettingsComponent:
    """Settings component"""
    
    @staticmethod
    def render(account_id: str, db_manager: Any, magics: List[int]):
        with st.expander("🔧 Settings", expanded=False):
            """Render settings section"""
            st.subheader("⚙️ Settings")
            
            # Account Title
            st.write("**Change Account Title:**")
            current_title = db_manager.get_account_title(account_id) or ""
            new_title = st.text_input(
                "Account Title",
                value=current_title,
                key="account_title_input"
            )
            if st.button("Save Account Title", key="save_account_title"):
                db_manager.set_account_title(account_id, new_title)
                st.success("Account title saved!")
                st.rerun()
            
            st.divider()
            
            # Magic Names (collapsible, expanded by default)
            with st.expander("📝 Magics", expanded=True):
                magic_description_component.render_magic_descriptions(magics, account_id, db_manager)
                st.divider()
                SettingsComponent._render_group_management(account_id, db_manager, magics)
                
    
    @staticmethod
    def _render_group_management(account_id: str, db_manager: Any, magics: List[int]):
        """Render group management interface"""
        groups = db_manager.get_magic_groups(account_id)
        magics_by_group = db_manager.get_magics_by_group(account_id)
        
        # Create new group
        st.write("**Create New Group:**")
        col1, col2 = st.columns([3, 1])
        with col1:
            new_group_name = st.text_input("Group Name", key="new_group_name")
        with col2:
            if st.button("Create Group", key="create_group"):
                if new_group_name:
                    group_id = db_manager.create_magic_group(account_id, new_group_name)
                    st.success(f"Group '{new_group_name}' created!")
                    st.rerun()
        
        st.divider()
        
        # Manage existing groups
        if groups:
            st.write("**Existing Groups:**")
            for group_id, group_data in groups.items():
                with st.expander(f"Group: {group_data['name']} (ID: {group_id})"):
                    # Edit group name
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        edited_name = st.text_input(
                            "Group Name",
                            value=group_data['name'],
                            key=f"edit_group_{group_id}"
                        )
                    with col2:
                        if st.button("Update Name", key=f"update_name_{group_id}"):
                            db_manager.update_magic_group_name(account_id, group_id, edited_name)
                            st.success("Group name updated!")
                            st.rerun()
                    
                    # Assign magics to group
                    st.write("**Assign Magics:**")
                    available_magics = [m for m in magics if m not in group_data['magics']]
                    if available_magics:
                        selected_magic = st.selectbox(
                            "Select Magic to Add",
                            available_magics,
                            key=f"add_magic_{group_id}"
                        )
                        if st.button("Add Magic", key=f"add_magic_btn_{group_id}"):
                            db_manager.add_magic_to_group(account_id, group_id, selected_magic)
                            st.success(f"Magic {selected_magic} added to group!")
                            st.rerun()
                    
                    # Show assigned magics
                    if group_data['magics']:
                        st.write("**Assigned Magics:**")
                        for magic in group_data['magics']:
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.write(f"Magic {magic}")
                            with col2:
                                if st.button("Remove", key=f"remove_{group_id}_{magic}"):
                                    db_manager.remove_magic_from_group(account_id, group_id, magic)
                                    st.success(f"Magic {magic} removed from group!")
                                    st.rerun()
                    
                    # Delete group
                    if st.button("🗑️ Delete Group", key=f"delete_group_{group_id}"):
                        db_manager.delete_magic_group(account_id, group_id)
                        st.success("Group deleted!")
                        st.rerun()


# Global component instances
chart_component = ChartComponent()
data_table_component = DataTableComponent()
date_range_component = DateRangeComponent()
magic_description_component = MagicDescriptionComponent()
status_component = StatusComponent()
account_info_component = AccountInfoComponent()
open_positions_dashboard_component = OpenPositionsDashboardComponent()
date_selector_component = DateSelectorComponent()
magic_grouping_component = MagicGroupingComponent()
settings_component = SettingsComponent()
