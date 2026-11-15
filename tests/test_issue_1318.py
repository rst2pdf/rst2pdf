import io

from rst2pdf import createpdf
from sphinx.application import Sphinx


def test_pdf_builder_propagates_pdf_generation_failure(monkeypatch, tmp_path):
    srcdir = tmp_path / "source"
    srcdir.mkdir()
    (srcdir / "conf.py").write_text(
        'project = "MRE"\n'
        'extensions = ["rst2pdf.pdfbuilder"]\n'
        'pdf_documents = [("index", "mre", "MRE", "Author")]\n'
    )
    (srcdir / "index.rst").write_text("MRE\n===\n")
    monkeypatch.setattr(createpdf.RstToPdf, "createPdf", lambda *args, **kwargs: 1)

    app = Sphinx(
        srcdir=str(srcdir),
        confdir=str(srcdir),
        outdir=str(tmp_path / "out"),
        doctreedir=str(tmp_path / "doctrees"),
        buildername="pdf",
        status=io.StringIO(),
        warning=io.StringIO(),
        freshenv=True,
    )
    app.build(force_all=True)

    assert app.statuscode == 1
