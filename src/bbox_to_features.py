import sys
from pathlib import Path
import json
import fitz
from PIL import Image, ImageDraw

import common as c


def preview_page(page: fitz.Page, labels=None) -> None:
    """
    Helper function to preview a page for debugging.
    """
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    if labels:
        # draw bounding boxes representing the labels
        draw = ImageDraw.Draw(img)
        for label in labels:
            rect = to_pdf_bbox(label)
            draw.rectangle(rect, outline="red")
            draw.text((rect.x0, rect.y0), label["rectanglelabels"][0], fill="red")

    img.show()


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


def to_pdf_bbox(label: dict, page: fitz.Page) -> fitz.Rect:
    """
    Converts the label studio bbox coordinates to pdf coordinates.
    Label studio coordinates appear to be percentages of the image size.
    """
    x_scale = label["original_width"] / 100
    y_scale = label["original_height"] / 100
    
    # make sure the bounding box is within the page mediabox
    mbox = page.mediabox
    return fitz.Rect(
        max(label["x"] * x_scale, mbox[0]),
        max(label["y"] * y_scale, mbox[1]),
        min((label["x"] + label["width"]) * x_scale, mbox[2]),
        min((label["y"] + label["height"]) * y_scale, mbox[3]),
    )


def process_labels(page: fitz.Page, label_data: dict) -> list:
    """
    Processes the label data for a given page and returns a list of features.
    """
    features = []
    for label in label_data["label"]:
        img_mat = fitz.Matrix(fitz.Identity)
        if label["rotation"]:
            # img_mat.prerotate(-label["rotation"])
            pass

        bbox = to_pdf_bbox(label, page)
        page.set_cropbox(bbox)
        pix = page.get_pixmap(matrix=img_mat, dpi=c.DPI)
        svg = page.get_svg_image(matrix=img_mat, text_as_path=False)

        # if it's a pattern piece, extract an svg for every layer
        if label["rectanglelabels"][0] == "pattern piece":
            svg = {"all": svg}
            for layer in page.parent.layer_ui_configs():
                name = layer["text"]
                c.activate_named_layers(page.parent, [name])
                svg[name] = page.get_svg_image(text_as_path=False)

        text = ""
        if label["rectanglelabels"][0] in c.TEXT_LABELS:
            text = page.get_textbox(bbox)
        features.append(
            {
                "label": label["rectanglelabels"][0],
                "pixmap": pix,
                "svg": svg,
                "text": text,
            }
        )

    return features


def main(label_path: Path, pdf_root: Path = c.PDF_ROOT) -> None:
    """
    Loads the json-min file exported from label studio and processes each item.
    """
    all_label_data = json.load(label_path.open())
    for label_data in all_label_data:
        pdf_info = get_doc_info(label_data)
        doc = fitz.open(pdf_root / f"{pdf_info['number']}.pdf")

        # select the specified layers and page
        if pdf_info["layer"] == "all_layers":
            c.activate_all_layers(doc)
        else:
            c.activate_named_layers(doc, [pdf_info["layer"]])

        # Make sure the mediabox isn't some weird arbitrary set of coordinates
        doc[pdf_info["page"]].mediabox.normalize()
        features = process_labels(doc[pdf_info["page"]], label_data)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(Path(sys.argv[1]), Path(sys.argv[2]))
    else:
        main(Path(sys.argv[1]))
