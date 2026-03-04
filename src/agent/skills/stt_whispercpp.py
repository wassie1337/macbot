from __future__ import annotations

import asyncio
from pathlib import Path

from telegram import Update

from agent.skills import SkillResult


class WhisperCppSTTSkill:
    name = "stt_whispercpp"

    def __init__(self, enabled: bool, whisper_bin: str, model: str, tmp_dir: str, timeout_sec: int) -> None:
        self.enabled = enabled
        self.whisper_bin = whisper_bin
        self.model = model
        self.tmp_dir = Path(tmp_dir)
        self.timeout_sec = timeout_sec
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def can_handle(self, update: Update, state: dict[str, str]) -> bool:
        if not self.enabled:
            return False
        return bool(update.message and update.message.voice)

    async def run(self, update: Update, state: dict[str, str], context) -> SkillResult:
        if not update.message or not update.message.voice:
            raise ValueError("No voice message found")

        voice = update.message.voice
        tg_file = await context.bot.get_file(voice.file_id)
        ogg_path = self.tmp_dir / f"{voice.file_unique_id}.ogg"
        wav_path = self.tmp_dir / f"{voice.file_unique_id}.wav"

        await tg_file.download_to_drive(custom_path=str(ogg_path))

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(ogg_path),
            "-ar",
            "16000",
            "-ac",
            "1",
            str(wav_path),
        ]
        await self._run_subprocess(ffmpeg_cmd, self.timeout_sec)

        whisper_cmd = [
            self.whisper_bin,
            "-m",
            self.model,
            "-f",
            str(wav_path),
            "-otxt",
            "-of",
            str(wav_path.with_suffix("")),
        ]
        await self._run_subprocess(whisper_cmd, self.timeout_sec)

        transcript_path = wav_path.with_suffix(".txt")
        transcript = transcript_path.read_text(encoding="utf-8").strip()
        if not transcript:
            transcript = "[geen transcript]"

        for path in (ogg_path, wav_path, transcript_path):
            if path.exists():
                path.unlink()

        return SkillResult(text=transcript, prefix="🎤 Transcript:\n")

    async def _run_subprocess(self, cmd: list[str], timeout: int) -> None:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError as exc:
            proc.kill()
            raise RuntimeError(f"Command timed out: {' '.join(cmd)}") from exc
        if proc.returncode != 0:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}")
