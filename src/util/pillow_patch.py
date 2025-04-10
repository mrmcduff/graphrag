"""
Monkey patch for Pillow's ImageDraw to handle the deprecated textsize method.
"""

from PIL import ImageDraw

# Store the original textsize method if it exists
original_textsize = getattr(ImageDraw.ImageDraw, "textsize", None)


def patched_textsize(self, text, font=None):
    """
    Replacement for the deprecated textsize method using textbbox.

    Args:
        text: Text to measure
        font: Font to use

    Returns:
        Tuple of (width, height)
    """
    try:
        # Use textbbox (newer Pillow versions)
        left, top, right, bottom = self.textbbox((0, 0), text, font=font)
        return right - left, bottom - top
    except Exception as e:
        # If something goes wrong, make a rough estimate
        if font:
            font_size = font.size
        else:
            font_size = 10  # Default size
        return len(text) * font_size // 2, font_size


# Apply the monkey patch only if textsize is missing
if not hasattr(ImageDraw.ImageDraw, "textsize"):
    ImageDraw.ImageDraw.textsize = patched_textsize
    print("Applied Pillow patch for textsize method")
