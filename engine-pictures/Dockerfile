# Pictures beside the yue2.cpp engine: stable-diffusion.cpp's server (github.com/leejet/stable-diffusion.cpp)
# on CUDA, which runs FLUX.2 klein from the same files the ComfyUI engine uses.  Pinned to the commit it was
# tested against.  The models are bind mounted at /models; nothing is baked in.
ARG CUDA_VERSION=13.0.3

FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu24.04 AS build
# sd-server embeds its web page at build time, so the build needs Node and pnpm.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential git cmake ca-certificates curl gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_24.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y --no-install-recommends nodejs && npm install -g pnpm@10.15.1 \
    && rm -rf /var/lib/apt/lists/*
ARG SDCPP_REF=0a067120b388bfefb9a87b96960cb548b97e9157
WORKDIR /src
RUN git clone --quiet https://github.com/leejet/stable-diffusion.cpp.git . \
    && git checkout --quiet ${SDCPP_REF} \
    && git submodule update --quiet --init --recursive
# Empty keeps upstream's list of GPU architectures; one (89-real for an RTX 40) builds much faster.
ARG CUDA_ARCHITECTURES=""
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DSD_CUDA=ON -DGGML_NATIVE=OFF \
        ${CUDA_ARCHITECTURES:+-DCMAKE_CUDA_ARCHITECTURES=${CUDA_ARCHITECTURES}} \
        -DCMAKE_EXE_LINKER_FLAGS=-Wl,--allow-shlib-undefined \
    && cmake --build build --config Release -j "$(nproc)" --target sd-server \
    && mkdir -p /out/lib && cp build/bin/sd-server /out/ \
    && find build -name '*.so*' -exec cp -a {} /out/lib/ \;

FROM nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu24.04
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 curl && rm -rf /var/lib/apt/lists/*
COPY --from=build /out/lib/ /usr/local/lib/
COPY --from=build /out/sd-server /usr/local/bin/sd-server
RUN ldconfig
EXPOSE 8088
ENTRYPOINT ["sd-server", "--listen-ip", "0.0.0.0", "--listen-port", "8088"]
