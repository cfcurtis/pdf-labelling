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
