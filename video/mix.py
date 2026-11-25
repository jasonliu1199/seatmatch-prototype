"""Synthesize an original upbeat background track, lay the voice clips at the scene marks, duck the music under speech.
usage: python3 mix.py <video.mp4> <timing.json> <vo dir> <out.mp4>"""
import json, sys, wave, subprocess
import numpy as np
import imageio_ffmpeg

video, timing, vodir, out = sys.argv[1:5]
SR = 48000
tm = json.load(open(timing))
L = tm['end'] - tm['t0'] + 0.3
N = int(L * SR)
t = np.arange(N) / SR

def note(m): return 440 * 2 ** ((m - 69) / 12)
BPM = 104; beat = 60 / BPM; bar = beat * 4
# C - G - Am - F, voiced around middle C
chords = [[48, 55, 60, 64], [43, 55, 59, 62], [45, 57, 60, 64], [41, 57, 60, 65]]

def env_adsr(n, a, r):
    e = np.ones(n); ai = int(a * SR); ri = int(r * SR)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if ri: e[-ri:] *= np.linspace(1, 0, ri)
    return e

pad = np.zeros(N); arp = np.zeros(N); bass = np.zeros(N); drums = np.zeros(N)
nbars = int(np.ceil(L / bar))
rng = np.random.default_rng(7)
for b in range(nbars):
    ch = chords[b % 4]; s0 = int(b * bar * SR); n = min(int(bar * SR), N - s0)
    if n <= 0: break
    tt = np.arange(n) / SR
    # warm pad: detuned sines with a soft second harmonic
    p = sum(np.sin(2 * np.pi * note(m) * d * tt) + .25 * np.sin(4 * np.pi * note(m) * d * tt) for m in ch[1:] for d in (1, 1.004))
    pad[s0:s0 + n] += p * env_adsr(n, .5, .5) * .05
    # bass on beats 1 and 3
    for k in (0, 2):
        bs = s0 + int(k * beat * SR); bn = min(int(beat * 1.8 * SR), N - bs)
        if bn > 0:
            bt = np.arange(bn) / SR
            bass[bs:bs + bn] += np.sin(2 * np.pi * note(ch[0] - 12) * bt) * np.exp(-bt * 2.5) * .32
    # marimba-like eighth-note arpeggio from bar 2
    if b >= 1:
        seq = [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 24, ch[3] + 12, ch[2] + 12, ch[3] + 12]
        for k, m in enumerate(seq):
            a0 = s0 + int(k * beat / 2 * SR); an = min(int(.45 * SR), N - a0)
            if an > 0:
                at = np.arange(an) / SR; f = note(m)
                arp[a0:a0 + an] += (np.sin(2 * np.pi * f * at) + .3 * np.sin(2 * np.pi * 4 * f * at) * np.exp(-at * 30)) * np.exp(-at * 9) * .12
    # soft kick on every beat, hats on off-beats, from bar 2
    if b >= 1 and b < nbars - 1:
        for k in range(4):
            ks = s0 + int(k * beat * SR); kn = min(int(.18 * SR), N - ks)
            if kn > 0:
                kt = np.arange(kn) / SR
                drums[ks:ks + kn] += np.sin(2 * np.pi * (50 + 90 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 18) * .45
            hs = ks + int(beat / 2 * SR); hn = min(int(.05 * SR), N - hs)
            if hn > 0 and b >= 2:
                hnz = rng.standard_normal(hn); hnz = np.diff(hnz, prepend=0)
                drums[hs:hs + hn] += hnz * np.exp(-np.arange(hn) / SR * 80) * .05

def delay(x, sec, fb, mix):
    d = int(sec * SR); y = x.copy()
    for i in range(1, 5):
        y[d * i:] += x[:-d * i] * (fb ** i) * mix
    return y
music = delay(pad + arp, beat * .75, .45, .6) + bass + drums
music = np.tanh(music * 1.2) / 1.2
fade = np.ones(N); fi = int(1.0 * SR); fo = int(2.2 * SR)
fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
music *= fade

# voice clips at the scene marks
voice = np.zeros(N)
for i, m in enumerate(tm['marks']):
    w = wave.open(f'{vodir}/v{i}.wav'); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2).mean(1) / 32768
    s0 = int((m - tm['t0'] + .15) * SR); n = min(len(x), N - s0)
    voice[s0:s0 + n] += x[:n]

# duck the music while someone speaks
lvl = np.abs(voice); k = int(.03 * SR)
lvl = np.convolve(lvl, np.ones(k) / k, mode='same')
target = np.where(lvl > .01, .32, 1.0)
k2 = int(.3 * SR)
g = np.convolve(target, np.ones(k2) / k2, mode='same')  # centred window: the duck starts a little before speech
mixd = music * .55 * g + voice * 1.0
mixd /= max(1e-6, np.abs(mixd).max()) / .89
stereo = np.stack([mixd, mixd], 1)
pcm = (stereo * 32767).astype(np.int16)
wav = out + '.wav'
with wave.open(wav, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
ff = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff, '-y', '-loglevel', 'error', '-i', video, '-i', wav, '-map', '0:v', '-map', '1:a', '-vf', 'scale=out_range=tv,format=yuv420p', '-c:v', 'libx264', '-crf', '23', '-preset', 'slow',
                '-tune', 'animation', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out], check=True)
print('ok', round(L, 1), 's')
