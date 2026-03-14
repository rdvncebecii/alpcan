"""Lung-RADS scoring logic tests."""

import sys
from pathlib import Path

import pytest

# Add ml/ to path so we can import without install
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ml"))

try:
    from evaluation.lung_rads_scoring import (
        NoduleInfo,
        classify_lung_rads,
        classify_overall_lung_rads,
        get_recommendation,
    )
    HAS_ML = True
except (ImportError, ModuleNotFoundError):
    HAS_ML = False

pytestmark = pytest.mark.skipif(not HAS_ML, reason="ML modules not available")


def test_solid_small():
    nodule = NoduleInfo(diameter_mm=4.0, density="solid")
    assert classify_lung_rads(nodule) == "2"


def test_solid_medium():
    nodule = NoduleInfo(diameter_mm=7.0, density="solid")
    assert classify_lung_rads(nodule) == "3"


def test_solid_large():
    nodule = NoduleInfo(diameter_mm=10.0, density="solid")
    assert classify_lung_rads(nodule) == "4A"


def test_solid_very_large():
    nodule = NoduleInfo(diameter_mm=16.0, density="solid")
    assert classify_lung_rads(nodule) == "4B"


def test_solid_growing():
    nodule = NoduleInfo(diameter_mm=7.0, density="solid", is_growing=True)
    assert classify_lung_rads(nodule) == "4A"


def test_solid_new():
    nodule = NoduleInfo(diameter_mm=5.0, density="solid", is_new=True)
    assert classify_lung_rads(nodule) == "4A"


def test_ground_glass_small():
    nodule = NoduleInfo(diameter_mm=15.0, density="ground_glass")
    assert classify_lung_rads(nodule) == "2"


def test_ground_glass_medium():
    nodule = NoduleInfo(diameter_mm=25.0, density="ground_glass")
    assert classify_lung_rads(nodule) == "3"


def test_ground_glass_large():
    nodule = NoduleInfo(diameter_mm=32.0, density="ground_glass")
    assert classify_lung_rads(nodule) == "4A"


def test_part_solid():
    nodule = NoduleInfo(diameter_mm=8.0, density="part_solid", solid_component_mm=4.0)
    assert classify_lung_rads(nodule) == "3"


def test_part_solid_large_component():
    nodule = NoduleInfo(diameter_mm=12.0, density="part_solid", solid_component_mm=9.0)
    assert classify_lung_rads(nodule) == "4B"


def test_perifissural():
    nodule = NoduleInfo(diameter_mm=7.0, density="solid", is_perifissural=True)
    assert classify_lung_rads(nodule) == "2"


def test_no_nodules():
    assert classify_overall_lung_rads([]) == "1"


def test_overall_highest():
    nodules = [
        NoduleInfo(diameter_mm=4.0, density="solid"),      # → 2
        NoduleInfo(diameter_mm=10.0, density="solid"),     # → 4A
    ]
    assert classify_overall_lung_rads(nodules) == "4A"


def test_recommendation():
    rec = get_recommendation("3")
    assert rec["category"] == "3"
    assert rec["follow_up_months"] == 6
    assert "%1-2" in rec["malignancy_risk"]
