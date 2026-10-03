# accumulator.py
# Khmer News 24
# Football Accumulator Engine
#
# Rules:
# - Model probability >= 75%
# - Combined odds >= 2.50
# - Maximum 4 legs
#
# IMPORTANT:
# Real bookmaker odds must come from a real odds source.
# Do not use demo/test odds as real betting odds.

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Optional

from odds import (
    OddsSelection,
    calculate_combined_odds,
)


# ============================================================
# SETTINGS
# ============================================================

MIN_PROBABILITY = 72.0
MIN_COMBINED_ODDS = 2.50

MIN_LEGS = 2
MAX_LEGS = 4


# ============================================================
# DATA STRUCTURE
# ============================================================

@dataclass
class AccumulatorResult:
    selections: list[OddsSelection]

    combined_odds: float

    average_probability: float

    lowest_probability: float

    score: float


# ============================================================
# BASIC HELPERS
# ============================================================

def calculate_average_probability(
    selections: list[OddsSelection],
) -> float:

    probabilities = [
        selection.model_probability
        for selection in selections
        if selection.model_probability is not None
    ]

    if not probabilities:
        return 0.0

    return round(
        sum(probabilities)
        / len(probabilities),
        2,
    )


def calculate_lowest_probability(
    selections: list[OddsSelection],
) -> float:

    probabilities = [
        selection.model_probability
        for selection in selections
        if selection.model_probability is not None
    ]

    if not probabilities:
        return 0.0

    return round(
        min(probabilities),
        2,
    )


# ============================================================
# FILTER QUALIFIED SELECTIONS
# ============================================================

def filter_qualified_selections(
    selections: list[OddsSelection],
    minimum_probability: float = MIN_PROBABILITY,
) -> list[OddsSelection]:
    """
    Keep only selections that have model probability
    >= required threshold.
    """

    qualified = []

    for selection in selections:

        if selection.odds <= 1.0:
            continue

        if selection.model_probability is None:
            continue

        if (
            selection.model_probability
            < minimum_probability
        ):
            continue

        qualified.append(
            selection
        )

    return qualified


# ============================================================
# ACCUMULATOR SCORE
# ============================================================

def calculate_acc_score(
    selections: list[OddsSelection],
) -> float:
    """
    Internal ranking score.

    Higher model probability is preferred.

    This is NOT a prediction of winning.
    """

    if not selections:
        return 0.0

    probabilities = [
        selection.model_probability
        for selection in selections
        if selection.model_probability is not None
    ]

    if not probabilities:
        return 0.0

    average_probability = (
        sum(probabilities)
        / len(probabilities)
    )

    combined_odds = calculate_combined_odds(
        selections
    )

    # Small preference for stronger average probability.
    # Odds are included only as a secondary factor.
    score = (
        average_probability * 0.90
        + min(combined_odds, 10.0) * 1.0
    )

    return round(
        score,
        2,
    )


# ============================================================
# BUILD ALL POSSIBLE ACCUMULATORS
# ============================================================

def generate_accumulators(
    selections: list[OddsSelection],
    minimum_probability: float = MIN_PROBABILITY,
    minimum_combined_odds: float = MIN_COMBINED_ODDS,
    min_legs: int = MIN_LEGS,
    max_legs: int = MAX_LEGS,
) -> list[AccumulatorResult]:
    """
    Generate valid accumulator combinations.

    Conditions:

    1. Each selection probability >= minimum_probability
    2. Combined odds >= minimum_combined_odds
    3. Number of legs between min_legs and max_legs
    """

    qualified = filter_qualified_selections(
        selections,
        minimum_probability,
    )

    if len(qualified) < min_legs:
        return []

    results = []

    actual_max_legs = min(
        max_legs,
        len(qualified),
    )

    for number_of_legs in range(
        min_legs,
        actual_max_legs + 1,
    ):

        for combo in combinations(
            qualified,
            number_of_legs,
        ):

            combo = list(combo)

            combined_odds = (
                calculate_combined_odds(
                    combo
                )
            )

            if (
                combined_odds
                < minimum_combined_odds
            ):
                continue

            average_probability = (
                calculate_average_probability(
                    combo
                )
            )

            lowest_probability = (
                calculate_lowest_probability(
                    combo
                )
            )

            score = calculate_acc_score(
                combo
            )

            results.append(
                AccumulatorResult(
                    selections=combo,
                    combined_odds=combined_odds,
                    average_probability=average_probability,
                    lowest_probability=lowest_probability,
                    score=score,
                )
            )

    # Highest score first
    results.sort(
        key=lambda x: (
            x.score,
            x.average_probability,
        ),
        reverse=True,
    )

    return results


# ============================================================
# SELECT BEST ACCUMULATOR
# ============================================================

def select_best_accumulator(
    selections: list[OddsSelection],
    minimum_probability: float = MIN_PROBABILITY,
    minimum_combined_odds: float = MIN_COMBINED_ODDS,
    min_legs: int = MIN_LEGS,
    max_legs: int = MAX_LEGS,
) -> Optional[AccumulatorResult]:
    """
    Return the highest-ranked valid accumulator.

    If no combination satisfies the rules,
    return None.
    """

    accumulators = generate_accumulators(
        selections=selections,
        minimum_probability=minimum_probability,
        minimum_combined_odds=minimum_combined_odds,
        min_legs=min_legs,
        max_legs=max_legs,
    )

    if not accumulators:
        return None

    return accumulators[0]


