import numpy as np
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import matplotlib.pyplot as plt
import os
import toml

# Load settings from the TOML file
config = toml.load("settings.toml")
tickers = config['tickers']['symbols']
years_back = config['analysis']['years_back']
y_min = None

timezone = pytz.timezone('Australia/Perth')
current_time = datetime.now(timezone).strftime("%Y%m%d_%H%M%S")

def fetch_dividend_yield(ticker, years_back=5):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years_back)
        end_date_str = end_date.strftime('%Y-%m-%d')
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        stock = yf.Ticker(ticker)
        
        # Get dividend data
        dividends = stock.dividends
        
        # Check if dividends exist
        if dividends.empty:
            return 0
            
        # Filter dividends for our time period
        dividends = dividends[(dividends.index >= start_date_str) & (dividends.index <= end_date_str)]
        if dividends.empty:
            return 0
        
        # Get latest stock price
        current_price_data = stock.history(period="1d")
        if current_price_data.empty:
            return 0
        current_price = current_price_data['Close'].iloc[-1]
        
        # Get the annual dividend rate (TTM - trailing twelve months)
        one_year_ago = end_date - timedelta(days=365)
        recent_dividends = dividends[dividends.index >= one_year_ago.strftime('%Y-%m-%d')]
        
        if not recent_dividends.empty:
            # We have at least some dividends in the last year
            annual_dividend = recent_dividends.sum()
        else:
            # We don't have dividends in the last year, extrapolate from what we have
            total_days = (dividends.index.max() - dividends.index.min()).days
            if total_days > 0:
                days_per_year = 365.0
                annual_dividend = (dividends.sum() / total_days) * days_per_year
            else:
                return 0
        
        # Calculate yield
        if current_price > 0:
            dividend_yield = (annual_dividend / current_price) * 100  # as percentage
            return dividend_yield
        else:
            return 0
            
    except Exception as e:
        print(f"Error fetching dividend yield for {ticker}: {str(e)}")
        return 0

def fetch_and_visualize(tickers, years_back=5, y_min=None):
    nrows, ncols = 2, 3
    plt.figure(figsize=(15, 5 * nrows))

    for i, ticker in enumerate(tickers):
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * years_back)
            data = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)
            
            # Check if data is empty
            if data.empty:
                print(f"No data fetched for {ticker}. Skipping...")
                continue
                
            data['Short_MA'] = data['Close'].rolling(window=50).mean()
            data['Long_MA'] = data['Close'].rolling(window=200).mean()
            
            # Create a Series for crosses, not just a boolean array
            golden_crosses = ((data['Short_MA'] > data['Long_MA']) & (data['Short_MA'].shift(1) <= data['Long_MA'].shift(1)))
            death_crosses = ((data['Short_MA'] < data['Long_MA']) & (data['Short_MA'].shift(1) >= data['Long_MA'].shift(1)))

            # Only calculate trend line if there's enough data
            if len(data['Close']) > 1:  # Need at least 2 points for a line
                # Convert to numpy array and remove any NaN values
                x = np.array(range(len(data['Close'])))
                y = data['Close'].values
                # Only use non-NaN values
                valid_indices = ~np.isnan(y)
                if np.sum(valid_indices) > 1:  # Ensure we have at least 2 valid points
                    z = np.polyfit(x, y, 1)
                    p = np.poly1d(z)
                    start_price = p(0)
                    end_price = p(len(data['Close']) - 1)
                    years = years_back
                    CAGR = ((end_price / start_price) ** (1 / years) - 1) * 100
                else:
                    p = None
                    CAGR = 0
            else:
                p = None
                CAGR = 0
            
            average_dividend_yield = fetch_dividend_yield(ticker, years_back=years_back)

            ax = plt.subplot(nrows, ncols, i + 1)
            ax.plot(data['Close'], label='Close Price', color='blue', alpha=0.6)
            
            # Only plot trend line if it was calculated
            if p is not None:
                ax.plot(data.index, p(range(len(data['Close']))), "r--", label='Trend Line')
            
            ax.plot(data['Short_MA'], label='50-day MA', color='black', alpha=0.6)
            ax.plot(data['Long_MA'], label='200-day MA', color='magenta', alpha=0.6)
            
            # FIX: Properly plot crosses by getting the dates first, then accessing values
            if golden_crosses.any():
                # Get dates where golden crosses occur
                cross_dates = data.index[golden_crosses]
                # Get corresponding values from Short_MA
                cross_values = data.loc[cross_dates, 'Short_MA']
                ax.scatter(cross_dates, cross_values, 
                          color='gold', label='Golden Cross', marker='^', zorder=5)
                
            if death_crosses.any():
                # Get dates where death crosses occur
                cross_dates = data.index[death_crosses]
                # Get corresponding values from Short_MA
                cross_values = data.loc[cross_dates, 'Short_MA']
                ax.scatter(cross_dates, cross_values, 
                          color='darkred', label='Death Cross', marker='v', zorder=5)
                
            ax.set_title(f'{ticker}\nYoY Growth: {CAGR:.2f}%, Avg Div Yield: {average_dividend_yield:.2f}%')
            ax.set_xlabel('Date')
            ax.set_ylabel('Price')
            ax.legend()
            if y_min is not None:
                ax.set_ylim(bottom=y_min)
        except Exception as e:
            print(f"Error processing {ticker}: {str(e)}")
            # Create an empty subplot with error message
            ax = plt.subplot(nrows, ncols, i + 1)
            ax.text(0.5, 0.5, f"Error loading {ticker}\n{str(e)}", 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=10, color='red')
            ax.set_title(f'{ticker} - Data Error')
            ax.axis('off')
        
    plt.tight_layout()

    save_path = os.path.join("stock_analysis", f"{current_time}.png")
    os.makedirs("stock_analysis", exist_ok=True)
    plt.savefig(save_path)
    return save_path


# Execute function and save the image
save_path = fetch_and_visualize(tickers, years_back=years_back, y_min=y_min)
print(f"Stock analysis chart saved to: {save_path}")
