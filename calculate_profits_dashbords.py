import MetaTrader5 as mt5
from datetime import datetime, timedelta, time
import psutil
import pprint
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import time as time_mod

# Run command:
# streamlit run calculate_profits_dashbords.py

# Установка заголовка вкладки браузера
st.set_page_config(page_title="Trading Dashboard")
# Custom CSS для размещения toast вверху по центру
st.markdown("""
<style>
div.stToast {
    position: fixed;
    top: 10px;  /* Отступ от верха */
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;  /* Над всем контентом */
    width: auto;  /* Авто-ширина */
    max-width: 80%;  /* Не шире экрана */
}
div.stToast > div {
    background-color: #28a745;  /* Зелёный фон, как у st.success */
    color: white;
    padding: 10px 20px;
    border-radius: 5px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

balance_start = 8736
custom_text = "2nd week of October"

LOCAL_TIMESHIFT = 3
pp = pprint.PrettyPrinter(indent=4)


def check_mt5_process():
    mt5_processes = [proc for proc in psutil.process_iter() if 'terminal64.exe' in proc.name()]
    return mt5_processes


def get_history(account=None, from_date=datetime(2020, 1, 1),
                to_date=datetime.now() + timedelta(hours=LOCAL_TIMESHIFT)):
    mt5_processes = check_mt5_process()
    all_terminal_exes = False
    if mt5_processes:
        all_terminal_exes = [process.exe() for process in mt5_processes]

    if all_terminal_exes and not mt5.initialize(all_terminal_exes[0]):
        mt5.initialize()

    if not all_terminal_exes:
        mt5.initialize()

    if account:
        authorized = mt5.login(account['login'], account['password'], account['server'])
        if not authorized:
            mt5.shutdown()
            return None

    account_info = mt5.account_info()
    if account_info is None:
        mt5.shutdown()
        return None

    deals = mt5.history_deals_get(from_date, to_date)
    mt5.shutdown()

    return deals, account_info


def get_open_positions(account=None):
    mt5_processes = check_mt5_process()
    all_terminal_exes = False
    if mt5_processes:
        all_terminal_exes = [process.exe() for process in mt5_processes]

    if all_terminal_exes and not mt5.initialize(all_terminal_exes[0]):
        mt5.initialize()

    if not all_terminal_exes:
        mt5.initialize()

    if account:
        authorized = mt5.login(account['login'], account['password'], account['server'])
        if not authorized:
            mt5.shutdown()
            return None

    account_info = mt5.account_info()
    if account_info is None:
        mt5.shutdown()
        return None

    positions = mt5.positions_get()
    mt5.shutdown()

    return list(positions), account_info


def calculate_open_profits_by_magics(positions):
    magic_profits = {}
    magics_total = {}
    magic_symbol_type = {}  # Nested: magic -> symbol -> type -> profit

    for pos in positions:
        if pos.type == 0:  # Buy
            type_str = "Buy"
        elif pos.type == 1:  # Sell
            type_str = "Sell"
        else:
            continue

        magic_key = pos.magic
        symbol_key = pos.symbol
        full_key = (magic_key, symbol_key, type_str)

        # Initialize nested dict
        if magic_key not in magic_symbol_type:
            magic_symbol_type[magic_key] = {}
        if symbol_key not in magic_symbol_type[magic_key]:
            magic_symbol_type[magic_key][symbol_key] = {}
        if type_str not in magic_symbol_type[magic_key][symbol_key]:
            magic_symbol_type[magic_key][symbol_key][type_str] = 0.0

        profit = pos.profit + pos.swap  # For open positions, commission is not yet applied
        magic_symbol_type[magic_key][symbol_key][type_str] += profit

        # Update totals
        if magic_key not in magics_total:
            magics_total[magic_key] = 0.0
        magics_total[magic_key] += profit

        if full_key not in magic_profits:
            magic_profits[full_key] = 0.0
        magic_profits[full_key] += profit

    total_floating = sum(magics_total.values())
    return {
        "by_magic": magics_total,
        "total_floating": total_floating,
        "detailed": magic_symbol_type
    }


def calculate_by_magics(deals, symbol=None, from_date=None, to_date=None):
    magic_profits = {}
    magics_summ = 0
    magic_total_sums = {}

    for deal in deals:
        if deal.type == 2:  # Balance changes
            continue
        if from_date and deal.time < from_date.timestamp():
            continue
        if to_date and deal.time > to_date.timestamp():
            continue

        magic_key = deal.magic
        if magic_key == 0:
            for d in deals:
                if d.position_id == deal.position_id and d.magic != 0:
                    magic_key = d.magic
                    break

        symbol_key = deal.symbol if symbol is None else symbol
        key = (magic_key, symbol_key)

        if key not in magic_profits:
            magic_profits[key] = 0.0

        magic_profits[key] += deal.profit + deal.commission + deal.swap
        magics_summ += deal.profit + deal.commission + deal.swap

        if magic_key not in magic_total_sums:
            magic_total_sums[magic_key] = 0.0
        magic_total_sums[magic_key] += deal.profit + deal.commission + deal.swap

    magic_profits["Summ"] = magics_summ
    if magic_total_sums and magic_total_sums.get(0) is not None:
        magic_profits["Summ only magics"] = magics_summ - magic_total_sums[0]
    magic_profits["Total by Magic"] = magic_total_sums

    return magic_profits


def init_db():
    conn = sqlite3.connect('magics.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS magic_descriptions
                 (account TEXT, magic INTEGER, description TEXT, PRIMARY KEY(account, magic))''')
    conn.commit()
    conn.close()


def get_description(account, magic):
    conn = sqlite3.connect('magics.db')
    c = conn.cursor()
    c.execute("SELECT description FROM magic_descriptions WHERE account=? AND magic=?", (account, magic))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None


def set_description(account, magic, description):
    conn = sqlite3.connect('magics.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO magic_descriptions (account, magic, description) VALUES (?, ?, ?)",
              (account, magic, description))
    conn.commit()
    conn.close()


init_db()

st.title("Trading Dashboard")

enable_auto = st.checkbox("Enable Auto-Refresh Every Minute", value=True)

now = datetime.now()
today = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=LOCAL_TIMESHIFT)
start_of_week = today - timedelta(days=now.weekday())
start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=LOCAL_TIMESHIFT)
start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(
    hours=LOCAL_TIMESHIFT)

if 'from_date' not in st.session_state:
    st.session_state.from_date = today
if 'to_date' not in st.session_state:
    st.session_state.to_date = now + timedelta(hours=LOCAL_TIMESHIFT)

# --- Pending dates (user input) ---
if 'pending_from_date' not in st.session_state:
    st.session_state.pending_from_date = st.session_state.from_date
if 'pending_to_date' not in st.session_state:
    st.session_state.pending_to_date = st.session_state.to_date

col1, col2 = st.columns(2)
pending_from = col1.date_input("From Date", value=st.session_state.pending_from_date.date())
pending_to = col2.date_input("To Date", value=st.session_state.pending_to_date.date())

# Обновляем только pending значения (без пересчёта)
st.session_state.pending_from_date = datetime.combine(pending_from, time(0, 0))
st.session_state.pending_to_date = datetime.combine(pending_to, time(23, 59, 59))

display_time_in = st.session_state.from_date
display_time_out = st.session_state.to_date

col_btn1, col2, col3, col4 = st.columns(4)
if col_btn1.button("Today"):
    if now.weekday() in [5, 6]:  # Saturday or Sunday
        st.session_state.pending_from_date = start_of_week
        st.session_state.pending_to_date = now + timedelta(hours=LOCAL_TIMESHIFT)
        st.info("Weekend detected, switching to This Week period.")
    else:
        st.session_state.pending_from_date = today
        st.session_state.pending_to_date = now + timedelta(hours=LOCAL_TIMESHIFT)
    st.rerun()

if col2.button("This Week"):
    st.session_state.pending_from_date = start_of_week
    st.session_state.pending_to_date = now + timedelta(hours=LOCAL_TIMESHIFT)
    st.rerun()

if col3.button("This Month"):
    st.session_state.pending_from_date = start_of_month
    st.session_state.pending_to_date = now + timedelta(hours=LOCAL_TIMESHIFT)
    st.rerun()

if col4.button("This Year"):
    st.session_state.pending_from_date = start_of_year
    st.session_state.pending_to_date = now + timedelta(hours=LOCAL_TIMESHIFT)
    st.rerun()

# Auto-refresh logic
if 'last_update' not in st.session_state:
    st.session_state.last_update = time_mod.time()

current_time = time_mod.time()
auto_refresh_interval = 60  # seconds

if enable_auto and current_time - st.session_state.last_update >= auto_refresh_interval:
    # Check for weekend and adjust period if needed
    if st.session_state.pending_from_date.date() == datetime.now().date() and datetime.now().weekday() in [5, 6]:
        st.session_state.pending_from_date = start_of_week
        st.session_state.pending_to_date = datetime.now() + timedelta(hours=LOCAL_TIMESHIFT)
        st.info("Weekend detected during auto-refresh, switching to This Week period.")

    # Auto-recalculate historical data
    st.session_state.from_date = st.session_state.pending_from_date
    st.session_state.to_date = st.session_state.pending_to_date
    # Update to_date to current time if it's dynamic (end of day)
    if st.session_state.pending_to_date == datetime.combine(st.session_state.pending_to_date.date(), time(23, 59, 59)):
        st.session_state.to_date = datetime.now() + timedelta(hours=LOCAL_TIMESHIFT)
    trade_history, account_info = get_history(
        from_date=st.session_state.from_date + timedelta(hours=LOCAL_TIMESHIFT),
        to_date=st.session_state.to_date + timedelta(hours=LOCAL_TIMESHIFT)
    )
    if trade_history is not None:
        account_id = str(account_info.login) if account_info else "default"
        magic_profits = calculate_by_magics(
            trade_history,
            from_date=st.session_state.from_date,
            to_date=st.session_state.to_date
        )
        st.session_state.magic_profits = magic_profits
        st.session_state.trade_history = trade_history
        st.session_state.account_id = account_id
        st.toast("Data auto-recalculated.", icon="🔄", duration=1)
        display_time_in = st.session_state.from_date
        display_time_out = st.session_state.to_date

    # Auto-refresh open positions
    open_positions, account_info_open = get_open_positions()
    if open_positions is not None:
        open_profits = calculate_open_profits_by_magics(open_positions)
        st.session_state.open_profits = open_profits
        st.session_state.open_positions = open_positions
        st.session_state.account_info_open = account_info_open
        st.toast("Open positions auto-refreshed.", icon="🔄", duration=1)

    st.session_state.last_update = current_time
    st.rerun()

# Автоматический расчёт при первом запуске (если данных ещё нет)
if 'magic_profits' not in st.session_state:
    # Check for weekend and adjust initial period if needed
    if st.session_state.pending_from_date.date() == today.date() and now.weekday() in [5, 6]:
        st.session_state.pending_from_date = start_of_week
        st.session_state.pending_to_date = now + timedelta(hours=LOCAL_TIMESHIFT)
        st.toast("Weekend detected at launch, switching to This Week period.", icon="ℹ️", duration=1)

    st.session_state.from_date = st.session_state.pending_from_date
    st.session_state.to_date = st.session_state.pending_to_date
    trade_history, account_info = get_history(
        from_date=st.session_state.from_date + timedelta(hours=LOCAL_TIMESHIFT),
        to_date=st.session_state.to_date + timedelta(hours=LOCAL_TIMESHIFT)
    )
    if trade_history is None:
        st.error("Failed to fetch trade history.")
    else:
        account_id = str(account_info.login) if account_info else "default"
        magic_profits = calculate_by_magics(
            trade_history,
            from_date=st.session_state.from_date,
            to_date=st.session_state.to_date
        )
        st.session_state.magic_profits = magic_profits
        st.session_state.trade_history = trade_history
        st.session_state.account_id = account_id
        st.toast("Data loaded automatically.", icon="✅", duration=1)
        display_time_in = st.session_state.from_date
        display_time_out = st.session_state.to_date

if st.button("Recalculate"):
    # Check for weekend and adjust if needed
    if st.session_state.pending_from_date.date() == datetime.now().date() and datetime.now().weekday() in [5, 6]:
        st.session_state.pending_from_date = start_of_week
        st.session_state.pending_to_date = datetime.now() + timedelta(hours=LOCAL_TIMESHIFT)
        st.info("Weekend detected during recalculate, switching to This Week period.")

    st.session_state.from_date = st.session_state.pending_from_date
    st.session_state.to_date = st.session_state.pending_to_date
    trade_history, account_info = get_history(
        from_date=st.session_state.from_date + timedelta(hours=LOCAL_TIMESHIFT),
        to_date=st.session_state.to_date + timedelta(hours=LOCAL_TIMESHIFT)
    )
    if trade_history is None:
        st.error("Failed to fetch trade history.")
    else:
        account_id = str(account_info.login) if account_info else "default"
        magic_profits = calculate_by_magics(
            trade_history,
            from_date=st.session_state.from_date,
            to_date=st.session_state.to_date
        )
        st.session_state.magic_profits = magic_profits
        st.session_state.trade_history = trade_history
        st.session_state.account_id = account_id
        st.toast("Data recalculated.", icon="✅", duration=1)
        display_time_in = st.session_state.from_date
        display_time_out = st.session_state.to_date

# Fetch open positions on load or recalculate
if 'open_profits' not in st.session_state:
    open_positions, account_info = get_open_positions()
    if open_positions is None:
        st.error("Failed to fetch open positions.")
    else:
        account_id = str(account_info.login) if account_info else "default"
        open_profits = calculate_open_profits_by_magics(open_positions)
        st.session_state.open_profits = open_profits
        st.session_state.open_positions = open_positions
        st.session_state.account_id = account_id  # Reuse if same
        st.toast("Open positions loaded.", icon="✅", duration=1)
        st.session_state.account_info_open = account_info

if st.button("Refresh Open Positions"):
    open_positions, account_info = get_open_positions()
    if open_positions is None:
        st.error("Failed to fetch open positions.")
    else:
        account_id = str(account_info.login) if account_info else "default"
        open_profits = calculate_open_profits_by_magics(open_positions)
        st.session_state.open_profits = open_profits
        st.session_state.open_positions = open_positions
        st.session_state.account_id = account_id
        st.toast("Open positions refreshed.", icon="✅", duration=1)
        st.session_state.account_info_open = account_info

if 'magic_profits' in st.session_state:
    magic_profits = st.session_state.magic_profits
    trade_history = st.session_state.trade_history
    account_id = st.session_state.account_id

    magic_total_sums = magic_profits["Total by Magic"]
    total_summ = magic_profits["Summ"]

    magics = list(magic_total_sums.keys())
    labels = {m: f"{m} - {get_description(account_id, m)}" if get_description(account_id, m) else str(m) for m in
              magics}
    labels_tab1 = {m: f"{get_description(account_id, m)} - {m}" if get_description(account_id, m) else str(m) for m in
                   magics}

    tab1, tab2, tab3, tab4 = st.tabs(["Open Positions", "Results", "Distribution", "Deals by Hour"])

    # New Open Positions tab
    with tab1:
        st.subheader("Open Positions")
        if 'open_profits' in st.session_state:
            open_profits = st.session_state.open_profits
            detailed = open_profits["detailed"]
            by_magic = open_profits["by_magic"]
            total_floating = open_profits["total_floating"]
            account_info_open = st.session_state.get('account_info_open', None)
            current_balance = account_info_open.balance if account_info_open else balance_start

            magics_open = list(by_magic.keys()) if by_magic else []
            labels_open = {
                m: f"{m} - {get_description(account_id, m)}" if get_description(account_id, m) else str(m)
                for m in magics_open}

            st.write(f"Current Floating P/L: {total_floating:.2f}")

            # Calculate percentages
            percentages = [(by_magic[m] / current_balance * 100) if current_balance != 0 else 0 for m in
                           magics_open]

            df_open_results = pd.DataFrame({
                'Magic': magics_open,
                'Label': [f"${by_magic[m]:.2f} ({percentages[i]:+.2f}%) - {labels_open[m]}" for i, m in
                          enumerate(magics_open)],
                'Floating': [round(by_magic[m], 2) for m in magics_open]
            })

            # Sort options similar to tab2
            sort_options = ["Floating ↓", "Floating ↑", "Magics ↓", "Magics ↑"]
            sort_option_open = st.selectbox("Sort by", sort_options, index=0)

            if sort_option_open == "Magics ↓":
                df_open_results = df_open_results.sort_values('Magic')
            elif sort_option_open == "Magics ↑":
                df_open_results = df_open_results.sort_values('Magic', ascending=False)
            elif sort_option_open == "Floating ↓":
                df_open_results = df_open_results.sort_values('Floating')
            elif sort_option_open == "Floating ↑":
                df_open_results = df_open_results.sort_values('Floating', ascending=False)

            # Bar chart similar to tab2
            fig_open = px.bar(df_open_results, x='Floating', y='Label', orientation='h',
                              color='Floating', color_continuous_scale='RdYlGn',
                              color_continuous_midpoint=0)
            fig_open.update_yaxes(type='category')

            current_balance = account_info_open.balance if account_info_open else balance_start
            percent_floating = (total_floating / current_balance * 100) if current_balance != 0 else 0
            change_color_open = "lime" if percent_floating >= 0 else "orange" if percent_floating >= -12 else "OrangeRed" if percent_floating >= -20 else "Red"
            fig_open.add_annotation(
                text=f"Current Floating P/L: {total_floating:.2f} USD ({percent_floating:+.2f}%)<br>Current Balance: {current_balance:.2f}",
                xref="paper", yref="paper", x=0.5, y=1,
                xanchor="center", yanchor="top", yshift=60,
                showarrow=False,
                font=dict(size=14, color=change_color_open, family="Arial"),
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="rgba(255,255,255,0.5)",
                borderwidth=1,
                borderpad=5
            )

            num_bars_open = len(df_open_results)
            fig_open.update_layout(
                height=max(300, num_bars_open * 30),
                showlegend=False,
                margin=dict(t=100, b=40, l=40, r=20)
            )

            st.plotly_chart(fig_open)

            # Drill-down: Select magic for symbol and type breakdown
            selected_magic_open = st.selectbox("Select Magic for Details (None for Overview)", [None] + magics_open)

            if selected_magic_open is not None and selected_magic_open in detailed:
                symbols_for_magic = detailed[selected_magic_open]
                st.subheader(f"Breakdown for Magic {selected_magic_open} ({labels_open[selected_magic_open]})")

                # Flatten for display: symbol - type - profit
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

                    # Bar chart for breakdown
                    fig_breakdown = px.bar(df_breakdown, x='Floating', y='Label', orientation='h',
                                           color='Floating', color_continuous_scale='RdYlGn',
                                           color_continuous_midpoint=0)
                    fig_breakdown.update_yaxes(type='category')
                    fig_breakdown.update_layout(
                        height=max(300, len(df_breakdown) * 30),
                        showlegend=False,
                        margin=dict(t=40, b=40, l=40, r=20)
                    )
                    st.plotly_chart(fig_breakdown)

                    # Table for precise values
                    st.dataframe(df_breakdown[['Symbol', 'Type', 'Floating']].round(2))

        with st.expander("Manage Magic Descriptions"):
            for magic in magics:
                col1, col2, col3 = st.columns([2, 3, 1])
                col1.write(f"Magic {magic}:")
                desc = get_description(account_id, magic)
                new_desc = col2.text_input("", value=desc or "", key=f"desc_{magic}_{account_id}")
                if col3.button("Save", key=f"save_{magic}_{account_id}"):
                    set_description(account_id, magic, new_desc)
                    st.success(f"Description for Magic {magic} saved.")


    # Updated Results tab section
    with tab2:
        st.subheader("Results")
        st.write(f"Period:")
        st.write(f"From {display_time_in} to {display_time_out}")
        st.write(f"Total Result: {total_summ:.2f}")

        df_results = pd.DataFrame({
            'Magic': magics,
            'Label': [f"${magic_total_sums[m]:.2f}  -  {labels_tab1[m]}" for m in magics],
            'Result': [round(magic_total_sums[m], 2) for m in magics]
        })

        # Updated sort options with arrows and default to "Results ↓"
        sort_options = ["Results ↓", "Results ↑", "Magics ↓", "Magics ↑"]
        sort_option = st.selectbox("Sort by", sort_options, index=0)  # Default to "Results ↓"

        # Mapping sort_option to sorting logic
        if sort_option == "Magics ↓":
            df_results = df_results.sort_values('Magic')
        elif sort_option == "Magics ↑":
            df_results = df_results.sort_values('Magic', ascending=False)
        elif sort_option == "Results ↓":
            df_results = df_results.sort_values('Result')
        elif sort_option == "Results ↑":
            df_results = df_results.sort_values('Result', ascending=False)

        # Построение графика
        fig_results = px.bar(df_results, x='Result', y='Label', orientation='h',
                             color='Result', color_continuous_scale='RdYlGn',
                             color_continuous_midpoint=0)

        # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Принудительно устанавливаем тип оси Y как category
        fig_results.update_yaxes(type='category')  # Это исправит слияние и шкалу

        change_color = "lime" if total_summ >= 0 else "red"
        percent_change = (total_summ / balance_start * 100) if balance_start != 0 else 0
        # Добавляем текст Total Result внизу графика
        fig_results.add_annotation(
            text=f"{custom_text}<br><br>Total Result: {total_summ:.2f} USD ({percent_change:+.2f}%)<br>Start Balance: {balance_start:.2f}",
            xref="paper",  # относительно всей области графика
            yref="paper",
            x=0.5,  # по центру по горизонтали (0 — слева, 1 — справа)
            y=1.15,
            showarrow=False,
            font=dict(size=14, color=change_color, family="Arial"),
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="rgba(255,255,255,0.5)",
            borderwidth=1,
            borderpad=5
        )

        # Дополнительно: Автоматическая высота на основе количества баров (чтобы все помещались без скролла)
        num_bars = len(df_results)
        fig_results.update_layout(
            height=max(300, num_bars * 30),
            showlegend=False,
            margin=dict(t=120, b=40, l=40, r=20)  # Увеличен top
        )

        st.plotly_chart(fig_results)

    with tab3:
        st.subheader("Distribution of Profits / Losses")

        selected_magic = st.selectbox("Select Magic for Symbol Details (None for Overall)", [None] + magics)

        if selected_magic is None:
            df_pos = pd.DataFrame({
                'Label': [f"{labels[m]}  -  ${magic_total_sums[m]:.2f}" for m in magics if magic_total_sums[m] > 0],
                'Profit': [v for m, v in magic_total_sums.items() if v > 0]
            })
            df_neg = pd.DataFrame({
                'Label': [f"{labels[m]}  -  ${magic_total_sums[m]:.2f}" for m in magics if magic_total_sums[m] < 0],
                'Loss': [abs(v) for m, v in magic_total_sums.items() if v < 0]
            })

            if not df_pos.empty:
                fig_pos = px.pie(df_pos, values='Profit', names='Label', title="Profit Distribution")
                st.plotly_chart(fig_pos)

            if not df_neg.empty:
                fig_neg = px.pie(df_neg, values='Loss', names='Label', title="Loss Distribution")
                st.plotly_chart(fig_neg)
        else:
            # Filter valid (magic, symbol) tuple keys where magic matches selected_magic
            per_symbol = {key[1]: val for key, val in magic_profits.items() if
                          isinstance(key, tuple) and len(key) == 2 and isinstance(key[0], (int, float)) and isinstance(
                              key[1], str) and key[0] == selected_magic}
            df_pos_sym = pd.DataFrame({
                'Symbol': [s for s, v in per_symbol.items() if v > 0],
                'Profit': [v for v in per_symbol.values() if v > 0]
            })
            df_neg_sym = pd.DataFrame({
                'Symbol': [s for s, v in per_symbol.items() if v < 0],
                'Loss': [abs(v) for v in per_symbol.values() if v < 0]
            })

            if not df_pos_sym.empty:
                fig_pos_sym = px.pie(df_pos_sym, values='Profit', names='Symbol',
                                     title=f"Profit Distribution for Magic {selected_magic}")
                st.plotly_chart(fig_pos_sym)
            if not df_neg_sym.empty:
                fig_neg_sym = px.pie(df_neg_sym, values='Loss', names='Symbol',
                                     title=f"Loss Distribution for Magic {selected_magic}")
                st.plotly_chart(fig_neg_sym)

    # Updated Deals by Hour tab section
    with tab4:
        st.subheader("Deals by Hour")
        if not trade_history or len(trade_history) == 0:
            st.info("No deals in the selected period.")
        else:
            df_deals = pd.DataFrame([d._asdict() for d in trade_history])
            if df_deals.empty:
                st.info("No deals to display.")
            else:
                df_deals = df_deals[df_deals['type'] != 2]
                df_deals['time_dt'] = pd.to_datetime(df_deals['time'], unit='s')
                df_deals['hour'] = df_deals['time_dt'].dt.hour
                counts = df_deals.groupby('hour').size().reset_index(name='count')
                counts = counts.sort_values('hour')
                counts['hour'] = counts['hour'].astype(str)  # For labeling

                # Changed to vertical bar chart: hours on x-axis (horizontal), deals on y-axis (vertical)
                fig_hours = px.bar(counts, x='hour', y='count',
                                   labels={'count': 'Number of Deals', 'hour': 'Hour'})
                st.plotly_chart(fig_hours)