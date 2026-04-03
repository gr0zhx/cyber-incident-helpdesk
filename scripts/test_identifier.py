"""
Script test manual untuk IncidentIdentifierAgent.

Penggunaan:
    python scripts/test_identifier.py "Saya menerima email dari CEO meminta transfer dana"
    python scripts/test_identifier.py "Komputer saya lambat dan ada popup minta bayar Bitcoin"
    python scripts/test_identifier.py "Ada yang aneh"
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from openai import AsyncOpenAI

from app.config import get_settings
from app.agents.identifier import IncidentIdentifierAgent


async def main() -> None:
    load_dotenv()

    if len(sys.argv) < 2:
        print("Penggunaan: python scripts/test_identifier.py \"<laporan insiden>\"")
        sys.exit(1)

    report = sys.argv[1]
    settings = get_settings()

    llm_client = AsyncOpenAI(api_key=settings.openai_api_key)
    agent = IncidentIdentifierAgent(llm_client=llm_client, model=settings.openai_model)

    print(f"\nLaporan: {report}")
    print("-" * 60)

    result = await agent.classify(report)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["requires_review"]:
        print("\n[PERINGATAN] Confidence rendah — perlu review manual.")


if __name__ == "__main__":
    asyncio.run(main())
