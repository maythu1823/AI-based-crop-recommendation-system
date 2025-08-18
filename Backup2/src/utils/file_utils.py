# src/utils/file_utils.py
import base64

def get_image_as_base64(image_path):
    """
    Reads an image file and returns a Base64 encoded string.
    If the image cannot be loaded, returns None.
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return f"data:image/jpeg;base64,{encoded_string}"
    except Exception:
        return None
