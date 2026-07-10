"""Render document previews to images for vision-model reading."""

from __future__ import annotations

import base64
import textwrap
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from backend.config import settings
from backend.schemas import DocumentAsset, DocumentPacket


@dataclass(frozen=True)
class RenderedPage:
    file_name: str
    category: str
    page_number: int
    data_url: str


def render_packet_for_vision(packet: DocumentPacket) -> list[RenderedPage]:
    pages: list[RenderedPage] = []
    for asset in packet.all_assets():
        pages.extend(render_asset_for_vision(asset))
    return pages


def render_asset_for_vision(asset: DocumentAsset) -> list[RenderedPage]:
    text = asset.extracted_text or f"No extracted preview text available for {asset.file_name}."
    chunks = _chunk_text(text, chars_per_page=2800)[: settings.max_vision_pages_per_document]
    rendered: list[RenderedPage] = []
    for index, chunk in enumerate(chunks, start=1):
        rendered.append(
            RenderedPage(
                file_name=asset.file_name,
                category=asset.category.value,
                page_number=index,
                data_url=_render_text_page(asset, chunk, index),
            )
        )
    return rendered


def vision_input_items(packet: DocumentPacket, task: str) -> list[dict]:
    pages = render_packet_for_vision(packet)
    content: list[dict] = [
        {
            "type": "input_text",
            "text": (
                f"{task}\n\n"
                f"Billing type: {packet.billing_type}\n"
                "Read the following rendered document preview images. "
                "Each image header includes file name, category, and page number. "
                "Extract only source-backed facts that are visible in the images."
            ),
        }
    ]
    for page in pages:
        content.append(
            {
                "type": "input_text",
                "text": f"Next image: {page.file_name} | {page.category} | page {page.page_number}",
            }
        )
        content.append({"type": "input_image", "image_url": page.data_url, "detail": "high"})
    return [{"role": "user", "content": content}]


def _render_text_page(asset: DocumentAsset, text: str, page_number: int) -> str:
    width, height = 1400, 1800
    margin = 70
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=28)
    mono = ImageFont.load_default(size=24)

    header = [
        f"File: {asset.file_name}",
        f"Category: {asset.category.value}",
        f"Billing type: {asset.billing_type or 'unknown'}",
        f"Preview page: {page_number}",
    ]
    y = margin
    for line in header:
        draw.text((margin, y), line, fill="#0f172a", font=font)
        y += 38
    y += 20
    draw.line((margin, y, width - margin, y), fill="#cbd5e1", width=3)
    y += 34

    for raw_line in text.splitlines():
        wrapped = textwrap.wrap(raw_line, width=90) or [""]
        for line in wrapped:
            if y > height - margin:
                break
            draw.text((margin, y), line, fill="#111827", font=mono)
            y += 31
        if y > height - margin:
            break

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _chunk_text(text: str, chars_per_page: int) -> list[str]:
    if len(text) <= chars_per_page:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chars_per_page])
        start += chars_per_page
    return chunks
