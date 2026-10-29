"""Quick check: can this computer reach Gemma 4 with your key?

Run:  python check_ai.py
"""

import os

from dotenv import load_dotenv

load_dotenv()
key = os.environ.get("GEMINI_API_KEY", "").strip()

if not key or key == "paste-your-key-here":
    raise SystemExit("❌ No key found. Open .env and set GEMINI_API_KEY=your-key")
print(f"✅ Key loaded (ends in ...{key[-4:]})")

from google import genai  # noqa: E402

client = genai.Client(api_key=key)

print("\nGemma models your key can use:")
try:
    names = [m.name for m in client.models.list() if "gemma" in m.name.lower()]
    print("  " + ("\n  ".join(names) if names else "(none listed)"))
except Exception as e:
    print(f"  couldn't list models: {type(e).__name__}: {getattr(e, 'code', '')}")

for model in [os.environ.get("GEMMA_MODEL", "gemma-4-26b-a4b-it"), "gemma-4-31b-it"]:
    print(f"\nTrying {model} ...")
    try:
        r = client.models.generate_content(model=model, contents="Say hi in 3 words.")
        print(f"  ✅ Works! Reply: {r.text.strip()[:80]}")
        print(f"\nAll good. If this isn't the default, add GEMMA_MODEL={model} to .env")
        break
    except Exception as e:
        msg = str(e).replace(key, "***")[:300]
        print(f"  ❌ {type(e).__name__} (code {getattr(e, 'code', '?')}): {msg}")
