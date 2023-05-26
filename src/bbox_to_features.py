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
            rect = to_pdf_bbox(label, page)
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

    # if the label has rotation, find the bounding box of the rotated label
    bbox = fitz.Rect(
        label["x"] * x_scale,
        label["y"] * y_scale,
        (label["x"] + label["width"]) * x_scale,
        (label["y"] + label["height"]) * y_scale,
    )

    if label["rotation"]:
        # just expand the bbox to include the rotated image
        to_origin = fitz.Matrix(fitz.Identity).pretranslate(-bbox.x0, -bbox.y0)
        rotation = fitz.Matrix(fitz.Identity).prerotate(label["rotation"])
        shift_back = fitz.Matrix(fitz.Identity).pretranslate(bbox.x0, bbox.y0)

        bbox.transform(to_origin)
        bbox.transform(rotation)
        bbox.transform(shift_back)

    # make sure the bounding box is within the page mediabox
    bbox.intersect(page.mediabox)
    return bbox


def extract_img(page: fitz.Page, label: dict) -> Image.Image | None:
    """
    Extracts the image from the page and returns it as a PIL Image.
    Upsamples by 4x (a DPI of 288). If the image has no meaningful content, returns None.
    """
    pix = page.get_pixmap(dpi=c.DPI * 4)

    # if the pixmap is all one colour, don't return it
    pil_img = None
    if pix.color_count() > 1:
        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return pil_img


def extract_svg(page: fitz.Page, label: dict) -> dict:
    """
    Extracts the image from the page and returns it as a dictionary of strings.
    """
    c.activate_all_layers(page.parent)
    svg = {"all_layers": page.get_svg_image(text_as_path=False)}

    # if it's one of the label types that applies to multiple layers, get the svg for each one
    if label["rectanglelabels"][0] in c.MULTI_LAYER:
        for layer in page.parent.layer_ui_configs():
            name = layer["text"]
            c.activate_named_layers(page.parent, [name])
            svg[name] = page.get_svg_image(text_as_path=False)

    c.activate_all_layers(page.parent)
    return svg


def create_annotation(page: fitz.Page, label: dict) -> None:
    """
    Creates a hidden annotation rectangle for a given label.
    """
    bbox = to_pdf_bbox(label, page)
    annot = page.add_rect_annot(bbox)
    annot.set_name(label["rectanglelabels"][0])
    annot.set_flags(2)  # hidden
    annot.set_rotation(int(label["rotation"]))
    # annot.set_oc() # set the optional content group, eventually
    annot.update()


def process_labels(page: fitz.Page, label_data: dict, **kwargs) -> list:
    """
    Processes the label data for a given page and returns a list of features.
    """
    features = []
    feat_counter = 0
    for label in label_data["label"]:
        bbox = to_pdf_bbox(label, page)
        page.set_cropbox(bbox)
        pix = extract_img(page, label)
        if not pix:
            continue

        svg = extract_svg(page, label)
        text = ""
        if label["rectanglelabels"][0] in c.TEXT_LABELS:
            text = page.get_textbox(bbox)

        features.append(
            {
                "label": label["rectanglelabels"][0],
                "number": feat_counter,
                "pixmap": pix,
                "svg": svg,
                "text": text,
            }
        )
        feat_counter += 1

    return features


def main(label_path: Path, pdf_root: Path = c.PDF_ROOT, docs: str | list = []) -> None:
    """
    Loads the json-min file exported from label studio and processes each item.
    """
    all_label_data = json.load(label_path.open())
    if isinstance(docs, str):
        docs = [docs]

    for label_data in all_label_data:
        pdf_info = get_doc_info(label_data)
        if docs and pdf_info["number"] not in docs:
            continue

        doc = fitz.open(pdf_root / f"{pdf_info['number']}.pdf")

        # select the specified layers and page
        if pdf_info["layer"] == "all_layers":
            c.activate_all_layers(doc)
        else:
            c.activate_named_layers(doc, [pdf_info["layer"]])

        # Make sure the mediabox isn't some weird arbitrary set of coordinates
        doc[pdf_info["page"]].mediabox.normalize()
        features = process_labels(doc[pdf_info["page"]], label_data)

        # save the svgs to a folder
        folder = Path(f"output/{pdf_info['number']}")
        if not folder.exists():
            folder.mkdir(parents=True)

        for feat, label in zip(features, label_data["label"]):
            base_path = str(
                folder
                / f"p{pdf_info['page']}_{c.sanitize(label['rectanglelabels'][0])}_{feat['number']}_"
            )

            for layer, text in feat["svg"].items():
                svg_path = base_path + c.sanitize(layer) + ".svg"
                try:
                    c.write_svg(text, svg_path)
                except IOError:
                    print(f"Could not write {svg_path}, skipping")

        # doc.save(pdf_root / f"{pdf_info['number']}_annotated.pdf")


if __name__ == "__main__":
    if len(sys.argv) > 3:
        # json, pdf_root, specific file number (without .pdf)
        main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
    elif len(sys.argv) > 2:
        # json, pdf_root
        main(Path(sys.argv[1]), Path(sys.argv[2]))
    else:
        # json
        main(Path(sys.argv[1]))
