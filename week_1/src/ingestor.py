"""Bronze layer: decode raw MHTML snapshots (0_source) into plain HTML (1_bronze)."""

import email
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_html_from_mhtml(mhtml_bytes: bytes) -> bytes | None:
    """Return the first text/html part of an MHTML document, or None if there isn't one.

    MHTML is a MIME multipart archive (the same format as an email), so the stdlib
    `email` parser can walk its parts and decode quoted-printable/base64 for us.
    """
    msg = email.message_from_bytes(mhtml_bytes)
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            return part.get_payload(decode=True)
    return None


def ingest_all_mhtml(input_dir: Path, output_dir: Path) -> dict[str, int]:
    """Decode every *.mhtml in input_dir into output_dir/<stem>.html."""
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {"total": 0, "extracted": 0, "failed": 0}
    for mhtml_file in sorted(input_dir.glob("*.mhtml")):
        stats["total"] += 1
        try:
            html = extract_html_from_mhtml(mhtml_file.read_bytes())
            if html is None:
                raise ValueError("no text/html part found")
            (output_dir / f"{mhtml_file.stem}.html").write_bytes(html)
            stats["extracted"] += 1
            logger.debug("Extracted %s", mhtml_file.name)
        except Exception as exc:  # noqa: BLE001 - one bad file must not stop the batch
            stats["failed"] += 1
            logger.warning("Failed %s: %s", mhtml_file.name, exc)

    logger.info(
        "Bronze summary: total=%(total)d extracted=%(extracted)d failed=%(failed)d",
        stats,
    )
    return stats
