from DataCollection import *
from AssessmentFunctions import *

tickers = [
    # Mega-cap / big tech
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOG", "META", "TSLA", "AVGO", "ORCL",
    "ADBE", "CRM", "NFLX", "AMD", "INTC", "QCOM", "TXN", "MU", "CSCO", "IBM",
    "NOW", "PANW", "CRWD", "DDOG", "NET", "SNOW", "PLTR", "SHOP", "UBER", "ABNB",
    "PYPL", "COIN", "HOOD", "ROKU", "ZM", "DOCU", "MDB", "TEAM", "OKTA", "APP",

    # Semis / hardware
    "AMAT", "LRCX", "KLAC", "ADI", "MRVL", "MCHP", "ON", "NXPI", "MPWR", "SWKS",
    "TER", "ENTG", "WDC", "STX", "DELL", "HPQ", "NTAP", "SMCI", "ARM", "TSM",

    # Financials
    "JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "V", "MA", "BLK",
    "SCHW", "COF", "USB", "PNC", "TFC", "BK", "STT", "AIG", "MET",
    "PRU", "ALL", "TRV", "CB", "CME", "ICE", "SPGI", "MCO", "NDAQ", "BR",

    # Healthcare / biotech
    "UNH", "LLY", "JNJ", "MRK", "ABBV", "PFE", "BMY", "AMGN", "GILD", "REGN",
    "VRTX", "BIIB", "MRNA", "ISRG", "TMO", "DHR", "ABT", "MDT", "SYK", "BSX",
    "ZBH", "HUM", "CI", "CVS", "ELV", "HCA", "IDXX", "ILMN", "DXCM", "EW",

    # Consumer / retail / restaurants
    "WMT", "COST", "TGT", "HD", "LOW", "NKE", "LULU", "SBUX", "MCD", "CMG",
    "YUM", "DPZ", "DRI", "CROX", "TJX", "ROST", "ULTA", "EL", "PG", "KO",
    "PEP", "KHC", "MDLZ", "GIS", "CL", "CLX", "KMB", "MNST", "CELH",

    # Energy
    "XOM", "CVX", "COP", "SLB", "OXY", "EOG", "MPC", "VLO", "PSX", "HAL",
    "BKR", "DVN", "FANG", "APA", "KMI", "WMB", "OKE", "LNG", "ENPH",
    "SEDG", "FSLR", "RUN", "NEE", "DUK", "SO", "AEP", "EXC", "D",

    # Industrials / defense / transport
    "CAT", "DE", "BA", "GE", "HON", "MMM", "RTX", "LMT", "NOC", "GD",
    "UPS", "FDX", "UNP", "CSX", "NSC", "DAL", "UAL", "AAL", "LUV", "JBLU",
    "RCL", "CCL", "NCLH", "MAR", "HLT", "ABNB", "BKNG", "EXPE", "URI", "ETN",

    # Communications / media / gaming
    "DIS", "CMCSA", "T", "VZ", "CHTR", "TMUS", "WBD", "EA", "TTWO",
    "RBLX", "SPOT", "SNAP", "PINS", "MTCH", "BMBL", "DJT", "FOX", "LYV",

    # Real estate / REITs
    "AMT", "PLD", "EQIX", "CCI", "SPG", "O", "VICI", "DLR", "PSA", "WELL",
    "AVB", "EQR", "MAA", "EXR", "CBRE", "WY", "IRM", "ARE", "BXP", "KIM",

    # Materials
    "LIN", "APD", "SHW", "ECL", "NEM", "FCX", "DD", "DOW", "NUE", "STLD",
    "AA", "CLF", "MOS", "CF", "ALB", "SQM", "RIO", "BHP", "VALE",

    # Autos / EV / mobility
    "F", "GM", "RIVN", "LCID", "NIO", "LI", "XPEV", "TM", "HMC", "STLA",
    "CAR", "HTZ", "AZO", "ORLY", "AAP", "GPC", "LKQ", "MGA", "BWA", "QS",

    # Popular mid/small/growth names
    "SOFI", "AFRM", "UPST", "OPEN", "DKNG", "PENN", "MARA", "RIOT", "HUT", "CLSK",
    "IONQ", "RGTI", "QBTS", "SOUN", "AI", "PATH", "U", "FUBO", "CHWY", "ETSY",
    "W", "CVNA", "GME", "AMC", "BB", "NOK", "TAL", "BABA", "JD", "PDD"
]

reversions = []

for ticker in tickers:
    HourData = Fetch_Yaohoo_Data(ticker, "max", "1h")
    FourHourData = Fetch_Yaohoo_Data(ticker, "max", "4h")
    bbBasisHour, bbUpperHour, bbLowerHour = BollingerBands(HourData[4], 50)
    bbPercentHour = BollingerBandsPercent(bbUpperHour[-1], bbLowerHour[-1], HourData[4][-1])
    bbBasisFourHour, bbUpperFourHour, bbLowerFourHour = BollingerBands(FourHourData[4], 20)
    bbPercentFourHour = BollingerBandsPercent(bbUpperFourHour[-1], bbLowerFourHour[-1], FourHourData[4][-1])
    basisDifferential, upperDifferential, lowerDifferential = BollingerBandsDifferentials(bbBasisHour[-1], bbUpperHour[-1], bbLowerHour[-1], bbBasisFourHour[-1], bbUpperFourHour[-1], bbLowerFourHour[-1])
    if(abs(basisDifferential) < .005 and (bbPercentHour > .9 or bbPercentHour < .1)):
        reversions.append(ticker)
exportTickers(reversions)