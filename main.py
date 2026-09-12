import os, random
from Utility.ChartImaging import generateChart
from Utility.Pannel import Pannel

tickers = ["OKLO"]

ROOT = os.path.dirname(os.path.abspath(__file__))
EXAMPLES = os.path.join(ROOT, "Examples")

pannel = Pannel(count=10, workers=10)

def sampleExamples(direction, count=4):
    prefix = "BullReversionSetup" if direction == "bull" else "BearReversionSetup"

    files = [
        os.path.join(EXAMPLES, f)
        for f in os.listdir(EXAMPLES)
        if f.startswith(prefix) and f.lower().endswith(".png")
    ]

    if len(files) < count:
        raise ValueError(f"Only found {len(files)} {direction} examples")

    return random.sample(files, count)


for ticker in tickers:
    try:
        chartPath, metrics = generateChart(ticker)

        bb = metrics["currentOneHourBollingerBandPercent"]

        if bb < .15:
            direction = "bull"
        elif bb > .85:
            direction = "bear"
        else:
            print(f"{ticker} | skipped | BB%={bb:.3f}")
            continue

        examples = sampleExamples(direction, 4)

        result = pannel.rank(
            ticker,
            chartPath,
            metrics,
            examples
        )

        print(
            f"\n{ticker} | "
            f"{direction.upper()} | "
            f"BB%={bb:.3f} | "
            f"confidence={result['score']:.1f}"
        )

        print("Examples:", [os.path.basename(x) for x in examples])
        print("Exact:", result["metrics"])
        print("Visual:", result["details"])

    except Exception as e:
        print(f"{ticker} ERROR: {e}")