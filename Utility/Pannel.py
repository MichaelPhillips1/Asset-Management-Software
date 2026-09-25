import json
import os
import statistics
from concurrent.futures import ThreadPoolExecutor

from ollama import chat


SCHEMA = {
    "type": "object",
    "properties": {
        "excursionSuddenness": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
        },
        "priorEquilibriumStability": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
        },
        "excursionExhaustion": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
        },
        "trendContinuationRisk": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
        },
    },
    "required": [
        "excursionSuddenness",
        "priorEquilibriumStability",
        "excursionExhaustion",
        "trendContinuationRisk",
    ],
}

REFERENCE_PROMPT = (
    "This is a GOOD example of the type of short-term "
    "mean-reversion setup you should recognize."
)


class Pannel:
    def __init__(self, model="qwen3-vl:8b", count=1, workers=1):
        count = int(count)
        workers = int(workers)

        if count < 1:
            raise ValueError("Agent count must be at least 1.")

        if workers < 1:
            raise ValueError("Worker count must be at least 1.")

        if workers > count:
            raise ValueError("Workers cannot be greater than agents.")

        self.model = model
        self.count = count
        self.workers = workers

    def _build_analysis_prompt(self, metrics):
        return (
            "Now analyze ONLY the far-right/current setup in this final chart. "
            "Compare its visual structure with the GOOD examples above. "
            f"These measurements are exact: {json.dumps(metrics)}. "
            "Do not estimate those measurements visually. "
            "Rate excursionSuddenness, priorEquilibriumStability, "
            "excursionExhaustion, and trendContinuationRisk from 0-100."
        )

    def _ask(self, image_bytes, metrics, examples):
        messages = []

        for path in examples:
            messages.append({
                "role": "user",
                "content": REFERENCE_PROMPT,
                "images": [path],
            })

        analysis_prompt = self._build_analysis_prompt(metrics)

        messages.append({
            "role": "user",
            "content": analysis_prompt,
            "images": [image_bytes],
        })

        result = chat(
            model=self.model,
            messages=messages,
            format=SCHEMA,
            think=False,
            keep_alive="30m",
            options={
                "temperature": 0.2,
                "num_ctx": 16384,
                "num_predict": 128,
            },
        )

        response_text = (
            (result.message.content or "").strip()
            or (getattr(result.message, "thinking", "") or "").strip()
        )

        if not response_text:
            raise ValueError("Qwen returned no response.")

        visual = json.loads(response_text)

        for key in visual:
            visual[key] = max(0, min(100, float(visual[key])))

        normalized_response = json.dumps(visual)

        prompt_log = json.dumps({
            "referenceInstruction": REFERENCE_PROMPT,
            "referenceExamples": [
                os.path.basename(path)
                for path in examples
            ],
            "analysisPrompt": analysis_prompt,
        })

        return visual, prompt_log, normalized_response

    def _score(self, metrics, visual):
        bb1 = metrics["currentOneHourBollingerBandPercent"]
        bb4 = metrics["currentFourHourBollingerBandPercent"]
        rsi = metrics["currentOneHourRSI"]
        basis_distance = abs(
            metrics["currentPricePercentDistanceFromOneHourBasis"]
        )

        one_hour_extension = min(100, abs(bb1 - 0.5) / 0.5 * 100)
        four_hour_extension = min(100, abs(bb4 - 0.5) / 0.5 * 100)
        rsi_extension = min(100, abs(rsi - 50) / 30 * 100)
        basis_extension = min(100, basis_distance / 4 * 100)

        objective = (
            one_hour_extension * 0.40
            + four_hour_extension * 0.20
            + rsi_extension * 0.15
            + basis_extension * 0.25
        )

        visual_score = (
            visual["excursionSuddenness"] * 0.30
            + visual["priorEquilibriumStability"] * 0.25
            + visual["excursionExhaustion"] * 0.25
            + (100 - visual["trendContinuationRisk"]) * 0.20
        )

        return objective * 0.55 + visual_score * 0.45

    def _run_agent(self, image_bytes, metrics, examples):
        visual, prompt, response = self._ask(
            image_bytes,
            metrics,
            examples,
        )

        score = self._score(metrics, visual)

        return {
            "score": score,
            "visual": visual,
            "prompt": prompt,
            "response": response,
        }

    def rank(self, ticker, image_bytes, metrics, examples):
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            results = list(
                executor.map(
                    lambda _: self._run_agent(
                        image_bytes,
                        metrics,
                        examples,
                    ),
                    range(self.count),
                )
            )

        scores = [result["score"] for result in results]

        agents = []

        for agent_number, result in enumerate(results, start=1):
            agents.append({
                "agentNumber": agent_number,
                "score": round(result["score"], 4),
                "visual": result["visual"],
                "prompt": result["prompt"],
                "response": result["response"],
            })

        return {
            "ticker": ticker,
            "score": round(statistics.mean(scores), 2),
            "std": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
            "metrics": metrics,
            "agents": agents,
        }
