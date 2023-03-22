import fitz
import sys
from pathlib import Path

import common as c


def write_svg(svg: str, filename: str) -> None:
    """Writes the svg string to the given filename."""
    with open(filename, "w") as f:
        f.write(svg)


def page_to_png(folder: Path, page: fitz.Page, layer_name: str) -> None:
    """Saves a page as a .png"""
    try:
        pix = page.get_pixmap(dpi=c.DPI)
        if pix.color_count() < 2:
            # there's nothing on this page, skip it
            print(f"Skipping page {page.number} {layer_name}, no content")
        else:
            pix.save(folder / f"{folder.stem}-p{page.number:02d}-{layer_name}.png")
    except OSError as e:
        print(e)


def explode_pdf(doc: fitz.Document) -> None:
    """
    Creates a folder of images for each layer and page in the PDF.
    """
    # Create a folder for the images with the basename of the pdf
    doc_path = Path(doc.name)
    im_dir = doc_path.parent / doc_path.stem
    if not im_dir.exists():
        im_dir.mkdir()

    try:
        # make sure all the non-grid layers are active
        c.activate_all_layers(doc)

        # then save an image of all the rest of the layers
        for page in doc:
            page_to_png(im_dir, page, "all_layers")

        # get the dictionary of layers
        ui_configs = doc.layer_ui_configs()
        
        # then turn them all off
        c.deactivate_all_layers(doc)

        # save the background layer
        for page in doc:
            page_to_png(im_dir, page, "background")

        for layer in ui_configs:
            layer_name = layer["text"].replace(" ", "")
            if any(grid in layer_name.lower() for grid in c.GRID_LAYERS):
                # skip the grid layers
                continue

            # turn on the current layer
            doc.set_layer_ui_config(layer["number"], action=0)

            # write the current layer to an image
            for page in doc:
                page_to_png(im_dir, page, layer_name)

            # turn the current layer back off
            doc.set_layer_ui_config(layer["number"], action=2)

    except Exception as e:
        print(e)


def main(pdf_path) -> None:
    doc = fitz.open(pdf_path)
    explode_pdf(doc)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_imgs.py path_to_pdf")
    else:
        main(sys.argv[1])
