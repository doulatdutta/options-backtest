import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# Add core modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

# Import core modules with fallback
try:
    from core.parser import TradingViewParser
    from core.engine import BacktestEngine
    from core.expiry_rules import ExpiryCalculator
    from core.strike_rules import StrikeCalculator
    from core.upstox_api import UpstoxAPI
    from core.report import ReportGenerator
except ImportError:
    from parser import TradingViewParser
    from engine import BacktestEngine
    from expiry_rules import ExpiryCalculator
    from strike_rules import StrikeCalculator
    from upstox_api import UpstoxAPI
    from report import ReportGenerator

# Page configuration
st.set_page_config(
    page_title="Options Backtesting Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Theme Initialisation ---
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'light'

def apply_theme():
    """Inject CSS based on the current theme stored in session_state"""
    dark = st.session_state['theme'] == 'dark'

    bg_main       = '#0e1117' if dark else '#ffffff'
    bg_sidebar    = '#161b22' if dark else '#f0f2f6'
    bg_card       = '#1e2530' if dark else '#f0f2f6'
    text_primary  = '#e6edf3' if dark else '#1a1a2e'
    text_h1       = '#58a6ff' if dark else '#1f77b4'
    text_h2       = '#ffa657' if dark else '#ff7f0e'
    border_color  = '#30363d' if dark else '#d0d7de'
    input_bg      = '#161b22' if dark else '#ffffff'
    input_border  = '#388bfd' if dark else '#1f77b4'
    btn_bg        = '#238636' if dark else '#1f77b4'
    btn_hover     = '#2ea043' if dark else '#1565c0'
    metric_val    = '#58a6ff' if dark else '#1a73e8'

    st.markdown(f"""
    <style>
        /* ===== Overall background ===== */
        .stApp {{ background-color: {bg_main}; color: {text_primary}; }}
        section[data-testid="stSidebar"] {{ background-color: {bg_sidebar}; }}

        /* ===== Typography ===== */
        h1, .stTitle {{ color: {text_h1} !important; padding-bottom: 10px; }}
        h2, h3 {{ color: {text_h2} !important; padding-top: 10px; }}
        p, label, div, span {{ color: {text_primary}; }}

        /* ===== Metric cards ===== */
        div[data-testid="stMetric"] {{
            background-color: {bg_card};
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid {border_color};
        }}
        div[data-testid="stMetricValue"] {{ color: {metric_val} !important; }}

        /* ===== Text / Password inputs only (NOT dropdowns) ===== */
        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea {{
            background-color: {input_bg} !important;
            color: {text_primary} !important;
            border-radius: 6px !important;
        }}
        /* Selectbox dropdown container */
        div[data-baseweb="select"] > div:first-child {{
            background-color: {input_bg} !important;
            color: {text_primary} !important;
            border: 1px solid {border_color} !important;
            border-radius: 6px !important;
        }}

        /* ===== Upload area ===== */
        .uploadedFile {{
            border: 2px dashed {input_border};
            border-radius: 8px;
            padding: 20px;
            background-color: {bg_card};
        }}

        /* ===== Dataframe / Table ===== */
        .stDataFrame {{ border: 1px solid {border_color}; border-radius: 8px; }}

        /* ===== Tabs ===== */
        button[data-baseweb="tab"] {{
            color: {text_primary} !important;
            background-color: transparent !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            border-bottom: 3px solid {text_h1} !important;
            color: {text_h1} !important;
        }}

        /* ===== Primary buttons ===== */
        .stButton > button[kind="primary"] {{
            background-color: {btn_bg} !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
        }}
        .stButton > button[kind="primary"]:hover {{
            background-color: {btn_hover} !important;
        }}

        /* ===== Divider ===== */
        hr {{ border-color: {border_color}; }}

        /* ===== Top-right floating toggle ===== */
        div[data-testid="stToggle"] {{
            position: fixed !important;
            top: 14px !important;
            right: 20px !important;
            z-index: 9999 !important;
            background: {bg_card};
            padding: 4px 12px 4px 8px;
            border-radius: 30px;
            border: 1px solid {border_color};
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        /* Toggle label text */
        div[data-testid="stToggle"] label p {{
            font-size: 13px !important;
            font-weight: 600 !important;
            color: {text_primary} !important;
        }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

def main():

    # --- Floating top-right toggle switch ---
    is_dark = st.session_state.get('theme', 'light') == 'dark'
    toggle_label = "🌙 Dark" if not is_dark else "☀️ Light"
    toggled = st.toggle(toggle_label, value=is_dark, key="theme_toggle")
    if toggled != is_dark:
        st.session_state['theme'] = 'dark' if toggled else 'light'
        st.rerun()

    # Title and header
    st.title("📈 Options Backtesting Platform")
    st.markdown("### Convert TradingView Strategy Reports into NIFTY Options Backtests")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        st.divider()
        
        # Upstox API Configuration
        st.subheader("🔐 Upstox Plus API Credentials")
        api_key = st.text_input("API Key", type="password", help="Your Upstox Plus API Key")
        api_secret = st.text_input("API Secret", type="password", help="Your Upstox Plus API Secret")
        access_token = st.text_input("Access Token", type="password", help="Your Upstox Plus Access Token")
        
        st.divider()
        
        # Backtest Parameters
        st.subheader("📊 Backtest Parameters")
        
        # Expiry and Rollover Configuration
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        expiryday = st.selectbox(
            "Expiry Weekday", weekdays, index=1,
            help="Day of the week when options expire"
        )

        rollover_choices = ["No rollover"] + weekdays
        rolloverday = st.selectbox(
            "Rollover Day", rollover_choices, index=0,
            help="Select 'No rollover' to always use the next expiry"
        )


        
        # Moneyness Configuration
        moneyness_mode = st.selectbox(
            "Moneyness Mode",
            ['ATM', 'ITM1', 'OTM1'],
            index=0,
            help="Strike price selection mode"
        )
        
        # Lot Size
        lot_size = st.number_input(
            "Lot Size",
            min_value=1,
            value=65,
            step=65,
            help="NIFTY lot size (default: 65)"
        )
        
        # Data Interval
        data_interval = st.selectbox(
            "Data Interval",
            ['1minute', '5minute'],
            index=0,
            help="Candle interval for price fetching"
        )
        
        st.divider()
        
        # Display Info
        st.info("📌 **Data Source:** Upstox Plus API\n📅 **Index:** NIFTY 50")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📁 Upload & Process", "📊 Results & Analysis", "📈 Performance Metrics"])
    
    with tab1:
        st.header("Step 1: Upload TradingView Strategy Report")
        
        uploaded_file = st.file_uploader(
            "Choose an Excel file exported from TradingView",
            type=['xlsx', 'xls'],
            help="Upload your TradingView strategy backtest report"
        )
        
        if uploaded_file is not None:
            try:
                # Show file details
                st.success(f"✅ File uploaded: {uploaded_file.name}")
                
                # Parse the uploaded file
                with st.spinner("Parsing TradingView report..."):
                    parser = TradingViewParser()
                    raw_df = pd.read_excel(uploaded_file)
                    
                    st.subheader("📋 Raw Data Preview")
                    st.dataframe(raw_df.head(10), use_container_width=True)
                    
                # Parse trades
                trades_df = parser.parse_trades(raw_df)
                # Add optional manual expiry override column
                if 'Expiry Override' not in trades_df.columns:
                    trades_df['Expiry Override'] = ''   # keep as string, e.g. 2025-10-30


                st.subheader("✅ Parsed Trades (editable, you can set Expiry Override)")

                edited_trades_df = st.data_editor(
                    trades_df,
                    use_container_width=True,
                    num_rows="dynamic",
                    key="parsed_trades_editor"
                )

                st.metric("Total Trades Identified", len(edited_trades_df))


                # Run Backtest Button
                if st.button("🚀 Run Backtest", type="primary", use_container_width=True):
                    if not api_key or not api_secret or not access_token:
                        st.error("⚠️ Please provide Upstox API credentials in the sidebar!")
                    else:
                        # Use the edited DataFrame, not the original
                        run_backtest(
                            trades_df=edited_trades_df,
                            api_key=api_key,
                            api_secret=api_secret,
                            access_token=access_token,
                            expiry_day=expiryday,
                            rollover_day=rolloverday,
                            moneyness_mode=moneyness_mode,
                            lot_size=lot_size,
                            data_interval=data_interval
                        )

                        
                        
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                st.exception(e)
        else:
            # Show sample format
            st.info("👆 Please upload a TradingView strategy report to begin")
            
            st.subheader("📝 Expected File Format")
            st.info("💡 **No Price needed!** NIFTY50 spot price is automatically fetched from the Upstox API based on Date & Time.")
            sample_data = {
                'Trade #': [1, 1, 2, 2],
                'Type': ['Entry', 'Exit', 'Entry', 'Exit'],
                'Signal': ['Long', 'Long', 'Short', 'Short'],
                'Date': ['2025-11-01', '2025-11-01', '2025-11-02', '2025-11-02'],
                'Time': ['09:30', '15:00', '10:15', '14:30']
            }
            st.dataframe(pd.DataFrame(sample_data), use_container_width=True)
    
    with tab2:
        st.header("Backtest Results")
        
        if 'backtest_results' in st.session_state:
            results_df = st.session_state['backtest_results']
            
            # Display results table
            st.subheader("📊 Trade-by-Trade Results")
            st.dataframe(results_df, use_container_width=True)
            
            # Download button
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name=f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # Excel download
            excel_file = ReportGenerator.create_excel_report(results_df)
            st.download_button(
                label="📥 Download Results as Excel",
                data=excel_file,
                file_name=f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        else:
            st.info("👈 Run a backtest to see results here")
    
    with tab3:
        st.header("Performance Metrics & Visualization")
        
        if 'backtest_results' in st.session_state:
            results_df = st.session_state['backtest_results']
            
            # Calculate metrics
            metrics = calculate_performance_metrics(results_df)
            
            # Display metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Trades", metrics['total_trades'])
                st.metric("Winning Trades", metrics['winning_trades'])
            
            with col2:
                st.metric("Win Rate", f"{metrics['win_rate']:.2f}%")
                st.metric("Losing Trades", metrics['losing_trades'])
            
            with col3:
                st.metric("Total P&L (Options)", f"₹{metrics['total_pnl_options']:,.2f}")
                st.metric("Avg Profit", f"₹{metrics['avg_profit']:,.2f}")
            
            with col4:
                st.metric("Total P&L (NIFTY)", f"₹{metrics['total_pnl_nifty']:,.2f}")
                st.metric("Avg Loss", f"₹{metrics['avg_loss']:,.2f}")
            
            st.divider()
            
            # Equity curve
            st.subheader("📈 Cumulative P&L (Equity Curve)")
            fig_equity = plot_equity_curve(results_df)
            st.plotly_chart(fig_equity, use_container_width=True)
            
            # P&L Distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 P&L Distribution (Options)")
                fig_dist = plot_pnl_distribution(results_df, 'P&L (Options)')
                st.plotly_chart(fig_dist, use_container_width=True)
            
            with col2:
                st.subheader("📊 P&L by Trade")
                fig_bar = plot_pnl_bars(results_df)
                st.plotly_chart(fig_bar, use_container_width=True)
                
        else:
            st.info("👈 Run a backtest to see performance metrics here")

def run_backtest(trades_df, api_key, api_secret, access_token, expiry_day, 
                 rollover_day, moneyness_mode, lot_size, data_interval):
    """Execute the backtest with given parameters"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize components
        status_text.text("🔧 Initializing Upstox API...")
        progress_bar.progress(10)
        
        upstox_api = UpstoxAPI(api_key, api_secret, access_token)
        
        status_text.text("📅 Calculating expiry dates...")
        progress_bar.progress(20)
        
        expiry_calculator = ExpiryCalculator()
        strike_calculator = StrikeCalculator()
        
        status_text.text("🔄 Processing trades...")
        progress_bar.progress(30)
        
        # Initialize backtest engine
        engine = BacktestEngine(
            upstox_api=upstox_api,
            expiry_calculator=expiry_calculator,
            strike_calculator=strike_calculator,
            expiry_day=expiry_day,
            rollover_day=rollover_day,
            moneyness_mode=moneyness_mode,
            lot_size=lot_size,
            data_interval=data_interval
        )
        
        # Run backtest
        results_df = engine.run_backtest(trades_df, progress_bar, status_text)
        
        status_text.text("✅ Backtest completed!")
        progress_bar.progress(100)
        
        # Store results in session state
        st.session_state['backtest_results'] = results_df
        
        st.success(f"✅ Backtest completed successfully! Processed {len(results_df)} trades.")
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ Error during backtest: {str(e)}")
        st.exception(e)

def calculate_performance_metrics(results_df):
    """Calculate performance metrics from results"""
    
    metrics = {}
    
    metrics['total_trades'] = len(results_df)
    metrics['winning_trades'] = len(results_df[results_df['P&L (Options)'] > 0])
    metrics['losing_trades'] = len(results_df[results_df['P&L (Options)'] <= 0])
    metrics['win_rate'] = (metrics['winning_trades'] / metrics['total_trades'] * 100) if metrics['total_trades'] > 0 else 0
    
    metrics['total_pnl_options'] = results_df['P&L (Options)'].sum()
    metrics['total_pnl_nifty'] = results_df['P&L (NIFTY)'].sum()
    
    winning_trades = results_df[results_df['P&L (Options)'] > 0]
    losing_trades = results_df[results_df['P&L (Options)'] <= 0]
    
    metrics['avg_profit'] = winning_trades['P&L (Options)'].mean() if len(winning_trades) > 0 else 0
    metrics['avg_loss'] = losing_trades['P&L (Options)'].mean() if len(losing_trades) > 0 else 0
    
    metrics['max_profit'] = results_df['P&L (Options)'].max() if len(results_df) > 0 else 0
    metrics['max_loss'] = results_df['P&L (Options)'].min() if len(results_df) > 0 else 0
    
    # Calculate cumulative P&L
    results_df['Cumulative P&L'] = results_df['P&L (Options)'].cumsum()
    
    # Calculate drawdown
    cumulative = results_df['Cumulative P&L']
    running_max = cumulative.cummax()
    drawdown = cumulative - running_max
    metrics['max_drawdown'] = drawdown.min() if len(drawdown) > 0 else 0
    
    return metrics

def plot_equity_curve(results_df):
    """Plot cumulative P&L equity curve"""
    
    results_df['Cumulative P&L (Options)'] = results_df['P&L (Options)'].cumsum()
    results_df['Cumulative P&L (NIFTY)'] = results_df['P&L (NIFTY)'].cumsum()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=results_df.index,
        y=results_df['Cumulative P&L (Options)'],
        mode='lines',
        name='Options P&L',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=results_df.index,
        y=results_df['Cumulative P&L (NIFTY)'],
        mode='lines',
        name='NIFTY P&L',
        line=dict(color='#ff7f0e', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='Cumulative P&L Over Time',
        xaxis_title='Trade Number',
        yaxis_title='Cumulative P&L (₹)',
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig

def plot_pnl_distribution(results_df, column):
    """Plot P&L distribution histogram"""
    
    fig = px.histogram(
        results_df,
        x=column,
        nbins=30,
        title=f'{column} Distribution',
        labels={column: 'P&L (₹)'},
        color_discrete_sequence=['#1f77b4']
    )
    
    fig.update_layout(
        xaxis_title='P&L (₹)',
        yaxis_title='Frequency',
        template='plotly_white',
        height=400
    )
    
    return fig

def plot_pnl_bars(results_df):
    """Plot P&L as bars for each trade"""
    
    colors = ['green' if x > 0 else 'red' for x in results_df['P&L (Options)']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=results_df.index,
            y=results_df['P&L (Options)'],
            marker_color=colors,
            name='P&L per Trade'
        )
    ])
    
    fig.update_layout(
        title='P&L per Trade',
        xaxis_title='Trade Number',
        yaxis_title='P&L (₹)',
        template='plotly_white',
        height=400,
        showlegend=False
    )
    
    return fig

if __name__ == "__main__":
    main()
