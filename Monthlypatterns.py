import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, date
import calendar
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Monthly Patterns Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6C757D;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .explanation-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-left: 4px solid #2E86AB;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown('<h1 class="main-header">📈 Monthly Patterns Analysis</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Analyze weekly progression, momentum trends, and success rates for any stock or index</p>', unsafe_allow_html=True)

# Sidebar controls
with st.sidebar:
    st.header("🎛️ Analysis Settings")
    
    # Asset selection
    st.subheader("📊 Asset Selection")
    
    # Popular assets dictionary
    popular_assets = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "Dow Jones": "^DJI",
        "Russell 2000": "^RUT",
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "Amazon": "AMZN",
        "Google": "GOOGL",
        "Tesla": "TSLA",
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Gold": "GC=F",
        "Crude Oil": "CL=F"
    }
    
    # Asset selection method
    asset_method = st.radio(
        "Choose selection method:",
        ["Popular Assets", "Custom Ticker"]
    )
    
    if asset_method == "Popular Assets":
        selected_asset_name = st.selectbox(
            "Select an asset:",
            list(popular_assets.keys()),
            index=0
        )
        ticker = popular_assets[selected_asset_name]
    else:
        ticker = st.text_input(
            "Enter ticker symbol:",
            value="^GSPC",
            help="Examples: AAPL, MSFT, ^GSPC, BTC-USD"
        ).upper()
        selected_asset_name = ticker
    
    # Date range selection
    st.subheader("📅 Date Range")
    
    # Preset date ranges
    preset_ranges = {
        "All Available Data": ("1950-01-01", "2024-12-31"),
        "Last 10 Years": ("2014-01-01", "2024-12-31"),
        "Last 5 Years": ("2019-01-01", "2024-12-31"),
        "Last 3 Years": ("2021-01-01", "2024-12-31"),
        "COVID Era": ("2020-01-01", "2024-12-31"),
        "Post-2008 Crisis": ("2010-01-01", "2024-12-31"),
        "Custom Range": None
    }
    
    date_range_option = st.selectbox(
        "Select date range:",
        list(preset_ranges.keys()),
        index=0
    )
    
    if date_range_option == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date:",
                value=date(2020, 1, 1),
                min_value=date(1950, 1, 1),
                max_value=date.today()
            )
        with col2:
            end_date = st.date_input(
                "End Date:",
                value=date.today(),
                min_value=date(1950, 1, 1),
                max_value=date.today()
            )
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
    else:
        start_date_str, end_date_str = preset_ranges[date_range_option]
    
    # Analysis options
    st.subheader("⚙️ Analysis Options")
    show_trend_lines = st.checkbox("Show trend lines", value=True)
    show_summary_stats = st.checkbox("Show summary statistics", value=True)

# Function to download and process data
@st.cache_data
def download_data(ticker, start_date, end_date):
    """Download and process stock data"""
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            return None, "No data available for the selected ticker and date range."
        
        # Handle MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        
        # Calculate returns and add date components
        data['Daily_Return'] = data['Close'].pct_change()
        data['Year'] = data.index.year
        data['Month'] = data.index.month
        data['Day'] = data.index.day
        
        return data, None
        
    except Exception as e:
        return None, f"Error downloading data: {str(e)}"

