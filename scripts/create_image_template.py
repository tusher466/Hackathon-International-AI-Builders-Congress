"""
Create a high-quality 2000x2500 image template with empty space for text.
Usage:
    python scripts/create_image_template.py --input path/to/your/image.jpg --output template.png --text-area bottom --text-area-ratio 0.35
If no input image provided, creates a clean factory-themed placeholder template.

Features:
- Output size 2000x2500 pixels, 300 DPI, high quality PNG/JPEG
- Empty space reserved for text (bottom, top, left, right, or center-overlay)
- Gradient / blur / solid fill for text area for readability
- High quality: PNG no compression or JPEG quality 95-100
"""

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

# Try to import ImageFont for text guides
try:
    from PIL import ImageFont
except ImportError:
    ImageFont = None


def create_placeholder_background(size=(2000, 2500)):
    """Create a high-quality placeholder background (factory theme) if no input image."""
    w, h = size
    # Create gradient from dark industrial blue to lighter
    img = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Vertical gradient
    top_color = (18, 32, 56)  # dark navy
    bottom_color = (245, 247, 250)  # light gray
    for y in range(h):
        ratio = y / h
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    # Add subtle factory grid pattern
    for x in range(0, w, 100):
        draw.line([(x, 0), (x, int(h*0.65))], fill=(255, 255, 255, 30), width=1)
    for y in range(0, int(h*0.65), 100):
        draw.line([(0, y), (w, y)], fill=(255, 255, 255, 20), width=1)
    # Add a soft glow circle (simulating light)
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([w*0.1, h*0.05, w*0.9, h*0.6], fill=(100, 180, 255, 25))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    return img


def prepare_input_image(input_path: Path, target_size=(2000, 2500), text_area="bottom", text_ratio=0.35):
    """
    Resize and crop input image to fill the non-text area, keeping aspect ratio.
    Returns full canvas image with image placed.
    """
    w, h = target_size
    base = create_placeholder_background(target_size) if input_path is None else None

    if input_path is None:
        img = base
    else:
        try:
            src = Image.open(input_path).convert("RGB")
        except Exception as e:
            print(f"Failed to open {input_path}: {e}, using placeholder")
            src = create_placeholder_background(target_size)

        # Determine image area based on text_area
        if text_area == "bottom":
            img_h = int(h * (1 - text_ratio))
            img_area = (0, 0, w, img_h)
        elif text_area == "top":
            img_h = int(h * (1 - text_ratio))
            img_area = (0, int(h * text_ratio), w, h)
        elif text_area == "right":
            img_w = int(w * (1 - text_ratio))
            img_area = (0, 0, img_w, h)
        elif text_area == "left":
            img_w = int(w * (1 - text_ratio))
            img_area = (int(w * text_ratio), 0, w, h)
        else:  # center or overlay
            img_area = (0, 0, w, h)

        area_w = img_area[2] - img_area[0]
        area_h = img_area[3] - img_area[1]

        # Resize with cover (fill area, keep aspect, crop)
        src_ratio = src.width / src.height
        area_ratio = area_w / area_h

        if src_ratio > area_ratio:
            # source wider, scale by height
            new_h = area_h
            new_w = int(new_h * src_ratio)
        else:
            new_w = area_w
            new_h = int(new_w / src_ratio)

        src_resized = src.resize((new_w, new_h), Image.LANCZOS)

        # Center crop to area
        left = (new_w - area_w) // 2
        top = (new_h - area_h) // 2
        src_cropped = src_resized.crop((left, top, left + area_w, top + area_h))

        # Create canvas 2000x2500
        canvas = Image.new("RGB", (w, h), (255, 255, 255))
        canvas.paste(src_cropped, (img_area[0], img_area[1]))
        img = canvas

    return img


