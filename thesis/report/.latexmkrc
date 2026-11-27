# Use pdflatex for PDF output
$pdf_mode = 1;
$pdflatex = 'pdflatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';
# Force latexmk to complete all passes even when warnings look like errors
$force_mode = 1;
