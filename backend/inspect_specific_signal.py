
import asyncio
from quantix_core.database.connection import db

async def inspect_signal(sid):
    print(f"Inspecting Signal ID: {sid}")
    res = db.client.table('fx_signals').select('*').eq('id', sid).execute()
    if res.data:
        s = res.data[0]
        print(f"Asset: {s.get('asset')}")
        print(f"Direction: {s.get('direction')}")
        print(f"Status: {s.get('status')}")
        print(f"AI Confidence: {s.get('ai_confidence')}")
        print(f"Release Confidence: {s.get('release_confidence')}")
        print(f"Refinement Reason: {s.get('refinement_reason')}")
        print(f"Generated At: {s.get('generated_at')}")
    else:
        print("Signal not found")

if __name__ == "__main__":
    import sys
    sid = "a58bffcf-e50e-4324-9b96-48b9c58bf48b"
    asyncio.run(inspect_signal(sid))
