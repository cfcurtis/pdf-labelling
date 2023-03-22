import sys
from pathlib import Path
import json
import fitz

import common as c


def get_doc_info(label_data: dict) -> dict:
    """
    Parses the image name and returns the associated pdf document, page number, and active layer.
    """
    if "image" not in label_data:
        raise ValueError(
            "Make sure the JSON-MIN format is selected for export in Label Studio."
        )

    img = Path(label_data["image"]).stem.split("-")
    info = {"number": img[0], "page": int(img[1][1:]), "layer": img[2]}
    return info


def to_pdf_bbox(label: dict) -> fitz.Rect:
    """
    Converts the label studio bbox coordinates to pdf coordinates.
    """
    return fitz.Rect(
        label["x"],
        label["y"],
        label["y"] + label["height"],
        label["x"] + label["width"]
    )


def process_labels(page: fitz.Page, label_data: dict) -> list:
    """
    Processes the label data and returns a list of features.
    """
    features = []
    for label in label_data["label"]:
        bbox = to_pdf_bbox(label)
        if label["rectanglelabels"][0] in c.TEXT_LABELS:
            text = page.get_textbox(bbox)


def main(label_path: Path, pdf_root: Path = c.PDF_ROOT) -> None:
    """
    Loads the json-min file exported from label studio and processes each item.
    """
    all_label_data = json.load(label_path.open())
    for label_data in all_label_data:
        pdf_info = get_doc_info(label_data)
        doc = fitz.open(pdf_root / f"{pdf_info['number']}.pdf")
        
        # select the specified layers and page
        if pdf_info['layer'] == 'all_layers':
            c.activate_all_layers(doc)
        else:
            c.deactivate_all_layers(doc)
            doc.set_layer_ui_config(pdf_info['layer'], action=0)

        features = process_labels(doc[pdf_info["page"]], label_data)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(Path(sys.argv[1]), Path(sys.argv[2]))
    else:
        main(Path(sys.argv[1]))
