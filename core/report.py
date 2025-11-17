import pandas as pd
import numpy as np
from io import BytesIO
import plotly.graph_objects as go
import plotly.express as px

class ReportGenerator:
    """Generate reports and visualizations"""
    
    @staticmethod
    def create_excel_report(results_df):
        """
        Create Excel report with multiple sheets
        
        Args:
            results_df: DataFrame with backtest results
            
        Returns:
            BytesIO: Excel file in memory
        """
        
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: All trades
            results_df.to_excel(writer, sheet_name='Trades', index=False)
            
            # Sheet 2: Summary statistics
            summary = ReportGenerator.calculate_summary(results_df)
            summary.to_excel(writer, sheet_name='Summary', index=True)
            
            # Sheet 3: Monthly breakdown
            monthly = ReportGenerator.monthly_breakdown(results_df)
            monthly.to_excel(writer, sheet_name='Monthly', index=False)
            
            # Sheet 4: Win/Loss analysis
            win_loss = ReportGenerator.win_loss_analysis(results_df)
            win_loss.to_excel(writer, sheet_name='Win-Loss', index=True)
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def calculate_summary(results_df):
        """Calculate summary statistics"""
        
        summary = {
            'Total Trades': len(results_df),
            'Winning Trades': len(results_df[results_df['P&L (Options)'] > 0]),
            'Losing Trades': len(results_df[results_df['P&L (Options)'] <= 0]),
            'Win Rate (%)': len(results_df[results_df['P&L (Options)'] > 0]) / len(results_df) * 100,
            'Total P&L (Options)': results_df['P&L (Options)'].sum(),
            'Total P&L (NIFTY)': results_df['P&L (NIFTY)'].sum(),
            'Average P&L per Trade': results_df['P&L (Options)'].mean(),
            'Max Profit': results_df['P&L (Options)'].max(),
            'Max Loss': results_df['P&L (Options)'].min(),
            'Avg Winning Trade': results_df[results_df['P&L (Options)'] > 0]['P&L (Options)'].mean(),
            'Avg Losing Trade': results_df[results_df['P&L (Options)'] <= 0]['P&L (Options)'].mean(),
            'Profit Factor': abs(results_df[results_df['P&L (Options)'] > 0]['P&L (Options)'].sum() / 
                               results_df[results_df['P&L (Options)'] <= 0]['P&L (Options)'].sum()) 
                               if results_df[results_df['P&L (Options)'] <= 0]['P&L (Options)'].sum() != 0 else 0,
        }
        
        # Calculate max drawdown
        cumulative = results_df['P&L (Options)'].cumsum()
        running_max = cumulative.cummax()
        drawdown = cumulative - running_max
        summary['Max Drawdown'] = drawdown.min()
        
        return pd.Series(summary, name='Value')
    
    @staticmethod
    def monthly_breakdown(results_df):
        """Calculate monthly breakdown"""
        
        df = results_df.copy()
        df['Month'] = pd.to_datetime(df['Entry Date']).dt.to_period('M')
        
        monthly = df.groupby('Month').agg({
            'Trade #': 'count',
            'P&L (Options)': ['sum', 'mean', 'min', 'max']
        }).reset_index()
        
        monthly.columns = ['Month', 'Trades', 'Total P&L', 'Avg P&L', 'Min P&L', 'Max P&L']
        
        return monthly
    
    @staticmethod
    def win_loss_analysis(results_df):
        """Analyze wins vs losses"""
        
        winning = results_df[results_df['P&L (Options)'] > 0]
        losing = results_df[results_df['P&L (Options)'] <= 0]
        
        analysis = {
            'Winning Trades': {
                'Count': len(winning),
                'Total P&L': winning['P&L (Options)'].sum(),
                'Average P&L': winning['P&L (Options)'].mean(),
                'Median P&L': winning['P&L (Options)'].median(),
                'Std Dev': winning['P&L (Options)'].std()
            },
            'Losing Trades': {
                'Count': len(losing),
                'Total P&L': losing['P&L (Options)'].sum(),
                'Average P&L': losing['P&L (Options)'].mean(),
                'Median P&L': losing['P&L (Options)'].median(),
                'Std Dev': losing['P&L (Options)'].std()
            }
        }
        
        return pd.DataFrame(analysis)
    
    @staticmethod
    def create_equity_curve_chart(results_df):
        """Create equity curve visualization"""
        
        df = results_df.copy()
        df['Cumulative P&L'] = df['P&L (Options)'].cumsum()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Cumulative P&L'],
            mode='lines',
            name='Equity Curve',
            line=dict(color='blue', width=2)
        ))
        
        fig.update_layout(
            title='Equity Curve',
            xaxis_title='Trade Number',
            yaxis_title='Cumulative P&L (₹)',
            template='plotly_white'
        )
        
        return fig
