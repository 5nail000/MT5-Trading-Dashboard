"""
MT5 Trading Dashboard - Main Application
Refactored with modular architecture
"""

import streamlit as st
import time as time_mod
from datetime import datetime, time, timedelta

# Import our modules
from src.config.settings import Config, UIConfig, get_config
from src.database.db_manager import db_manager
from src.mt5.mt5_client import mt5_data_provider, mt5_calculator
from src.utils.helpers import date_utils, session_utils, validation_utils
from src.ui.components.ui_components import (
    account_info_component, open_positions_dashboard_component,
    date_selector_component, magic_grouping_component, settings_component
)
from src.ui.pages.pages import (
    results_page, distribution_page, deals_by_hour_page, chart_page, deals_page
)

# Initialize configuration
config = get_config()

# Run command:
# streamlit run app.py

def main():
    """Main application function"""
    
    # Page configuration
    st.set_page_config(page_title=config.PAGE_TITLE)
    
    # Apply custom CSS
    st.markdown(UIConfig.CUSTOM_CSS, unsafe_allow_html=True)
    
    # Initialize database
    db_manager.init_database()
    
    # Initialize session state
    session_utils.init_session_state(st.session_state)
    
    # Load open positions early for dashboard (before displaying account info)
    if 'open_profits' not in st.session_state:
        load_open_positions(st.session_state)
    
    # Get account info for display
    account_info = None
    account_id = "default"
    
    # Try to get account info from session state (after loading)
    if 'account_info_open' in st.session_state:
        account_info = st.session_state.account_info_open
        account_id = str(account_info.login) if account_info else "default"
    elif 'account_id' in st.session_state:
        account_id = st.session_state.account_id
    
    # Application title (smaller, below account info)
    st.markdown(f"<h3 style='margin-top: 0.5rem; text-align: center;'>{config.APP_NAME}</h3>", unsafe_allow_html=True)
    
    # Display Account Title (large, at top) and other account info
    # Always render if we have account_id (even if it's "default", to show "No Title")
    account_info_component.render(account_info, account_id, db_manager)
    
    st.divider()
    
    # 1. Open Positions Dashboard (collapsible)
    if 'open_profits' in st.session_state:
        open_positions_dashboard_component.render(
            st.session_state.open_profits,
            account_id,
            db_manager,
            st.session_state.get('balance_start', 0),
            st.session_state.get('account_info_open'),
            on_refresh=lambda: load_open_positions(st.session_state)
        )
    
    st.divider()
    
    # 2. Data View Section
    st.header("Data View")
    
    # Get date presets
    date_presets = config.get_date_presets()
    
    # Auto-refresh logic (if enabled) - outside expander
    enable_auto = st.checkbox(
        "Enable Auto-Refresh Every Minute", 
        value=config.AUTO_REFRESH_ENABLED,
        key="main_auto_refresh"
    )
    
    if enable_auto and session_utils.should_auto_refresh(st.session_state):
        handle_auto_refresh(st.session_state, date_presets)
    
    # Initial data load
    if 'magic_profits' not in st.session_state:
        load_initial_data(st.session_state, date_presets)
    
    # Update account_id after data load
    if 'account_id' in st.session_state:
        account_id = st.session_state.account_id
    
    # 2.3. Tabs Section (collapsible, collapsed by default, auto-expand after recalculate)
    tabs_expanded = st.session_state.get('tabs_expanded', False)
    
    with st.expander("📊 Data View Tabs", expanded=tabs_expanded):
        # 2.1. Date Selector and Quick Filters (inside tabs expander)
        recalculate_clicked = date_selector_component.render(st.session_state, date_presets)
        
        # Handle recalculate
        if recalculate_clicked:
            handle_manual_recalculate(st.session_state, date_presets)
            # Auto-expand tabs section after recalculate
            tabs_expanded = True
            st.session_state.tabs_expanded = True
            st.rerun()
        
        # 2.2. Magic Number Selection (inside tabs expander, collapsed by default)
        if account_id != "default":
            # Get previous mode from session state or database
            if 'previous_view_mode' not in st.session_state:
                st.session_state.previous_view_mode = db_manager.get_view_mode(account_id)
            
            previous_view_mode = st.session_state.previous_view_mode
            view_mode = magic_grouping_component.render(account_id, db_manager)
            
            # If view mode changed, recalculate data with new grouping
            if view_mode != previous_view_mode:
                # Check if groups exist when switching to grouped mode
                if view_mode == "grouped":
                    groups_data = db_manager.get_magic_groups(account_id)
                    if not groups_data:
                        st.warning("No groups defined. Please create groups in Settings first.")
                        # Revert to individual mode
                        db_manager.set_view_mode(account_id, "individual")
                        st.session_state.previous_view_mode = "individual"
                        view_mode = "individual"
                    else:
                        # Check if groups have magics assigned
                        groups_with_magics = {
                            gid: gdata for gid, gdata in groups_data.items() 
                            if gdata.get('magics', [])
                        }
                        if not groups_with_magics:
                            st.warning("All groups are empty. Please assign magics to groups in Settings.")
                            db_manager.set_view_mode(account_id, "individual")
                            st.session_state.previous_view_mode = "individual"
                            view_mode = "individual"
                            st.rerun()  # Rerun to update UI after revert
                            return
                
                # Update previous mode and recalculate
                if view_mode != previous_view_mode:
                    st.session_state.previous_view_mode = view_mode
                    
                    # Recalculate if data exists
                    if 'magic_profits' in st.session_state:
                        recalculate_with_grouping(st.session_state, account_id, view_mode)
                        st.rerun()  # Rerun to update UI with recalculated data
                        return
        else:
            view_mode = "individual"
            if 'previous_view_mode' not in st.session_state:
                st.session_state.previous_view_mode = "individual"
        
        # Tabs content
        if 'magic_profits' in st.session_state:
            render_main_content(st.session_state, account_id, view_mode)
        else:
            st.info("Please select a date range and click 'Recalculate' to load data.")
    
    st.divider()
    
    # 3. Settings Section
    if 'magic_profits' in st.session_state and account_id != "default":
        magic_total_sums = st.session_state.magic_profits.get("Total by Magic", {})
        magics = list(magic_total_sums.keys())
        if magics:
            settings_component.render(account_id, db_manager, magics)
        else:
            st.info("No magic numbers found. Load trading data first.")
    elif account_id != "default":
        st.info("Load trading data first to access settings.")


