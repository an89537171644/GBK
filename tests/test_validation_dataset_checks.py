from sp63_core.dataset import generate_dataset_cases, split_dataset_cases
from sp63_core.validation import validate_dataset_cases


def test_validate_dataset_cases_passes_generated_group_split_dataset():
    cases = generate_dataset_cases(limit=20, load_duration="short")
    split = split_dataset_cases(cases, group_by="group_key")

    result = validate_dataset_cases(cases, split)

    assert result.status == "pass"
    assert result.total_rows == 20
    assert result.unsafe_rows_count == 0
    assert result.geometry_stirrup_mismatch_count == 0
    assert result.duplicate_case_id_count == 0
    assert result.group_leakage_count == 0
    assert result.warnings == ()
