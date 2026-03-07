"""Tests for the harness modules: metrics, report, registry, sweep_table."""

import json
from harness.metrics import TxMetrics, ExperimentResult, ComparisonResult


# ── TxMetrics ───────────────────────────────────────────────────────────

def test_txmetrics_feerate():
    m = TxMetrics(label="test", vsize=200, fee_sats=1000)
    assert m.feerate_sat_vb() == 5.0


def test_txmetrics_feerate_zero_vsize():
    m = TxMetrics(label="test", vsize=0, fee_sats=1000)
    assert m.feerate_sat_vb() == 0.0


def test_txmetrics_to_dict():
    m = TxMetrics(label="test", txid="aa" * 32, vsize=200, weight=800, fee_sats=1000)
    d = m.to_dict()
    assert d["label"] == "test"
    assert d["feerate_sat_vb"] == 5.0


# ── ExperimentResult ────────────────────────────────────────────────────

def test_experiment_result_add_tx():
    r = ExperimentResult(experiment="test", covenant="mock")
    r.add_tx(TxMetrics(label="tovault", vsize=150, fee_sats=300))
    r.add_tx(TxMetrics(label="withdraw", vsize=200, fee_sats=500))
    assert r.total_vsize() == 350
    assert r.total_fees() == 800


def test_experiment_result_observe():
    r = ExperimentResult(experiment="test", covenant="mock")
    r.observe("Something happened")
    r.observe("Something else")
    assert len(r.observations) == 2
    assert "Something happened" in r.observations


def test_experiment_result_tx_by_label():
    r = ExperimentResult(experiment="test", covenant="mock")
    r.add_tx(TxMetrics(label="tovault", vsize=150))
    r.add_tx(TxMetrics(label="withdraw", vsize=200))
    assert r.tx_by_label("tovault").vsize == 150
    assert r.tx_by_label("nonexistent") is None


def test_experiment_result_serialization():
    r = ExperimentResult(experiment="test", covenant="mock")
    r.add_tx(TxMetrics(label="tovault", vsize=150, fee_sats=300))
    r.observe("Note 1")
    d = r.to_dict()
    assert d["experiment"] == "test"
    assert len(d["transactions"]) == 1
    # Round-trip through JSON
    s = r.to_json()
    parsed = json.loads(s)
    assert parsed["covenant"] == "mock"


# ── ComparisonResult ────────────────────────────────────────────────────

def test_comparison_result_delta():
    comp = ComparisonResult(experiment="test")
    r1 = ExperimentResult(experiment="test", covenant="ctv")
    r1.add_tx(TxMetrics(label="tovault", vsize=150))
    r2 = ExperimentResult(experiment="test", covenant="ccv")
    r2.add_tx(TxMetrics(label="tovault", vsize=200))
    r3 = ExperimentResult(experiment="test", covenant="opvault")
    r3.add_tx(TxMetrics(label="tovault", vsize=180))
    comp.add(r1)
    comp.add(r2)
    comp.add(r3)

    delta = comp.delta("vsize", "tovault")
    assert delta["min"] == 150
    assert delta["max"] == 200
    assert delta["range"] == 50


def test_comparison_result_serialization():
    comp = ComparisonResult(experiment="test")
    r1 = ExperimentResult(experiment="test", covenant="ctv")
    comp.add(r1)
    d = comp.to_dict()
    assert "ctv" in d["results"]
    s = comp.to_json()
    parsed = json.loads(s)
    assert parsed["experiment"] == "test"
