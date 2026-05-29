import statistics

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

def BollingerBandsPercent(high, low, close):
    return (close - low) / (high - low)

def lineSlopePercent(line, window):
    return ((line[-1] - line[-(window + 1)]) / window) / line[-1]
