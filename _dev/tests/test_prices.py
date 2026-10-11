import pytest

from _harness.awslib import prices


def test_sections():
    assert prices.section("data_transfer")["inter_az_per_gb_each_way"] == 0.01
    assert prices.load()["meta"]["region"] == "us-east-1"


def test_tiers_and_tiered_cost():
    tiers = prices.tiers("s3_standard_tiers")
    assert tiers == [(51200, 0.023), (512000, 0.022), (None, 0.021)]
    assert prices.tiered_cost(1000, tiers) == pytest.approx(23.0)
    assert prices.tiered_cost(60000, tiers) == pytest.approx(51200 * 0.023 + 8800 * 0.022)
    assert prices.tiered_cost(600000, tiers) == pytest.approx(51200 * 0.023 + 460800 * 0.022 + 88000 * 0.021)
    assert prices.tiered_cost(0, tiers) == 0


def test_unknown_section():
    with pytest.raises(KeyError, match="no_such"):
        prices.section("no_such")
