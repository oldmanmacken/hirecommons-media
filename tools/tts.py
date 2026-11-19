import json, os, re, subprocess, sys
import numpy as np, onnxruntime as ort
from scipy.io import wavfile
D = os.path.dirname(os.path.abspath(__file__)); P = f"{D}/pp/piper_phonemize"
VOCAB = json.load(open(f"{D}/src/src/kokoro_onnx/config.json"))["vocab"]; SR = 24000
def espeak(t):
    out = subprocess.run([f"{P}/bin/espeak-ng", f"--path={P}/share", "-q", "--ipa", "-v", "en-us", t],
        capture_output=True, text=True, env={**os.environ, "LD_LIBRARY_PATH": f"{P}/lib"}).stdout
    return " ".join(out.split())
def phonemize(text):
    out = ""
    for p in re.split(r"([,.!?:;—])", text):
        if not p.strip(): continue
        if re.fullmatch(r"[,.!?:;—]", p): out = out.rstrip() + ("," if p == "—" else p) + " "
        else: out += espeak(p) + " "
    return "".join(c for c in out.strip() if c in VOCAB)
sess = ort.InferenceSession(f"{D}/kokoro-v1.0.onnx", providers=["CPUExecutionProvider"])
names = {i.name: i for i in sess.get_inputs()}; tok = "input_ids" if "input_ids" in names else "tokens"
voice = np.load(f"{D}/voices-v1.0.bin")[sys.argv[1]]
lines = json.load(open(sys.argv[2])); outdir = sys.argv[3]; os.makedirs(outdir, exist_ok=True); durs = []
for i, text in enumerate(lines):
    toks = [VOCAB[c] for c in phonemize(text)]
    sd = np.int32 if "int" in names["speed"].type else np.float32
    a = sess.run(None, {tok: np.array([[0, *toks, 0]], dtype=np.int64),
        "style": np.asarray(voice[min(len(toks), len(voice)) - 1], dtype=np.float32),
        "speed": np.array([1.0], dtype=sd)})[0].squeeze()
    idx = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, idx[0] - 1200): idx[-1] + 2400]
    wavfile.write(f"{outdir}/line{i:02d}.wav", SR, (np.clip(a, -1, 1) * 32767).astype(np.int16))
    durs.append(len(a) / SR)
json.dump(durs, open(f"{outdir}/durs.json", "w"))
