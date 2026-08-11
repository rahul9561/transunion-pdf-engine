import json
from pathlib import Path

from transunion_pdf_engine.generator import generate_report


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "input" / "transunion_response.json"
OUTPUT_FILE = BASE_DIR / "output" / "reportnew.pdf"


def main():
    print("=" * 60)
    print("TRANSUNION PDF ENGINE TEST")
    print("=" * 60)

    # Check JSON
    if not INPUT_FILE.exists():
        print(f"❌ JSON file not found: {INPUT_FILE}")
        return

    # Create output directory
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Load JSON
    print(f"\n📄 Loading: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_json = json.load(f)

    print("✅ JSON loaded")

    # Generate PDF
    print("\n🔄 Generating PDF...")

    pdf_path = generate_report(
        raw_json,
        str(OUTPUT_FILE),
        mask_account_numbers=False,
    )

    print("\n" + "=" * 60)
    print("✅ PDF GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"📄 PDF: {pdf_path}")
    print(f"📦 Size: {OUTPUT_FILE.stat().st_size / 1024:.2f} KB")


if __name__ == "__main__":
    main()