def add_text_area_overlay(img: Image.Image, text_area="bottom", text_ratio=0.35, style="solid_light", blur_text_image=False):
    """
    Add empty space for text with styling for readability.
    style: solid_light, solid_dark, gradient, blur, transparent_dark
    """
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if text_area == "bottom":
        x0, y0, x1, y1 = 0, int(h * (1 - text_ratio)), w, h
    elif text_area == "top":
        x0, y0, x1, y1 = 0, 0, w, int(h * text_ratio)
    elif text_area == "right":
        x0, y0, x1, y1 = int(w * (1 - text_ratio)), 0, w, h
    elif text_area == "left":
        x0, y0, x1, y1 = 0, 0, int(w * text_ratio), h
    elif text_area == "center_box":
        box_w = int(w * 0.8)
        box_h = int(h * 0.35)
        x0 = (w - box_w)//2
        y0 = int(h*0.6)
        x1 = x0 + box_w
        y1 = y0 + box_h
    else:
        x0, y0, x1, y1 = 0, 0, w, h

    if style == "solid_light":
        draw.rectangle([x0, y0, x1, y1], fill=(255, 255, 255, 255))
    elif style == "solid_dark":
        draw.rectangle([x0, y0, x1, y1], fill=(18, 32, 56, 255))
    elif style == "gradient_light":
        # white to transparent gradient
        for i in range(y1 - y0):
            alpha = int(255 * (1 - i/(y1-y0)*0.3)) if text_area=="bottom" else 255
            draw.line([(x0, y0+i), (x1, y0+i)], fill=(255,255,255,alpha))
    elif style == "transparent_dark":
        draw.rectangle([x0, y0, x1, y1], fill=(0, 0, 0, 120))
    elif style == "blur":
        # blur underlying image in text area
        crop = img.crop((x0, y0, x1, y1))
        blurred = crop.filter(ImageFilter.GaussianBlur(radius=15))
        # lighten blur
        white = Image.new("RGB", (x1-x0, y1-y0), (255,255,255))
        blended = Image.blend(blurred, white, 0.7)
        img.paste(blended, (x0, y0))
        # add semi-transparent white overlay
        draw.rectangle([x0, y0, x1, y1], fill=(255, 255, 255, 180))
    elif style == "factory_light":
        draw.rectangle([x0, y0, x1, y1], fill=(245, 247, 250, 255))
        # add border line on top for bottom area
        if text_area=="bottom":
            draw.line([(x0, y0), (x1, y0)], fill=(18, 32, 56), width=4)

    # Composite
    combined = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    # Add guide text boxes (optional, for template visualization)
    guide_draw = ImageDraw.Draw(combined)
    # Try to load font
    try:
        # Use default font, size scaled for 2000px
        font_large = ImageFont.truetype("arial.ttf", 80)
        font_small = ImageFont.truetype("arial.ttf", 50)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw placeholder lines indicating text area
    # dotted border
    margin = 80
    gx0, gy0, gx1, gy1 = x0+margin, y0+margin, x1-margin, y1-margin
    # Dashed rectangle for text safe area
    for i in range(0, (gx1-gx0), 20):
        guide_draw.line([(gx0+i, gy0), (gx0+i+10, gy0)], fill=(180,180,180), width=2)
        guide_draw.line([(gx0+i, gy1), (gx0+i+10, gy1)], fill=(180,180,180), width=2)
    for i in range(0, (gy1-gy0), 20):
        guide_draw.line([(gx0, gy0+i), (gx0, gy0+i+10)], fill=(180,180,180), width=2)
        guide_draw.line([(gx1, gy0+i), (gx1, gy0+i+10)], fill=(180,180,180), width=2)

    # Placeholder text
    if style not in ("solid_dark", "transparent_dark"):
        text_color = (90, 90, 90)
    else:
        text_color = (230, 230, 230)

    guide_draw.text((gx0, gy0), "YOUR TEXT HERE", fill=text_color, font=font_large)
    guide_draw.text((gx0, gy0+120), "Add title, description, or logo in this empty space.", fill=text_color, font=font_small)
    guide_draw.text((gx0, gy0+190), f"Canvas: 2000x2500 px | 300 DPI | High Quality", fill=(150,150,150), font=font_small)

    return combined