# Function to analyze monthly patterns
def analyze_month_patterns(month_num, data):
    """Analyze patterns for a specific month"""
    month_data = data[data['Month'] == month_num].copy()
    
    weekly_returns = {}
    momentum_by_day = {}
    positive_days_by_day = {}
    years_processed = []
    
    for year in month_data['Year'].unique():
        year_month = month_data[month_data['Year'] == year].copy()
        
        # Filter valid data
        valid_mask = year_month['Daily_Return'].notna() & year_month['Close'].notna()
        year_month = year_month[valid_mask]
        
        if len(year_month) < 10:  # Skip months with insufficient data
            continue
            
        years_processed.append(year)
        year_month = year_month.sort_index()
        
        # Calculate monthly returns
        first_price = year_month['Close'].iloc[0]
        year_month['Month_Return'] = (year_month['Close'] / first_price) - 1
        
        # Assign trading days and weeks
        year_month['Trading_Day'] = range(1, len(year_month) + 1)
        year_month['Trading_Week'] = ((year_month['Trading_Day'] - 1) // 5) + 1
        year_month['Day_of_Month'] = year_month.index.day
        
        # Weekly progression
        for week in range(1, 5):
            week_data = year_month[year_month['Trading_Week'] == week]
            if len(week_data) > 0:
                week_return = week_data['Month_Return'].iloc[-1]
                if week not in weekly_returns:
                    weekly_returns[week] = []
                weekly_returns[week].append(week_return)
        
        # Momentum analysis
        if len(year_month) >= 3:
            year_month['Rolling_Return'] = year_month['Daily_Return'].rolling(window=3, center=True).mean()
            
            for day, momentum in zip(year_month['Day_of_Month'], year_month['Rolling_Return']):
                if not np.isnan(momentum):
                    if day not in momentum_by_day:
                        momentum_by_day[day] = []
                    momentum_by_day[day].append(momentum)
        
        # Win rate analysis
        for day, daily_return in zip(year_month['Day_of_Month'], year_month['Daily_Return']):
            if not np.isnan(daily_return):
                if day not in positive_days_by_day:
                    positive_days_by_day[day] = []
                positive_days_by_day[day].append(1 if daily_return > 0 else 0)
    
    # Calculate averages
    weekly_avg_returns = {week: np.mean(returns)*100 for week, returns in weekly_returns.items()}
    momentum_avg = {day: np.mean(momentum)*100 for day, momentum in momentum_by_day.items()}
    win_rates = {day: np.mean(positive)*100 for day, positive in positive_days_by_day.items()}
    
    return weekly_avg_returns, momentum_avg, win_rates, years_processed

# Function to create visualizations
def create_monthly_chart(month_num, weekly_returns, momentum, win_rates, show_trends=True):
    """Create interactive chart for a specific month"""
    month_name = calendar.month_name[month_num]
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=('Weekly Progression', 'Momentum Patterns', 'Success Rates'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Colors
    colors = {
        'primary': '#2E86AB',
        'secondary': '#A23B72',
        'positive': '#06D6A0',
        'negative': '#F18F01'
    }
    
    # 1. Weekly Progression
    if weekly_returns:
        weeks = list(weekly_returns.keys())
        week_values = list(weekly_returns.values())
        
        plot_weeks = [0] + weeks
        plot_values = [0] + week_values
        
        fig.add_trace(
            go.Scatter(
                x=plot_weeks,
                y=plot_values,
                mode='lines+markers',
                name='Weekly Returns',
                line=dict(color=colors['primary'], width=3),
                marker=dict(size=8, color='white', line=dict(color=colors['primary'], width=2)),
                fill='tonexty',
                fillcolor=f"rgba{tuple(list(px.colors.hex_to_rgb(colors['primary'])) + [0.3])}"
            ),
            row=1, col=1
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.7, row=1, col=1)
    
    # 2. Momentum Patterns
    if momentum:
        days = sorted(momentum.keys())
        mom_values = [momentum[day] for day in days]
        
        fig.add_trace(
            go.Scatter(
                x=days,
                y=mom_values,
                mode='lines',
                name='Momentum',
                line=dict(color=colors['secondary'], width=3),
            ),
            row=1, col=2
        )
        
        # Add trend line if requested
        if show_trends and len(days) > 5:
            z = np.polyfit(days, mom_values, 1)
            p = np.poly1d(z)
            trend_color = colors['positive'] if z[0] > 0 else colors['negative']
            
            fig.add_trace(
                go.Scatter(
                    x=days,
                    y=p(days),
                    mode='lines',
                    name='Trend',
                    line=dict(color=trend_color, width=2, dash='dash'),
                ),
                row=1, col=2
            )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.7, row=1, col=2)
    
    # 3. Success Rates
    if win_rates:
        days = sorted(win_rates.keys())
        win_values = [win_rates[day] for day in days]
        
        # Color bars based on win rate
        bar_colors = []
        for w in win_values:
            if w >= 55:
                bar_colors.append(colors['positive'])
            elif w >= 50:
                bar_colors.append(colors['primary'])
            else:
                bar_colors.append(colors['negative'])
        
        fig.add_trace(
            go.Bar(
                x=days,
                y=win_values,
                name='Win Rate',
                marker_color=bar_colors,
                opacity=0.8
            ),
            row=1, col=3
        )
        
        fig.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.7, row=1, col=3)
    
    # Update layout
    fig.update_layout(
        title=f"{month_name} Analysis",
        height=400,
        showlegend=False,
        template="plotly_white"
    )
    
    # Update x-axis labels
    fig.update_xaxes(title_text="Trading Week", row=1, col=1)
    fig.update_xaxes(title_text="Calendar Day", row=1, col=2)
    fig.update_xaxes(title_text="Calendar Day", row=1, col=3)
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Cumulative Return (%)", row=1, col=1)
    fig.update_yaxes(title_text="Momentum (%)", row=1, col=2)
    fig.update_yaxes(title_text="Win Rate (%)", row=1, col=3)
    
    return fig

