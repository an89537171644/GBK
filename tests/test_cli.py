from sp63_core.cli import main


def test_cli_main_outputs_mvp_summary(capsys):
    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "sp63-core 0.1.0" in captured.out
    assert "MVP status" in captured.out
    assert "Effective depth h0: 452.00 mm" in captured.out
    assert "Bending check" in captured.out
    assert "status: pass" in captured.out


def test_cli_main_accepts_custom_section(capsys):
    exit_code = main(["--b", "250", "--h", "450", "--cover", "25"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Section: b=250 mm, h=450 mm" in captured.out
    assert "Effective depth h0: 407.00 mm" in captured.out


def test_cli_main_accepts_golden_h0_override(capsys):
    exit_code = main(["--h0-override", "450"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Effective depth h0: 450.00 mm" in captured.out
    assert "Mult: 165170619.03 N*mm" in captured.out
