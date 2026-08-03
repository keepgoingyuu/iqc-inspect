import pytest

from app.inspections.state_machine import TransitionError, ensure_editable, transition
from app.models import InspectionSheet, ModelInspection, Photo, Sample


def make_sheet(status: str = "draft") -> InspectionSheet:
    return InspectionSheet(container_no="TEST123", created_by=1, status=status)


def make_model(
    sheet: InspectionSheet,
    result: str,
    confirmed_seqs: list[int],
    *,
    with_marking_photo: bool = True,
    marking_confirmed: bool = True,
) -> ModelInspection:
    mi = ModelInspection(
        product_name="測試型號", result=result, spec_template_id=1,
        marking_confirmed=marking_confirmed,
    )
    mi.samples = [Sample(seq=seq, confirmed=True) for seq in confirmed_seqs]
    if with_marking_photo and mi.samples:
        mi.samples[0].photos = [Photo(kind="marking", filename="m.jpg")]
    sheet.model_inspections.append(mi)
    return mi


def test_normal_flow_pass():
    sheet = make_sheet()
    make_model(sheet, "pass", [1])
    transition(sheet, "data_entered")
    transition(sheet, "judged")
    transition(sheet, "pending_review")
    transition(sheet, "approved")
    transition(sheet, "archived")
    assert sheet.status == "archived"


def test_illegal_jump_rejected():
    sheet = make_sheet()
    with pytest.raises(TransitionError):
        transition(sheet, "approved")  # draft 直接跳簽核


def test_fail_without_second_sample_blocked():
    """核心防呆:判不合格、只有一件樣品 → 不得送審。"""
    sheet = make_sheet("judged")
    make_model(sheet, "fail", [1])
    with pytest.raises(TransitionError, match="二次拆檢"):
        transition(sheet, "pending_review")


def test_fail_with_second_sample_allowed():
    sheet = make_sheet("judged")
    make_model(sheet, "fail", [1, 2])
    transition(sheet, "pending_review")
    assert sheet.status == "pending_review"


def test_second_sample_unconfirmed_blocked():
    sheet = make_sheet("judged")
    mi = make_model(sheet, "fail", [1])
    mi.samples.append(Sample(seq=2, confirmed=False))
    with pytest.raises(TransitionError, match="二次拆檢"):
        transition(sheet, "pending_review")


def test_no_marking_photo_blocks_review():
    """送審關卡:沒有主機板標示照 → 不得送審(主管無從比對)。"""
    sheet = make_sheet("judged")
    make_model(sheet, "pass", [1], with_marking_photo=False)
    with pytest.raises(TransitionError, match="主機板標示照"):
        transition(sheet, "pending_review")


def test_unconfirmed_marking_blocks_approve():
    """簽核關卡:主管未逐型號確認標示一致 → 不得簽核。"""
    sheet = make_sheet("pending_review")
    make_model(sheet, "pass", [1], marking_confirmed=False)
    with pytest.raises(TransitionError, match="標示"):
        transition(sheet, "approved")


def test_confirmed_marking_allows_approve():
    sheet = make_sheet("pending_review")
    make_model(sheet, "pass", [1], marking_confirmed=True)
    transition(sheet, "approved")
    assert sheet.status == "approved"


def test_approved_sheet_locked():
    sheet = make_sheet("approved")
    with pytest.raises(TransitionError, match="鎖定"):
        ensure_editable(sheet)


def test_reject_path():
    sheet = make_sheet("pending_review")
    transition(sheet, "rejected")
    transition(sheet, "defect_ticket")
    transition(sheet, "archived")
    assert sheet.status == "archived"