# Main app logic
def main():
    # Download data
    with st.spinner(f"Downloading data for {selected_asset_name}..."):
        data, error = download_data(ticker, start_date_str, end_date_str)
    
    if error:
        st.error(error)
        st.stop()
    
    if data is None or data.empty:
        st.error("No data available for the selected parameters.")
        st.stop()
    
    # Display data info
    st.success(f"✅ Data loaded successfully for {selected_asset_name}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Date Range", f"{start_date_str} to {end_date_str}")
    with col2:
        st.metric("Total Days", f"{len(data):,}")
    with col3:
        st.metric("Years Covered", f"{data['Year'].nunique()}")
    with col4:
        st.metric("Data Points", f"{data['Daily_Return'].notna().sum():,}")
    
    # Analysis explanation
    with st.expander("📚 What does this analysis show?", expanded=False):
        st.markdown("""
        <div class="explanation-box">
        <h3>📊 Understanding the Monthly Patterns Analysis</h3>
        
        This tool analyzes three key aspects of monthly stock behavior:
        
        <h4>1. 📈 Weekly Progression</h4>
        <ul>
            <li><strong>What it shows:</strong> How returns typically accumulate throughout each trading week of the month</li>
            <li><strong>Why it matters:</strong> Reveals if certain weeks consistently outperform others</li>
            <li><strong>How to read:</strong> Each point shows cumulative return from month start to end of that trading week</li>
        </ul>
        
        <h4>2. 🎯 Momentum Patterns</h4>
        <ul>
            <li><strong>What it shows:</strong> 3-day rolling average of daily returns by calendar day</li>
            <li><strong>Why it matters:</strong> Identifies if momentum accelerates or decelerates during the month</li>
            <li><strong>How to read:</strong> Upward trending line = accelerating momentum, downward = decelerating</li>
        </ul>
        
        <h4>3. ✅ Success Rates</h4>
        <ul>
            <li><strong>What it shows:</strong> Percentage of years that had positive returns on each calendar day</li>
            <li><strong>Why it matters:</strong> More robust than averages - shows consistency of positive performance</li>
            <li><strong>How to read:</strong> Above 50% = more often positive than negative, higher = more reliable</li>
        </ul>
        
        <h4>🎨 Color Coding</h4>
        <ul>
            <li><strong>Green:</strong> Strong positive performance (>55% win rate)</li>
            <li><strong>Blue:</strong> Moderate positive performance (50-55% win rate)</li>
            <li><strong>Orange/Red:</strong> Weak/negative performance (<50% win rate)</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Create tabs for different months
    tab_names = ["Overview"] + [calendar.month_name[i] for i in range(1, 13)]
    tabs = st.tabs(tab_names)
    
    # Overview tab
    with tabs[0]:
        st.subheader("📊 Annual Overview")
        
        # Calculate summary statistics for all months
        summary_data = []
        for month_num in range(1, 13):
            weekly_returns, momentum, win_rates, years = analyze_month_patterns(month_num, data)
            
            if years:
                total_return = max(weekly_returns.values()) if weekly_returns else 0
                avg_momentum = np.mean(list(momentum.values())) if momentum else 0
                avg_win_rate = np.mean(list(win_rates.values())) if win_rates else 0
                
                summary_data.append({
                    'Month': calendar.month_name[month_num],
                    'Monthly_Return': total_return,
                    'Avg_Momentum': avg_momentum * 100,
                    'Win_Rate': avg_win_rate,
                    'Years': len(years)
                })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            
            # Create overview charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Monthly returns chart
                fig_returns = px.bar(
                    summary_df,
                    x='Month',
                    y='Monthly_Return',
                    title='Average Monthly Returns (%)',
                    color='Monthly_Return',
                    color_continuous_scale='RdYlGn'
                )
                fig_returns.update_layout(height=400)
                st.plotly_chart(fig_returns, use_container_width=True)
            
            with col2:
                # Win rates chart
                fig_win_rates = px.bar(
                    summary_df,
                    x='Month',
                    y='Win_Rate',
                    title='Average Win Rates (%)',
                    color='Win_Rate',
                    color_continuous_scale='RdYlGn'
                )
                fig_win_rates.add_hline(y=50, line_dash="dash", line_color="gray")
                fig_win_rates.update_layout(height=400)
                st.plotly_chart(fig_win_rates, use_container_width=True)
            
            # Summary statistics table
            if show_summary_stats:
                st.subheader("📋 Monthly Summary Statistics")
                
                # Format the dataframe for display
                display_df = summary_df.copy()
                display_df['Monthly_Return'] = display_df['Monthly_Return'].apply(lambda x: f"{x:.2f}%")
                display_df['Avg_Momentum'] = display_df['Avg_Momentum'].apply(lambda x: f"{x:.3f}%")
                display_df['Win_Rate'] = display_df['Win_Rate'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(
                    display_df,
                    column_config={
                        'Month': 'Month',
                        'Monthly_Return': 'Avg Monthly Return',
                        'Avg_Momentum': 'Avg Momentum',
                        'Win_Rate': 'Win Rate',
                        'Years': 'Years of Data'
                    },
                    hide_index=True,
                    use_container_width=True
                )
    
    # Individual month tabs
    for month_num in range(1, 13):
        with tabs[month_num]:
            monthly_data = analyze_month_patterns(month_num, data)
            weekly_returns, momentum, win_rates, years = monthly_data
            
            if not years:
                st.warning(f"Insufficient data for {calendar.month_name[month_num]}")
                continue
            
            # Create and display chart
            fig = create_monthly_chart(month_num, weekly_returns, momentum, win_rates, show_trend_lines)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display summary statistics
            if show_summary_stats:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if weekly_returns:
                        total_return = max(weekly_returns.values())
                        best_week = max(weekly_returns, key=weekly_returns.get)
                        st.metric(
                            "Monthly Return",
                            f"{total_return:.2f}%",
                            help="Average cumulative return for the month"
                        )
                        st.info(f"Best week: Week {best_week}")
                
                with col2:
                    if momentum:
                        avg_momentum = np.mean(list(momentum.values()))
                        days = sorted(momentum.keys())
                        mom_values = [momentum[day] for day in days]
                        trend = "Accelerating" if len(days) > 5 and np.corrcoef(days, mom_values)[0,1] > 0.1 else "Stable"
                        st.metric(
                            "Avg Momentum",
                            f"{avg_momentum:.3f}%",
                            help="3-day rolling average of daily returns"
                        )
                        st.info(f"Trend: {trend}")
                
                with col3:
                    if win_rates:
                        avg_win_rate = np.mean(list(win_rates.values()))
                        st.metric(
                            "Win Rate",
                            f"{avg_win_rate:.1f}%",
                            help="Percentage of years with positive returns"
                        )
                        st.info(f"Years analyzed: {len(years)}")

if __name__ == "__main__":
    main()
