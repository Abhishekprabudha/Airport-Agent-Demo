import asyncio
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parents[1]
TEXT_PATH = ROOT / "assets" / "audio" / "narration.txt"
OUT_PATH = ROOT / "assets" / "audio" / "airport-agent-narration.mp3"
VOICE = "en-US-GuyNeural"
RATE = "-2%"
MAX_RETRIES = 4


async def save_with_retries(text: str):
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
            await communicate.save(str(OUT_PATH))
            return
        except Exception as exc:
            last_exc = exc
            if attempt == MAX_RETRIES:
                break
            wait_s = 2 ** (attempt - 1)
            print(f"Narration attempt {attempt}/{MAX_RETRIES} failed: {exc}. Retrying in {wait_s}s...")
            await asyncio.sleep(wait_s)
    if last_exc is not None:
        status = getattr(last_exc, "status", None)
        msg = str(last_exc).lower()
        if status == 403 or "name resolution" in msg or "cannot connect to host" in msg:
            print(
                "Warning: Edge TTS is unreachable or rejected in this environment "
                "(for example HTTP 403, DNS, or outbound network limits). "
                "Continuing without generating narration MP3."
            )
            return False
    raise RuntimeError(
        "Unable to generate narration via Edge TTS after multiple retries. "
        "Check DNS/network access to speech.platform.bing.com:443."
    ) from last_exc


async def main():
    text = TEXT_PATH.read_text(encoding="utf-8")
    ok = await save_with_retries(text)
    if ok is False:
        print("No narration file generated; downstream render can proceed silently.")
        return
    print(f"Narration written to {OUT_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
