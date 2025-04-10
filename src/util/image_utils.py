"""
Utility functions for image processing.
"""


def get_text_dimensions(draw, text, font):
    """
    Get text dimensions using textbbox instead of deprecated textsize.

    This is a compatibility function to replace the deprecated textsize method
    in the Pillow library with the newer textbbox method.

    Args:
        draw: ImageDraw object
        text: Text to measure
        font: Font to use

    Returns:
        Tuple of (width, height)
    """
    try:
        # Try using textbbox (newer Pillow versions)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return right - left, bottom - top
    except AttributeError:
        # Fall back to textsize for older Pillow versions
        try:
            return draw.textsize(text, font=font)
        except Exception as e:
            # If all else fails, make a rough estimate
            font_size = font.size
            return len(text) * font_size // 2, font_size