def add_safe_margins_and_guides(img):
    """Add small safe margin indicators on corners."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    margin = 40
    length = 80
    color = (200, 200, 200)
    # top-left
    draw.line([(margin, margin), (margin+length, margin)], fill=color, width=2)
    draw.line([(margin, margin), (margin, margin+length)], fill=color, width=2)
    # top-right
    draw.line([(w-margin, margin), (w-margin-length, margin)], fill=color, width=2)
    draw.line([(w-margin, margin), (w-margin, margin+length)], fill=color, width=2)
    # bottom-left
    draw.line([(margin, h-margin), (margin+length, h-margin)], fill=color, width=2)
    draw.line([(margin, h-margin), (margin, h-margin-length)], fill=color, width=2)
    # bottom-right
    draw.line([(w-margin, h-margin), (w-margin-length, h-margin)], fill=color, width=2)
    draw.line([(w-margin, h-margin), (w-margin, h-margin-length)], fill=color, width=2)
    return img


def save_high_quality(img: Image.Image, output_path: Path, dpi=300):
    """Save high quality PNG and JPEG."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save PNG (lossless, highest quality)
    if output_path.suffix.lower() in (".png", ""):
        if output_path.suffix == "":
            output_path = output_path.with_suffix(".png")
        img.save(output_path, "PNG", dpi=(dpi, dpi), optimize=False)
        print(f"Saved PNG high quality: {output_path} {img.size} DPI {dpi}")

        # Also save JPEG version for smaller size
        jpeg_path = output_path.with_suffix(".jpg")
        img.save(jpeg_path, "JPEG", quality=98, dpi=(dpi, dpi), subsampling=0)
        print(f"Saved JPEG high quality: {jpeg_path}")

    elif output_path.suffix.lower() in (".jpg", ".jpeg"):
        img.save(output_path, "JPEG", quality=98, dpi=(dpi, dpi), subsampling=0)
        print(f"Saved JPEG high quality: {output_path} {img.size} DPI {dpi}")
        # Also PNG
        png_path = output_path.with_suffix(".png")
        img.save(png_path, "PNG", dpi=(dpi, dpi))
        print(f"Saved PNG: {png_path}")
    else:
        img.save(output_path, dpi=(dpi, dpi))
        print(f"Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Create 2000x2500 image template with text space")
    parser.add_argument("--input", "-i", type=str, default=None, help="Input image path (your source image)")
    parser.add_argument("--output", "-o", type=str, default="E:/Backend/data/template_2000x2500.png", help="Output path")
    parser.add_argument("--text-area", type=str, default="bottom", choices=["bottom","top","left","right","center_box","full"], help="Where empty text space should be")
    parser.add_argument("--text-ratio", type=float, default=0.35, help="Ratio of canvas reserved for text (0.2-0.6)")
    parser.add_argument("--style", type=str, default="solid_light", choices=["solid_light","solid_dark","gradient_light","transparent_dark","blur","factory_light"], help="Text area overlay style")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for high quality")
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else None
    output_path = Path(args.output)

    print(f"Creating template size 2000x2500 DPI {args.dpi}")
    print(f"Input: {input_path}")
    print(f"Text area: {args.text_area} ratio {args.text_ratio} style {args.style}")

    base_img = prepare_input_image(input_path, target_size=(2000, 2500), text_area=args.text_area, text_ratio=args.text_ratio)
    final_img = add_text_area_overlay(base_img, text_area=args.text_area, text_ratio=args.text_ratio, style=args.style)
    final_img = add_safe_margins_and_guides(final_img)

    save_high_quality(final_img, output_path, dpi=args.dpi)
    print("Done! Template ready for adding text.")


if __name__ == "__main__":
    main()
