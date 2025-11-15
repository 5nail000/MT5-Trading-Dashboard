"""
Application pages for MT5 Trading Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ...ui.components.ui_components import (
    chart_component, data_table_component, 
    magic_description_component, status_component
)
from ...utils.helpers import data_utils
from ...config.settings import Config, UIConfig
from ...database.db_manager import db_manager


def create_magic_selection_checkboxes(display_keys: List, labels_dict: Dict, 
                                      account_id: str, session_key_prefix: str,
                                      title: str = "Select magics/groups to display:") -> List:
    """Create checkboxes for magic/group selection with expander and control buttons"""
    # Initialize selected keys in session state if not exists
    session_key = f"{session_key_prefix}_selected_keys_{account_id}"
    update_counter_key = f"{session_key_prefix}_update_counter_{account_id}"
    button_action_key = f"{session_key_prefix}_button_action_{account_id}"
    
    if session_key not in st.session_state:
        # Normalize keys when initializing
        normalized_display = set(
            int(k) if isinstance(k, (int, float)) else k
            for k in display_keys
        )
        st.session_state[session_key] = normalized_display
    if update_counter_key not in st.session_state:
        st.session_state[update_counter_key] = 0
    if button_action_key not in st.session_state:
        st.session_state[button_action_key] = None
    
    # Sort display_keys by labels alphabetically
    sorted_keys = sorted(display_keys, key=lambda k: labels_dict.get(k, str(k)).lower())
    
    # Check if we just performed a button action (from previous rerun)
    just_performed_action = st.session_state[button_action_key] is not None
    action_type = st.session_state[button_action_key] if just_performed_action else None
    
    with st.expander(title, expanded=False):
        # Control buttons - 3 in a row
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Show All", key=f"{session_key_prefix}_show_all_{account_id}"):
                # Normalize keys when setting Show All
                normalized_sorted = set(
                    int(k) if isinstance(k, (int, float)) else k
                    for k in sorted_keys
                )
                st.session_state[session_key] = normalized_sorted
                st.session_state[update_counter_key] += 1
                st.session_state[button_action_key] = "show_all"
                st.rerun()
        with col2:
            if st.button("❌ Hide All", key=f"{session_key_prefix}_hide_all_{account_id}"):
                # Explicitly set empty set - this should clear all selections
                st.session_state[session_key] = set()
                st.session_state[update_counter_key] += 1
                st.session_state[button_action_key] = "hide_all"
                st.rerun()
        with col3:
            if st.button("🔄 Refresh", key=f"{session_key_prefix}_refresh_{account_id}"):
                st.session_state[update_counter_key] += 1
                st.session_state[button_action_key] = "refresh"
                st.rerun()
        
        # Create checkboxes - read from session_state which may have been updated by buttons
        # Use update_counter in key to force recreation of checkboxes when state changes
        selected_keys = []
        cols = st.columns(3)  # 3 columns for checkboxes
        
        # Get current session state value (may be empty if Hide All was clicked)
        current_session_set = st.session_state.get(session_key, set())
        
        # If Hide All was just clicked, ensure we have empty set
        if action_type == "hide_all":
            current_session_set = set()
            st.session_state[session_key] = set()
        
        for idx, key in enumerate(sorted_keys):
            col_idx = idx % 3
            with cols[col_idx]:
                label = labels_dict.get(key, str(key))
                # Read current value from session_state (may have been updated by buttons)
                # Normalize key for comparison (convert to int if numeric)
                normalized_key = int(key) if isinstance(key, (int, float)) else key
                # Check if normalized key is in session_state (normalize stored keys too)
                # If session_state is empty (Hide All), current_value should be False
                current_value = False
                if len(current_session_set) > 0:  # Only check if set is not empty
                    for stored_key in current_session_set:
                        normalized_stored = int(stored_key) if isinstance(stored_key, (int, float)) else stored_key
                        if normalized_stored == normalized_key:
                            current_value = True
                            break
                
                # Include update_counter in key to force widget recreation
                is_selected = st.checkbox(
                    label,
                    value=current_value,
                    key=f"{session_key_prefix}_checkbox_{account_id}_{key}_{st.session_state[update_counter_key]}"
                )
                if is_selected:
                    selected_keys.append(key)
        
        # Update session state with current checkbox selections
        # Only update if we didn't just perform a button action (to preserve button state)
        # Normalize keys to ensure consistent types (int for numeric keys)
        if not just_performed_action:
            normalized_selected = set(
                int(k) if isinstance(k, (int, float)) else k
                for k in selected_keys
            )
            st.session_state[session_key] = normalized_selected
        elif action_type == "hide_all":
            # Explicitly ensure empty set is maintained after Hide All
            # Don't update from checkboxes - keep the empty set
            st.session_state[session_key] = set()
        
        # Clear button action flag after processing
        st.session_state[button_action_key] = None
    
    return selected_keys


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
        
        st.plotly_chart(fig_open)
        
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
            
            st.plotly_chart(fig_breakdown)
            
            # Display table
            st.dataframe(df_breakdown[['Symbol', 'Type', 'Floating']].round(2))


class ResultsPage:
    """Results page"""
    
    @staticmethod
    def render(magic_profits: Dict[str, Any], account_id: str, 
              db_manager: Any, balance_start: float, custom_text: str,
              display_time_in: Any, display_time_out: Any,
              magic_groups: Optional[Dict[int, List[int]]] = None,
              full_trade_history: Optional[List] = None,
              from_date: Optional[datetime] = None,
              to_date: Optional[datetime] = None):
        """Render results page"""
        st.subheader("Results")
        
        st.write("Period:")
        st.write(f"From {display_time_in} to {display_time_out}")
        
        magic_total_sums = magic_profits["Total by Magic"]
        total_summ = magic_profits["Summ"]
        
        st.write(f"Total Result: {total_summ:.2f}")
        
        # Calculate initial balance using full trade history (not filtered) for info panel
        # Use FULL trade history (not filtered) for accurate balance calculation - same as in "Total Result (Selected)"
        balance_at_period_start = None
        if from_date:
            from ...mt5.mt5_client import mt5_data_provider, mt5_calculator
            # Get FULL history from the beginning, not filtered
            full_history, _ = mt5_data_provider.get_history(
                from_date=datetime(2020, 1, 1),
                to_date=to_date if to_date else datetime.now()
            )
            if full_history:
                balance_at_period_start = mt5_calculator.calculate_balance_at_date(
                    target_date=from_date,
                    deals=full_history,  # Use FULL history, not filtered
                    end_of_day=False  # Beginning of day
                )
        elif balance_start and balance_start != 0:
            # Fallback to passed balance_start if calculation failed
            balance_at_period_start = balance_start
        
        # Calculate percentage change
        percentage_change = (total_summ / balance_at_period_start * 100) if balance_at_period_start and balance_at_period_start != 0 else 0
        
        # Format dates for display
        date_from_str = display_time_in.strftime("%d.%m.%Y %H:%M") if isinstance(display_time_in, datetime) else str(display_time_in)
        date_to_str = display_time_out.strftime("%d.%m.%Y %H:%M") if isinstance(display_time_out, datetime) else str(display_time_out)
        
        # Get labels for display (groups or individual magics)
        display_keys = list(magic_total_sums.keys())
        labels_dict = {}
        
        if magic_groups and len(magic_groups) > 0:
            # In grouped mode: show only groups and magics NOT in groups
            groups_data = db_manager.get_magic_groups(account_id)
            all_grouped_magics = set()
            for group_data in groups_data.values():
                all_grouped_magics.update(group_data['magics'])
            
            # Filter display_keys to exclude individual magics that are in groups
            filtered_display_keys = []
            for key in display_keys:
                # Include group IDs - check if this key is a group_id
                # Convert to int if needed for comparison
                key_int = int(key) if isinstance(key, (int, float)) else key
                if key_int in groups_data:
                    filtered_display_keys.append(key)
                    # Use group name as label
                    group_name = groups_data[key_int]['name']
                    labels_dict[key] = group_name
                # Include magics that are NOT in any group
                elif key not in all_grouped_magics:
                    filtered_display_keys.append(key)
                    desc = db_manager.get_magic_description(account_id, key)
                    labels_dict[key] = f"{key} - {desc}" if desc else str(key)
            
            display_keys = filtered_display_keys
            
            # Debug: ensure all groups with data are included
            # If a group_id is in magic_total_sums but not in filtered_display_keys, add it
            for group_id, group_data in groups_data.items():
                if group_id in magic_total_sums and group_id not in display_keys:
                    display_keys.append(group_id)
                    labels_dict[group_id] = group_data['name']
        else:
            # Individual magics mode: show all magics
            descriptions = db_manager.get_all_magic_descriptions(account_id)
            labels_dict = data_utils.create_labels_dict(display_keys, descriptions, account_id, reverse_order=True)
        
        # Store all display_keys and labels_dict for later use (before filtering)
        all_display_keys = display_keys.copy()
        all_labels_dict = labels_dict.copy()
        
        # Get selected keys from session state (or use all if not set)
        session_key = f"results_selected_keys_{account_id}"
        if session_key not in st.session_state:
            st.session_state[session_key] = set(all_display_keys)
        
        # Get currently selected keys from session state
        # Normalize for comparison
        stored_selected = st.session_state.get(session_key, set())
        selected_keys = []
        for k in all_display_keys:
            normalized_k = int(k) if isinstance(k, (int, float)) else k
            for stored_k in stored_selected:
                normalized_stored = int(stored_k) if isinstance(stored_k, (int, float)) else stored_k
                if normalized_k == normalized_stored:
                    selected_keys.append(k)
                    break
        
        # Only initialize with all keys if session_state was never set (first time)
        # Don't auto-initialize if user explicitly cleared all (Hide All)
        if not selected_keys:
            # Check if this is first time (session_key was just created above)
            # Or if it was explicitly cleared (empty set exists in session_state)
            if len(stored_selected) == 0 and session_key in st.session_state:
                # User explicitly cleared all - keep it empty, don't auto-initialize
                pass
            else:
                # First time initialization - set all keys
                selected_keys = all_display_keys.copy()
                normalized_all = set(
                    int(k) if isinstance(k, (int, float)) else k
                    for k in all_display_keys
                )
                st.session_state[session_key] = normalized_all
        
        # Filter display_keys by selected
        display_keys = [k for k in all_display_keys if k in selected_keys]
        
        if not display_keys:
            st.warning("No magics/groups selected. Please select at least one.")
            # Show checkboxes so user can select, but don't create chart
            new_selected_keys = create_magic_selection_checkboxes(
                all_display_keys, all_labels_dict, account_id, "results"
            )
            # Don't rerun if selection is still empty (to prevent infinite loop)
            # Only rerun if user selected something
            if new_selected_keys:
                st.rerun()
            return
        
        # Top: Vertical bar chart
        # Add Magic column for sorting by magic numbers
        def get_magic_for_sorting(key):
            """Extract magic number from key for sorting"""
            # If key is a group_id (in groups_data), use a large number to sort groups after magics
            # Otherwise, use the key itself (which is the magic number)
            if magic_groups and len(magic_groups) > 0:
                groups_data = db_manager.get_magic_groups(account_id)
                key_int = int(key) if isinstance(key, (int, float)) else key
                if key_int in groups_data:
                    # For groups, use a very large number (999999 + group_id) to sort them after magics
                    return 999999 + key_int
            # For individual magics, use the magic number itself
            return int(key) if isinstance(key, (int, float)) else 0
        
        df_results = pd.DataFrame({
            'Label': [all_labels_dict.get(k, str(k)) for k in display_keys],
            'Result': [magic_total_sums[k] for k in display_keys],
            'Magic': [get_magic_for_sorting(k) for k in display_keys]
        })
        
        # Sort options
        sort_options = UIConfig.SORT_OPTIONS["results"]
        sort_option = st.selectbox("Sort by", sort_options, index=0, key="results_sort_main")
        df_results = data_table_component.sort_table(df_results, sort_option)
        
        # Create two-column legend: name on left, value on right
        # Calculate max width for alignment
        max_label_width = df_results['Label'].str.len().max() if len(df_results) > 0 else 20
        max_value_width = 15  # "$X,XXX,XXX.XX" format
        
        # Create formatted labels with two columns (name left, value right)
        formatted_labels = []
        for idx, row in df_results.iterrows():
            label = row['Label']
            result_value = row['Result']
            formatted_value = f"${result_value:,.2f}"
            # Left-align label, right-align value with fixed spacing
            formatted_label = f"{label:<{max_label_width}}  {formatted_value:>{max_value_width}}"
            formatted_labels.append(formatted_label)
        
        df_results['Label_Formatted'] = formatted_labels
        
        # Create horizontal bar chart (bars go left/right, categories vertical)
        # Use the order from sorted DataFrame instead of categoryorder
        # For horizontal charts, Plotly displays categories bottom-to-top, so reverse the list
        label_order = df_results['Label_Formatted'].tolist()
        label_order.reverse()  # First row in DataFrame should be at bottom
        
        fig_results = px.bar(
            df_results,
            x='Result',
            y='Label_Formatted',  # Use formatted labels with two columns
            color='Result',
            color_continuous_scale=Config.COLOR_SCHEMES["profit_loss"],
            color_continuous_midpoint=0,
            labels={'Result': 'Result ($)', 'Label_Formatted': 'Magic/Group'},
            orientation='h',  # Horizontal bars (categories on y-axis, values on x-axis)
            category_orders={'Label_Formatted': label_order}  # Use sorted order (reversed for horizontal display)
        )
        
        # Configure y-axis to use monospace font for better alignment
        fig_results.update_yaxes(
            tickfont=dict(family='JetBrains Mono, monospace', size=12)
        )
        
        # Calculate total result for selected magics/groups (same as in "Total Result (Selected)")
        selected_total = sum(magic_total_sums.get(k, 0.0) for k in display_keys)
        
        # Recalculate percentage change based on selected total
        selected_percentage_change = (selected_total / balance_at_period_start * 100) if balance_at_period_start and balance_at_period_start != 0 else 0
        
        # Add information panel as annotation on the chart
        # Determine color for percentage
        info_color = "lime" if selected_percentage_change >= 0 else "red"
        sign = "+" if selected_total >= 0 else "-"
        formatted_total = f"{sign}${abs(selected_total):,.2f}"
        
        # Create info text (English, no icons)
        info_text = (
            f"{date_from_str} → {date_to_str}<br>"
            f"Initial Balance: ${balance_at_period_start:,.2f}<br>"
            f"Total Result: {formatted_total}<br>"
            f"Change: {selected_percentage_change:+.2f}%"
        )
        
        fig_results.add_annotation(
            text=info_text,
            xref="paper", yref="paper",
            x=0.15, y=1.05,  # Top center
            xanchor="center", yanchor="bottom",
            showarrow=False,
            font=dict(size=14, color=info_color, family="Arial"),
            bgcolor="rgba(0, 0, 0, 0.7)",
            bordercolor="rgba(255, 255, 255, 0.5)",
            borderwidth=1,
            borderpad=8,
            align="left"
        )
        
        # Adjust layout to accommodate wider two-column legend and info panel
        fig_results.update_layout(
            height=max(Config.MIN_CHART_HEIGHT, len(df_results) * Config.CHART_HEIGHT_MULTIPLIER),
            showlegend=False,
            margin=dict(l=280, r=50, t=150, b=50)  # Increased top margin for info panel, left for two-column legend
        )
        
        st.plotly_chart(fig_results)
        
        # Add checkboxes for magic/group selection (after chart)
        new_selected_keys = create_magic_selection_checkboxes(
            all_display_keys, all_labels_dict, account_id, "results"
        )
        
        # Check if selection changed and rerun if needed
        # Normalize new_selected_keys for comparison
        normalized_new = set(
            int(k) if isinstance(k, (int, float)) else k
            for k in new_selected_keys
        )
        normalized_old = set(
            int(k) if isinstance(k, (int, float)) else k
            for k in selected_keys
        )
        
        # Only rerun if selection actually changed
        # Prevent infinite loop: don't rerun if both old and new are empty
        if normalized_new != normalized_old:
            if len(normalized_new) > 0:
                # Selection changed and not empty, rerun to update chart
                st.rerun()
            elif len(normalized_old) > 0:
                # All checkboxes cleared (was not empty, now empty) - rerun once to show warning
                st.rerun()
            # If both are empty, don't rerun (prevents infinite loop)
        
        # Calculate and display total for selected magics/groups
        if new_selected_keys:
            selected_total = sum(magic_total_sums.get(k, 0.0) for k in new_selected_keys)
            # Calculate percentage change relative to balance at start of period
            # Use FULL trade history (not filtered) for accurate balance calculation
            balance_at_period_start_selected = None
            if from_date:
                from ...mt5.mt5_client import mt5_data_provider, mt5_calculator
                # Get FULL history from the beginning, not filtered
                full_history, _ = mt5_data_provider.get_history(
                    from_date=datetime(2020, 1, 1),
                    to_date=to_date if to_date else datetime.now()
                )
                if full_history:
                    balance_at_period_start_selected = mt5_calculator.calculate_balance_at_date(
                        target_date=from_date,
                        deals=full_history,  # Use FULL history, not filtered
                        end_of_day=False  # Beginning of day
                    )
            elif balance_start and balance_start != 0:
                # Fallback to passed balance_start if calculation failed
                balance_at_period_start_selected = balance_start
            
            if balance_at_period_start_selected and balance_at_period_start_selected != 0:
                percentage_change = (selected_total / balance_at_period_start_selected) * 100
                st.markdown(f"**Total Result (Selected):** ${selected_total:,.2f}")
                st.markdown(f"*({percentage_change:+.2f}% от баланса ${balance_at_period_start_selected:,.2f} на начало периода)*")
            else:
                st.markdown(f"**Total Result (Selected):** ${selected_total:,.2f}")
        else:
            st.warning("No magics/groups selected. Please select at least one.")
            return
        
        # Group details: show individual magics for each group
        if magic_groups and len(magic_groups) > 0 and full_trade_history:
            # Get groups data
            groups_data = db_manager.get_magic_groups(account_id)
            
            # Calculate individual magic profits for detail charts
            from ...mt5.mt5_client import mt5_calculator
            individual_magic_profits = mt5_calculator.calculate_by_magics(
                full_trade_history,
                from_date=from_date,
                to_date=to_date,
                magic_groups=None  # No grouping - get individual magic data
            )
            individual_magic_sums = individual_magic_profits.get("Total by Magic", {})
            
            # Get all group IDs that are in display_keys (have data)
            group_ids_with_data = [
                int(key) for key in display_keys 
                if isinstance(key, (int, float)) and int(key) in groups_data
            ]
            
            # Sort groups by the same order as in main chart
            if group_ids_with_data:
                # Create a mapping of group_id to its position in main chart
                main_chart_order = {label: idx for idx, label in enumerate(df_results['Label'].tolist())}
                group_positions = {}
                for group_id in group_ids_with_data:
                    group_name = groups_data[group_id]['name']
                    if group_name in main_chart_order:
                        group_positions[group_id] = main_chart_order[group_name]
                
                # Sort groups by their position in main chart
                group_ids_with_data.sort(key=lambda gid: group_positions.get(gid, 999))
                
                # Add spacing between groups
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### Group Details")
                
                for group_id in group_ids_with_data:
                    group_data = groups_data[group_id]
                    group_name = group_data['name']
                    group_magics = group_data['magics']
                    
                    # Filter magics that have data
                    magics_with_data = [
                        magic for magic in group_magics 
                        if magic in individual_magic_sums
                    ]
                    
                    if not magics_with_data:
                        continue
                    
                    # Create DataFrame for this group
                    group_labels = {}
                    descriptions = db_manager.get_all_magic_descriptions(account_id)
                    for magic in magics_with_data:
                        desc = descriptions.get(magic, "")
                        group_labels[magic] = f"{magic} - {desc}" if desc else str(magic)
                    
                    df_group = pd.DataFrame({
                        'Label': [group_labels.get(m, str(m)) for m in magics_with_data],
                        'Result': [individual_magic_sums[m] for m in magics_with_data],
                        'Magic': magics_with_data  # Add Magic column for sorting by magic numbers
                    })
                    
                    # Apply same sorting as main chart
                    df_group = data_table_component.sort_table(df_group, sort_option)
                    
                    # Create two-column legend for group chart (same as main chart)
                    max_label_width_group = df_group['Label'].str.len().max() if len(df_group) > 0 else 20
                    max_value_width_group = 15
                    
                    formatted_labels_group = []
                    for idx, row in df_group.iterrows():
                        label = row['Label']
                        result_value = row['Result']
                        formatted_value = f"${result_value:,.2f}"
                        formatted_label = f"{label:<{max_label_width_group}}  {formatted_value:>{max_value_width_group}}"
                        formatted_labels_group.append(formatted_label)
                    
                    df_group['Label_Formatted'] = formatted_labels_group
                    
                    # Create chart for this group
                    # For horizontal charts, reverse the label order
                    group_label_order = df_group['Label_Formatted'].tolist()
                    group_label_order.reverse()
                    fig_group = px.bar(
                        df_group,
                        x='Result',
                        y='Label_Formatted',  # Use formatted labels with two columns
                        color='Result',
                        color_continuous_scale=Config.COLOR_SCHEMES["profit_loss"],
                        color_continuous_midpoint=0,
                        labels={'Result': 'Result ($)', 'Label_Formatted': 'Magic'},
                        orientation='h',
                        category_orders={'Label_Formatted': group_label_order},
                        title=f"{group_name} - Individual Magics"
                    )
                    
                    fig_group.update_layout(
                        height=max(Config.MIN_CHART_HEIGHT, len(df_group) * Config.CHART_HEIGHT_MULTIPLIER),
                        showlegend=False,
                        margin=dict(l=280, r=50, t=50, b=50)  # Increase left margin for two-column legend
                    )
                    
                    # Configure y-axis to use monospace font for better alignment
                    fig_group.update_yaxes(
                        tickfont=dict(family='JetBrains Mono, monospace', size=13)
                    )
                    st.plotly_chart(fig_group)
                    
                    # Add spacing between groups
                    st.markdown("<br>", unsafe_allow_html=True)


class DistributionPage:
    """Distribution page"""
    
    @staticmethod
    def render(magic_profits: Dict[str, Any], account_id: str, db_manager: Any,
              magic_groups: Optional[Dict[int, List[int]]] = None):
        """Render distribution page"""
        st.subheader("Distribution of Profits / Losses")
        
        magic_total_sums = magic_profits["Total by Magic"]
        display_keys = list(magic_total_sums.keys())
        labels = {}
        
        # Get labels for display (groups or individual magics)
        if magic_groups and len(magic_groups) > 0:
            # In grouped mode: show only groups and magics NOT in groups
            groups_data = db_manager.get_magic_groups(account_id)
            all_grouped_magics = set()
            for group_data in groups_data.values():
                all_grouped_magics.update(group_data['magics'])
            
            # Filter display_keys and create labels
            filtered_display_keys = []
            for key in display_keys:
                key_int = int(key) if isinstance(key, (int, float)) else key
                if key_int in groups_data:
                    filtered_display_keys.append(key)
                    labels[key] = groups_data[key_int]['name']
                elif key not in all_grouped_magics:
                    filtered_display_keys.append(key)
                    desc = db_manager.get_magic_description(account_id, key)
                    labels[key] = f"{key} - {desc}" if desc else str(key)
            
            # Ensure all groups with data are included
            for group_id, group_data in groups_data.items():
                if group_id in magic_total_sums and group_id not in filtered_display_keys:
                    filtered_display_keys.append(group_id)
                    labels[group_id] = group_data['name']
            
            display_keys = filtered_display_keys
        else:
            # Individual magics mode
            descriptions = db_manager.get_all_magic_descriptions(account_id)
            labels = data_utils.create_labels_dict(display_keys, descriptions, account_id)
        
        selected_magic = st.selectbox(
            "Select Magic/Group for Symbol Details (None for Overall)", 
            [None] + display_keys
        )
        
        if selected_magic is None:
            DistributionPage._render_overall_distribution(magic_total_sums, labels, display_keys)
        else:
            DistributionPage._render_magic_distribution(magic_profits, selected_magic)
    
    @staticmethod
    def _render_overall_distribution(magic_total_sums: Dict[int, float], labels: Dict[int, str], display_keys: List):
        """Render overall profit/loss distribution"""
        # Profit distribution
        profit_items = {k: v for k, v in magic_total_sums.items() if k in display_keys and v > 0}
        df_pos = pd.DataFrame({
            'Label': [f"{labels.get(m, str(m))}  -  ${magic_total_sums[m]:.2f}" 
                     for m in profit_items.keys()],
            'Profit': list(profit_items.values())
        })
        
        # Loss distribution
        loss_items = {k: abs(v) for k, v in magic_total_sums.items() if k in display_keys and v < 0}
        df_neg = pd.DataFrame({
            'Label': [f"{labels.get(m, str(m))}  -  ${magic_total_sums[m]:.2f}" 
                     for m in loss_items.keys()],
            'Loss': list(loss_items.values())
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


class ChartPage:
    """Chart page (balance change chart - not yet implemented)"""
    
    @staticmethod
    def render():
        """Render chart page"""
        st.subheader("Balance Change Chart")
        st.info("This feature is under development. Balance, equity, drawdowns, and margin charts will be available soon.")


class DealsPage:
    """Deals page - displays aggregated positions data in a sortable table"""
    
    @staticmethod
    def render(trade_history: List, account_id: str, db_manager: Any,
              full_trade_history: List = None, from_date: datetime = None, 
              to_date: datetime = None,
              magic_groups: Optional[Dict[int, List[int]]] = None):
        """Render deals page with aggregated positions"""
        st.subheader("Deals (Aggregated by Position)")
        
        if not trade_history or len(trade_history) == 0:
            st.info("No deals in the selected period.")
            return
        
        # Filter out balance changes from selected period to find position_ids
        trading_deals_in_period = [d for d in trade_history if d._asdict().get('type', 0) != 2]
        
        if not trading_deals_in_period:
            st.info("No trading deals in the selected period.")
            return
        
        # Find all position_ids that have deals in the selected period
        position_ids_in_period = set()
        for deal in trading_deals_in_period:
            position_id = deal._asdict().get('position_id', 0)
            if position_id != 0:
                position_ids_in_period.add(position_id)
        
        if not position_ids_in_period:
            st.info("No positions found in the selected period.")
            return
        
        # Use full history to get ALL deals for positions that closed in the period
        # This includes entry deals that happened before the period start
        all_deals = full_trade_history if full_trade_history else trade_history
        
        # Filter out balance changes from full history
        all_trading_deals = [d for d in all_deals if d._asdict().get('type', 0) != 2]
        
        # Group ALL deals by position_id (including entry deals before period start)
        positions_dict = {}
        
        for deal in all_trading_deals:
            deal_dict = deal._asdict()
            position_id = deal_dict.get('position_id', 0)
            
            # Only process positions that have deals in the selected period
            if position_id == 0 or position_id not in position_ids_in_period:
                continue
            
            if position_id not in positions_dict:
                positions_dict[position_id] = {
                    'deals': [],
                    'symbol': deal_dict.get('symbol', ''),
                    'magic': deal_dict.get('magic', 0)
                }
            
            positions_dict[position_id]['deals'].append(deal)
        
        # Aggregate data for each position
        positions_data = []
        
        for position_id, pos_data in positions_dict.items():
            deals = sorted(pos_data['deals'], key=lambda d: d.time)
            
            if not deals:
                continue
            
            # Get first deal (entry) and last deal (exit)
            first_deal = deals[0]
            last_deal = deals[-1]
            
            first_deal_dict = first_deal._asdict()
            last_deal_dict = last_deal._asdict()
            
            # Check if position is closed
            # Position is closed if last deal is opposite type to first deal (closing deal)
            first_deal_type = first_deal_dict.get('type', 0)
            last_deal_type = last_deal_dict.get('type', 0)
            
            # If last deal is same type as first deal, position might still be open
            # Only consider positions where last deal is opposite type (closing deal)
            if first_deal_type == last_deal_type:
                # Same type - might be open position, skip it
                continue
            
            # Convert times
            entry_time = datetime.fromtimestamp(first_deal.time) - timedelta(hours=Config.LOCAL_TIMESHIFT)
            exit_time = datetime.fromtimestamp(last_deal.time) - timedelta(hours=Config.LOCAL_TIMESHIFT)
            
            # Check if position was closed within the selected period
            # Last deal (closing deal) must be in selected period
            if from_date and exit_time < from_date:
                continue
            if to_date and exit_time > to_date:
                continue
            
            # Determine direction from first deal
            deal_type = first_deal_dict.get('type', 0)
            direction = "Buy" if deal_type == 0 else "Sell"
            
            # Aggregate volumes, profits, commissions, swaps
            total_volume = sum(d._asdict().get('volume', 0.0) for d in deals)
            total_profit = sum(d._asdict().get('profit', 0.0) for d in deals)
            total_commission = sum(d._asdict().get('commission', 0.0) for d in deals)
            total_swap = sum(d._asdict().get('swap', 0.0) for d in deals)
            total_pl = total_profit + total_commission + total_swap
            
            # Get entry and exit prices
            # Entry price from first deal
            entry_price = first_deal_dict.get('price', 0.0)
            # Exit price from last deal
            exit_price = last_deal_dict.get('price', 0.0)
            
            # Get magic description
            magic = pos_data['magic']
            magic_desc = db_manager.get_magic_description(account_id, magic)
            magic_label = f"{magic} - {magic_desc}" if magic_desc else str(magic)
            
            # Calculate duration
            duration = exit_time - entry_time
            duration_str = f"{duration.days}d {duration.seconds // 3600}h {(duration.seconds % 3600) // 60}m"
            
            positions_data.append({
                'Position ID': position_id,
                'Symbol': pos_data['symbol'],
                'Direction': direction,
                'Magic': magic,
                'Magic Label': magic_label,
                'Entry Time': entry_time,
                'Entry Price': entry_price,
                'Exit Time': exit_time,
                'Exit Price': exit_price,
                'Duration': duration_str,
                'Volume': total_volume,
                'Profit': total_profit,
                'Commission': total_commission,
                'Swap': total_swap,
                'Total P/L': total_pl,
                'Deals Count': len(deals)
            })
        
        if not positions_data:
            st.info("No positions found in the selected period.")
            return
        
        # Get unique magics from positions and create display keys/labels
        unique_magics = set(pos['Magic'] for pos in positions_data)
        display_keys = list(unique_magics)
        labels_dict = {}
        
        # Create labels for display (groups or individual magics)
        if magic_groups and len(magic_groups) > 0:
            # In grouped mode: show groups and magics NOT in groups
            groups_data = db_manager.get_magic_groups(account_id)
            all_grouped_magics = set()
            for group_data in groups_data.values():
                all_grouped_magics.update(group_data['magics'])
            
            # Create reverse mapping: magic -> group_id
            magic_to_group = {}
            for group_id, group_data in groups_data.items():
                for magic in group_data['magics']:
                    magic_to_group[magic] = group_id
            
            # Build display_keys and labels_dict
            filtered_display_keys = []
            group_ids_seen = set()
            
            for magic in display_keys:
                if magic in magic_to_group:
                    # Magic is in a group
                    group_id = magic_to_group[magic]
                    if group_id not in group_ids_seen:
                        filtered_display_keys.append(group_id)
                        labels_dict[group_id] = groups_data[group_id]['name']
                        group_ids_seen.add(group_id)
                else:
                    # Magic is not in any group
                    filtered_display_keys.append(magic)
                    desc = db_manager.get_magic_description(account_id, magic)
                    labels_dict[magic] = f"{magic} - {desc}" if desc else str(magic)
            
            display_keys = filtered_display_keys
        else:
            # Individual magics mode: show all magics
            descriptions = db_manager.get_all_magic_descriptions(account_id)
            for magic in display_keys:
                desc = descriptions.get(magic, "")
                labels_dict[magic] = f"{magic} - {desc}" if desc else str(magic)
        
        # Add checkboxes for magic/group selection
        selected_keys = create_magic_selection_checkboxes(
            display_keys, labels_dict, account_id, "deals"
        )
        
        # Filter positions_data by selected magics/groups
        if selected_keys:
            # Get groups data if in grouped mode
            groups_data = None
            if magic_groups and len(magic_groups) > 0:
                groups_data = db_manager.get_magic_groups(account_id)
            
            # Create set of allowed magics
            allowed_magics = set()
            for key in selected_keys:
                key_int = int(key) if isinstance(key, (int, float)) else key
                # If key is a group_id, add all magics in that group
                if groups_data and key_int in groups_data:
                    allowed_magics.update(groups_data[key_int]['magics'])
                else:
                    # Key is an individual magic
                    allowed_magics.add(key_int)
            
            # Filter positions_data
            positions_data = [
                pos for pos in positions_data 
                if pos['Magic'] in allowed_magics
            ]
        else:
            st.warning("No magics/groups selected. Please select at least one.")
            return
        
        if not positions_data:
            st.info("No positions found for selected magics/groups.")
            return
        
        df_positions = pd.DataFrame(positions_data)
        
        # Calculate and display Total P/L under checkboxes
        total_pl = df_positions['Total P/L'].sum()
        st.write(f"**Total P/L:** ${total_pl:.2f}")
        
        # Display summary
        total_positions = len(df_positions)
        st.write(f"**Total Positions:** {total_positions}")
        
        # Sort options
        sort_column = st.selectbox(
            "Sort by Column:",
            options=df_positions.columns.tolist(),
            index=5,  # Default: Entry Time
            key="deals_sort_column"
        )
        
        sort_ascending = st.checkbox("Ascending", value=False, key="deals_sort_ascending")
        
        # Sort DataFrame
        df_sorted = df_positions.sort_values(by=sort_column, ascending=sort_ascending)
        
        # Format datetime columns for display
        df_display = df_sorted.copy()
        df_display['Entry Time'] = df_display['Entry Time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_display['Exit Time'] = df_display['Exit Time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Display table with sorting capability
        st.dataframe(
            df_display,
            width='stretch',
            height=600,
            hide_index=True
        )
        
        # Download button
        csv = df_sorted.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"positions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_positions_csv"
        )


class DealsByHourPage:
    """Time Distribution page"""
    
    @staticmethod
    def render(trade_history: List, from_date: datetime = None, to_date: datetime = None,
              full_trade_history: List = None):
        """Render time distribution page"""
        st.subheader("Time Distribution")
        
        # Use full_trade_history if available (for consistency with calculations)
        # But filter by time for display (only deals in selected period)
        deals_to_use = full_trade_history if full_trade_history else trade_history
        
        if not deals_to_use or len(deals_to_use) == 0:
            st.info("No deals in the selected period.")
            return
        
        # Convert to DataFrame and filter by time period
        df_deals = pd.DataFrame([d._asdict() for d in deals_to_use])
        if df_deals.empty:
            st.info("No deals to display.")
            return
        
        # Filter out balance changes
        df_deals = df_deals[df_deals['type'] != 2]
        
        # Convert time with LOCAL_TIMESHIFT and filter by date range
        df_deals['time_dt'] = pd.to_datetime(df_deals['time'], unit='s') - pd.Timedelta(hours=Config.LOCAL_TIMESHIFT)
        if from_date:
            df_deals = df_deals[df_deals['time_dt'] >= from_date]
        if to_date:
            df_deals = df_deals[df_deals['time_dt'] <= to_date]
        
        if df_deals.empty:
            st.info("No deals in the selected period.")
            return
        
        df_deals['hour'] = df_deals['time_dt'].dt.hour
        
        # Top: Vertical bar chart by hour
        counts = df_deals.groupby('hour').size().reset_index(name='count')
        counts = counts.sort_values('hour')
        counts['hour'] = counts['hour'].astype(str) + ':00'
        
        fig_hours = px.bar(
            counts,
            x='hour',
            y='count',
            orientation='v',  # Vertical bars
            labels={'count': 'Number of Deals', 'hour': 'Hour'},
            title="Deals by Hour"
        )
        fig_hours.update_layout(height=500)
        st.plotly_chart(fig_hours)
        
        # Bottom: Vertical bar chart by day of week (if period > 1 month)
        if from_date and to_date:
            period_days = (to_date - from_date).days
            if period_days > 30:
                df_deals['day_of_week'] = df_deals['time_dt'].dt.day_name()
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                counts_by_day = df_deals.groupby('day_of_week').size().reset_index(name='count')
                counts_by_day['day_of_week'] = pd.Categorical(counts_by_day['day_of_week'], categories=day_order, ordered=True)
                counts_by_day = counts_by_day.sort_values('day_of_week')
                
                fig_days = px.bar(
                    counts_by_day,
                    x='day_of_week',
                    y='count',
                    orientation='v',  # Vertical bars
                    labels={'count': 'Number of Deals', 'day_of_week': 'Day of Week'},
                    title="Deals by Day of Week"
                )
                fig_days.update_layout(height=400)
                st.plotly_chart(fig_days)


# Global page instances
open_positions_page = OpenPositionsPage()
results_page = ResultsPage()
distribution_page = DistributionPage()
deals_by_hour_page = DealsByHourPage()
chart_page = ChartPage()
deals_page = DealsPage()
