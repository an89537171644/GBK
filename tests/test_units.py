from sp63_core.units import MPa_to_N_per_mm2, cm2_to_mm2, kN_to_N, kNm_to_Nmm, mm2_to_cm2


def test_kN_to_N():
    assert kN_to_N(1) == 1000


def test_kNm_to_Nmm():
    assert kNm_to_Nmm(1) == 1_000_000


def test_cm2_to_mm2():
    assert cm2_to_mm2(1) == 100


def test_mm2_to_cm2():
    assert mm2_to_cm2(100) == 1


def test_MPa_to_N_per_mm2():
    assert MPa_to_N_per_mm2(25) == 25


def test_unit_conversions_preserve_sign_for_signed_inputs():
    assert kN_to_N(-2) == -2000
    assert kNm_to_Nmm(-3) == -3_000_000
    assert cm2_to_mm2(-4) == -400
    assert mm2_to_cm2(-500) == -5
