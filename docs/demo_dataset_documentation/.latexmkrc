# Latexmk configuration file for the Digital Karyotyping Pipeline guide

# Continue processing even if there are errors
$force_mode = 1;

# PDF generation mode (1 = pdflatex)
$pdf_mode = 1;

# Use pdflatex
$pdflatex = 'pdflatex -interaction=nonstopmode -synctex=1 %O %S';

# Use bibtex instead of biber (better compatibility)
$bibtex_use = 2;

# Maximum number of compilation passes
$max_repeat = 5;

# Return success if PDF was generated, even with warnings
$success_cmd = 'true';

# Ignore certain error patterns (UTF-8 warnings are non-fatal)
$warnings_as_errors = 0;

# Clean up auxiliary files
$clean_ext = 'synctex.gz synctex.gz(busy) run.xml tex.bak bbl bcf fdb_latexmk run tdo %R-blx.bib';

