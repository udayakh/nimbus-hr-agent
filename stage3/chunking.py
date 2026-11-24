import os
import re

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "handbook.md")


def load_document(path=DATA_FILE):
    with open(path, encoding="utf-8") as f:
        return f.read()


# --- Strategy 1: Fixed-size chunks ---
# Cut every N characters. Simple, but it cuts through words and sentences.
def chunk_fixed(text, size=300):
    return [text[i : i + size] for i in range(0, len(text), size)]


# --- Strategy 2: Fixed-size chunks WITH overlap ---
# Each chunk repeats the end of the previous one, so an idea cut
# at a boundary still appears whole in at least one chunk.
def chunk_with_overlap(text, size=300, overlap=60):
    step = size - overlap
    return [text[i : i + size] for i in range(0, len(text), step)]


# --- Strategy 3: Structure-aware chunks (what we'll actually use) ---
# Respect the document's own structure: split by section heading, then
# by paragraph, and pack paragraphs together up to max_chars.
# Each chunk is prefixed with its section title and keeps metadata.
def chunk_by_structure(text, max_chars=600):
    chunks = []
    # Split on "## Heading" lines. The part before the first heading is the intro.
    parts = re.split(r"^## (.+)$", text, flags=re.MULTILINE)
    sections = [("Introduction", parts[0])] + list(zip(parts[1::2], parts[2::2]))

    for title, body in sections:
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip() and not p.startswith("# ")]
        current = ""
        for para in paragraphs:
            if current and len(current) + len(para) + 2 > max_chars:
                chunks.append({"text": f"{title}\n{current}", "section": title})
                current = para
            else:
                current = f"{current}\n\n{para}" if current else para
        if current:
            chunks.append({"text": f"{title}\n{current}", "section": title})

    return chunks


def show(label, chunks, n=3):
    print(f"\n{'=' * 60}\n{label}: {len(chunks)} chunks\n{'=' * 60}")
    for i, c in enumerate(chunks[:n]):
        text = c["text"] if isinstance(c, dict) else c
        print(f"--- chunk {i} ({len(text)} chars) ---")
        print(text)
    if len(chunks) > n:
        print(f"... and {len(chunks) - n} more")


if __name__ == "__main__":
    doc = load_document()
    print(f"Loaded handbook: {len(doc)} characters, ~{len(doc) // 4} tokens")

    show("STRATEGY 1: Fixed size (300 chars)", chunk_fixed(doc), n=2)
    show("STRATEGY 2: Fixed size + 60 char overlap", chunk_with_overlap(doc), n=2)

    smart = chunk_by_structure(doc)
    show("STRATEGY 3: Structure-aware (by section + paragraph)", smart, n=3)

    print("\nSections covered:", sorted({c["section"] for c in smart}))
