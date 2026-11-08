# The voice service: trains a recorded voice (RVC v2) and converts a take's vocal to it, with a BS-Roformer
# separator in front.  Its own image because RVC pins an older transformers, numpy and librosa than ComfyUI's.
# The models it needs live in models/voice on the host (scripts/fetch-models.sh --voice).
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg build-essential \
    && rm -rf /var/lib/apt/lists/*

# RVC, MIT.  Pinned: its training scripts are driven by argument position, so a newer commit can break them.
ARG RVC_COMMIT=81eed5e8f68b6bed1789f682fe78cdd324495afc
# Our unchanged mirror first (a repository a build needs can vanish), RVC-Project's own after: the same commit.
RUN (git clone https://github.com/yeufonic/Retrieval-based-Voice-Conversion-WebUI /opt/rvc \
     || git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI /opt/rvc) \
    && git -C /opt/rvc checkout "$RVC_COMMIT" && rm -rf /opt/rvc/.git

ARG TORCH_CUDA=cu128
RUN pip install --no-cache-dir torch==2.7.1 torchaudio==2.7.1 --index-url "https://download.pytorch.org/whl/${TORCH_CUDA}"
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY server.py /opt/voice/server.py
# RVC's scripts import each other from the repository root; the script's own folder must not shadow `train`.
ENV PYTHONPATH=/opt/rvc PYTHONSAFEPATH=1 RVC_CUDA_GRAPH=0 PYTHONUNBUFFERED=1
WORKDIR /opt/rvc
EXPOSE 8190
CMD ["python", "/opt/voice/server.py"]
