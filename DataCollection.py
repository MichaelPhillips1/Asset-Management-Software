import yfinance as yf
from datetime import datetime
from AssessmentFunctions import *

def fetchDataYahoo(ticker):
    dataRaw = yf.download(tickers=ticker, period="max", interval="1h", progress=False)
    dataRaw = dataRaw.tz_convert("America/New_York")
    dataRaw = dataRaw.between_time("09:30", "16:00")
    dataRaw = dataRaw.reset_index()
    dataRaw = dataRaw.rename(columns={"Datetime": "Date"})
    data1h , data4h = [], []

    # ---------- 1H DATA ----------
    for i in range(len(dataRaw)):
        date = dataRaw["Date"].iloc[i]
        dateStr = date.strftime("%Y-%m-%d %H:%M:%S")
        o = float(dataRaw[("Open", ticker)].iloc[i])
        h = float(dataRaw[("High", ticker)].iloc[i])
        l = float(dataRaw[("Low", ticker)].iloc[i])
        c = float(dataRaw[("Close", ticker)].iloc[i])
        v = int(dataRaw[("Volume", ticker)].iloc[i])

        data1h.append([dateStr, o, h, l, c, v])

    # ---------- CUSTOM 4H DATA ----------
    groupedByDay = {}
    for i in range(len(dataRaw)):
        date = dataRaw["Date"].iloc[i]
        day = date.strftime("%Y-%m-%d")
        time = date.strftime("%H:%M:%S")
        o = float(dataRaw[("Open", ticker)].iloc[i])
        h = float(dataRaw[("High", ticker)].iloc[i])
        l = float(dataRaw[("Low", ticker)].iloc[i])
        c = float(dataRaw[("Close", ticker)].iloc[i])
        v = int(dataRaw[("Volume", ticker)].iloc[i])
        if day not in groupedByDay:
            groupedByDay[day] = {
                "morning": [],
                "afternoon": []
            }
        bar = [date.strftime("%Y-%m-%d %H:%M:%S"), o, h, l, c, v]
        if time <= "12:30:00":
            groupedByDay[day]["morning"].append(bar)
        else:
            groupedByDay[day]["afternoon"].append(bar)
    for day in groupedByDay:
        morningBars = groupedByDay[day]["morning"]
        afternoonBars = groupedByDay[day]["afternoon"]
        if len(morningBars) > 0:
            data4h.append([
                day + " 09:30:00",
                float(morningBars[0][1]),
                float(max(bar[2] for bar in morningBars)),
                float(min(bar[3] for bar in morningBars)),
                float(morningBars[-1][4]),
                int(sum(bar[5] for bar in morningBars))
            ])
        if len(afternoonBars) > 0:
            data4h.append([
                day + " 12:30:00",
                float(afternoonBars[0][1]),
                float(max(bar[2] for bar in afternoonBars)),
                float(min(bar[3] for bar in afternoonBars)),
                float(afternoonBars[-1][4]),
                int(sum(bar[5] for bar in afternoonBars))
            ])

    return [data1h, data4h]

def fetchTickerResults(ticker):
    OneHourData, FourHourData = fetchDataYahoo(ticker)
    OneHourBasis, OneHourHigh, OneHourLow = BollingerBands(OneHourData, 50)
    FourHourBasis, FourHourHigh, FourHourLow = BollingerBands(FourHourData, 20)
    OneHourBBP, FourHourBBP = BollingerBandsPercent(OneHourHigh, OneHourLow, OneHourData), BollingerBandsPercent(FourHourHigh, FourHourLow, FourHourData)
    basisDifferential, upperDifferential, lowerDifferential = BollingerBandsDifferentials(OneHourBasis[-1], OneHourHigh[-1], OneHourLow[-1],
                                                                                          FourHourBasis[-1], FourHourHigh[-1], FourHourLow[-1])
    OneHourBasisSlope, FourHourBasisSlope = lineSlopePercent(OneHourBasis, 5), lineSlopePercent(FourHourBasis, 5)
    if abs(basisDifferential) < .005 and abs(OneHourBasisSlope + FourHourBasisSlope) / 2 < .005:
        if OneHourBBP[-1] < .1:
            return 1
        elif OneHourBBP[-1] > .9:
            return -1
    return 0