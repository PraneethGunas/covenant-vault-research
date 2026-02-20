#!/usr/bin/env python3
"""Standalone runner for the fee sensitivity analysis.

This script runs the analytical fee sensitivity experiment without
requiring Bitcoin nodes.  It produces:
  - results/<timestamp>/fee_sensitivity/analytical.json
  - results/<timestamp>/fee_sensitivity/analysis.md
  - results/<timestamp>/fee_sensitivity/analysis_chart.html

Usage:
    uv run run_fee_analysis.py
"""

import sys
import json
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.metrics import ExperimentResult
from experiments.exp_fee_sensitivity import (
    run as run_fee_sensitivity,
    FEE_ENVIRONMENTS,
    VAULT_AMOUNT_SATS,
    CTV_LIFECYCLE_TOTAL, CCV_LIFECYCLE_TOTAL,
    CTV_TOVAULT_VSIZE, CTV_UNVAULT_VSIZE, CTV_WITHDRAW_VSIZE, CTV_TOCOLD_VSIZE,
    CCV_TOVAULT_VSIZE, CCV_TRIGGER_VSIZE, CCV_WITHDRAW_VSIZE, CCV_RECOVER_VSIZE,
    CCV_TRIGGER_REVAULT_VSIZE,
    FEE_PIN_TOTAL_CHAIN_VSIZE, FEE_PIN_CHAIN_COUNT,
    WT_TRIGGER_VSIZE, WT_RECOVER_VSIZE,
    WT_BATCHED_RECOVERY_OVERHEAD, WT_BATCHED_RECOVERY_PER_INPUT,
)


