import fitz
import sys
from pathlib import Path

DPI = 72 # default PDF DPI
GRID_LAYERS = ["grid", "calibration", "grille", "calibrage"]


def write_svg(svg: str, filename: str) -> None:
    """Writes the svg string to the given filename."""
    with open(filename, "w") as f:
        f.write(svg)


def page_to_png(folder: Path, page: fitz.Page, layer_name: str) -> None:
    """Saves a page as a .png"""
    try:
        pix = page.get_pixmap(dpi=DPI)
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
        # turn off all layers
        ui_configs = doc.layer_ui_configs()

        # first turn off any of the grid/calibration layers
        for layer in ui_configs:
            if any(grid in layer["text"].lower() for grid in GRID_LAYERS):
                doc.set_layer_ui_config(layer["number"], action=2)

        # then save an image of all the rest of the layers
        for page in doc:
            page_to_png(im_dir, page, "all_layers")

        for layer in ui_configs:
            doc.set_layer_ui_config(layer["number"], action=2)

        # save the background layer
        for page in doc:
            page_to_png(im_dir, page, "background")

        for layer in ui_configs:
            layer_name = layer["text"].replace(" ", "")
            if any(grid in layer_name.lower() for grid in GRID_LAYERS):
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
