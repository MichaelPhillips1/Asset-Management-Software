from DataCollection import *
from AssessmentFunctions import *


tickers = ["AAPL", "MSFT", "NVDA", "SMCI", "APP", "GOOG", "AMZN" "META", "TSLA", "GS", "MS", "IONQ", "C", "COIN", "SPOT", "DUOL"]
for ticker in tickers:
    DayData = Fetch_Yaohoo_Data(ticker, "max", "1d")
    WeekData = Fetch_Yaohoo_Data(ticker, "max", "1wk")

    bbBasisDay, bbUpperDay, bbLowerDay = BollingerBands(DayData[4])
    bbPercentDay = BollingerBandsPercent(bbUpperDay[-1], bbLowerDay[-1], DayData[4][-1])
    bbBasisWeek, bbUpperWeek, bbLowerWeek = BollingerBands(WeekData[4])
    bbPercentWeek = BollingerBandsPercent(bbUpperWeek[-1], bbLowerWeek[-1], WeekData[4][-1])
    basisDifferential, upperDifferential, lowerDifferential = BollingerBandsDifferentials(bbBasisDay[-1], bbUpperDay[-1], bbLowerDay[-1], bbBasisWeek[-1], bbUpperWeek[-1], bbLowerWeek[-1])