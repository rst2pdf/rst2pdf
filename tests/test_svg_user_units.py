# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

import gzip

import pytest
from reportlab.graphics.shapes import Drawing, String
from svglib.svglib import svg2rlg

from rst2pdf.svgimage import (
    _USER_UNIT_TO_PT,
    _is_user_unit,
    _restore_user_unit_size,
    _rewrite_px_font_sizes,
    _root_width_height,
    _svg2rlg,
    _svglib_uses_css_px,
)


def _write_svg(tmp_path, name, attrs, body=''):
    text = (
        '<?xml version="1.0"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" %s>%s</svg>' % (attrs, body)
    )
    path = tmp_path / name
    path.write_text(text, encoding='utf-8')
    return path


def _rendered_strings(drawing):
    """Yield each text shape and the point size it renders at."""

    def walk(node, scale):
        for item in getattr(node, 'contents', []):
            item_scale = scale * abs(getattr(item, 'transform', (1,))[0])
            if hasattr(item, 'contents'):
                yield from walk(item, item_scale)
            elif isinstance(item, String):
                yield item, item.fontSize * item_scale

    yield from walk(drawing, abs(drawing.transform[0]))


@pytest.mark.parametrize(
    ('value', 'is_user_unit'),
    [
        (None, True),
        ('100', True),
        (' 100.5 ', True),
        ('1e2', True),
        ('.5', True),
        ('100px', False),
        ('100pt', False),
        ('25.4mm', False),
        ('1in', False),
    ],
)
def test_user_unit_detection(value, is_user_unit):
    assert _is_user_unit(value) is is_user_unit


def test_root_width_and_height_ignore_nested_elements(tmp_path):
    path = _write_svg(
        tmp_path,
        'nested.svg',
        'width="100" height="40"',
        '<svg width="5px" height="5px"/>',
    )
    assert _root_width_height(str(path)) == ('100', '40')


def test_root_width_and_height_read_svgz(tmp_path):
    path = tmp_path / 'figure.svgz'
    with gzip.open(path, 'wt', encoding='utf-8') as handle:
        handle.write(
            '<?xml version="1.0"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'width="80" height="20"></svg>'
        )
    assert _root_width_height(str(path)) == ('80', '20')


def test_root_width_and_height_of_unreadable_svg(tmp_path):
    path = tmp_path / 'broken.svg'
    path.write_text('<not-svg', encoding='utf-8')
    assert _root_width_height(str(path)) == (None, None)


def test_rewrite_px_font_sizes_to_points():
    source = (
        '<text font-size="12px"/>'
        "<text font-size='16px'/>"
        '<text style="font-size:10px"/>'
        '<text font-size: 13.5px />'
        '<text font-size="12"/>'
        '<text font-size="12pt"/>'
    )
    rewritten = _rewrite_px_font_sizes(source)
    assert rewritten == (
        '<text font-size="9"/>'
        "<text font-size='12'/>"
        '<text style="font-size:7.5"/>'
        '<text font-size: 10.125 />'
        '<text font-size="12"/>'
        '<text font-size="12pt"/>'
    )


def test_restore_user_unit_size_scales_by_four_thirds():
    drawing = Drawing(75, 37.5)
    _restore_user_unit_size(drawing)
    assert drawing.width == pytest.approx(75 * _USER_UNIT_TO_PT)
    assert drawing.height == pytest.approx(37.5 * _USER_UNIT_TO_PT)
    assert drawing.transform[0] == pytest.approx(_USER_UNIT_TO_PT)
    assert drawing.transform[3] == pytest.approx(_USER_UNIT_TO_PT)


@pytest.mark.parametrize(
    ('attrs', 'width', 'height', 'compensate'),
    [
        ('width="100" height="50"', 100, 50, True),
        ('viewBox="0 0 100 40"', 100, 40, True),
        ('width="100px" height="50px"', 75, 37.5, False),
        ('width="100pt" height="50pt"', 100, 50, False),
        ('width="25.4mm" height="25.4mm"', 72, 72, False),
        ('width="100" height="50pt"', None, None, False),
    ],
)
def test_viewport_keeps_historical_point_size(
    tmp_path, attrs, width, height, compensate
):
    path = _write_svg(tmp_path, 'figure.svg', attrs, '<rect width="10" height="10"/>')
    drawing = _svg2rlg(str(path))
    raw = svg2rlg(str(path))
    if compensate and _svglib_uses_css_px():
        assert drawing.width == pytest.approx(raw.width * _USER_UNIT_TO_PT)
        assert drawing.height == pytest.approx(raw.height * _USER_UNIT_TO_PT)
    else:
        assert drawing.width == pytest.approx(raw.width)
        assert drawing.height == pytest.approx(raw.height)
    if width is not None:
        assert drawing.width == pytest.approx(width)
        assert drawing.height == pytest.approx(height)


def test_px_font_sizes_render_in_points_and_labels_stay_separate(tmp_path):
    path = _write_svg(
        tmp_path,
        'labels.svg',
        'width="200" height="40"',
        '<text font-size="10px" x="0" y="20">Left</text>'
        '<text style="font-size:10px" x="40" y="20">Right</text>',
    )
    strings = list(_rendered_strings(_svg2rlg(str(path))))
    assert [shape.text for shape, _size in strings] == ['Left', 'Right']
    assert strings[0][1] == pytest.approx(7.5)
    assert strings[1][1] == pytest.approx(7.5)
    assert strings[0][0].x != strings[1][0].x


def test_bare_font_size_is_not_rewritten(tmp_path):
    path = _write_svg(
        tmp_path,
        'bare.svg',
        'width="100" height="50"',
        '<text font-size="12" x="1" y="12">Hi</text>',
    )
    strings = list(_rendered_strings(_svg2rlg(str(path))))
    assert len(strings) == 1
    assert strings[0][1] == pytest.approx(12)


def test_svgz_unitless_viewport(tmp_path):
    path = tmp_path / 'figure.svgz'
    with gzip.open(path, 'wt', encoding='utf-8') as handle:
        handle.write(
            '<?xml version="1.0"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="20">'
            '<rect width="80" height="20"/>'
            '</svg>'
        )
    drawing = _svg2rlg(str(path))
    assert drawing.width == pytest.approx(80)
    assert drawing.height == pytest.approx(20)
