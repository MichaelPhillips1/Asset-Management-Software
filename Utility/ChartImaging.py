import os, bisect
import matplotlib.pyplot as plt

from datetime import datetime
from matplotlib.patches import Rectangle
from .DataCollection import fetchDataYahoo, BollingerBands, BollingerBandsPercent, RSI

BARS = 500
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ChartImages"))
os.makedirs(OUT, exist_ok=True)


def generateChart(ticker):
    ticker = ticker.upper()
    d1, d4 = fetchDataYahoo(ticker)

    bb1 = BollingerBands(d1, length=50)
    bb4 = BollingerBands(d4, length=20)

    bbp1 = BollingerBandsPercent(bb1, d1)
    bbp4 = BollingerBandsPercent(bb4, d4)
    rsi1 = RSI(d1)

    currentPrice = d1[-1][4]
    oneHourBasis = bb1[-1][0]

    metrics = {
        "currentOneHourBollingerBandPercent": float(bbp1[-1]),
        "currentFourHourBollingerBandPercent": float(bbp4[-1]),
        "currentOneHourRSI": float(rsi1[-1]),
        "currentPricePercentDistanceFromOneHourBasis": float(
            (currentPrice - oneHourBasis) / oneHourBasis * 100
        )
    }

    visible1 = d1[-BARS:]
    visibleBB1 = bb1[-BARS:]

    dates1 = [datetime.strptime(x[0], "%Y-%m-%d %H:%M:%S") for x in visible1]
    dates4 = [datetime.strptime(x[0], "%Y-%m-%d %H:%M:%S") for x in d4]

    expanded4 = []
    for dt in dates1:
        i = bisect.bisect_right(dates4, dt) - 1
        expanded4.append(bb4[i] if i >= 0 and bb4[i] is not None else None)

    x = list(range(len(visible1)))

    fig, ax = plt.subplots(figsize=(12, 6), constrained_layout=True)
    fig.patch.set_facecolor("#111111")
    ax.set_facecolor("#111111")

    for i, (_, o, h, l, c, _) in enumerate(visible1):
        color = "#00bfa5" if c >= o else "#ef5350"

        ax.vlines(i, l, h, color=color, linewidth=1, zorder=3)

        ax.add_patch(Rectangle(
            (i - .36, min(o, c)),
            .72,
            max(abs(c - o), c * .0002, .01),
            facecolor=color,
            edgecolor=color,
            linewidth=.8,
            zorder=4
        ))

    def plotBands(bands, prefix, basisColor, bandColor, width):
        basis = [b[0] if b else None for b in bands]
        upper = [b[1] if b else None for b in bands]
        lower = [b[2] if b else None for b in bands]

        ax.plot(x, upper, color=bandColor, linewidth=width, label=f"{prefix} Upper")
        ax.plot(x, basis, color=basisColor, linewidth=width + .4, label=f"{prefix} Basis")
        ax.plot(x, lower, color=bandColor, linewidth=width, label=f"{prefix} Lower")

    plotBands(visibleBB1, "1H BB (50)", "#2196f3", "#00acc1", 1.2)
    plotBands(expanded4, "4H BB (20)", "#4caf50", "#ff5722", 1.5)

    ticks = list(range(0, len(visible1), 50))
    ax.set_xticks(ticks)
    ax.set_xticklabels([dates1[i].strftime("%m/%d") for i in ticks], color="#aaaaaa")
    ax.tick_params(axis="y", colors="#aaaaaa")
    ax.set_xlim(-2, len(visible1) + 2)

    values = [v for c in visible1 for v in (c[2], c[3])]
    values += [v for bands in (visibleBB1, expanded4) for b in bands if b for v in b]

    low, high = min(values), max(values)
    pad = (high - low) * .07
    ax.set_ylim(low - pad, high + pad)

    ax.grid(True, color="#2a2a2a", linewidth=.6, alpha=.7)

    for spine in ax.spines.values():
        spine.set_color("#333333")

    ax.set_title(
        f"{ticker} — Last {BARS} 1H Candles — 1H BB(50) + 4H BB(20)",
        color="white"
    )

    legend = ax.legend(loc="upper left", facecolor="#181818", edgecolor="#333333")
    for text in legend.get_texts():
        text.set_color("white")

    path = os.path.join(OUT, f"{ticker}.png")
    plt.savefig(path, dpi=100, facecolor=fig.get_facecolor())
    plt.close(fig)

    return path, metrics