def generate_markdown_report(result: ExperimentResult) -> str:
    """Generate a polished markdown report from the experiment result."""
    lines = []
    lines.append("# Fee Environment Sensitivity Analysis")
    lines.append("")
    lines.append(f"Generated: {result.timestamp}")
    lines.append(f"Vault amount: {VAULT_AMOUNT_SATS:,} sats (~{VAULT_AMOUNT_SATS / 1e8:.2f} BTC)")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("This analysis uses **structural vsize measurements** — deterministic values")
    lines.append("from each vault design's script and witness structure — and projects them")
    lines.append("into real-world economic costs at historically observed Bitcoin fee rates.")
    lines.append("vsize is the primary metric; fees are computed as `vsize × fee_rate` where")
    lines.append("`fee_rate` is an exogenous parameter.")
    lines.append("")

    lines.append("### Historical Fee Rate Context")
    lines.append("")
    lines.append("| Fee Rate (sat/vB) | Historical Period |")
    lines.append("|------------------:|:------------------|")
    for rate, period in FEE_ENVIRONMENTS:
        lines.append(f"| {rate:>17} | {period} |")
    lines.append("")

    # Section 1: Lifecycle
    lines.append("## 1. Vault Lifecycle Costs")
    lines.append("")
    lines.append(f"| Component | CTV (vB) | CCV (vB) |")
    lines.append(f"|:----------|:--------:|:--------:|")
    lines.append(f"| Deposit (tovault) | {CTV_TOVAULT_VSIZE} | {CCV_TOVAULT_VSIZE} |")
    lines.append(f"| Trigger (unvault) | {CTV_UNVAULT_VSIZE} | {CCV_TRIGGER_VSIZE} |")
    lines.append(f"| Withdrawal | {CTV_WITHDRAW_VSIZE} | {CCV_WITHDRAW_VSIZE} |")
    lines.append(f"| **Total lifecycle** | **{CTV_LIFECYCLE_TOTAL}** | **{CCV_LIFECYCLE_TOTAL}** |")
    savings = CTV_LIFECYCLE_TOTAL - CCV_LIFECYCLE_TOTAL
    lines.append(f"| Difference | | CCV saves {savings} vB ({savings/CTV_LIFECYCLE_TOTAL*100:.1f}%) |")
    lines.append("")

    lines.append("### Lifecycle cost by fee environment")
    lines.append("")
    lines.append("| Fee Rate | Period | CTV Cost | CCV Cost | Savings | % of Vault |")
    lines.append("|:--------:|:-------|:--------:|:--------:|:-------:|:----------:|")
    for rate, period in FEE_ENVIRONMENTS:
        ctv = CTV_LIFECYCLE_TOTAL * rate
        ccv = CCV_LIFECYCLE_TOTAL * rate
        sv = ctv - ccv
        pct = ctv / VAULT_AMOUNT_SATS * 100
        lines.append(f"| {rate} s/vB | {period} | {ctv:,} | {ccv:,} | {sv:,} | {pct:.3f}% |")
    lines.append("")

    # Section 2: Fee pinning
    lines.append("## 2. Fee Pinning Attack (CTV-Specific)")
    lines.append("")
    lines.append(f"Attack structure: {FEE_PIN_CHAIN_COUNT - 1} descendant txs × 110 vB = **{FEE_PIN_TOTAL_CHAIN_VSIZE} vB**")
    lines.append("")
    lines.append("| Fee Rate | Attack Fees | Dust Capital | Total Deployed | % of Vault | Verdict |")
    lines.append("|:--------:|:----------:|:------------:|:--------------:|:----------:|:-------:|")
    for rate, period in FEE_ENVIRONMENTS:
        fees = FEE_PIN_TOTAL_CHAIN_VSIZE * rate
        dust = 546 * (FEE_PIN_CHAIN_COUNT - 1)
        total = fees + dust
        pct = total / VAULT_AMOUNT_SATS * 100
        verdict = "ALWAYS rational" if pct < 10 else "LIKELY" if pct < 50 else "MARGINAL"
        lines.append(f"| {rate} s/vB | {fees:,} | {dust:,} | {total:,} | {pct:.4f}% | {verdict} |")
    lines.append("")
    lines.append("> **Key finding:** Fee pinning is ALWAYS rational as a component of hot-key theft.")
    lines.append("> The attack costs <0.5% of vault value at any observed historical fee rate.")
    lines.append("> High-fee environments make pinning MORE dangerous (harder to escape), not less.")
    lines.append("")

    # Section 3: Recovery griefing
    lines.append("## 3. Recovery Griefing")
    lines.append("")
    lines.append("### CCV: Keyless Recovery Griefing")
    lines.append("")
    asymmetry = CCV_TRIGGER_VSIZE / CCV_RECOVER_VSIZE
    lines.append(f"- Attacker cost/round: **{CCV_RECOVER_VSIZE} vB** (no key needed)")
    lines.append(f"- Defender cost/round: **{CCV_TRIGGER_VSIZE} vB** (re-trigger)")
    lines.append(f"- Asymmetry: **{asymmetry:.2f}x** (defender pays more)")
    lines.append("")
    lines.append("| Fee Rate | Atk/Round | Def/Round | 10 Rounds (Atk) | 10 Rounds (Def) | Rounds to 1% | Rounds to 10% |")
    lines.append("|:--------:|:---------:|:---------:|:---------------:|:---------------:|:------------:|:-------------:|")
    for rate, period in FEE_ENVIRONMENTS:
        ar = CCV_RECOVER_VSIZE * rate
        dr = CCV_TRIGGER_VSIZE * rate
        r1 = int(VAULT_AMOUNT_SATS * 0.01 / dr) if dr > 0 else 999999
        r10 = int(VAULT_AMOUNT_SATS * 0.10 / dr) if dr > 0 else 999999
        lines.append(f"| {rate} s/vB | {ar:,} | {dr:,} | {ar*10:,} | {dr*10:,} | {r1:,} | {r10:,} |")
    lines.append("")

    lines.append("### CTV: Hot-Key Sweep Griefing")
    lines.append("")
    ctv_asym = CTV_UNVAULT_VSIZE / CTV_TOCOLD_VSIZE
    lines.append(f"- Attacker cost/round: **{CTV_UNVAULT_VSIZE} vB** (needs hot key)")
    lines.append(f"- Defender cost/round: **{CTV_TOCOLD_VSIZE} vB** (cold sweep)")
    lines.append(f"- Asymmetry: **{ctv_asym:.2f}x** ({'attacker' if ctv_asym > 1 else 'defender'} pays more)")
    lines.append("")
    lines.append("> CCV griefing has a wider attack surface (anyone can grief) — liveness-only, but indefinite delays may be operationally severe.")
    lines.append("> CTV griefing has a narrower surface (needs hot key) but can escalate to fund theft via fee pinning under current relay policy (mitigable by TRUC/v3).")
    lines.append("")

    # Section 4: Watchtower exhaustion
    lines.append("## 4. Watchtower Exhaustion (CCV-Specific)")
    lines.append("")
    lines.append(f"- Trigger cost: **{WT_TRIGGER_VSIZE} vB** per split (attacker)")
    lines.append(f"- Recovery cost: **{WT_RECOVER_VSIZE} vB** per recovery (watchtower)")
    lines.append(f"- Batched recovery: ~{WT_BATCHED_RECOVERY_OVERHEAD} + {WT_BATCHED_RECOVERY_PER_INPUT} × N vB")
    lines.append("")

    lines.append("### Individual recovery analysis")
    lines.append("")
    lines.append("| Fee Rate | Trigger Cost | Recover Cost | Splits to Exhaust | Attacker Spend | Net Gain |")
    lines.append("|:--------:|:-----------:|:------------:|:-----------------:|:--------------:|:--------:|")
    for rate, period in FEE_ENVIRONMENTS:
        tc = WT_TRIGGER_VSIZE * rate
        rc = WT_RECOVER_VSIZE * rate
        splits = VAULT_AMOUNT_SATS // rc if rc > 0 else 999999
        atk_spend = splits * tc
        net = VAULT_AMOUNT_SATS - atk_spend
        lines.append(f"| {rate} s/vB | {tc:,} | {rc:,} | {splits:,} | {atk_spend:,} | {net:,} |")
    lines.append("")

    lines.append("### Batched recovery defense")
    lines.append("")
    lines.append("| Batch Size | Total vB | Per-Input vB | Savings vs Individual |")
    lines.append("|:----------:|:--------:|:------------:|:---------------------:|")
    for n in [1, 10, 25, 50, 100]:
        bv = WT_BATCHED_RECOVERY_OVERHEAD + WT_BATCHED_RECOVERY_PER_INPUT * n
        pi = bv / n
        ind = WT_RECOVER_VSIZE * n
        sv = (1 - bv / ind) * 100 if ind else 0
        lines.append(f"| {n} | {bv} | {pi:.1f} | {sv:.1f}% |")
    lines.append("")

    lines.append("> **Key finding:** Watchtower exhaustion has a **fee-dependent crossover**.")
    lines.append("> At 1 sat/vB, ~410k splits needed (infeasible). At 300 sat/vB, ~1,366 splits")
    lines.append("> (feasible over hours). High fees make this attack MORE viable.")
    lines.append("> Batched recovery (100 inputs) saves ~45%, extending watchtower budget significantly.")
    lines.append("")

    # Section 5: Synthesis
    lines.append("## 5. Synthesis: Attack Severity by Fee Environment")
    lines.append("")
    lines.append("| Attack | Low (1 s/vB) | Medium (50) | High (300) | Stress (500) | Consequence |")
    lines.append("|:-------|:------------:|:-----------:|:----------:|:------------:|:------------|")
    lines.append("| Fee pinning (CTV) | CRITICAL | CRITICAL | CRITICAL | CRITICAL | Fund loss (with hot key) |")
    lines.append("| Recovery griefing (CCV) | Low | Low | Moderate | Moderate | Liveness denial only |")
    lines.append("| WT exhaustion (CCV) | Infeasible | Low | Moderate | Significant | Partial fund loss |")
    lines.append("| Hot-key griefing (CTV) | Low | Low | Moderate | Moderate | Liveness denial only |")
    lines.append("")

    lines.append("### Key Takeaways")
    lines.append("")
    lines.append("1. **Fee pinning is fee-invariant in severity** — always <0.5% of vault value")
    lines.append("2. **Recovery griefing scales linearly** — high fees deter but don't eliminate")
    lines.append("3. **Watchtower exhaustion has a fee-dependent crossover** — more viable at high fees")
    lines.append("4. **CTV and CCV trade different failure modes** — CTV risks fund loss (mitigable by TRUC/v3); CCV risks liveness denial and partial fund loss via watchtower exhaustion (mitigable by batched recovery). Relative severity is deployment-dependent")
    lines.append("5. **CTV and CCV have complementary vulnerability profiles** — neither is strictly better across all fee environments")
    lines.append("")

    return "\n".join(lines)


