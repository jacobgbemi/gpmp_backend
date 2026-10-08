"""
Shared file-upload validation and storage-path helpers.

Security model (see README "file security review" for the full writeup):
    1. Extension, client-reported content-type, AND the file's own magic
       bytes must all agree with one of our whitelisted categories. Any
       one of the three lying is enough to reject the upload — we never
       trust the client-reported content-type or the filename alone.
    2. The storage path is *never* derived from the client-supplied
       filename. `safe_upload_path()` builds it entirely from
       server-controlled values (a UUID and a whitelisted extension), so
       there is no path-traversal surface at all — not "sanitized," but
       structurally impossible.
    3. The original filename is preserved separately, purely for display,
       after being stripped of anything that isn't a safe display
       character.

No `libmagic`/system dependency: the signature table below covers exactly
the file kinds we whitelist, which keeps this portable and fully under
test without a native library.
"""

import re
import uuid
from dataclasses import dataclass

from rest_framework.exceptions import ValidationError


@dataclass(frozen=True)
class FileKind:
    extensions: frozenset[str]
    content_types: frozenset[str]
    # Magic-byte signatures checked at specific offsets. A kind with no
    # reliable signature (e.g. plain text) uses an empty tuple and is
    # validated by extension + content-type only.
    signatures: tuple[tuple[int, bytes], ...]


IMAGE = FileKind(
    extensions=frozenset({"jpg", "jpeg", "png", "gif"}),
    content_types=frozenset({"image/jpeg", "image/png", "image/gif"}),
    signatures=(
        (0, b"\xff\xd8\xff"),  # JPEG
        (0, b"\x89PNG\r\n\x1a\n"),  # PNG
        (0, b"GIF87a"),
        (0, b"GIF89a"),
    ),
)

VIDEO = FileKind(
    extensions=frozenset({"mp4", "mov", "avi"}),
    content_types=frozenset({"video/mp4", "video/quicktime", "video/x-msvideo"}),
    signatures=(
        (4, b"ftyp"),  # MP4 / MOV (ISO base media container)
        (0, b"RIFF"),  # AVI
    ),
)

DOCUMENT = FileKind(
    extensions=frozenset({"pdf", "docx", "xlsx", "pptx", "csv", "txt"}),
    content_types=frozenset(
        {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/csv",
            "text/plain",
            "application/octet-stream",  # browsers sometimes send this for csv/txt
        }
    ),
    signatures=(
        (0, b"%PDF-"),
        (0, b"PK\x03\x04"),  # docx/xlsx/pptx are all zip containers
        # csv/txt have no reliable magic number — extension + content-type
        # + the text-sniff in _looks_like_text() below stand in for it.
    ),
)

_TEXT_LIKE_EXTENSIONS = frozenset({"csv", "txt"})

_SAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9 ._\-]")
_MAX_DISPLAY_FILENAME_LENGTH = 200


def _extension_of(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def _looks_like_text(head: bytes) -> bool:
    """Heuristic for csv/txt: mostly printable, no NUL bytes."""
    if b"\x00" in head:
        return False
    printable = sum(1 for b in head if 9 <= b <= 13 or 32 <= b <= 126)
    return not head or printable / len(head) > 0.85


def validate_upload(uploaded_file, *, kinds: tuple[FileKind, ...], max_size_bytes: int) -> str:
    """
    Validate an uploaded file against a whitelist of FileKinds.

    Checks, in order — the first failure wins:
        1. size <= max_size_bytes
        2. extension is in some kind's whitelist
        3. the browser-reported content_type is in that same kind's whitelist
        4. the file's own magic bytes match that kind (skipped for
           text-like extensions, which have no reliable signature)

    Returns the validated (lowercased) extension on success. Raises
    rest_framework.exceptions.ValidationError on any failure.
    """
    if uploaded_file.size > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        raise ValidationError(
            {"file": f"File exceeds the maximum allowed size of {max_mb:.0f} MB."}
        )

    extension = _extension_of(uploaded_file.name or "")
    matching_kind = next((kind for kind in kinds if extension in kind.extensions), None)
    if matching_kind is None:
        allowed = sorted({ext for kind in kinds for ext in kind.extensions})
        raise ValidationError(
            {"file": f"Unsupported file type '.{extension}'. Allowed: {', '.join(allowed)}."}
        )

    content_type = (uploaded_file.content_type or "").lower()
    if content_type not in matching_kind.content_types:
        raise ValidationError(
            {"file": f"Declared content type '{content_type}' does not match a '.{extension}' file."}
        )

    uploaded_file.seek(0)
    head = uploaded_file.read(64)
    uploaded_file.seek(0)

    if extension in _TEXT_LIKE_EXTENSIONS:
        if not _looks_like_text(head):
            raise ValidationError(
                {"file": "File content does not look like plain text/CSV."}
            )
    else:
        if not any(
            head[offset : offset + len(signature)] == signature
            for offset, signature in matching_kind.signatures
        ):
            raise ValidationError(
                {"file": "File content does not match its extension — upload rejected."}
            )

    return extension


def safe_display_filename(original_name: str) -> str:
    """
    Sanitize a filename for storage as *display metadata only* — this is
    never used to build a storage path (see safe_upload_path).
    """
    name = (original_name or "upload").strip()
    name = name.replace("\x00", "")
    # Drop any directory components a hostile client might have sent.
    name = name.replace("\\", "/").rsplit("/", 1)[-1]
    name = _SAFE_FILENAME_CHARS.sub("_", name)
    return name[:_MAX_DISPLAY_FILENAME_LENGTH] or "upload"


def safe_upload_path(*, prefix: str, project_id, extension: str) -> str:
    """
    Build a storage path with zero client input in it: a fixed prefix, the
    project's own UUID, and a freshly generated UUID filename with the
    already-whitelisted extension. Structurally immune to path traversal
    — there is nothing here for a client to control.
    """
    return f"{prefix}/{project_id}/{uuid.uuid4().hex}.{extension}"
