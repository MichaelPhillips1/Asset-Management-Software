import json, statistics
from ollama import chat
from concurrent.futures import ThreadPoolExecutor


SCHEMA = {
    "type": "object",
    "properties": {
        "excursionSuddenness": {"type": "number", "minimum": 0, "maximum": 100},
        "priorEquilibriumStability": {"type": "number", "minimum": 0, "maximum": 100},
        "excursionExhaustion": {"type": "number", "minimum": 0, "maximum": 100},
        "trendContinuationRisk": {"type": "number", "minimum": 0, "maximum": 100}
    },
    "required": [
        "excursionSuddenness",
        "priorEquilibriumStability",
        "excursionExhaustion",
        "trendContinuationRisk"
    ]
}


class Pannel:
    def __init__(self, model="qwen3-vl:8b", count=1, workers=1):
        self.model = model
        self.count = count
        self.workers = workers

    def _ask(self, imagePath, metrics, examples):
        messages = []

        for path in examples:
            messages.append({
                "role": "user",
                "content": (
                    "This is a GOOD example of the type of short-term "
                    "mean-reversion setup you should recognize."
                ),
                "images": [path]
            })

        messages.append({
            "role": "user",
            "content": (
                "Now analyze ONLY the far-right/current setup in this final chart. "
                "Compare its visual structure with the GOOD examples above. "
                f"These measurements are exact: {json.dumps(metrics)}. "
                "Do not estimate those measurements visually. "
                "Rate excursionSuddenness, priorEquilibriumStability, "
                "excursionExhaustion, and trendContinuationRisk from 0-100."
            ),
            "images": [imagePath]
        })

        r = chat(
            model=self.model,
            messages=messages,
            format=SCHEMA,
            think=False,
            keep_alive="30m",
            options={
                "temperature": .2,
                "num_ctx": 16384,
                "num_predict": 128
            }
        )

        response = (
            (r.message.content or "").strip()
            or (getattr(r.message, "thinking", "") or "").strip()
        )

        if not response:
            raise ValueError("Qwen returned no response")

        d = json.loads(response)

        for key in d:
            d[key] = max(0, min(100, float(d[key])))

        return d

    def _score(self, metrics, visual):
        bb1 = metrics["currentOneHourBollingerBandPercent"]
        bb4 = metrics["currentFourHourBollingerBandPercent"]
        rsi = metrics["currentOneHourRSI"]
        basisDistance = abs(
            metrics["currentPricePercentDistanceFromOneHourBasis"]
        )

        oneHourExtension = min(100, abs(bb1 - .5) / .5 * 100)
        fourHourExtension = min(100, abs(bb4 - .5) / .5 * 100)
        rsiExtension = min(100, abs(rsi - 50) / 30 * 100)
        basisExtension = min(100, basisDistance / 4 * 100)

        objective = (
            oneHourExtension * .40 +
            fourHourExtension * .20 +
            rsiExtension * .15 +
            basisExtension * .25
        )

        visualScore = (
            visual["excursionSuddenness"] * .30 +
            visual["priorEquilibriumStability"] * .25 +
            visual["excursionExhaustion"] * .25 +
            (100 - visual["trendContinuationRisk"]) * .20
        )

        return objective * .55 + visualScore * .45

    def _run(self, imagePath, metrics, examples):
        visual = self._ask(imagePath, metrics, examples)
        return self._score(metrics, visual), visual

    def rank(self, ticker, imagePath, metrics, examples):
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            results = list(ex.map(
                lambda _: self._run(imagePath, metrics, examples),
                range(self.count)
            ))

        scores = [x[0] for x in results]

        return {
            "ticker": ticker,
            "score": round(statistics.mean(scores), 2),
            "std": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
            "metrics": metrics,
            "details": results[0][1]
        }