def generate_html_chart() -> str:
    """Generate an interactive HTML chart showing attack economics across fee rates."""
    rates = [r for r, _ in FEE_ENVIRONMENTS]

    # Data series
    fee_pin_cost = [FEE_PIN_TOTAL_CHAIN_VSIZE * r for r in rates]
    fee_pin_pct = [c / VAULT_AMOUNT_SATS * 100 for c in fee_pin_cost]

    grief_atk_10 = [CCV_RECOVER_VSIZE * r * 10 for r in rates]
    grief_atk_10_pct = [c / VAULT_AMOUNT_SATS * 100 for c in grief_atk_10]

    wt_splits = [VAULT_AMOUNT_SATS // (WT_RECOVER_VSIZE * r) if WT_RECOVER_VSIZE * r > 0 else 999999 for r in rates]
    wt_atk_cost = [wt_splits[i] * WT_TRIGGER_VSIZE * rates[i] for i in range(len(rates))]
    wt_atk_pct = [c / VAULT_AMOUNT_SATS * 100 for c in wt_atk_cost]

    lifecycle_ctv = [CTV_LIFECYCLE_TOTAL * r for r in rates]
    lifecycle_ccv = [CCV_LIFECYCLE_TOTAL * r for r in rates]
    lifecycle_ctv_pct = [c / VAULT_AMOUNT_SATS * 100 for c in lifecycle_ctv]
    lifecycle_ccv_pct = [c / VAULT_AMOUNT_SATS * 100 for c in lifecycle_ccv]

    labels = [f"{r} sat/vB" for r in rates]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fee Environment Sensitivity Analysis</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    max-width: 1200px; margin: 40px auto; padding: 0 20px;
    background: #fafafa; color: #1a1a2e;
  }}
  h1 {{ text-align: center; margin-bottom: 5px; }}
  .subtitle {{ text-align: center; color: #666; margin-bottom: 30px; font-size: 14px; }}
  .chart-container {{
    background: white; border-radius: 12px; padding: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 30px;
  }}
  .chart-container h2 {{ margin-top: 0; font-size: 18px; color: #333; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
  @media (max-width: 800px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  .insight {{
    background: #e8f4fd; border-left: 4px solid #2196F3;
    padding: 12px 16px; margin: 16px 0; border-radius: 0 8px 8px 0;
    font-size: 14px;
  }}
  .warning {{
    background: #fff3e0; border-left: 4px solid #ff9800;
    padding: 12px 16px; margin: 16px 0; border-radius: 0 8px 8px 0;
    font-size: 14px;
  }}
  table {{
    width: 100%; border-collapse: collapse; font-size: 13px;
    margin: 16px 0;
  }}
  th, td {{ padding: 8px 12px; text-align: right; border-bottom: 1px solid #eee; }}
  th {{ background: #f5f5f5; font-weight: 600; }}
  td:first-child, th:first-child {{ text-align: left; }}
  .severity-critical {{ color: #d32f2f; font-weight: bold; }}
  .severity-moderate {{ color: #f57c00; }}
  .severity-low {{ color: #388e3c; }}
  .severity-infeasible {{ color: #9e9e9e; }}
</style>
</head>
<body>
<h1>Fee Environment Sensitivity Analysis</h1>
<p class="subtitle">Bitcoin Covenant Vault Comparison: CTV (BIP-119) vs CCV (BIP-443) | Vault: {VAULT_AMOUNT_SATS:,} sats (~{VAULT_AMOUNT_SATS/1e8:.2f} BTC)</p>

<div class="grid">
  <div class="chart-container">
    <h2>Attack Cost as % of Vault Value</h2>
    <canvas id="attackCostChart"></canvas>
    <div class="insight">
      Fee pinning costs &lt;0.5% of vault at ALL fee rates.
      Watchtower exhaustion attacker cost exceeds 100% at high fees
      (net-negative for attacker unless watchtower abandons UTXOs).
    </div>
  </div>

  <div class="chart-container">
    <h2>Lifecycle Cost Comparison (sats)</h2>
    <canvas id="lifecycleChart"></canvas>
    <div class="insight">
      CCV saves {CTV_LIFECYCLE_TOTAL - CCV_LIFECYCLE_TOTAL} vB per lifecycle
      ({(CTV_LIFECYCLE_TOTAL - CCV_LIFECYCLE_TOTAL)/CTV_LIFECYCLE_TOTAL*100:.1f}% reduction).
      At 500 sat/vB, this saves {(CTV_LIFECYCLE_TOTAL - CCV_LIFECYCLE_TOTAL) * 500:,} sats.
    </div>
  </div>
</div>

<div class="chart-container">
  <h2>Watchtower Exhaustion: Splits Required vs Fee Rate</h2>
  <canvas id="wtSplitsChart"></canvas>
  <div class="warning">
    At 300+ sat/vB, watchtower exhaustion requires &lt;2,000 splits — feasible for a
    sustained attacker.  Batched recovery is the primary defense.
  </div>
</div>

<div class="chart-container">
  <h2>Attack Severity Matrix</h2>
  <table>
    <tr>
      <th>Attack Vector</th>
      <th>1 sat/vB</th><th>10 sat/vB</th><th>50 sat/vB</th>
      <th>100 sat/vB</th><th>300 sat/vB</th><th>500 sat/vB</th>
      <th>Consequence</th>
    </tr>
    <tr>
      <td>Fee pinning (CTV)</td>
      <td class="severity-critical">CRITICAL</td>
      <td class="severity-critical">CRITICAL</td>
      <td class="severity-critical">CRITICAL</td>
      <td class="severity-critical">CRITICAL</td>
      <td class="severity-critical">CRITICAL</td>
      <td class="severity-critical">CRITICAL</td>
      <td>Fund loss (w/ hot key)</td>
    </tr>
    <tr>
      <td>Recovery griefing (CCV)</td>
      <td class="severity-low">LOW</td>
      <td class="severity-low">LOW</td>
      <td class="severity-low">LOW</td>
      <td class="severity-moderate">MODERATE</td>
      <td class="severity-moderate">MODERATE</td>
      <td class="severity-moderate">MODERATE</td>
      <td>Liveness denial</td>
    </tr>
    <tr>
      <td>WT exhaustion (CCV)</td>
      <td class="severity-infeasible">INFEASIBLE</td>
      <td class="severity-low">LOW</td>
      <td class="severity-low">LOW</td>
      <td class="severity-moderate">MODERATE</td>
      <td class="severity-moderate">MODERATE</td>
      <td class="severity-critical">SIGNIFICANT</td>
      <td>Partial fund loss</td>
    </tr>
    <tr>
      <td>Hot-key griefing (CTV)</td>
      <td class="severity-low">LOW</td>
      <td class="severity-low">LOW</td>
      <td class="severity-low">LOW</td>
      <td class="severity-moderate">MODERATE</td>
      <td class="severity-moderate">MODERATE</td>
      <td class="severity-moderate">MODERATE</td>
      <td>Liveness denial</td>
    </tr>
  </table>
</div>

<script>
const labels = {json.dumps(labels)};

// Chart 1: Attack cost as % of vault
new Chart(document.getElementById('attackCostChart'), {{
  type: 'line',
  data: {{
    labels: labels,
    datasets: [
      {{
        label: 'Fee pinning (CTV) — chain cost',
        data: {json.dumps([round(x, 4) for x in fee_pin_pct])},
        borderColor: '#d32f2f',
        backgroundColor: 'rgba(211, 47, 47, 0.1)',
        fill: false,
        tension: 0.3,
        pointRadius: 5,
      }},
      {{
        label: 'Recovery griefing (CCV) — 10 rounds',
        data: {json.dumps([round(x, 4) for x in grief_atk_10_pct])},
        borderColor: '#f57c00',
        backgroundColor: 'rgba(245, 124, 0, 0.1)',
        fill: false,
        tension: 0.3,
        pointRadius: 5,
      }},
      {{
        label: 'WT exhaustion (CCV) — attacker total',
        data: {json.dumps([round(x, 2) for x in wt_atk_pct])},
        borderColor: '#7b1fa2',
        backgroundColor: 'rgba(123, 31, 162, 0.1)',
        fill: false,
        tension: 0.3,
        pointRadius: 5,
        borderDash: [5, 5],
      }},
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ position: 'bottom' }},
      tooltip: {{ callbacks: {{ label: (ctx) => ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(3) + '%' }} }}
    }},
    scales: {{
      y: {{
        title: {{ display: true, text: '% of Vault Value' }},
        type: 'logarithmic',
        min: 0.001,
      }},
      x: {{ title: {{ display: true, text: 'Fee Rate' }} }}
    }}
  }}
}});

// Chart 2: Lifecycle costs
new Chart(document.getElementById('lifecycleChart'), {{
  type: 'bar',
  data: {{
    labels: labels,
    datasets: [
      {{
        label: 'CTV Lifecycle',
        data: {json.dumps(lifecycle_ctv)},
        backgroundColor: 'rgba(33, 150, 243, 0.7)',
        borderColor: '#2196F3',
        borderWidth: 1,
      }},
      {{
        label: 'CCV Lifecycle',
        data: {json.dumps(lifecycle_ccv)},
        backgroundColor: 'rgba(76, 175, 80, 0.7)',
        borderColor: '#4CAF50',
        borderWidth: 1,
      }},
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ position: 'bottom' }},
      tooltip: {{ callbacks: {{ label: (ctx) => ctx.dataset.label + ': ' + ctx.parsed.y.toLocaleString() + ' sats' }} }}
    }},
    scales: {{
      y: {{ title: {{ display: true, text: 'Cost (sats)' }} }},
      x: {{ title: {{ display: true, text: 'Fee Rate' }} }}
    }}
  }}
}});

// Chart 3: WT splits required
new Chart(document.getElementById('wtSplitsChart'), {{
  type: 'line',
  data: {{
    labels: labels,
    datasets: [{{
      label: 'Splits to exhaust watchtower',
      data: {json.dumps(wt_splits)},
      borderColor: '#7b1fa2',
      backgroundColor: 'rgba(123, 31, 162, 0.15)',
      fill: true,
      tension: 0.3,
      pointRadius: 6,
      pointBackgroundColor: '#7b1fa2',
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{ callbacks: {{ label: (ctx) => ctx.parsed.y.toLocaleString() + ' splits needed' }} }}
    }},
    scales: {{
      y: {{
        title: {{ display: true, text: 'Splits Required' }},
        type: 'logarithmic',
      }},
      x: {{ title: {{ display: true, text: 'Fee Rate' }} }}
    }}
  }}
}});
</script>
</body>
</html>"""
    return html


def main():
    print("=" * 60)
    print("Fee Environment Sensitivity Analysis")
    print("=" * 60)

    # Create a mock adapter-like object for interface compatibility
    class AnalyticalAdapter:
        name = "analytical"
        description = "Analytical (no on-chain transactions)"

    result = run_fee_sensitivity(AnalyticalAdapter())

    # Print observations
    for obs in result.observations:
        print(f"  {obs}")

    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_dir = PROJECT_ROOT / "results" / timestamp / "fee_sensitivity"
    results_dir.mkdir(parents=True, exist_ok=True)

    # JSON result
    json_path = results_dir / "analytical.json"
    json_path.write_text(result.to_json())
    print(f"\nJSON result: {json_path}")

    # Markdown report
    md_report = generate_markdown_report(result)
    md_path = results_dir / "analysis.md"
    md_path.write_text(md_report)
    print(f"Markdown report: {md_path}")

    # HTML chart
    html_chart = generate_html_chart()
    html_path = results_dir / "analysis_chart.html"
    html_path.write_text(html_chart)
    print(f"Interactive chart: {html_path}")

    # Also save to the workspace root for easy access
    workspace_md = PROJECT_ROOT / "fee_sensitivity_analysis.md"
    workspace_md.write_text(md_report)
    print(f"\nReport also saved to: {workspace_md}")

    workspace_html = PROJECT_ROOT / "fee_sensitivity_chart.html"
    workspace_html.write_text(html_chart)
    print(f"Chart also saved to: {workspace_html}")

    print(f"\nResults directory: {results_dir}")
    print("Done.")


if __name__ == "__main__":
    main()
