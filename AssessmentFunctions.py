import statistics

# Function for calculating the Bollinger Bands indicator.
# Parameters:
#       data = The list of data points.
#       length = The length of the average.
#       stdDev = The number of standard deviations
# Return:
#       A list of lists with the first list being basis values, the seocnd list being
#       upper band values, and the third list being the lower band values.

def BollingerBands(data, length = 20, stdDev = 2):
    basis, high, low = [None] * length, [None] * length, [None] * length
    for i in range(length, len(data)):
        calculatedStdDev = statistics.stdev(data[i-length:i])
        basisTemp = sum(data[i-length:i]) / length
        highTemp = basisTemp + (stdDev * calculatedStdDev)
        lowTemp = basisTemp - (stdDev * calculatedStdDev)
        basis.append(basisTemp)
        high.append(highTemp)
        low.append(lowTemp)
    return [basis, high, low]

# Function for caluclating the differents for two different Bollinger Bands.
# Parameters:
#       lowerBasis = The basis line value for the lower time frames Bollinger Bands.
#       lowerUpper = The upper Bollinger Band line value for the lower time frame.
#       lowerLower = The lower Bollinger Band line value for the lower time frame.
#       higherBasis = The basis line value for the higher time frames Bollinger Bands.
#       higherUpper = The upper Bollinger Band line value for the higher time frame.
#       higherLower = The lower Bollinger Band line value for the higher time frame.
# Return:
#       A list of lists with the first list beinf the difference between the basis values
#       for the twp time frames recorded in percent, the second being the differents in the
#       upper Bollinger Band lines for the two times frames recorded in percent, and the
#       third being the difference in lower Bollinger Band lines for the two time frames
#       recorded in percent.

def BollingerBandsDifferentials(lowerBasis, lowerUpper, lowerLower, higherBasis, higherUpper, higherLower):
    basisDifferential = (lowerBasis - higherBasis) / higherBasis
    upperDifferential = (lowerUpper - higherUpper) / higherUpper
    lowerDifferential = (lowerLower - higherLower) / lowerLower
    return [basisDifferential, upperDifferential, lowerDifferential]

# Function for calculating the Bollinger Band Percent given price.
# Parameters:
#       high = The upper line value of the Bollinger Band.
#       low = The lower line value of the Bollinger Band.
#       close = The price value for the Bollinger Band.
# Return:
#       A value representing the position of the price relative to the channel created
#       by the upper and lower band, with values < 0 meaning a position beneath the lower
#       band, values > 1 meaning above the upper band, and values between 0 and 1 meaning
#       contained within the bands.

def BollingerBandsPercent(high, low, close):
    return (close - low) / (high - low)