import statistics
from DataCollection import fetchDataYahoo

def BollingerBands(data, length = 20, stdDev = 2):
    basis, high, low = [None] * length, [None] * length, [None] * length
    data = [element[4] for element in data]
    for i in range(length, len(data)):
        calculatedStdDev = statistics.stdev(data[i-length:i])
        basisTemp = sum(data[i-length:i]) / length
        highTemp = basisTemp + (stdDev * calculatedStdDev)
        lowTemp = basisTemp - (stdDev * calculatedStdDev)
        basis.append(basisTemp)
        high.append(highTemp)
        low.append(lowTemp)
    return [basis, high, low]

def BollingerBandsDifferentials(lowerBasis, lowerUpper, lowerLower, higherBasis, higherUpper, higherLower):
    basisDifferential = (lowerBasis - higherBasis) / higherBasis
    upperDifferential = (lowerUpper - higherUpper) / higherUpper
    lowerDifferential = (lowerLower - higherLower) / lowerLower
    return [basisDifferential, upperDifferential, lowerDifferential]

def BollingerBandsPercent(bollingerHigh, bollingerLow, tickerData):
    closes = [element[4] for element in tickerData]
    bbPercent = []
    for i in range(len(closes)):
        if bollingerHigh[i] is None or bollingerLow[i] is None:
            bbPercent.append(None)
        elif bollingerHigh[i] == bollingerLow[i]:
            bbPercent.append(None)
        else:
            bbPercent.append((closes[i] - bollingerLow[i]) / (bollingerHigh[i] - bollingerLow[i]))
    return bbPercent

def lineSlopePercent(line, window):
    return ((line[-1] - line[-(window + 1)]) / window) / line[-1]

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