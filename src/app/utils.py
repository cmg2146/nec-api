import os
import uuid
import mimetypes

import aiofiles
import aiofiles.os as aioos
from fastapi import UploadFile, HTTPException, status
from pydantic import BaseModel, ByteSize

UPLOAD_CHUNK_SIZE = 1024 #1KB

class _ByteSize(BaseModel):
    size: ByteSize

def format_byte_size(
    size_in_bytes: int
):
    """Returns a string with the byte size in human readable format"""
    byte_size_model = _ByteSize(size=size_in_bytes)

    return byte_size_model.size.human_readable(decimal=True)

def validate_file_extension(
    file: UploadFile,
    validate_content_type: bool,
    *valid_extensions: str
):
    """Validates extension of uploaded file.

    Parameters:
        file:
            The uploaded file (FastAPI UploadFile).
        validate_content_type:
            Indicates if the content type should also be validated (bool). The
            content type is validated by using mimetypes.guess_type using the
            file's extension.
        *valid_extensions:
            One or more valid extension(s) (str).

    If validation fails, an HTTPException with a 422 status code will be raised.

    Returns the case-insensitive extension of the file, if validation passed.
    """
    if not valid_extensions:
        raise ValueError(valid_extensions)

    extension = os.path.splitext(file.filename)[-1].casefold()
    content_type = file.content_type.casefold()
    valid_extensions_lower = [x.casefold() for x in valid_extensions]

    if extension not in valid_extensions_lower:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File extension is invalid. Must be one of {valid_extensions_lower}."
        )

    if validate_content_type:
        expected_content_type = mimetypes.guess_type(extension)[0].casefold()
        if content_type != expected_content_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"File content type is invalid, expected {expected_content_type}."
            )

    return extension

def generate_random_filename(
    current_filename: str
) -> str:
    """Generates a random filename, using a GUID, from an input filename or filepath."""
    extension = os.path.splitext(current_filename)[-1]
    return f'{uuid.uuid4()}{extension.lower()}'

async def store_uploaded_file(
    file: UploadFile,
    directory: str,
    max_size_bytes: int | None
) -> str:
    """Store a file uploaded through an API endpoint into the specified directory.

    If max_size_bytes is not None, an exception will be raised if the file exceeds
    the limit.

    Returns the path to the stored file.
    """
    file_name = generate_random_filename(file.filename)
    file_path = os.path.join(directory, file_name)

    num_bytes_read = 0
    try:
        async with aiofiles.open(file_path, 'wb') as dest:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                num_bytes_read += len(chunk)
                if max_size_bytes and num_bytes_read > max_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"The file exceeds the max size of {format_byte_size(max_size_bytes)}"
                    )

                await dest.write(chunk)
    except HTTPException:
        await aioos.unlink(file_path)
        raise

    return file_path
