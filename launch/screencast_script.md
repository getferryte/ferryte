# Screencast cut script

**Duration target:** 75–90 seconds.
**Resolution:** 1920 × 1080 (downscale to 1080 × 1080 square for X autoplay
if you have time; otherwise 1080p landscape is fine).
**Tooling:** QuickTime Screen Recording (macOS) → CleanShot / iMovie /
Descript for trims and captions. Or `asciinema` for terminal-only.
**Frame rate:** 30 fps. 60 if your editor is fast.

**Setup once before recording:**

1. Close every app except Terminal and a browser window. Black wallpaper.
2. Terminal: Geist Mono, size 18, 100% transparency, hide tab bar.
3. Window dimensions: 1280 × 720 (centred — leave breathing room around it).
4. `cd /Users/pranavchahal/Documents/recall && source .venv/bin/activate`
5. `unset RECALL_STATE_DIR FERRYTE_STATE_DIR`
6. Clear the terminal. Increase font size so commands are readable when
   downscaled.
7. Have ferryte.dev open in a fresh browser tab — do not load it during
   the take.

**Recording pass:** record the whole thing in one take if you can. If not,
record in two halves (terminal → dashboard) and cut on the `[transition]`
beat below. **No talking.** Captions only.

---

## Beat sheet (seconds : action : on-screen caption)

| Time | What viewer sees | Caption (Geist Mono, 24pt, bottom-left, royal blue) |
|---|---|---|
| 00:00 | Black frame fade-in. Wordmark "ferryte." appears, royal-blue dot pulses once. | — |
| 00:02 | Cut to terminal. Prompt waiting. | `the leak (no test in place)` |
| 00:04 | Type, slowly: `python demo/multi_tenant_leak.py` — hit enter. | — |
| 00:06 | Output prints the "Act 1" panel: two tenants seed memories, Acme deletes its secret, agent answers and still leaks `ORION-DELTA-77`. | Hold caption: `the leak (no test in place)` |
| 00:20 | Slow stop on the red "leak" panel. Hold for 1.5 seconds. | `agent leaked revoked data` |
| 00:22 | Output continues automatically: "Act 2" — `ferryte` turns on, instruments, runs scenarios. | `ferryte on. same agent. same code.` |
| 00:32 | The scenario results table prints. Three FAILs in red. | `caught: 3 leaks. exit code 1.` |
| 00:42 | The "report json/html" panel prints. The cursor pauses. | — |
| 00:44 | **[transition]** Cut to browser. ferryte.dev/app loads. The dashboard hero fills the frame. "Forgetting failed." in 88px. | `verdict at a glance` |
| 00:48 | Scroll slowly. The 4 huge stat numbers come into frame: Leaks · Partial · Verified · Blind spots. | — |
| 00:54 | Continue scrolling. The 4 scenario rows are visible. Source revocation: FAILED. | `every scenario. every artifact id.` |
| 01:00 | Scroll into the AWS quote section. Hold on the blockquote for 2 seconds. | `the platform vendors said it first.` |
| 01:08 | Cut back to terminal. Show: `ferryte test --scenario source-revocation` running, then exit code 1 printed. | `non-zero exit = build break.` |
| 01:18 | Cut to black. Wordmark again. Caption fills the screen: | `ferryte.dev · pip install ferryte` |
| 01:23 | Hold black + wordmark for 2 seconds. Fade out. | — |
| 01:25 | End. | — |

---

## What to do in post

1. **Compress aggressively.** Target ≤ 8 MB so X plays it inline without
   asking the viewer to tap. ffmpeg one-liner:

   ```bash
   ffmpeg -i raw.mov -vcodec libx264 -crf 24 -preset slow \
     -vf "scale='min(1080,iw)':-2,format=yuv420p" \
     -an screencast.mp4
   ```

2. **No music.** Silence is the brand. (If a sponsor or a future spot needs
   audio, use one piano note on the cut transitions — no full track.)

3. **Captions burned in**, not as SRT. X strips them otherwise.

4. **Cover frame.** Pick the frame at 00:46 (the "Forgetting failed." hero)
   as the static cover.

---

## Backup plan: animated GIF

If you cannot record the video the day of the launch, an animated GIF of the
terminal portion (Act 1 + Act 2) is the minimum viable demo. Tools:

- [`vhs`](https://github.com/charmbracelet/vhs) — script-driven terminal
  recordings, perfect frame timing. Write a `demo.tape` file, run `vhs`,
  get a .gif.
- `asciinema rec` then `agg` for terminal → GIF.

A clean GIF beats a polished video that misses the launch window.
