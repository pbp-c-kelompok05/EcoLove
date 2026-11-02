"""Normalize comment uploads before they reach storage (Pillow is already used)."""
from io import BytesIO
import uuid
import warnings

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageOps, UnidentifiedImageError


MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
MAX_IMAGE_SIDE = 1024


def square_comment_image(upload):
    if upload.size > MAX_IMAGE_BYTES:
        raise ValidationError('Ukuran foto maksimal 5 MB.', code='image_size')
    try:
        upload.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(upload) as source:
                if source.format not in {'JPEG', 'PNG', 'WEBP'}:
                    raise ValidationError('Gunakan foto JPG, PNG, atau WebP.', code='image_format')
                if source.width * source.height > MAX_IMAGE_PIXELS:
                    raise ValidationError('Resolusi foto maksimal 20 megapiksel.', code='image_resolution')
                if getattr(source, 'is_animated', False):
                    raise ValidationError('Gunakan foto diam, bukan gambar animasi.', code='image_animation')
                oriented = ImageOps.exif_transpose(source)
                side = min(oriented.width, oriented.height, MAX_IMAGE_SIDE)
                square = ImageOps.fit(oriented, (side, side), method=Image.Resampling.LANCZOS)
                # Flatten transparency and create a fresh image without EXIF metadata.
                rgba = square.convert('RGBA')
                result = Image.new('RGB', square.size, '#faf8f1')
                result.paste(rgba, mask=rgba.getchannel('A'))
                output = BytesIO()
                result.save(output, format='JPEG', quality=88, optimize=True)
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError,
            Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError('Foto tidak dapat dibaca. Pilih gambar lain.', code='invalid_image') from exc
    finally:
        upload.seek(0)
    return SimpleUploadedFile(f'{uuid.uuid4().hex}.jpg', output.getvalue(), content_type='image/jpeg')