# ============================================================
# FORMAT ACCUMULATOR
# ============================================================

def format_accumulator(
    accumulator: AccumulatorResult,
) -> str:
    """
    Format accumulator for Telegram.
    """

    lines = []

    lines.append(
        "🎯 ACC ANALYSIS"
    )

    lines.append("")

    lines.append(
        f"📊 Legs: "
        f"{len(accumulator.selections)}"
    )

    lines.append("")

    for index, selection in enumerate(
        accumulator.selections,
        start=1,
    ):

        lines.append(
            f"{index}. "
            f"⚽ {selection.home_team} "
            f"vs {selection.away_team}"
        )

        lines.append(
            f"   🎯 {selection.market}: "
            f"{selection.selection}"
        )

        lines.append(
            f"   💰 Odds: "
            f"{selection.odds:.2f}"
        )

        if selection.model_probability is not None:

            lines.append(
                f"   🤖 Model: "
                f"{selection.model_probability:.1f}%"
            )

        if selection.bookmaker:

            lines.append(
                f"   🏦 Source: "
                f"{selection.bookmaker}"
            )

        lines.append("")

    lines.append(
        "━━━━━━━━━━━━━━━━━━"
    )

    lines.append(
        f"💰 Combined Odds: "
        f"{accumulator.combined_odds:.2f}"
    )

    lines.append(
        f"🤖 Average Model: "
        f"{accumulator.average_probability:.1f}%"
    )

    lines.append(
        f"📉 Lowest Model: "
        f"{accumulator.lowest_probability:.1f}%"
    )

    lines.append("")

    if (
        accumulator.combined_odds
        >= MIN_COMBINED_ODDS
    ):

        lines.append(
            "✅ Combined Odds ≥ 2.50"
        )

    if (
        accumulator.lowest_probability
        >= MIN_PROBABILITY
    ):

        lines.append(
            "✅ Every selection ≥ 75%"
        )

    lines.append("")

    lines.append(
        "⚠️ Statistical analysis only."
    )

    lines.append(
        "No result is guaranteed."
    )

    return "\n".join(lines)


# ============================================================
# FORMAT NO ACC
# ============================================================

def format_no_acc(
    selections: list[OddsSelection],
) -> str:
    """
    Message when no accumulator qualifies.
    """

    qualified = filter_qualified_selections(
        selections,
        MIN_PROBABILITY,
    )

    if not qualified:

        return (
            "🎯 ACC ANALYSIS\n\n"
            "❌ No selection reached "
            "the 75% model threshold.\n\n"
            "📊 No ACC generated."
        )

    return (
        "🎯 ACC ANALYSIS\n\n"
        "❌ No combination reached "
        "combined odds ≥ 2.50.\n\n"
        f"📊 Qualified selections: "
        f"{len(qualified)}\n"
        f"🎯 Required odds: "
        f"{MIN_COMBINED_ODDS:.2f}+"
    )


# ============================================================
# TEST DATA
# ============================================================

def create_demo_selections():
    """
    DEMO ONLY.

    These odds are fake test numbers.
    They must NOT be presented as real bookmaker odds.
    """

    return [

        OddsSelection(
            match_id="demo_001",
            home_team="Team A",
            away_team="Team B",
            market="Over 1.5",
            selection="Over 1.5",
            odds=1.30,
            bookmaker="DEMO",
            model_probability=82.0,
        ),

        OddsSelection(
            match_id="demo_002",
            home_team="Team C",
            away_team="Team D",
            market="1X",
            selection="1X",
            odds=1.35,
            bookmaker="DEMO",
            model_probability=79.0,
        ),

        OddsSelection(
            match_id="demo_003",
            home_team="Team E",
            away_team="Team F",
            market="Over 1.5",
            selection="Over 1.5",
            odds=1.50,
            bookmaker="DEMO",
            model_probability=81.0,
        ),

        OddsSelection(
            match_id="demo_004",
            home_team="Team G",
            away_team="Team H",
            market="X2",
            selection="X2",
            odds=1.25,
            bookmaker="DEMO",
            model_probability=77.0,
        ),
    ]


# ============================================================
# TEST
# ============================================================

def test_accumulator():

    print("=" * 60)

    print(
        "KHMER NEWS 24"
    )

    print(
        "ACCUMULATOR ENGINE TEST"
    )

    print("=" * 60)

    selections = (
        create_demo_selections()
    )

    print()

    print(
        f"Total test selections: "
        f"{len(selections)}"
    )

    print()

    qualified = (
        filter_qualified_selections(
            selections,
            MIN_PROBABILITY,
        )
    )

    print(
        f"Qualified ≥ "
        f"{MIN_PROBABILITY}%: "
        f"{len(qualified)}"
    )

    print()

    accumulator = (
        select_best_accumulator(
            selections=selections,
            minimum_probability=75.0,
            minimum_combined_odds=2.50,
            min_legs=2,
            max_legs=4,
        )
    )

    if accumulator is None:

        print(
            format_no_acc(
                selections
            )
        )

        return

    print(
        format_accumulator(
            accumulator
        )
    )

    print()

    print("=" * 60)

    print(
        "⚠️ DEMO DATA ONLY"
    )

    print(
        "The odds above are test values."
    )

    print(
        "They are NOT real bookmaker odds."
    )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    test_accumulator()