def handle_auto_refresh(session_state, date_presets):
    """Handle auto-refresh functionality"""
    # Check for weekend and adjust period if needed
    if (session_state.pending_from_date.date() == datetime.now().date() 
        and date_utils.is_weekend()):
        preset = date_presets["this_week"]
        session_state.pending_from_date = preset["from"]
        session_state.pending_to_date = preset["to"]
        st.info("Weekend detected during auto-refresh, switching to This Week period.")
    
    # Auto-recalculate historical data
    session_state.from_date = session_state.pending_from_date
    session_state.to_date = session_state.pending_to_date
    
    # Update to_date to current time if it's dynamic (end of day)
    if (session_state.pending_to_date == 
        datetime.combine(session_state.pending_to_date.date(), time(23, 59, 59))):
        session_state.to_date = date_utils.get_current_time()
    
    # Fetch data for selected period (to find which positions to include)
    trade_history, account_info = mt5_data_provider.get_history(
        from_date=session_state.from_date,
        to_date=session_state.to_date
    )
    
    if trade_history is not None:
        account_id = str(account_info.login) if account_info else "default"
        
        # Get full history for positions that have deals in the selected period
        # This includes entry deals before period start
        full_trade_history, _ = mt5_data_provider.get_history(
            from_date=datetime(2020, 1, 1),
            to_date=session_state.to_date
        )
        
        # Find position_ids that have deals in selected period
        position_ids_in_period = set()
        for deal in trade_history:
            if deal._asdict().get('type', 0) != 2:  # Not balance change
                position_id = deal._asdict().get('position_id', 0)
                if position_id != 0:
                    position_ids_in_period.add(position_id)
        
        # Filter full history to include only deals from positions in period
        # But include ALL deals for these positions (entry + exit)
        filtered_full_history = []
        if full_trade_history:
            for deal in full_trade_history:
                deal_dict = deal._asdict()
                position_id = deal_dict.get('position_id', 0)
                # Include all deals for positions that have deals in period
                if position_id != 0 and position_id in position_ids_in_period:
                    filtered_full_history.append(deal)
                # Also include deals in period without position_id (shouldn't happen, but just in case)
                elif position_id == 0:
                    deal_time = datetime.fromtimestamp(deal.time) - timedelta(hours=Config.LOCAL_TIMESHIFT)
                    if (session_state.from_date <= deal_time <= session_state.to_date 
                        and deal_dict.get('type', 0) != 2):
                        filtered_full_history.append(deal)
        
        # Use filtered full history for calculations
        deals_for_calculation = filtered_full_history if filtered_full_history else trade_history
        
        # Get magic groups if grouped mode
        magic_groups = None
        view_mode = db_manager.get_view_mode(account_id)
        if view_mode == "grouped":
            groups_data = db_manager.get_magic_groups(account_id)
            if groups_data:
                magic_groups = {group_id: group_data['magics'] for group_id, group_data in groups_data.items()}
        
        magic_profits = mt5_calculator.calculate_by_magics(
            deals_for_calculation,
            from_date=session_state.from_date,
            to_date=session_state.to_date,
            magic_groups=magic_groups
        )
        
        session_state.magic_profits = magic_profits
        session_state.trade_history = trade_history  # Keep original for display
        session_state.full_trade_history = filtered_full_history if filtered_full_history else trade_history  # Full history for positions
        session_state.account_id = account_id
        
        st.toast("Data auto-recalculated.", icon="🔄", duration=1)
        display_time_in = session_state.from_date
        display_time_out = session_state.to_date
    
    # Auto-refresh open positions
    open_positions, account_info_open = mt5_data_provider.get_open_positions()
    if open_positions is not None:
        open_profits = mt5_calculator.calculate_open_profits_by_magics(open_positions)
        session_state.open_profits = open_profits
        session_state.open_positions = open_positions
        session_state.account_info_open = account_info_open
        st.toast("Open positions auto-refreshed.", icon="🔄", duration=1)
    
    session_utils.update_session_timestamp(session_state)
    st.rerun()


