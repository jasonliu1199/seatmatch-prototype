"""Record stage.html via CDP screencast frames, then encode an MP4 with timestamps.
usage: python3 record.py <site dir> <out.mp4>"""
import asyncio, base64, os, subprocess, sys, threading, http.server, functools, shutil
from playwright.async_api import async_playwright
import imageio_ffmpeg

site, out = sys.argv[1], sys.argv[2]
page_name = sys.argv[3] if len(sys.argv) > 3 else 'stage.html'
W, H = (int(v) for v in (sys.argv[4] if len(sys.argv) > 4 else '1080x1920').split('x'))
frames_dir = os.path.join(os.path.dirname(out), 'frames'); shutil.rmtree(frames_dir, ignore_errors=True); os.makedirs(frames_dir)
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8765), functools.partial(http.server.SimpleHTTPRequestHandler, directory=site))
threading.Thread(target=srv.serve_forever, daemon=True).start()

async def main():
    frames = []
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome')
        page = await b.new_page(viewport={'width': W, 'height': H})
        await page.goto('http://127.0.0.1:8765/' + page_name); await page.wait_for_load_state('networkidle'); await page.wait_for_timeout(1200)
        cdp = await page.context.new_cdp_session(page)
        async def on_frame(e):
            frames.append((e['metadata']['timestamp'], e['data']))
            await cdp.send('Page.screencastFrameAck', {'sessionId': e['sessionId']})
        cdp.on('Page.screencastFrame', lambda e: asyncio.ensure_future(on_frame(e)))
        await cdp.send('Page.startScreencast', {'format': 'jpeg', 'quality': 92, 'maxWidth': W, 'maxHeight': H, 'everyNthFrame': 1})
        await page.evaluate('START()')
        await page.wait_for_function('window.DONE === true', timeout=120000, polling=200)
        await cdp.send('Page.stopScreencast'); await b.close()
    return frames

frames = asyncio.run(main()); srv.shutdown()
t0 = frames[0][0]
lines = []
for i, (ts, data) in enumerate(frames):
    fn = os.path.join(frames_dir, f'f{i:05d}.jpg'); open(fn, 'wb').write(base64.b64decode(data))
    nxt = frames[i + 1][0] if i + 1 < len(frames) else ts + 0.5
    lines.append(f"file '{fn}'\nduration {max(nxt - ts, 0.001):.4f}")
lines.append(f"file '{fn}'")
lst = os.path.join(frames_dir, 'list.txt'); open(lst, 'w').write('\n'.join(lines))
ff = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-vf', f'fps=30,scale={W}:{H},format=yuv420p',
                '-c:v', 'libx264', '-crf', '18', '-preset', 'slow', '-movflags', '+faststart', out], check=True)
print(len(frames), 'frames', round(frames[-1][0] - t0, 1), 's')
