from app.ocr import compare_marking, normalize


def test_normalize_strips_format_noise():
    assert normalize("5205-G4-0150-3VC0101") == "5205G40150" + "3VC0101"
    assert normalize(" 5205 g4 0150 3vc0101 ") == normalize("5205-G4-0150-3VC0101")


def test_compare_exact_and_contains():
    expected = "5205-G4-0150-3VC0101"
    assert compare_marking(expected, "5205-G4-0150-3VC0101")
    # 模型多讀到其他版面文字仍算一致
    assert compare_marking(expected, "Model: 5205-G4-0150-3VC0101 REV.A")
    # 一字之差(G4 vs B4)必須抓出來
    assert not compare_marking(expected, "5205-B4-0150-3VC0101")


def test_compare_empty_inputs():
    assert not compare_marking("", "anything")
    assert not compare_marking("expected", "")
