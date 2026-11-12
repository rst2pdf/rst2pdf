from rst2pdf.math_flowable import Math, enclose, unpack_glyph


def test_enclose_normalizes_multiline_expression():
    expression = r"""\Delta\varepsilon_{X} = \frac
    { E_{m} \Delta\varepsilon^{sh}_{m} \left(1-V_{f}\right) }
    { E^{XX}_{f}V_{f}+E_{m}\left(1-V_{f}\right) }"""

    assert enclose(expression) == (
        r'$\Delta\varepsilon_{X} = \frac '
        r'{ E_{m} \Delta\varepsilon^{sh}_{m} \left(1-V_{f}\right) } '
        r'{ E^{XX}_{f}V_{f}+E_{m}\left(1-V_{f}\right) }$'
    )


def test_enclose_normalizes_already_enclosed_expression():
    assert enclose('$a +\n b$') == '$a + b$'


def test_math_wrap_accepts_source_line_breaks():
    math = Math(
        r'\Delta\varepsilon_{X} = \frac '
        '{ E_{m} \\Delta\\varepsilon^{sh}_{m} \\left(1-V_{f}\\right) }\n'
        r'{ E^{XX}_{f}V_{f}+E_{m}\left(1-V_{f}\right) }'
    )

    width, height = math.wrap(100, 100)

    assert width > 10
    assert height > 0


def test_unpack_glyph_accepts_old_and_new_matplotlib_results():
    old_glyph = ('font', 10, 97, 1.5, 2.5)
    new_glyph = ('font', 10, 97, 68, 1.5, 2.5)

    assert unpack_glyph(old_glyph) == ('font', 10, 97, 1.5, 2.5)
    assert unpack_glyph(new_glyph) == ('font', 10, 97, 1.5, 2.5)