def load_initial_data(session_state, date_presets):
    """Load initial data on first run"""
    # Check for weekend and adjust initial period if needed
    if (session_state.pending_from_date.date() == date_utils.get_today().date() 
        and date_utils.is_weekend()):
        preset = date_presets["this_week"]
        session_state.pending_from_date = preset["from"]
        session_state.pending_to_date = preset["to"]
        st.toast("Weekend detected at launch, switching to This Week period.", icon="ℹ️", duration=1)
    
    session_state.from_date = session_state.pending_from_date
    session_state.to_date = session_state.pending_to_date
    
    # Fetch data for selected period (to find which positions to include)
    trade_history, account_info = mt5_data_provider.get_history(
        from_date=session_state.from_date,
        to_date=session_state.to_date
    )
    
    if trade_history is None:
        st.error("Failed to fetch trade history.")
    else:
        account_id = str(account_info.login) if account_info else "default"
        
        # Get full history for positions that have deals in the selected period
        full_trade_history, _ = mt5_data_provider.get_history(
            from_date=datetime(2020, 1, 1),
            to_date=session_state.to_date
        )
        
        # Find position_ids that have deals in selected period
        position_ids_in_period = set()
        for deal in trade_history:
            if deal._asdict().get('type', 0) != 2:  # Not balance change
                position_id = deal._asdict().get('position_id', 0)
                if position_id != 0:
                    position_ids_in_period.add(position_id)
        
        # Filter full history to include only deals from positions in period
        filtered_full_history = []
        if full_trade_history:
            for deal in full_trade_history:
                deal_dict = deal._asdict()
                position_id = deal_dict.get('position_id', 0)
                if position_id != 0 and position_id in position_ids_in_period:
                    filtered_full_history.append(deal)
                elif position_id == 0:
                    deal_time = datetime.fromtimestamp(deal.time) - timedelta(hours=Config.LOCAL_TIMESHIFT)
                    if (session_state.from_date <= deal_time <= session_state.to_date 
                        and deal_dict.get('type', 0) != 2):
                        filtered_full_history.append(deal)
        
        # Use filtered full history for calculations
        deals_for_calculation = filtered_full_history if filtered_full_history else trade_history
        
        # Get magic groups if grouped mode
        magic_groups = None
        view_mode = db_manager.get_view_mode(account_id)
        if view_mode == "grouped":
            groups_data = db_manager.get_magic_groups(account_id)
            if groups_data:
                magic_groups = {group_id: group_data['magics'] for group_id, group_data in groups_data.items()}
        
        magic_profits = mt5_calculator.calculate_by_magics(
            deals_for_calculation,
            from_date=session_state.from_date,
            to_date=session_state.to_date,
            magic_groups=magic_groups
        )
        
        session_state.magic_profits = magic_profits
        session_state.trade_history = trade_history
        session_state.full_trade_history = filtered_full_history if filtered_full_history else trade_history
        session_state.account_id = account_id
        
        st.toast("Data loaded automatically.", icon="✅", duration=1)
        display_time_in = session_state.from_date
        display_time_out = session_state.to_date


