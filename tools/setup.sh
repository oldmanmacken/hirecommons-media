#!/usr/bin/env bash
# One-time setup per session: downloads the free offline voice (Kokoro) into ~/tts.
# Needs onnxruntime, numpy, scipy, Pillow and ffmpeg (normally preinstalled). Downloads come from GitHub only.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p ~/tts && cd ~/tts
[ -f kokoro-v1.0.onnx ] || curl -sSL -O https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
[ -f voices-v1.0.bin ]  || curl -sSL -O https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
[ -d src ] || git clone -q --depth 1 https://github.com/thewh1teagle/kokoro-onnx.git src
if [ ! -d pp/piper_phonemize ]; then
  curl -sSL -o pp.tgz https://github.com/rhasspy/piper-phonemize/releases/download/2023.11.14-4/piper-phonemize_linux_x86_64.tar.gz
  mkdir -p pp && tar xzf pp.tgz -C pp && chmod +x pp/piper_phonemize/bin/*
fi
cp "$HERE/tts.py" ~/tts/tts.py
echo "voice setup ok"
