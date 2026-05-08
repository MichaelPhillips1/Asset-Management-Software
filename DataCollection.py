import yfinance as yf
import pandas as pd

# Function for collecting Date, Open, High, Low, and Close values for a provided ticker.
# Parameters:
#       ticker = The string value of the ticker.
#       period = The time period of data to fetch.
#       interval = The interval to apply to the data.
# Return:
#       A list of lists, where the first list containsdates, the second list contains opening
#       prices, the third list contains highs, the fouth list contains lows, the fifth list
#       contains closes, and the sixth list contains volumes for each interval of the period.

def Fetch_Yaohoo_Data(ticker, period, interval):
    dataRaw = yf.download(tickers=ticker, period=period, interval=interval).reset_index()
    dates  = dataRaw["Date"].dt.strftime("%Y-%m-%d").tolist()
    opens  = dataRaw[("Open", ticker)].tolist()
    highs  = dataRaw[("High", ticker)].tolist()
    lows   = dataRaw[("Low", ticker)].tolist()
    closes = dataRaw[("Close", ticker)].tolist()
    vols   = dataRaw[("Volume", ticker)].tolist()
    returnData = [dates, opens, highs, lows, closes, vols]
    return(returnData)