import yfinance as yf
import datetime

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
    dataRaw = yf.download(tickers=ticker, period=period, interval="1h", progress=False)   
    dataRaw = dataRaw.tz_convert("America/New_York")
    dataRaw = dataRaw.between_time("09:30", "16:00")
    if interval == "4h":
        dataRaw = dataRaw.resample(
            "4h",
            origin="start_day",
            offset="9h30min",
            label="left",
            closed="left"
        ).agg({
            ("Open", ticker): "first",
            ("High", ticker): "max",
            ("Low", ticker): "min",
            ("Close", ticker): "last",
            ("Volume", ticker): "sum"
        }).dropna()
    dataRaw = dataRaw.reset_index()
    dataRaw = dataRaw.rename(columns={
        "Datetime": "Date"
    })

    dates  = dataRaw["Date"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
    opens  = dataRaw[("Open", ticker)].tolist()
    highs  = dataRaw[("High", ticker)].tolist()
    lows   = dataRaw[("Low", ticker)].tolist()
    closes = dataRaw[("Close", ticker)].tolist()
    vols   = dataRaw[("Volume", ticker)].tolist()
    returnData = [dates, opens, highs, lows, closes, vols]
    return(returnData)

# Function for writing output summaries for a set of flagged tickers to a labeled text file.
# Parameters:
#       tickers = The list of flagged tickers to output.
#       fileName = The name of the file to output them to (defaults to current date).
# Return:
#       There is no return to this function, instead there is a written file.

def exportTickers(tickers, fileName=None):
    if fileName == None:
        tempDate = datetime.datetime.now()
        fileName = "{}-{}-{}.txt".format(str(tempDate.year),str(tempDate.month),str(tempDate.day))
    outputFile = open(fileName, "w")
    outputFile.writelines([element + " REVERSION DETECTED" for element in tickers])
    outputFile.close()