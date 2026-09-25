import bisect
import io
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from .DataCollection import fetchDataYahoo, BollingerBands, BollingerBandsPercent, RSI


MIN_BARS = 250


def generateChart(ticker, bars=500):
    ticker = ticker.upper()
    bars = int(bars)

    if bars < MIN_BARS:
        raise ValueError(f"Lookback must be at least {MIN_BARS} 1-hour bars.")

    d1, d4 = fetchDataYahoo(ticker)

    if len(d1) < bars:
        raise ValueError(
            f"{ticker} only returned {len(d1)} 1-hour bars; {bars} were requested."
        )

    bb1 = BollingerBands(d1, length=50)
    bb4 = BollingerBands(d4, length=20)

    bbp1 = BollingerBandsPercent(bb1, d1)
    bbp4 = BollingerBandsPercent(bb4, d4)
    rsi1 = RSI(d1)

    if bb1[-1] is None or bb4[-1] is None or bbp1[-1] is None or bbp4[-1] is None:
        raise ValueError("Not enough data to calculate the current Bollinger metrics.")

    current_price = d1[-1][4]
    one_hour_basis = bb1[-1][0]

    metrics = {
        "currentOneHourBollingerBandPercent": float(bbp1[-1]),
        "currentFourHourBollingerBandPercent": float(bbp4[-1]),
        "currentOneHourRSI": float(rsi1[-1]),
        "currentPricePercentDistanceFromOneHourBasis": float(
            (current_price - one_hour_basis) / one_hour_basis * 100
        ),
    }

    visible1 = d1[-bars:]
    visible_bb1 = bb1[-bars:]

    dates1 = [
        datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        for row in visible1
    ]

    dates4 = [
        datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        for row in d4
    ]

    expanded4 = []

    for dt in dates1:
        index = bisect.bisect_right(dates4, dt) - 1
        expanded4.append(
            bb4[index]
            if index >= 0 and bb4[index] is not None
            else None
        )

    x = list(range(len(visible1)))

    fig, ax = plt.subplots(figsize=(12, 6), constrained_layout=True)
    fig.patch.set_facecolor("#111111")
    ax.set_facecolor("#111111")

    for index, (_, open_price, high, low, close, _) in enumerate(visible1):
        color = "#00bfa5" if close >= open_price else "#ef5350"

        ax.vlines(
            index,
            low,
            high,
            color=color,
            linewidth=1,
            zorder=3,
        )

        ax.add_patch(
            Rectangle(
                (index - 0.36, min(open_price, close)),
                0.72,
                max(abs(close - open_price), close * 0.0002, 0.01),
                facecolor=color,
                edgecolor=color,
                linewidth=0.8,
                zorder=4,
            )
        )

    def plot_bands(bands, prefix, basis_color, band_color, width):
        basis = [band[0] if band else None for band in bands]
        upper = [band[1] if band else None for band in bands]
        lower = [band[2] if band else None for band in bands]

        ax.plot(x, upper, color=band_color, linewidth=width, label=f"{prefix} Upper")
        ax.plot(
            x,
            basis,
            color=basis_color,
            linewidth=width + 0.4,
            label=f"{prefix} Basis",
        )
        ax.plot(x, lower, color=band_color, linewidth=width, label=f"{prefix} Lower")

    plot_bands(visible_bb1, "1H BB (50)", "#2196f3", "#00acc1", 1.2)
    plot_bands(expanded4, "4H BB (20)", "#4caf50", "#ff5722", 1.5)

    tick_step = max(1, len(visible1) // 10)
    ticks = list(range(0, len(visible1), tick_step))

    ax.set_xticks(ticks)
    ax.set_xticklabels(
        [dates1[index].strftime("%m/%d") for index in ticks],
        color="#aaaaaa",
    )

    ax.tick_params(axis="y", colors="#aaaaaa")
    ax.set_xlim(-2, len(visible1) + 2)

    values = [value for candle in visible1 for value in (candle[2], candle[3])]
    values += [
        value
        for bands in (visible_bb1, expanded4)
        for band in bands
        if band
        for value in band
    ]

    low = min(values)
    high = max(values)
    pad = (high - low) * 0.07 if high != low else max(abs(high) * 0.01, 1)

    ax.set_ylim(low - pad, high + pad)
    ax.grid(True, color="#2a2a2a", linewidth=0.6, alpha=0.7)

    for spine in ax.spines.values():
        spine.set_color("#333333")

    ax.set_title(
        f"{ticker} — Last {len(visible1)} 1H Candles — 1H BB(50) + 4H BB(20)",
        color="white",
    )

    legend = ax.legend(
        loc="upper left",
        facecolor="#181818",
        edgecolor="#333333",
    )

    for text in legend.get_texts():
        text.set_color("white")

    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        dpi=100,
        facecolor=fig.get_facecolor(),
    )

    plt.close(fig)

    image_bytes = buffer.getvalue()
    buffer.close()

    run_range = {
        "startDateTime": visible1[0][0],
        "endDateTime": visible1[-1][0],
        "barCount": len(visible1),
    }

    return image_bytes, metrics, run_range
