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
from src.ui.components.ui_components import date_range_component, magic_description_component
from src.ui.pages.pages import (
    open_positions_page, results_page, 
    distribution_page, deals_by_hour_page
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
    
    # Application title
    st.title(config.APP_NAME)
    
    # Auto-refresh checkbox
    enable_auto = st.checkbox(
        "Enable Auto-Refresh Every Minute", 
        value=config.AUTO_REFRESH_ENABLED
    )
    
    # Get date presets
    date_presets = config.get_date_presets()
    
    # Date range inputs
    pending_from, pending_to = date_range_component.render_date_inputs(st.session_state)
    
    # Update pending values
    st.session_state.pending_from_date = datetime.combine(pending_from, time(0, 0))
    st.session_state.pending_to_date = datetime.combine(pending_to, time(23, 59, 59))
    
    display_time_in = st.session_state.from_date
    display_time_out = st.session_state.to_date
    
    # Preset buttons
    date_range_component.render_preset_buttons(st.session_state, date_presets)
    
    # Auto-refresh logic
    if enable_auto and session_utils.should_auto_refresh(st.session_state):
        handle_auto_refresh(st.session_state, date_presets)
    
    # Initial data load
    if 'magic_profits' not in st.session_state:
        load_initial_data(st.session_state, date_presets)
    
    # Manual recalculate button
    if st.button("Recalculate"):
        handle_manual_recalculate(st.session_state, date_presets)
    
    # Load open positions
    if 'open_profits' not in st.session_state:
        load_open_positions(st.session_state)
    
    # Refresh open positions button
    if st.button("Refresh Open Positions"):
        load_open_positions(st.session_state)
    
    # Main content
    if 'magic_profits' in st.session_state:
        render_main_content(st.session_state)


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
    
    # Fetch and process data
    trade_history, account_info = mt5_data_provider.get_history(
        from_date=session_state.from_date + timedelta(hours=config.LOCAL_TIMESHIFT),
        to_date=session_state.to_date + timedelta(hours=config.LOCAL_TIMESHIFT)
    )
    
    if trade_history is not None:
        account_id = str(account_info.login) if account_info else "default"
        magic_profits = mt5_calculator.calculate_by_magics(
            trade_history,
            from_date=session_state.from_date,
            to_date=session_state.to_date
        )
        
        session_state.magic_profits = magic_profits
        session_state.trade_history = trade_history
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
    
    trade_history, account_info = mt5_data_provider.get_history(
        from_date=session_state.from_date + timedelta(hours=config.LOCAL_TIMESHIFT),
        to_date=session_state.to_date + timedelta(hours=config.LOCAL_TIMESHIFT)
    )
    
    if trade_history is None:
        st.error("Failed to fetch trade history.")
    else:
        account_id = str(account_info.login) if account_info else "default"
        magic_profits = mt5_calculator.calculate_by_magics(
            trade_history,
            from_date=session_state.from_date,
            to_date=session_state.to_date
        )
        
        session_state.magic_profits = magic_profits
        session_state.trade_history = trade_history
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
    
    trade_history, account_info = mt5_data_provider.get_history(
        from_date=session_state.from_date + timedelta(hours=config.LOCAL_TIMESHIFT),
        to_date=session_state.to_date + timedelta(hours=config.LOCAL_TIMESHIFT)
    )
    
    if trade_history is None:
        st.error("Failed to fetch trade history.")
    else:
        account_id = str(account_info.login) if account_info else "default"
        magic_profits = mt5_calculator.calculate_by_magics(
            trade_history,
            from_date=session_state.from_date,
            to_date=session_state.to_date
        )
        
        session_state.magic_profits = magic_profits
        session_state.trade_history = trade_history
        session_state.account_id = account_id
        
        st.toast("Data recalculated.", icon="✅", duration=1)
        display_time_in = session_state.from_date
        display_time_out = session_state.to_date


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


def render_main_content(session_state):
    """Render main application content"""
    magic_profits = session_state.magic_profits
    trade_history = session_state.trade_history
    account_id = session_state.account_id
    
    magic_total_sums = magic_profits["Total by Magic"]
    total_summ = magic_profits["Summ"]
    magics = list(magic_total_sums.keys())
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(UIConfig.TABS)
    
    # Render each tab
    with tab1:
        open_positions_page.render(
            session_state.get('open_profits', {}),
            account_id,
            db_manager,
            config.BALANCE_START,
            session_state.get('account_info_open')
        )
        
        # Magic descriptions management
        magic_description_component.render_magic_descriptions(magics, account_id, db_manager)
    
    with tab2:
        results_page.render(
            magic_profits,
            account_id,
            db_manager,
            config.BALANCE_START,
            config.CUSTOM_TEXT,
            session_state.from_date,
            session_state.to_date
        )
    
    with tab3:
        distribution_page.render(magic_profits, account_id, db_manager)
    
    with tab4:
        deals_by_hour_page.render(trade_history)


if __name__ == "__main__":
    main()
