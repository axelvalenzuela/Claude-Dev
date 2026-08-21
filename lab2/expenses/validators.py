"""Generic file-upload validators for TravelDocument.file.

PDF-specific validation (page count) lives in pdf_analysis.py instead,
since it needs pypdf to actually open the file — keeping it out of this
module means validating a plain file size never pulls that dependency in.
"""
from django.core.exceptions import ValidationError

MAX_FILE_SIZE_MB = 10


def validate_file_size(file):
    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"File exceeds the maximum size of {MAX_FILE_SIZE_MB} MB.")