def handle_manual_recalculate(session_state, date_presets):
    """Handle manual recalculate"""
    # Check for weekend and adjust if needed
    if (session_state.pending_from_date.date() == datetime.now().date() 
        and date_utils.is_weekend()):
        preset = date_presets["this_week"]
        session_state.pending_from_date = preset["from"]
        session_state.pending_to_date = preset["to"]
        st.info("Weekend detected during recalculate, switching to This Week period.")
    
    session_state.from_date = session_state.pending_from_date
    session_state.to_date = session_state.pending_to_date
    
    # Fetch data for selected period (to find which positions to include)
    trade_history, account_info = mt5_data_provider.get_history(
        from_date=session_state.from_date,
        to_date=session_state.to_date
    )
    
    if trade_history is None:
        st.error("Failed to fetch trade history.")
    else:
        account_id = str(account_info.login) if account_info else "default"
        
        # Get full history for positions that have deals in the selected period
        full_trade_history, _ = mt5_data_provider.get_history(
            from_date=datetime(2020, 1, 1),
            to_date=session_state.to_date
        )
        
        # Find position_ids that have deals in selected period
        position_ids_in_period = set()
        for deal in trade_history:
            if deal._asdict().get('type', 0) != 2:  # Not balance change
                position_id = deal._asdict().get('position_id', 0)
                if position_id != 0:
                    position_ids_in_period.add(position_id)
        
        # Filter full history to include only deals from positions in period
        filtered_full_history = []
        if full_trade_history:
            for deal in full_trade_history:
                deal_dict = deal._asdict()
                position_id = deal_dict.get('position_id', 0)
                if position_id != 0 and position_id in position_ids_in_period:
                    filtered_full_history.append(deal)
                elif position_id == 0:
                    deal_time = datetime.fromtimestamp(deal.time) - timedelta(hours=Config.LOCAL_TIMESHIFT)
                    if (session_state.from_date <= deal_time <= session_state.to_date 
                        and deal_dict.get('type', 0) != 2):
                        filtered_full_history.append(deal)
        
        # Use filtered full history for calculations
        deals_for_calculation = filtered_full_history if filtered_full_history else trade_history
        
        # Get magic groups if grouped mode
        magic_groups = None
        view_mode = db_manager.get_view_mode(account_id)
        if view_mode == "grouped":
            groups_data = db_manager.get_magic_groups(account_id)
            if groups_data:
                magic_groups = {group_id: group_data['magics'] for group_id, group_data in groups_data.items()}
        
        magic_profits = mt5_calculator.calculate_by_magics(
            deals_for_calculation,
            from_date=session_state.from_date,
            to_date=session_state.to_date,
            magic_groups=magic_groups
        )
        
        session_state.magic_profits = magic_profits
        session_state.trade_history = trade_history
        session_state.full_trade_history = filtered_full_history if filtered_full_history else trade_history
        session_state.account_id = account_id
        
        st.toast("Data recalculated.", icon="✅", duration=1)
        display_time_in = session_state.from_date
        display_time_out = session_state.to_date


