import yfinance as yf
import statistics

def DMI(data, length=14):
    n = len(data)

    adx = [None] * n
    plusDI = [None] * n
    minusDI = [None] * n

    if n <= length:
        return adx, plusDI, minusDI

    tr = [0] * n
    plusDM = [0] * n
    minusDM = [0] * n
    dx = [None] * n

    for i in range(1, n):
        high = data[i][2]
        low = data[i][3]
        prevHigh = data[i-1][2]
        prevLow = data[i-1][3]
        prevClose = data[i-1][4]

        upMove = high - prevHigh
        downMove = prevLow - low

        plusDM[i] = upMove if upMove > downMove and upMove > 0 else 0
        minusDM[i] = downMove if downMove > upMove and downMove > 0 else 0

        tr[i] = max(
            high - low,
            abs(high - prevClose),
            abs(low - prevClose)
        )

    smoothedTR = sum(tr[1:length+1])
    smoothedPlusDM = sum(plusDM[1:length+1])
    smoothedMinusDM = sum(minusDM[1:length+1])

    for i in range(length, n):
        if i > length:
            smoothedTR = smoothedTR - smoothedTR / length + tr[i]
            smoothedPlusDM = smoothedPlusDM - smoothedPlusDM / length + plusDM[i]
            smoothedMinusDM = smoothedMinusDM - smoothedMinusDM / length + minusDM[i]

        if smoothedTR == 0:
            plusDI[i] = 0
            minusDI[i] = 0
        else:
            plusDI[i] = 100 * smoothedPlusDM / smoothedTR
            minusDI[i] = 100 * smoothedMinusDM / smoothedTR

        totalDI = plusDI[i] + minusDI[i]

        dx[i] = (
            0
            if totalDI == 0
            else 100 * abs(plusDI[i] - minusDI[i]) / totalDI
        )

        if i == (2 * length) - 1:
            adx[i] = sum(dx[length:i+1]) / length

        elif i > (2 * length) - 1:
            adx[i] = (
                (adx[i-1] * (length - 1)) + dx[i]
            ) / length

    return adx, plusDI, minusDI

def BollingerBands(data, length=20, stdDev=2):
    closes = [x[4] for x in data]
    bands = [None] * length
    for i in range(length, len(closes)):
        window = closes[i-length:i]
        basis = sum(window) / length
        std = statistics.stdev(window)
        bands.append([basis, basis + stdDev * std, basis - stdDev * std])
    return bands

def BollingerBandsPercent(bands, data):
    closes = [x[4] for x in data]
    return [
        None if bands[i] is None or bands[i][1] == bands[i][2]
        else (closes[i] - bands[i][2]) / (bands[i][1] - bands[i][2])
        for i in range(len(data))
    ]

def RSI(data, length=14):
    closes = [x[4] for x in data]
    rsi = [None] * length
    for i in range(length, len(closes)):
        changes = [closes[j] - closes[j-1] for j in range(i-length+1, i+1)]
        avgGain = sum(max(x, 0) for x in changes) / length
        avgLoss = sum(max(-x, 0) for x in changes) / length
        rsi.append(100 if avgLoss == 0 else 100 - (100 / (1 + avgGain / avgLoss)))
    return rsi

def BollingerBandsDifferentials(lowerBasis, lowerUpper, lowerLower, higherBasis, higherUpper, higherLower):
    return [
        (lowerBasis - higherBasis) / higherBasis,
        (lowerUpper - higherUpper) / higherUpper,
        (lowerLower - higherLower) / lowerLower
    ]

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