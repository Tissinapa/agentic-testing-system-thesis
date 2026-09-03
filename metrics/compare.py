import json
from pathlib import Path

INPUT_PRICE_PER_M = 3.00   # USD per million input tokens
OUTPUT_PRICE_PER_M = 15.00  # USD per million output tokens
BLENDED_PRICE_PER_M = 6.60  # 70% input / 30% output blended estimate
USD_TO_EUR = 0.8631 # 2.9.2026

RESULTS_FILE = Path("results/metrics_summary.json")



def load_results() -> list[dict]:
    with open(RESULTS_FILE) as f:
        data = json.load(f)
    return data["results"]


def print_comparison_table(results: list[dict]):
    print("\n" + "="*90)
    print("FRAMEWORK COMPARISON TABLE")
    print("="*90)
    print(f"{'Framework':<20} {'App':<8} {'Mode':<8} {'Total':<8} {'Passed':<8} {'Bugs':<8} {'FP':<6} {'Tokens':<10}")
    print("-"*90)

    for r in results:
        print(
            f"{r['framework']:<20} "
            f"{r['app']:<8} "
            f"{r['mode']:<8} "
            f"{r.get('tests_executed', 0):<8} "
            f"{r.get('tests_passed', 0):<8} "
            f"{r['bugs_detected']:<8} "
            f"{r['false_positives']:<6} "
            f"{r['token_usage']:<10}"
        )


def print_bug_detection_summary(results: list[dict]):
    print("\n" + "="*90)
    print("BUG DETECTION SUMMARY BY APP")
    print("="*90)

    all_apps = sorted(set(r["app"] for r in results))
    
    for app in all_apps:
        print(f"\n{app.upper()} APP:")
        print(f"  {'Framework':<25} {'Mode':<10} {'Bugs detected':<15} {'False positives'}")
        print(f"  {'-'*65}")
        app_results = [r for r in results if r["app"] == app]
        for r in app_results:
            print(
                f"  {r['framework']:<25} "
                f"{r['mode']:<10} "
                f"{r['bugs_detected']:<15} "
                f"{r['false_positives']}"
            )


def print_efficiency_summary(results: list[dict]):
    print("\n" + "="*90)
    print("AGENT EFFICIENCY BY MODE")
    print("="*90)

    agent_results = [r for r in results if r["framework"] == "AI Agent"]
    print(f"{'App':<10} {'Mode':<10} {'Bugs':<8} {'Tokens':<12} {'Bugs/1k tokens'}")
    print("-"*60)
    for r in agent_results:
        if r["token_usage"] > 0:
            efficiency = r["bugs_detected"] / (r["token_usage"] / 1000)
            print(
                f"{r['app']:<10} "
                f"{r['mode']:<10} "
                f"{r['bugs_detected']:<8} "
                f"{r['token_usage']:<12} "
                f"{efficiency:.2f}"
            )

def calculate_cost_usd(tokens: int) -> float:
    return (tokens / 1_000_000) * BLENDED_PRICE_PER_M

def calculate_cost_eur(tokens: int) -> float:
    return calculate_cost_usd(tokens) * USD_TO_EUR

def print_cost_summary(results: list[dict]):
    print("\n" + "="*95)
    print("AGENT COST ANALYSIS (Claude Sonnet 4-6 @ $3/$15 per 1M tokens)")
    print(f"Blended: $6.60/1M tokens | Rate: 1 USD = {USD_TO_EUR} EUR (2 Sep 2026)")
    print("="*95)
    print(f"{'App':<10} {'Mode':<10} {'Tokens':<12} {'USD':<12} {'EUR':<12} {'Bugs':<8} {'€/Bug'}")
    print("-"*95)

    agent_results = [r for r in results if r["framework"] == "AI Agent"]
    for r in sorted(agent_results, key=lambda x: (x["app"], x["mode"])):
        tokens = r["token_usage"]
        cost_usd = calculate_cost_usd(tokens)
        cost_eur = calculate_cost_eur(tokens)
        bugs = r["bugs_detected"]
        cost_per_bug_eur = cost_eur / bugs if bugs > 0 else 0
        print(
            f"{r['app']:<10} "
            f"{r['mode']:<10} "
            f"{tokens:<12} "
            f"${cost_usd:<11.4f} "
            f"€{cost_eur:<11.4f} "
            f"{bugs:<8} "
            f"€{cost_per_bug_eur:.4f}"
        )

    # Total cost summary
    total_tokens = sum(r["token_usage"] for r in agent_results)
    total_usd = calculate_cost_usd(total_tokens)
    total_eur = calculate_cost_eur(total_tokens)
    print("-"*95)
    print(f"{'TOTAL':<10} {'all':<10} {total_tokens:<12} ${total_usd:<11.4f} €{total_eur:<11.4f}")

    
    print("="*95)


if __name__ == "__main__":
    results = load_results()
    print_comparison_table(results)
    print_bug_detection_summary(results)
    print_efficiency_summary(results)
    print_cost_summary(results) 
    