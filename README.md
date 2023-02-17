# pdf-labelling
Various scripts to convert multi-layered PDF sewing patterns into images for labelling.

Requirements can be installed with pip:
```python
pip install -r requirements.txt
```

## Preprocessing
Preprocessing takes an input PDF and creates a .png image from each layer and page. The output is stored in a folder with the same name as the PDF, and the images are named with the page number and layer name.

```python
python preprocessing/pdf_to_imgs.py input_pdf.pdf
```

## Postprocessing
TBD, but we'll need to take the labelled images and extract the vector graphics/text from the original PDF. Text within a box can be extracted with PyMuPDF using `page.get_textbox` (see [docs](https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/textbox-extraction)). Vector graphics are trickier.