from app.inspections.judge import evaluate_item, judge_model
from app.models import ModelInspection, Sample, SpecTemplate


def test_range_by_min_max():
    rule = {"type": "range", "min": 1350, "max": 1500}
    assert evaluate_item(rule, 1455.289)["verdict"] == "pass"
    # 紙本表單上被黃螢光筆標記的實際異常值
    assert evaluate_item(rule, 1821.457)["verdict"] == "fail"


def test_range_by_percent_of_nominal():
    # 功率:標稱 15W,下限≥90%(13.5)/上限≤110%(16.5)
    rule = {"type": "range", "nominal": 15, "min_pct": 90, "max_pct": 110}
    assert evaluate_item(rule, 13.6)["verdict"] == "pass"
    assert evaluate_item(rule, 13.4)["verdict"] == "fail"
    assert evaluate_item(rule, 16.6)["verdict"] == "fail"


def test_range_by_tolerance_percent():
    rule = {"type": "range", "nominal": 258, "tol_pct": 5}
    assert evaluate_item(rule, 258.0)["verdict"] == "pass"
    assert evaluate_item(rule, 245.0)["verdict"] == "fail"  # 下限 245.1


def test_min_and_check_rules():
    assert evaluate_item({"type": "min", "min": 0.4}, 0.593)["verdict"] == "pass"
    assert evaluate_item({"type": "min", "min": 80}, 79.9)["verdict"] == "fail"
    assert evaluate_item({"type": "check"}, "OK")["verdict"] == "pass"
    assert evaluate_item({"type": "check"}, "NG")["verdict"] == "fail"


def test_missing_value():
    assert evaluate_item({"type": "min", "min": 1}, None)["verdict"] == "missing"


def make_model_with_spec() -> ModelInspection:
    spec = SpecTemplate(
        name="t", product_category="t", version=1,
        items=[
            {"key": "efficacy", "label": "光效", "source_type": "pdf",
             "rule": {"type": "range", "min": 90, "max": 100}},
            {"key": "visual", "label": "目視", "source_type": "check",
             "rule": {"type": "check"}},
        ],
    )
    mi = ModelInspection(product_name="測試", spec_template_id=1, item_values={}, judgement={})
    mi.spec = spec
    return mi


def test_judge_model_fail_and_highlight():
    """光效 133.0 超標(紙本上的實際異常)→ fail + 高亮。"""
    mi = make_model_with_spec()
    mi.item_values = {"visual": "OK"}
    mi.samples = [Sample(seq=1, photometric={"efficacy": 133.0}, confirmed=True)]
    judge_model(mi)
    assert mi.result == "fail"
    assert any(h["item"] == "efficacy" for h in mi.judgement["highlights"])


def test_judge_model_pass():
    mi = make_model_with_spec()
    mi.item_values = {"visual": "OK"}
    mi.samples = [Sample(seq=1, photometric={"efficacy": 95.0}, confirmed=True)]
    judge_model(mi)
    assert mi.result == "pass"


def test_judge_model_pending_when_missing():
    mi = make_model_with_spec()
    mi.samples = [Sample(seq=1, photometric={"efficacy": 95.0}, confirmed=True)]
    judge_model(mi)  # visual 未勾選
    assert mi.result == "pending"


def test_param_referenced_rules():
    """兩層設計核心:同一條公式,不同型號參數算出不同範圍。"""
    rule = {"type": "range", "param": "nominal_power", "min_pct": 90, "max_pct": 110}
    p15 = {"nominal_power": 15}
    p24 = {"nominal_power": 24}
    assert evaluate_item(rule, 13.6, p15)["verdict"] == "pass"   # 13.5~16.5
    assert evaluate_item(rule, 13.6, p24)["verdict"] == "fail"   # 21.6~26.4
    assert evaluate_item(rule, 22.0, p24)["verdict"] == "pass"

    flux_rule = {"type": "range", "param_min": "flux_min", "param_max": "flux_max"}
    assert evaluate_item(flux_rule, 1455.0, {"flux_min": 1350, "flux_max": 1500})["verdict"] == "pass"
    assert evaluate_item(flux_rule, 1821.457, {"flux_min": 1350, "flux_max": 1500})["verdict"] == "fail"
