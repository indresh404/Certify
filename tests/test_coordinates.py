import pytest

from app.core.coordinates import original_to_preview, preview_to_original


def test_roundtrip_coordinates():
    scale = 1.5
    offset = (10.0, 20.0)
    original_x, original_y = 100.0, 200.0

    px, py = original_to_preview(original_x, original_y, scale, offset)
    ox, oy = preview_to_original(px, py, scale, offset)

    assert pytest.approx(ox) == original_x
    assert pytest.approx(oy) == original_y


def test_zoom_does_not_mutate_original():
    scale1 = 1.0
    offset = (0.0, 0.0)
    original_x, original_y = 100.0, 200.0

    px1, py1 = original_to_preview(original_x, original_y, scale1, offset)

    # Zoom in
    scale2 = 2.0
    px2, py2 = original_to_preview(original_x, original_y, scale2, offset)

    # Assert preview changed but original is invariant
    assert px1 != px2
    assert py1 != py2

    ox1, oy1 = preview_to_original(px1, py1, scale1, offset)
    ox2, oy2 = preview_to_original(px2, py2, scale2, offset)

    assert pytest.approx(ox1) == pytest.approx(ox2)
    assert pytest.approx(oy1) == pytest.approx(oy2)
