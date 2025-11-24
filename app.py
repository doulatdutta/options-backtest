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

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    h1 {
        color: #1f77b4;
        padding-bottom: 10px;
    }
    h2 {
        color: #ff7f0e;
        padding-top: 20px;
    }
    .uploadedFile {
        border: 2px dashed #1f77b4;
        border-radius: 5px;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Title and header
    st.title("📈 Options Backtesting Platform")
    st.markdown("### Convert TradingView Strategy Reports into NIFTY Options Backtests")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Upstox API Configuration
        st.subheader("🔐 Upstox API Credentials")
        api_key = st.text_input("API Key", type="password", help="Your Upstox API Key")
        api_secret = st.text_input("API Secret", type="password", help="Your Upstox API Secret")
        access_token = st.text_input("Access Token", type="password", help="Your Upstox Access Token")
        
        st.divider()
        
        # Backtest Parameters
        st.subheader("📊 Backtest Parameters")
        
        # Expiry and Rollover Configuration
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        expiry_day = st.selectbox(
            "Expiry Weekday",
            weekdays,
            index=1,  # Default Thursday
            help="Day of the week when options expire"
        )
        
        rollover_day = st.selectbox(
            "Rollover Day",
            weekdays,
            index=1,  # Default Tuesday
            help="Day after which trades roll to next week's expiry"
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
            value=75,
            step=1,
            help="NIFTY lot size (default: 75)"
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
        st.info("📌 **Data Source:** Upstox API\n📅 **Index:** NIFTY 50")
    
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
                    
                    st.subheader("✅ Parsed Trades")
                    st.dataframe(trades_df.head(10), use_container_width=True)
                    
                    st.metric("Total Trades Identified", len(trades_df))
                
                # Run Backtest Button
                if st.button("🚀 Run Backtest", type="primary", use_container_width=True):
                    if not api_key or not api_secret or not access_token:
                        st.error("⚠️ Please provide Upstox API credentials in the sidebar!")
                    else:
                        run_backtest(
                            trades_df=trades_df,
                            api_key=api_key,
                            api_secret=api_secret,
                            access_token=access_token,
                            expiry_day=expiry_day,
                            rollover_day=rollover_day,
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
            sample_data = {
                'Trade #': [1, 1, 2, 2],
                'Type': ['Entry', 'Exit', 'Entry', 'Exit'],
                'Signal': ['Long', 'Long', 'Short', 'Short'],
                'Date': ['2025-11-01', '2025-11-01', '2025-11-02', '2025-11-02'],
                'Time': ['09:30', '15:00', '10:15', '14:30'],
                'Price': [25550.0, 25600.0, 25650.0, 25620.0]
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
