# The yue2.cpp engine: yue2.cpp's server (github.com/ServeurpersoCom/yue2.cpp) on CUDA, the
# render engine for smaller GPUs.  Pinned to the commit it was tested against, with the
# patches in patches/ on top (plan-only jobs, per-half LoRA strengths, more LoRA layouts,
# adapter rescans, device memory).  The GGUF models are not baked in: they are bind mounted
# at /models, and the LoRA folder at /adapters.
ARG CUDA_VERSION=13.0.3

FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu24.04 AS build
RUN apt-get update && apt-get install -y --no-install-recommends cmake build-essential git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ARG YUE2CPP_REF=8af01740686824ffd4a1839a457954f42e2a8ce7
WORKDIR /src
RUN git clone --quiet https://github.com/ServeurpersoCom/yue2.cpp.git . \
    && git checkout --quiet ${YUE2CPP_REF} \
    && git submodule update --quiet --init --recursive
COPY patches/ /patches/
RUN git -c user.name=build -c user.email=build@localhost am --quiet /patches/*.patch
# Empty keeps upstream's list of GPU architectures; one (89-real for an RTX 40) builds much
# faster.  GGML_NATIVE=OFF: the binary is not tied to the build machine's CPU.  A build has no
# GPU driver, so libcuda's symbols are left for the runtime to resolve (as llama.cpp does).
ARG CUDA_ARCHITECTURES=""
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DGGML_NATIVE=OFF \
        ${CUDA_ARCHITECTURES:+-DCMAKE_CUDA_ARCHITECTURES=${CUDA_ARCHITECTURES}} \
        -DCMAKE_EXE_LINKER_FLAGS=-Wl,--allow-shlib-undefined \
    && cmake --build build --config Release -j "$(nproc)" --target yue-server \
    && mkdir -p /out/lib \
    && cp build/yue-server /out/ \
    && find build -name '*.so*' -exec cp -a {} /out/lib/ \;

FROM nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu24.04
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /out/lib/ /usr/local/lib/
COPY --from=build /out/yue-server /usr/local/bin/yue-server
RUN ldconfig
EXPOSE 8087
HEALTHCHECK --interval=30s --timeout=5s CMD curl -fs http://127.0.0.1:8087/health || exit 1
ENTRYPOINT ["yue-server", "--host", "0.0.0.0", "--port", "8087"]
