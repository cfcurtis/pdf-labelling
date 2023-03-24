from pathlib import Path
import fitz

DPI = 72  # default PDF DPI
GRID_LAYERS = ["grid", "calibration", "grille", "calibrage"]
PDF_ROOT = Path("/projects/pattern-labelling/documents/processed_pdfs")
TEXT_LABELS = ["piece label"]


def activate_all_layers(doc: fitz.Document) -> None:
    """
    Turns on all the layers except for calibration grids.
    """
    # get the dictionary of layers
    ui_configs = doc.layer_ui_configs()

    # action=2 turns off the layer, action=0 turns it on
    for layer in ui_configs:
        if any(grid in layer["text"].lower() for grid in GRID_LAYERS):
            doc.set_layer_ui_config(layer["number"], action=2)
        else:
            doc.set_layer_ui_config(layer["number"], action=0)


def deactivate_all_layers(doc: fitz.Document) -> None:
    """
    Turns off all the layers.
    """
    # get the dictionary of layers and disable all of them
    ui_configs = doc.layer_ui_configs()
    for layer in ui_configs:
        doc.set_layer_ui_config(layer["number"], action=2)


def activate_named_layers(doc: fitz.Document, layers: list) -> None:
    """
    Turns on all the layers in the list.
    """
    # first turn off all the layers
    deactivate_all_layers(doc)
    ui_configs = doc.layer_ui_configs()

    # then go through them all and find the corresponding numbers
    for layer in ui_configs:
        if layer["text"] in layers:
            doc.set_layer_ui_config(layer["number"], action=0)



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