def recalculate_with_grouping(session_state, account_id: str, view_mode: str):
    """Recalculate magic_profits with new grouping mode"""
    if 'trade_history' not in session_state:
        return
    
    # Use full_trade_history if available, otherwise use trade_history
    deals_for_calculation = session_state.get('full_trade_history', session_state.trade_history)
    
    # Get magic groups if grouped mode
    magic_groups = None
    if view_mode == "grouped":
        groups_data = db_manager.get_magic_groups(account_id)
        if groups_data:
            # Filter out empty groups
            magic_groups = {
                group_id: group_data['magics'] 
                for group_id, group_data in groups_data.items() 
                if group_data['magics']  # Only include groups with magics
            }
            
            if not magic_groups:
                st.warning("All groups are empty. Please assign magics to groups in Settings.")
                return
    
    # Recalculate with new grouping
    magic_profits = mt5_calculator.calculate_by_magics(
        deals_for_calculation,
        from_date=session_state.from_date,
        to_date=session_state.to_date,
        magic_groups=magic_groups
    )
    
    session_state.magic_profits = magic_profits
    mode_text = "grouped" if view_mode == "grouped" else "individual"
    st.toast(f"Data recalculated with {mode_text} mode.", icon="🔄", duration=2)


def load_open_positions(session_state):
    """Load open positions data"""
    open_positions, account_info = mt5_data_provider.get_open_positions()
    if open_positions is None:
        st.error("Failed to fetch open positions.")
    else:
        account_id = str(account_info.login) if account_info else "default"
        open_profits = mt5_calculator.calculate_open_profits_by_magics(open_positions)
        
        session_state.open_profits = open_profits
        session_state.open_positions = open_positions
        session_state.account_id = account_id
        
        st.toast("Open positions loaded.", icon="✅", duration=1)
        session_state.account_info_open = account_info


def render_main_content(session_state, account_id: str, view_mode: str):
    """Render main application content"""
    magic_profits = session_state.magic_profits
    trade_history = session_state.trade_history
    
    magic_total_sums = magic_profits["Total by Magic"]
    total_summ = magic_profits["Summ"]
    magics = list(magic_total_sums.keys())
    
    # Get magic groups if grouped mode
    magic_groups = None
    if view_mode == "grouped":
        groups_data = db_manager.get_magic_groups(account_id)
        if groups_data:
            # Convert to format expected by calculate_by_magics: {group_id: [magics]}
            magic_groups = {group_id: group_data['magics'] for group_id, group_data in groups_data.items()}
    
    # Create tabs - updated tab names
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Chart", "Results", "Time Distribution", "Distribution", "Deals"])

    # Calculate balance at the beginning of the period
    # Use full_trade_history from session state if available
    full_trade_history = session_state.get('full_trade_history')
    
    if full_trade_history is None:
        # Get full history if not in session state
        full_trade_history, _ = mt5_data_provider.get_history(
            from_date=datetime(2020, 1, 1),
            to_date=session_state.to_date
        )
    
    if full_trade_history is not None:
        balance_at_start = mt5_calculator.calculate_balance_at_date(
            target_date=session_state.from_date,
            deals=full_trade_history,
            end_of_day=False  # Beginning of day
        )
    else:
        # Fallback на ограниченные данные если полная история недоступна
        balance_at_start = mt5_calculator.calculate_balance_at_date(
            target_date=session_state.from_date,
            deals=trade_history,
            end_of_day=False  # Beginning of day
        )
    
    session_state.balance_start = balance_at_start
    
    # Render each tab
    with tab1:
        chart_page.render()
    
    with tab2:
        results_page.render(
            magic_profits,
            account_id,
            db_manager,
            balance_at_start,
            config.CUSTOM_TEXT,
            session_state.from_date,
            session_state.to_date,
            magic_groups=magic_groups,
            full_trade_history=session_state.get('full_trade_history'),
            from_date=session_state.from_date,
            to_date=session_state.to_date
        )
    
    with tab3:
        # Use full_trade_history for consistency with calculations
        full_history_for_time = session_state.get('full_trade_history', trade_history)
        deals_by_hour_page.render(
            trade_history,
            from_date=session_state.from_date,
            to_date=session_state.to_date,
            full_trade_history=full_history_for_time
        )
    
    with tab4:
        distribution_page.render(magic_profits, account_id, db_manager, magic_groups=magic_groups)
    
    with tab5:
        # Use full_trade_history from session state for positions aggregation
        full_history_for_deals = session_state.get('full_trade_history', trade_history)
        deals_page.render(
            trade_history, 
            account_id, 
            db_manager,
            full_trade_history=full_history_for_deals,
            from_date=session_state.from_date,
            to_date=session_state.to_date,
            magic_groups=magic_groups
        )


if __name__ == "__main__":
    main()
