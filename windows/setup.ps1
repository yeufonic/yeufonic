# Yeufonic for Windows: checks this PC, then fetches and sets up everything the
# installer does not carry.  Every part comes from its own publisher, pinned to a
# version and checked by sha256 where the publisher gives one.  Safe to run again:
# whatever is already in place is kept, and an interrupted download carries on.
#
#   powershell -ExecutionPolicy Bypass -File setup.ps1 -InstallDir <folder> [-Engine comfyui|yue2cpp] [-NoLyrics] [-Int8] [-Pictures] [-Loras]
#   ... -Engine           comfyui (everything, the default) or yue2cpp (yue2.cpp's server, for less video memory: no
#                         training; Gemma in Ollama and pictures in stable-diffusion.cpp beside it).  Left out, the
#                         engine settings.ini names, so Repair keeps it.
#   ... -Int8             the smaller, low-memory YuE2 model instead of the full-quality one (ComfyUI)
#   ... -Pictures         FLUX.2 klein, which draws each take's picture on this PC (about 8.3 GB)
#   ... -Loras            39 style LoRAs by their authors, CC BY-NC 4.0, gathered on Hugging Face (about 3.8 GB)
#   ... -CheckOnly        only the system check
#   ... -SkipModels       everything but the 18 GB of models (for testing)

param(
    [Parameter(Mandatory = $true)][string]$InstallDir,
    [string]$Engine = '',
    [switch]$NoLyrics,
    [switch]$Int8,
    [switch]$Pictures,
    [switch]$Loras,
    [switch]$CheckOnly,
    [switch]$SkipModels
)

# 32-bit PowerShell sees SysWOW64 where System32 should be, so it cannot find
# nvidia-smi, among other things.  Start again in the 64-bit one.
if ([Environment]::Is64BitOperatingSystem -and -not [Environment]::Is64BitProcess) {
    $native = Join-Path $env:WINDIR 'Sysnative\WindowsPowerShell\v1.0\powershell.exe'
    $again = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, '-InstallDir', $InstallDir)
    if ($Engine) { $again += @('-Engine', $Engine) }
    foreach ($flag in @('NoLyrics', 'Int8', 'Pictures', 'Loras', 'CheckOnly', 'SkipModels')) { if ($PSBoundParameters[$flag]) { $again += "-$flag" } }
    & $native @again
    exit $LASTEXITCODE
}

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # Invoke-WebRequest's bar is very slow in 5.1
$Host.UI.RawUI.WindowTitle = 'Setting up Yeufonic'

$InstallDir = [System.IO.Path]::GetFullPath($InstallDir)
$Downloads = Join-Path $InstallDir 'downloads'
$Tools = Join-Path $InstallDir 'tools'
# Which engine: the one asked for, else the one settings.ini names (Repair runs with no arguments), else ComfyUI.
$EngineKind = $Engine.Trim().ToLower()
$Engine = Join-Path $InstallDir 'engine'
$ComfyDir = Join-Path $Engine 'ComfyUI'
# The models folder is ComfyUI's for either engine, so switching engines keeps the LoRAs and the shared files.
$Models = Join-Path $ComfyDir 'models'
# yue2.cpp and the programs beside it, apart from ComfyUI, so replacing either engine leaves the other alone.
$CppDir = Join-Path $InstallDir 'engine-cpp'
$Logs = Join-Path $InstallDir 'logs'
$State = Join-Path $InstallDir 'state'
foreach ($d in @($InstallDir, $Downloads, $Tools, $Logs, $State)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
Start-Transcript -Path (Join-Path $Logs 'install.log') -Append | Out-Null
$settingsIni = Join-Path $InstallDir 'settings.ini'
if (-not $EngineKind -and (Test-Path $settingsIni)) {
    $named = Get-Content $settingsIni | Where-Object { $_ -match '^\s*engine\s*=\s*(\w+)' } | Select-Object -First 1
    if ($named) { $EngineKind = $Matches[1].ToLower() }
}
if ($EngineKind -notin @('comfyui', 'yue2cpp')) { $EngineKind = 'comfyui' }
$Cpp = $EngineKind -eq 'yue2cpp'

# A key in settings.ini's [yue2] section, set or replaced, the rest of the file left as it is.
function Set-IniValue([string]$path, [string]$key, [string]$value) {
    $lines = @(if (Test-Path $path) { Get-Content $path } else { @() })
    if (-not ($lines | Where-Object { $_ -match '^\s*\[yue2\]' })) { $lines = @('[yue2]') + $lines }
    $found = $false
    $lines = @($lines | ForEach-Object { if ($_ -match ('^\s*' + $key + '\s*=')) { $found = $true; "$key = $value" } else { $_ } })
    if (-not $found) {
        $at = [array]::IndexOf($lines, ($lines | Where-Object { $_ -match '^\s*\[yue2\]' } | Select-Object -First 1))
        $lines = @($lines[0..$at]) + @("$key = $value") + @(if ($at + 1 -lt $lines.Count) { $lines[($at + 1)..($lines.Count - 1)] } else { @() })
    }
    # UTF-8 without a byte order mark: the launcher's configparser would read one as part of "[yue2]".
    [System.IO.File]::WriteAllLines($path, [string[]]$lines)
}

# ------------------------------------------------------------------------ pins
# What was tested together.  Change one deliberately, and test again.
$Pins = @{
    ComfyCommit       = '36da3ff763687eab86a35e1019995dd1fb369b0d'   # the commit engine/Dockerfile builds
    Yue2TrainerCommit = '6a9355efff60589d93b41b569676f09d5db85d09'
    AppPython         = '3.13'
}
# ComfyUI's own Windows build: its embedded Python and CUDA torch.  The default wants
# an NVIDIA driver of 580 or later (CUDA 13.0); the cu126 build serves older ones.
$Portables = @{
    cu130 = @{ Url = 'https://github.com/Comfy-Org/ComfyUI/releases/download/v0.37.0/ComfyUI_windows_portable_nvidia.7z'
               Sha = '7805f634fab51f63a238aaf0cfe2a9833bb7c86ddfc8400a60919f44460d7d65'; Size = 1925204508 }
    cu126 = @{ Url = 'https://github.com/Comfy-Org/ComfyUI/releases/download/v0.37.0/ComfyUI_windows_portable_nvidia_cu126.7z'
               Sha = '4f8c587c8319a3595dcdc6b8fbfc7234d2d02fa6b1a328c1ab3e819c97d95fb8'; Size = 1867201814 }
}
$Files = @{
    SevenZip = @{ Url = 'https://github.com/ip7z/7zip/releases/download/26.03/7zr.exe'
                  Sha = 'ad4c82fadcbdf93c03b4fc440f300509c7d60c5c2f4d183e35d9d70d6957037d'; Size = 602624 }
    Uv       = @{ Url = 'https://github.com/astral-sh/uv/releases/download/0.12.18/uv-x86_64-pc-windows-msvc.zip'
                  Sha = 'cae6a3bc25239f83dffb467a4b180508d9da23986c04639ebfa44e43e6a84bff'; Size = 17891221 }
    Ffmpeg     = @{ Url = 'https://github.com/GyanD/codexffmpeg/releases/download/9.0.2/ffmpeg-9.0.2-essentials_build.zip'
                  Sha = '60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba'; Size = 114768076 }
    Fluidsynth = @{ Url = 'https://github.com/FluidSynth/fluidsynth/releases/download/v2.6.1/fluidsynth-v2.6.1-win10-x64-cpp11.zip'
                  Sha = 'fab7a2e4b85675b66970f97a39bbc239729c5e0f237198b5922a6a73cbc8677c'; Size = 2727529 }
}
$HF = 'https://huggingface.co'
# The yue2.cpp engine.  Its server is built for Windows with Yeufonic's patches by .github/workflows/engine-cpp-windows.yml
# and published as a pre-release named for the upstream commit and the patches; Ollama and stable-diffusion.cpp come
# from their own releases.
$CppPrograms = @{
    Server  = @{ Url = 'https://github.com/yeufonic/yeufonic/releases/download/yue2cpp-windows-8af0174-133a0d60/yue2cpp-windows-8af0174-133a0d60.zip'
                 Sha = ''; Size = 0 }
    Ollama  = @{ Url = 'https://github.com/ollama/ollama/releases/download/v0.40.13/ollama-windows-amd64.zip'
                 Sha = '7afa38624fa62ee5d8293422d0ab084c1bb4603134c7f4dafce11a033b57cc19'; Size = 1601969847 }
    Sdcpp   = @{ Url = 'https://github.com/leejet/stable-diffusion.cpp/releases/download/master-1030-0a06712/sd-master-0a06712-bin-win-cuda12-x64.zip'
                 Sha = '916c6f4b1a98e94de627d9901d0229d60fd3fc05266be8be57f2280b2548b5c4'; Size = 354211822 }
    SdCudart = @{ Url = 'https://github.com/leejet/stable-diffusion.cpp/releases/download/master-1030-0a06712/cudart-sd-bin-win-cu12-x64.zip'
                 Sha = 'fe20366827d357c00797eebb58244dddab7fd9a348d70090c3871004c320f38d'; Size = 563452046 }
}
$GemmaModel = 'gemma4:e4b-it-qat'   # Gemma 4 E4B for Ollama, about 6.1 GB
$Gguf = "$HF/Serveurperso/YuE2-GGUF/resolve/main"
$CppModelFiles = @(
    @{ Name = 'YuE2, Q8 (plans and renders)'; Dir = 'yue2cpp'; File = 'YuE2-3B-Q8_0.gguf'; Url = "$Gguf/YuE2-3B-Q8_0.gguf"
       Sha = '41121ce97786d7795a325bcf123ca196956c03bb252c9e75384cfc1f2fc19e6b'; Size = 3810232064 }
    @{ Name = 'YuE2 VAE (renders)'; Dir = 'yue2cpp'; File = 'YuE2-Vae-F32.gguf'; Url = "$Gguf/YuE2-Vae-F32.gguf"
       Sha = '93e49dfb1970e89ad64cacb17cf13b5d05f6bb30ef7ed3adae3050bcb728638a'; Size = 530497344 }
    @{ Name = 'SheetSage2 (transcription)'; Dir = 'yue2cpp'; File = 'SheetSage2-Q8_0.gguf'; Url = "$Gguf/SheetSage2-Q8_0.gguf"
       Sha = '95d8fa8761753b4833782a52b68d5c0afa3bd3cfbc03d3dcbbf8ded0c13f611e'; Size = 105629856 }
    @{ Name = 'MERT (transcription)'; Dir = 'yue2cpp'; File = 'MERT-v2-FullSong-Q8_0.gguf'; Url = "$Gguf/MERT-v2-FullSong-Q8_0.gguf"
       Sha = '35a6032ec7e8123c02becdefc7bfe10a3adb33faa8a1951dc0af864b4494b8ef'; Size = 902283712 }
)
# Its picture server reads klein's model and VAE as ComfyUI does, but not ComfyUI's text encoder: Qwen 3 4B as GGUF.
$CppPictureEncoder = @{ Name = 'Qwen3 4B text encoder, GGUF (take pictures)'; Dir = 'text_encoders'; File = 'Qwen3-4B-Q4_K_M.gguf'; Pictures = $true
    Url = "$HF/unsloth/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q4_K_M.gguf"
    Sha = 'f6f851777709861056efcdad3af01da38b31223a3ba26e61a4f8bf3a2195813a'; Size = 2497281312 }
# Unchanged copies of the files by Mothersuperior, a single author's account: tried first, with the author's own as the
# fallback, and either must match the checksum.  The copies' README credits the author and keeps the licence.
$Copies = "$HF/pshields/yue2-mothersuperior-copies/resolve/main"
$ModelFiles = @(
    @{ Name = 'YuE2 (plans and renders)'; Dir = 'checkpoints'; File = 'yue2_3b_bf16.safetensors'
       Url = "$HF/Comfy-Org/YuE2/resolve/main/checkpoints/yue2_3b_bf16.safetensors"
       Sha = '33765adbf9813c9a50318218760b2fd819a319862460a04884607581961c6fee'; Size = 7799983228 }
    @{ Name = 'SheetSage2 (transcription)'; Dir = 'audio_encoders'; File = 'sheetsage2_bf16.safetensors'
       Url = "$HF/Comfy-Org/YuE2/resolve/main/audio_encoders/sheetsage2_bf16.safetensors"
       Sha = '5fd960ce3df281e3f3a889d174584d88f96247711480cf96377b12d7e8b6adc5'; Size = 1386868122 }
    @{ Name = 'Gemma 4 (lyric drafts, song analysis)'; Dir = 'text_encoders'; File = 'gemma4_e4b_it_int8_convrot.safetensors'; Lyrics = $true
       Url = "$HF/Comfy-Org/gemma-4/resolve/main/text_encoders/gemma4_e4b_it_int8_convrot.safetensors"
       Sha = '974d0c838ef4ac1a989b06ccb4e57691c21b6270dd8e345ffa7531f9388f117c'; Size = 8090965702 }
    @{ Name = 'Instrumental LoRA'; Dir = 'loras'; File = 'ar_lora_inst_v3abc_comfyui.safetensors'
       Copy = "$Copies/ar_lora_inst_v3abc_comfyui.safetensors"
       Url = "$HF/Mothersuperior/YuE2-instrumental-cot-full-loras/resolve/main/ar_lora_inst_v3abc_comfyui.safetensors"
       Sha = 'de6a11d5701df103a191c87dc73115266e2420f3834739319dec5c24d2119f31'; Size = 212891736 }
    @{ Name = 'Production polish LoRA'; Dir = 'loras'; File = 'nar_lora_joint_v9_comfyui.safetensors'
       Copy = "$Copies/nar_lora_joint_v9_comfyui.safetensors"
       Url = "$HF/Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4/resolve/main/nar_lora_joint_v9_comfyui.safetensors"
       Sha = 'cd2bf0d3ce4bf68697daa016671da7d70e34e2f5545617ab9094c96b14a581db'; Size = 107518800 }
    @{ Name = 'Realaudio tokenizer head'; Dir = 'audio_encoders'; File = 'tokenizer_head_joint_v9.safetensors'
       Copy = "$Copies/tokenizer_head_joint_v9.safetensors"
       Url = "$HF/Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4/resolve/main/tokenizer_head_joint_v9.safetensors"
       Sha = '06440f25605c6c12c4e517ef033d7b70b8d9e961b3b06aa3848b1f8028fd7eb8'; Size = 171278808 }
    @{ Name = 'Training regularizer pack'; Dir = 'fs_audio'; File = 'minted_regularizer_pack_v2.pt'
       Copy = "$Copies/minted_regularizer_pack_v2.pt"
       Url = "$HF/Mothersuperior/YuE2-hum-to-song/resolve/main/minted_regularizer_pack_v2.pt"
       Sha = '587631eec5946f9f87d4b422abcda7e35dee43299efb7b7d2fcba4cd8752c475'; Size = 296098847 }
)
# Take pictures drawn on this PC: FLUX.2 klein 4B, its text encoder and its VAE (Apache 2.0), only when chosen.
# Left out, a take's picture is drawn by the external LLM's image model, if it has one, or not at all.
$PictureFiles = @(
    @{ Name = 'FLUX.2 klein 4B (take pictures)'; Dir = 'diffusion_models'; File = 'flux-2-klein-4b-fp8.safetensors'; Pictures = $true
       Url = "$HF/black-forest-labs/FLUX.2-klein-4b-fp8/resolve/main/flux-2-klein-4b-fp8.safetensors"
       Sha = '97ed34fe0567e436200f2faee3939b88f2b5d99f8af2a4dc16532c4245c0ccb6'; Size = 4070624520 }
    @{ Name = 'Qwen3 4B text encoder (take pictures)'; Dir = 'text_encoders'; File = 'qwen_3_4b_fp4_flux2.safetensors'; Pictures = $true
       Url = "$HF/Comfy-Org/Flux-2-Klein-4B/resolve/main/split_files/text_encoders/qwen_3_4b_fp4_flux2.safetensors"
       Sha = '3eab03a77adb0ee5304a4e677d5c10ac22f9049c1d7c894adca4f8bb39206ca8'; Size = 3848213998 }
    @{ Name = 'FLUX.2 VAE (take pictures)'; Dir = 'vae'; File = 'flux2-vae.safetensors'; Pictures = $true
       Url = "$HF/Comfy-Org/Flux-2-Klein-4B/resolve/main/split_files/vae/flux2-vae.safetensors"
       Sha = '868fe7b343cc8f3a19dbcfcafbc3d5f888802be3f89bd81b65b3621a066ce8f3'; Size = 336211292 }
)
if ($Pictures) { $ModelFiles = @($ModelFiles) + $PictureFiles }
# Style LoRAs, only when chosen: each its author's work under CC BY-NC 4.0, gathered unchanged in one Hugging Face
# repository (its README credits them; the guide links it).  Each comes with a description (.txt) the picker reads.
# A file already in the folder is left as it is, never checked against these and never replaced: it may be the
# user's own copy, or a description they have written over.
$StyleLoras = "$HF/pshields/yue2-style-loras/resolve/main"
$LoraFiles = @(
    @{ Name = 'Style LoRA blgr_kargyraa'; Dir = 'loras'; File = 'blgr_kargyraa.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/blgr_kargyraa.safetensors"
       Sha = '5f5e0274fa0233c7f97fc1408d67184d0dafa621508767d02c2c65f74b7e0642'; Size = 177279864 }
    @{ Name = 'Style LoRA blgr_kargyraa (description)'; Dir = 'loras'; File = 'blgr_kargyraa.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/blgr_kargyraa.txt"
       Sha = 'ef6c73a5739e9100330f004b8563ee523df483a9f912f6f52e5e0666800587e0'; Size = 218 }
    @{ Name = 'Style LoRA blgr_rhodope'; Dir = 'loras'; File = 'blgr_rhodope.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/blgr_rhodope.safetensors"
       Sha = 'e6c216c5ee55683e1d75bd4f9fa6b92c67dc5960dc52706fa98f3eeab192656d'; Size = 177279960 }
    @{ Name = 'Style LoRA blgr_rhodope (description)'; Dir = 'loras'; File = 'blgr_rhodope.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/blgr_rhodope.txt"
       Sha = '96bb6d99644b8a5fe30bf9380d054642ca0bfbadfa5c273e1fb0a7a061d13b55'; Size = 252 }
    @{ Name = 'Style LoRA blgr_steppe'; Dir = 'loras'; File = 'blgr_steppe.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/blgr_steppe.safetensors"
       Sha = 'adfd9dabaeb5f9cfd61f98e6dfe1a4f908e79e276fd40587c355d8634497f77d'; Size = 177279864 }
    @{ Name = 'Style LoRA blgr_steppe (description)'; Dir = 'loras'; File = 'blgr_steppe.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/blgr_steppe.txt"
       Sha = '738d050a0a0abbefaa59c5ecbf93e253563a393111a0bf6f79b03399df813b7c'; Size = 243 }
    @{ Name = 'Style LoRA chnsn_cabaret'; Dir = 'loras'; File = 'chnsn_cabaret.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/chnsn_cabaret.safetensors"
       Sha = '0230ff0ba9f75fcf1586b36a8dcfe67f526703c193d9a63cf1c3f5de9c7f896e'; Size = 117500808 }
    @{ Name = 'Style LoRA chnsn_cabaret (description)'; Dir = 'loras'; File = 'chnsn_cabaret.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/chnsn_cabaret.txt"
       Sha = '2da7dbc56629c46814228a26719dcf42155ca32ef9f4350c74272cb46f2d2ace'; Size = 315 }
    @{ Name = 'Style LoRA chnsn_grand_boulevard'; Dir = 'loras'; File = 'chnsn_grand_boulevard.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/chnsn_grand_boulevard.safetensors"
       Sha = '42527d1f61d26693905316f4392e93a2a404906309a37b884c124e38190ae101'; Size = 177279864 }
    @{ Name = 'Style LoRA chnsn_grand_boulevard (description)'; Dir = 'loras'; File = 'chnsn_grand_boulevard.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/chnsn_grand_boulevard.txt"
       Sha = '874064b90d57d0f1c97f5cacc3e294fa4aa1081a5b848c0e978623cb27d9902d'; Size = 264 }
    @{ Name = 'Style LoRA chnsn_montmartre'; Dir = 'loras'; File = 'chnsn_montmartre.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/chnsn_montmartre.safetensors"
       Sha = 'bcbf1b5aebe2947b1677f87265f0d422adf868745bec12462e39ed9897c9dc65'; Size = 117500808 }
    @{ Name = 'Style LoRA chnsn_montmartre (description)'; Dir = 'loras'; File = 'chnsn_montmartre.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/chnsn_montmartre.txt"
       Sha = 'c808d526e4423bfd984d284ffd66d2ada3894cfaadd1250c92dd4225e2ddf470'; Size = 310 }
    @{ Name = 'Style LoRA chnsn_rive_gauche'; Dir = 'loras'; File = 'chnsn_rive_gauche.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/chnsn_rive_gauche.safetensors"
       Sha = '8421a25b6650febf8e6b7418b1830dc27d79fab57605962f2c6890be98c42ef6'; Size = 177279864 }
    @{ Name = 'Style LoRA chnsn_rive_gauche (description)'; Dir = 'loras'; File = 'chnsn_rive_gauche.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/chnsn_rive_gauche.txt"
       Sha = 'f6a6e6a20dda3bd7daee7e53cbd6dd37b438e40b85095dd7e001d13bcb92ec06'; Size = 308 }
    @{ Name = 'Style LoRA cnzn_coro'; Dir = 'loras'; File = 'cnzn_coro.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/cnzn_coro.safetensors"
       Sha = 'c0708785f63a7f6d582d172120aa64e8085a3f578ac5b722cb36a2c2b1e347ed'; Size = 117500808 }
    @{ Name = 'Style LoRA cnzn_coro (description)'; Dir = 'loras'; File = 'cnzn_coro.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/cnzn_coro.txt"
       Sha = 'f8180110ba36e12488e521f5695f08edd05eceb1392150905f576e0901074849'; Size = 232 }
    @{ Name = 'Style LoRA cnzn_notte'; Dir = 'loras'; File = 'cnzn_notte.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/cnzn_notte.safetensors"
       Sha = '93b87d31bbce1dfb4e83be9d1f55e155b71f3572e640eda5351e7a34f0f32527'; Size = 117500808 }
    @{ Name = 'Style LoRA cnzn_notte (description)'; Dir = 'loras'; File = 'cnzn_notte.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/cnzn_notte.txt"
       Sha = '46ef979461e8505fcf80f3f99fbef1659c29468e50554ff5439e2a435a270ad1'; Size = 279 }
    @{ Name = 'Style LoRA cnzn_sanremo'; Dir = 'loras'; File = 'cnzn_sanremo.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/cnzn_sanremo.safetensors"
       Sha = '8a0322971cfe484414d01f0765092f2454384a18cfa4167824832346451cade0'; Size = 177279960 }
    @{ Name = 'Style LoRA cnzn_sanremo (description)'; Dir = 'loras'; File = 'cnzn_sanremo.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/cnzn_sanremo.txt"
       Sha = 'fc4c4bb3d82617a2dd3b66ff0f809360a5311144d4ed5caba020aa54c9e1fe25'; Size = 299 }
    @{ Name = 'Style LoRA cnzn_sussurro'; Dir = 'loras'; File = 'cnzn_sussurro.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/cnzn_sussurro.safetensors"
       Sha = '2ec3fc4eab4413623c600015ba3f5b7ce59f5604668344912cd2eb495b0bbd63'; Size = 117500808 }
    @{ Name = 'Style LoRA cnzn_sussurro (description)'; Dir = 'loras'; File = 'cnzn_sussurro.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/cnzn_sussurro.txt"
       Sha = '3f9c829d54356dfcef44fcbb15b8f2ca89cf95c3faa215001d6e13f9f37060d9'; Size = 342 }
    @{ Name = 'Style LoRA cnzn_teatro'; Dir = 'loras'; File = 'cnzn_teatro.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/cnzn_teatro.safetensors"
       Sha = '6faef04d10c20a28b311815421e12676b3abfa5c650bfbd1fff1a0c01d48f31d'; Size = 117500808 }
    @{ Name = 'Style LoRA cnzn_teatro (description)'; Dir = 'loras'; File = 'cnzn_teatro.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/cnzn_teatro.txt"
       Sha = '15a125c3e2a268e7fcbcd09e95e9cd58fa5747b0bd6be559770557b450b53944'; Size = 285 }
    @{ Name = 'Style LoRA dreampop_sv_dreampop'; Dir = 'loras'; File = 'dreampop_sv_dreampop.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/dreampop_sv_dreampop.safetensors"
       Sha = '617852d379c66b0407879421a353233d29cda8188cca82973a94c61b512ca03d'; Size = 234969024 }
    @{ Name = 'Style LoRA dreampop_sv_dreampop (description)'; Dir = 'loras'; File = 'dreampop_sv_dreampop.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/dreampop_sv_dreampop.txt"
       Sha = '588c63e08b70640b78eb141cb4d6a3f99e42f54f50e49e6465cef4a4ef65a7fe'; Size = 387 }
    @{ Name = 'Style LoRA drksf_midnight'; Dir = 'loras'; File = 'drksf_midnight.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/drksf_midnight.safetensors"
       Sha = '924076bc78c0ef29d6705341e82c4d292bf557dcc9743045b4fca9bb77e7f580'; Size = 177279760 }
    @{ Name = 'Style LoRA drksf_midnight (description)'; Dir = 'loras'; File = 'drksf_midnight.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/drksf_midnight.txt"
       Sha = 'd38ea4d03e69eb3c79d4415fee82b603118d4be86e6b0b24e15a891344c24f59'; Size = 334 }
    @{ Name = 'Style LoRA mltnt_chanter'; Dir = 'loras'; File = 'mltnt_chanter.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/mltnt_chanter.safetensors"
       Sha = '4aaaa42f7c61b4a3226880dd1e6f1a36bd585171d26a45358c3dba3c9d56b20c'; Size = 117500816 }
    @{ Name = 'Style LoRA mltnt_chanter (description)'; Dir = 'loras'; File = 'mltnt_chanter.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/mltnt_chanter.txt"
       Sha = 'b7e1f6ede32b6578d5e2cd33fad975aeb85141d0a83e260c698224e6cd3ef1f5'; Size = 359 }
    @{ Name = 'Style LoRA mltnt_frontline'; Dir = 'loras'; File = 'mltnt_frontline.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/mltnt_frontline.safetensors"
       Sha = '9c8960158db6340156cc1b44fbec1ff58d0bfabfc96e933ee5a1d14b0bc26574'; Size = 177279880 }
    @{ Name = 'Style LoRA mltnt_frontline (description)'; Dir = 'loras'; File = 'mltnt_frontline.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/mltnt_frontline.txt"
       Sha = 'cb33570cfc0005371ef1888546cc6dc020bde8be6a7960b0f9203d9c7c390903'; Size = 357 }
    @{ Name = 'Style LoRA mltnt_fusion'; Dir = 'loras'; File = 'mltnt_fusion.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/mltnt_fusion.safetensors"
       Sha = 'e9525b892ce625ac7491a13c21b39b7623ef132884996a87eb341370f459aa7b'; Size = 177279784 }
    @{ Name = 'Style LoRA mltnt_fusion (description)'; Dir = 'loras'; File = 'mltnt_fusion.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/mltnt_fusion.txt"
       Sha = '4a4886eb5d4e554f5ac9e7f4e73843b8920bcefaead50f95ba46a6e7502df29c'; Size = 272 }
    @{ Name = 'Style LoRA mltnt_roots'; Dir = 'loras'; File = 'mltnt_roots.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/mltnt_roots.safetensors"
       Sha = 'e829f3af1534614bc28f85e821115d48888edf35aead317e9b5cdf179a79f5f3'; Size = 177279888 }
    @{ Name = 'Style LoRA mltnt_roots (description)'; Dir = 'loras'; File = 'mltnt_roots.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/mltnt_roots.txt"
       Sha = '3304dd0f8c160eee5465be5c169780916bd7487824cd6b19c1defd0d0abe69d0'; Size = 209 }
    @{ Name = 'Style LoRA mltnt_soundclash'; Dir = 'loras'; File = 'mltnt_soundclash.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/mltnt_soundclash.safetensors"
       Sha = 'fa43a4ddb7af26fb0e7821c1ad3386fc90db84897efd00571e0c7f27cf790537'; Size = 117500816 }
    @{ Name = 'Style LoRA mltnt_soundclash (description)'; Dir = 'loras'; File = 'mltnt_soundclash.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/mltnt_soundclash.txt"
       Sha = 'd5a988ebbe5ee8dceee6f758a178eeb04430cbf11984ff84ede647769d3c04d7'; Size = 330 }
    @{ Name = 'Style LoRA mltnt_steppers'; Dir = 'loras'; File = 'mltnt_steppers.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/mltnt_steppers.safetensors"
       Sha = '63094f0bbf8dd1e1fb2654a94aaba77e7360b0bef08d2254ef4a972ea8dce10e'; Size = 177279888 }
    @{ Name = 'Style LoRA mltnt_steppers (description)'; Dir = 'loras'; File = 'mltnt_steppers.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/mltnt_steppers.txt"
       Sha = 'dade8fa79bf12ea685b02b9a3fb5b4a9243a34ba42bd9f622f01d789b77f57b9'; Size = 232 }
    @{ Name = 'Style LoRA qwwl_mehfil'; Dir = 'loras'; File = 'qwwl_mehfil.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/qwwl_mehfil.safetensors"
       Sha = '28132e4b545b3c57a831179553e509408fa11d6eed96811c50f0d2629ddceb2e'; Size = 177279760 }
    @{ Name = 'Style LoRA qwwl_mehfil (description)'; Dir = 'loras'; File = 'qwwl_mehfil.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/qwwl_mehfil.txt"
       Sha = '5d09c0ec81338395b17b8788bd8c6cf597f0307f9b26d3ff8aa7ca0a7c831582'; Size = 359 }
    @{ Name = 'Style LoRA slider-acoustic-folk'; Dir = 'loras'; File = 'slider-acoustic-folk.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-acoustic-folk.safetensors"
       Sha = 'b51c0f8a80d1001e19a2650e3184ed188c3aac97c1e2cd9cb3ec5ed03a6efef0'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-acoustic-folk (description)'; Dir = 'loras'; File = 'slider-acoustic-folk.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-acoustic-folk.txt"
       Sha = '0b9a3f253d774133f0f021e07d1e484354b06993e7211376ae7ecc43fcc9ecec'; Size = 341 }
    @{ Name = 'Style LoRA slider-afrobeats'; Dir = 'loras'; File = 'slider-afrobeats.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-afrobeats.safetensors"
       Sha = '7b0be8a08aa9bb63579d3daf6f23f08f36084282c1e143be7aa2184088a86982'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-afrobeats (description)'; Dir = 'loras'; File = 'slider-afrobeats.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-afrobeats.txt"
       Sha = '921d7cea8aba2282a771fdfb20e0b5ed3e2284b2c4dc595201794fcd11951878'; Size = 339 }
    @{ Name = 'Style LoRA slider-country'; Dir = 'loras'; File = 'slider-country.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-country.safetensors"
       Sha = 'c41c13e09e0daf764808be8cdbe6970b3bce359c11460584ccb09b4d502aee2a'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-country (description)'; Dir = 'loras'; File = 'slider-country.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-country.txt"
       Sha = 'cbbe724e264dc8548dec51d1123dc91da7d82a37010518279bb2eeae56e8ef3e'; Size = 330 }
    @{ Name = 'Style LoRA slider-disco-funk'; Dir = 'loras'; File = 'slider-disco-funk.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-disco-funk.safetensors"
       Sha = '89149145bc3f69518a7b9de63672083f994786c9af66822ef11d7b521f82cb27'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-disco-funk (description)'; Dir = 'loras'; File = 'slider-disco-funk.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-disco-funk.txt"
       Sha = 'd3e3759eeb72ac67e8a30545bfe5bfde618352d16b240b78202d6a8a41d50ed7'; Size = 343 }
    @{ Name = 'Style LoRA slider-female'; Dir = 'loras'; File = 'slider-female.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-female.safetensors"
       Sha = 'a760f6535b9be6412aec12e8ebd30c45c7886ecb01007dc900c944d57cce4a53'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-female (description)'; Dir = 'loras'; File = 'slider-female.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-female.txt"
       Sha = '6b9c69609cc65d1ffdb14f0761283741f98124ae90daaad4ae5954c701032ab5'; Size = 329 }
    @{ Name = 'Style LoRA slider-hiphop'; Dir = 'loras'; File = 'slider-hiphop.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-hiphop.safetensors"
       Sha = '544481919541a7f97fa581911a71fdeace03a55ddd15172a58a60ec60b963cad'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-hiphop (description)'; Dir = 'loras'; File = 'slider-hiphop.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-hiphop.txt"
       Sha = 'cb5aba62431e1f480d6502ddea6678ae68e3b11f2878f820d8e89cc787c95144'; Size = 325 }
    @{ Name = 'Style LoRA slider-house'; Dir = 'loras'; File = 'slider-house.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-house.safetensors"
       Sha = '6149fcde75b7f959c323ebd90f760dc7994183aef1a9345482fddf530c06737a'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-house (description)'; Dir = 'loras'; File = 'slider-house.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-house.txt"
       Sha = '5bf43f69b59d8b8f7eb3da675bec0b2e5a0c6fc8456871e9e9037c42390b7306'; Size = 333 }
    @{ Name = 'Style LoRA slider-indie-rock'; Dir = 'loras'; File = 'slider-indie-rock.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-indie-rock.safetensors"
       Sha = 'bf97b12ae89317343b1498f0bb066dbf01aa547381d60b6cf9b163db05f1b5d9'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-indie-rock (description)'; Dir = 'loras'; File = 'slider-indie-rock.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-indie-rock.txt"
       Sha = '25fe649e8b414b09760b2fac5e6e7970f9f733ba838997af8cef3dba688a0a7a'; Size = 333 }
    @{ Name = 'Style LoRA slider-kpop'; Dir = 'loras'; File = 'slider-kpop.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-kpop.safetensors"
       Sha = 'eca99b3b12bf94e1a605122a99c42bb3123c0d32bdb93758ee9967d20fc7458c'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-kpop (description)'; Dir = 'loras'; File = 'slider-kpop.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-kpop.txt"
       Sha = '9e1a9e8057178c689ea4d869c883eddc62b041c28b96c346eaf380b42c23f9be'; Size = 331 }
    @{ Name = 'Style LoRA slider-lofi'; Dir = 'loras'; File = 'slider-lofi.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-lofi.safetensors"
       Sha = '14474d0273924c7abe3b3b2caae794ae9052cff9a392985ff9540f0829067db4'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-lofi (description)'; Dir = 'loras'; File = 'slider-lofi.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-lofi.txt"
       Sha = '4d37f0cc153b6f2486a36c44a093eca0729feaedcdd452baddab9d4f7b22349b'; Size = 331 }
    @{ Name = 'Style LoRA slider-male'; Dir = 'loras'; File = 'slider-male.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-male.safetensors"
       Sha = '125a5e3adad5e1c541ad47bd377f1e7ff4edffc02f7552895dd6eb86dda7b5c1'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-male (description)'; Dir = 'loras'; File = 'slider-male.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-male.txt"
       Sha = '0b65c5e885a29267fd1141b486edc07a47d9c039bdde813d33308c0cc7a10ae5'; Size = 325 }
    @{ Name = 'Style LoRA slider-metal'; Dir = 'loras'; File = 'slider-metal.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-metal.safetensors"
       Sha = '8ae844629dcaf4fd55f13ed123f24ace69fa28951382e7652e169a6c9b7a4d5b'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-metal (description)'; Dir = 'loras'; File = 'slider-metal.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-metal.txt"
       Sha = '93a52f3f387f20906d1a9dfc9352ad0c09a620aab60251247cd25f46688a7522'; Size = 335 }
    @{ Name = 'Style LoRA slider-pop-punk'; Dir = 'loras'; File = 'slider-pop-punk.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-pop-punk.safetensors"
       Sha = 'bb8d8e4146f872c74ade1e6982946f84be1538a618a922ff9eb9674539ec34c3'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-pop-punk (description)'; Dir = 'loras'; File = 'slider-pop-punk.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-pop-punk.txt"
       Sha = 'dafbe727ea18498a1334fa836a81ffebe47d79ec9c032ae2fe78e937cc1ed7f2'; Size = 330 }
    @{ Name = 'Style LoRA slider-pop'; Dir = 'loras'; File = 'slider-pop.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-pop.safetensors"
       Sha = 'bc6642b68882fbc0f73df4a0e89a51c1ebe144bc1ded5b877b5dd157ffa48cd2'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-pop (description)'; Dir = 'loras'; File = 'slider-pop.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-pop.txt"
       Sha = '66699ef7c06098f77d4514d72aed2e12ceae22735d91829ea1984c20442b7604'; Size = 323 }
    @{ Name = 'Style LoRA slider-reggaeton'; Dir = 'loras'; File = 'slider-reggaeton.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-reggaeton.safetensors"
       Sha = '297623d8a2546749bfa7190acc5de7bfdb02135358156558cd7a8506f1a905ff'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-reggaeton (description)'; Dir = 'loras'; File = 'slider-reggaeton.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-reggaeton.txt"
       Sha = '730d823a662eb143088ada83e838f49851cd4ea0a5282c7467045a784ad574f6'; Size = 339 }
    @{ Name = 'Style LoRA slider-rnb'; Dir = 'loras'; File = 'slider-rnb.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-rnb.safetensors"
       Sha = 'faa89944f0d3c9a7e17f62374e29ee76d1d82f5283674060d11a811eaf9f632d'; Size = 10113448 }
    @{ Name = 'Style LoRA slider-rnb (description)'; Dir = 'loras'; File = 'slider-rnb.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/slider-rnb.txt"
       Sha = '220d04247170392e2dfe9c2daaa13d5e648034da547ef49e72d36b47951f7b9c'; Size = 324 }
    @{ Name = 'Style LoRA sv_oldschoolhiphop'; Dir = 'loras'; File = 'sv_oldschoolhiphop.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/sv_oldschoolhiphop.safetensors"
       Sha = 'ca176909d55998d4f78426439885ff79cc96ba4daaaaea22a9936590d6e72694'; Size = 234969032 }
    @{ Name = 'Style LoRA sv_oldschoolhiphop (description)'; Dir = 'loras'; File = 'sv_oldschoolhiphop.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/sv_oldschoolhiphop.txt"
       Sha = '93c332bb5c5cfb6b387cb32335a4e398381804597af888d47e7b620e7ea7086a'; Size = 431 }
    @{ Name = 'Style LoRA yue2_jpop_t4'; Dir = 'loras'; File = 'yue2_jpop_t4.safetensors'; KeepIfPresent = $true
       Url = "$StyleLoras/yue2_jpop_t4.safetensors"
       Sha = '8cdbe15cf1968ff586d734a8ce4f8e7c823f8a8005fe1466c5aa9f442d257d57'; Size = 106474864 }
    @{ Name = 'Style LoRA yue2_jpop_t4 (description)'; Dir = 'loras'; File = 'yue2_jpop_t4.txt'; KeepIfPresent = $true
       Url = "$StyleLoras/yue2_jpop_t4.txt"
       Sha = 'f799ce448332f646850d3dab41c182d5819c39c2840a8f3617464574fab2f173'; Size = 231 }
)
if ($Loras) { $ModelFiles = @($ModelFiles) + $LoraFiles }
if ($NoLyrics) { $ModelFiles = @($ModelFiles | Where-Object { -not $_.Lyrics }) }
# The model comes in two sizes and an install has one of them: the full-quality file, or with -Int8 the
# smaller one for a GPU with little memory.  The other is taken off the entry list here, and removed from
# the folder once the chosen one is in place (below), so choosing differently later is just running this again.
$FullModel = 'yue2_3b_bf16.safetensors'
$SmallModel = 'yue2_3b_int8_convrot.safetensors'
if ($Int8) {
    $ModelFiles = @($ModelFiles | ForEach-Object {
        if ($_.File -eq $FullModel) {
            @{ Name = 'YuE2, low-memory size (plans and renders)'; Dir = 'checkpoints'; File = $SmallModel
               Url = "$HF/Comfy-Org/YuE2/resolve/main/checkpoints/$SmallModel"
               Sha = '96fe199377309001ed8cd26a944baeee8cc31a20ba7c36d1d3c0a7e1f4149db6'; Size = 3960938800 }
        } else { $_ }
    })
}
# The yue2.cpp engine needs its own YuE2 files, none of ComfyUI's model files but the LoRAs, and with pictures klein's
# model and VAE with a GGUF encoder.  Gemma comes through Ollama (below), not as a file here.
if ($Cpp) {
    $shared = @($ModelFiles | Where-Object { $_.Dir -eq 'loras' -or ($_.Pictures -and $_.Dir -ne 'text_encoders') })
    $ModelFiles = @($CppModelFiles) + $shared
    if ($Pictures) { $ModelFiles = @($ModelFiles) + @($CppPictureEncoder) }
}
$SoundFontFiles = @(
    @{ Name = 'Jnsgm2 GM SoundFont'; File = 'github_Jnsgm2.sf2'
       Url = 'https://raw.githubusercontent.com/wrightflyer/SF2_SoundFonts/master/Jnsgm2.sf2'
       Sha = 'dc48cb5c322cab23fce1b18442066be30ccc49a184603c7a3bf7615003ee137d'; Size = 33187490 }
    @{ Name = 'Arachno SoundFont 1.0'; File = 'Arachno_SoundFont_Version_1.0.sf2'
       Url = 'https://archive.org/download/free-soundfonts-sf2-2019-04/Arachno_SoundFont_Version_1.0.sf2'
       Sha = '9a57fb3b6714e69dda12390e351b087e81fc3b1eca15c6b4bbe172799f4cf3cd'; Size = 155405818 }
)

# ------------------------------------------------------------------- helpers
function Say([string]$text, [string]$colour = 'Gray') { Write-Host $text -ForegroundColor $colour }
function Step([string]$text) { Write-Host ''; Write-Host "== $text" -ForegroundColor Cyan }
function Done([string]$name) { Set-Content -Path (Join-Path $State "$name.done") -Value (Get-Date -Format s) }
function IsDone([string]$name) { Test-Path (Join-Path $State "$name.done") }

function Stop-Setup([string]$why) {
    Write-Host ''
    Write-Host "Setup stopped: $why" -ForegroundColor Red
    Write-Host "The details are in $(Join-Path $Logs 'install.log')."
    Write-Host 'Run the installer again to carry on from here.'
    Stop-Transcript | Out-Null
    Read-Host 'Press Enter to close this window' | Out-Null
    exit 1
}

# A file from its publisher.  curl (built into Windows) resumes a broken download;
# the sha256 is checked once and remembered, so a second run does not read 8 GB again.
function Get-Verified($spec, [string]$dest) {
    $ok = "$dest.sha256ok"
    if ((Test-Path $dest) -and (Test-Path $ok)) { return }
    if ($spec.KeepIfPresent -and (Test-Path $dest)) { return }   # someone's own copy: not ours to check or replace
    $part = "$dest.part"
    if (-not (Test-Path $dest)) {
        Say ("Downloading {0} ({1:N0} MB)" -f (Split-Path $dest -Leaf), ($spec.Size / 1e6))
        # Our copy first where there is one, then the publisher.  A refusal (404 and the like, curl's 22) moves on at
        # once; a broken download is tried again, and a part left by one source is not resumed from another.
        $sources = @(@($spec.Copy, $spec.Url) | Where-Object { $_ })
        $tries = if ($sources.Count -gt 1) { 3 } else { 6 }
        $got = $false
        foreach ($url in $sources) {
            for ($try = 1; $try -le $tries; $try++) {
                & curl.exe -L --fail --retry 5 -C - -# -o $part $url
                if ($LASTEXITCODE -eq 0) { $got = $true; break }
                if ($LASTEXITCODE -eq 22 -or $try -eq $tries) { break }
                Say "  the download broke off; trying again ($try of $($tries - 1))" 'Yellow'
                Start-Sleep -Seconds (5 * $try)
            }
            if ($got) { break }
            if (Test-Path $part) { Remove-Item -Force $part }
            if ($url -ne $sources[-1]) { Say "  could not download it from $url; trying $($sources[-1])" 'Yellow' }
        }
        if (-not $got) { Stop-Setup "could not download $($spec.Url)" }
        Move-Item -Force $part $dest
    }
    if ($spec.Size -and (Get-Item $dest).Length -ne $spec.Size) {
        Remove-Item -Force $dest
        Stop-Setup "$(Split-Path $dest -Leaf) came down the wrong size; it has been removed, so the next run fetches it again"
    }
    if ($spec.Sha) {
        Say "  checking $(Split-Path $dest -Leaf)"
        $hash = (Get-FileHash -Algorithm SHA256 $dest).Hash.ToLower()
        if ($hash -ne $spec.Sha) {
            Remove-Item -Force $dest
            Stop-Setup "$(Split-Path $dest -Leaf) did not match its published checksum; it has been removed, so the next run fetches it again"
        }
    }
    Set-Content -Path $ok -Value (Get-Date -Format s)
}

function Expand-Zip([string]$zip, [string]$to) {
    if (Test-Path $to) { Remove-Item -Recurse -Force $to }
    Expand-Archive -Path $zip -DestinationPath $to -Force
}

# An archive of one commit from GitHub.  GitHub builds these on request, so they have
# no fixed checksum; the commit id pins the contents.
function Get-Commit([string]$repo, [string]$commit, [string]$dest) {
    $zip = Join-Path $Downloads "$($repo.Replace('/', '_'))-$($commit.Substring(0, 8)).zip"
    if (-not (Test-Path $zip)) {
        Say "Downloading $repo at $($commit.Substring(0, 8))"
        & curl.exe -L --fail --retry 5 -# -o "$zip.part" "https://codeload.github.com/$repo/zip/$commit"
        if ($LASTEXITCODE -ne 0) { Stop-Setup "could not download $repo" }
        Move-Item -Force "$zip.part" $zip
    }
    $tmp = Join-Path $Downloads 'unpack'
    Expand-Zip $zip $tmp
    $inner = Get-ChildItem $tmp | Select-Object -First 1
    if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
    Move-Item $inner.FullName $dest
    Remove-Item -Recurse -Force $tmp
}

function Invoke-Checked([string]$what, [string]$exe, [string[]]$arguments) {
    & $exe @arguments
    if ($LASTEXITCODE -ne 0) { Stop-Setup "$what failed (exit code $LASTEXITCODE)" }
}

function Test-Port([int]$port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try { $client.Connect('127.0.0.1', $port); return $true } catch { return $false } finally { $client.Close() }
}

# Anything unforeseen stops here too, with the window left open to read, rather
# than closing on the error.
trap {
    $where = $_.InvocationInfo.ScriptLineNumber
    Stop-Setup "an unexpected error at line ${where}: $($_.Exception.Message)"
}

# -------------------------------------------------------------- system check
Step 'Checking this PC'
$problems = New-Object System.Collections.ArrayList
$warnings = New-Object System.Collections.ArrayList

$os = [Environment]::OSVersion.Version
if (-not [Environment]::Is64BitOperatingSystem) { [void]$problems.Add('Windows must be 64-bit.') }
if ($os.Build -lt 19045) { [void]$problems.Add("Windows 10 22H2 or Windows 11 is needed (this is build $($os.Build)).") }
Say ("Windows build {0}, PowerShell {1}, {2}-bit" -f $os.Build, $PSVersionTable.PSVersion, $(if ([Environment]::Is64BitProcess) { 64 } else { 32 }))

$variant = $null
$smi = Join-Path $env:SystemRoot 'System32\nvidia-smi.exe'
if (-not (Test-Path $smi)) { $cmd = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue; if ($cmd) { $smi = $cmd.Source } }
if (-not (Test-Path $smi)) {
    [void]$problems.Add('No NVIDIA graphics card was found (nvidia-smi is missing). Yeufonic needs an NVIDIA card, RTX 30-series or newer, with its driver installed.')
} else {
    $line = (& $smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader,nounits 2>$null | Select-Object -First 1)
    if (-not $line) {
        [void]$problems.Add('The NVIDIA driver did not answer. Install or update it from nvidia.com, then run the installer again.')
    } else {
        $f = $line.Split(',') | ForEach-Object { $_.Trim() }
        $gpu = $f[0]; $vramGB = [math]::Round([double]$f[1] / 1024, 1); $driver = $f[2]; $cap = $f[3]
        Say ("Graphics card: {0}, {1} GB, driver {2}, compute {3}" -f $gpu, $vramGB, $driver, $cap)
        $major = [int]($driver.Split('.')[0])
        if ($major -ge 580) { $variant = 'cu130' }
        elseif ($major -ge 528) { $variant = 'cu126' }
        else { [void]$problems.Add("The NVIDIA driver ($driver) is too old. Update it from nvidia.com, then run the installer again.") }
        if ($cap -and [double]$cap -lt 8.0) {
            [void]$problems.Add("$gpu is too old for YuE2, which needs an RTX 30-series card or newer (bf16).")
        }
        if ($vramGB -lt 7.5) { [void]$problems.Add("$gpu has $vramGB GB of video memory; YuE2 needs 8 GB, and 12 GB or more is recommended.") }
        elseif ($vramGB -lt 11.5) { [void]$warnings.Add("$vramGB GB of video memory works, but lyric drafts on this PC will be slow. 12 GB or more is recommended.") }
    }
}

$ramGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
Say "Memory: $ramGB GB"
if ($ramGB -lt 15) { [void]$warnings.Add("This PC has $ramGB GB of memory; 16 GB is recommended.") }

# Room for what is still to come: the missing models, plus about 12 GB for the engine,
# the app and the downloads while they unpack.
# Sizes are shown in thousands, as the installer's own pages and download sites count.
$needBytes = 16e9   # the engine, the app, Whisper and demucs, and room to unpack
foreach ($m in $ModelFiles) { if (-not (Test-Path (Join-Path (Join-Path $Models $m.Dir) $m.File))) { $needBytes += $m.Size } }
if ($Cpp -and -not $NoLyrics -and -not (Test-Path (Join-Path $Models 'ollama\manifests'))) { $needBytes += 6.2e9 + 1.7e9 }
if ($SkipModels) { $needBytes = 12e9 }
$drive = (Get-Item $InstallDir).PSDrive
$freeGB = [math]::Round($drive.Free / 1e9, 1)
Say ("Free space on {0}: {1} GB (needed: about {2} GB)" -f $drive.Name, $freeGB, [math]::Ceiling($needBytes / 1e9))
if ($drive.Free -lt $needBytes) { [void]$problems.Add("Not enough free space on $($drive.Name): about $([math]::Ceiling($needBytes / 1e9)) GB is needed.") }

if ($InstallDir.Length -gt 60) { [void]$warnings.Add("The install folder's path is long ($($InstallDir.Length) characters); a shorter one avoids Windows' path length limit.") }

# The ports this install uses: the defaults, or what its settings.ini says (an install beside a Docker copy of the
# app, which holds 8090, is usually moved to another).
$ports = @(8090, 8188)
$settingsFile = Join-Path $InstallDir 'settings.ini'
if (Test-Path $settingsFile) {
    $names = @('app_port', 'engine_port')
    for ($i = 0; $i -lt $names.Count; $i++) {
        $line = Get-Content $settingsFile | Where-Object { $_ -match ('^\s*' + $names[$i] + '\s*=') } | Select-Object -First 1
        if ($line -and ($line -match '=\s*(\d{2,5})\s*$')) { $ports[$i] = [int]$Matches[1] }
    }
}
foreach ($port in $ports) {
    if (Test-Port $port) { [void]$warnings.Add("Something is already using port $port (Docker Desktop, or another copy of Yeufonic or ComfyUI?). Stop it before starting Yeufonic.") }
}

foreach ($site in @('https://huggingface.co', 'https://github.com', 'https://pypi.org', 'https://download.pytorch.org')) {
    & curl.exe -s -o NUL -I --max-time 15 $site
    if ($LASTEXITCODE -ne 0) { [void]$problems.Add("Cannot reach $site. Check the internet connection, or a firewall or proxy.") }
}

foreach ($w in $warnings) { Say "  note: $w" 'Yellow' }
if ($problems.Count) {
    foreach ($p in $problems) { Say "  problem: $p" 'Red' }
    Stop-Setup 'this PC does not meet the requirements above'
}
Say 'This PC is suitable.' 'Green'
if ($CheckOnly) { Stop-Transcript | Out-Null; exit 0 }

# ------------------------------------------------------------------- tools
Step 'Tools'
Get-Verified $Files.SevenZip (Join-Path $Tools '7zr.exe')
$uvZip = Join-Path $Downloads 'uv.zip'
Get-Verified $Files.Uv $uvZip
if (-not (Test-Path (Join-Path $Tools 'uv\uv.exe'))) { Expand-Zip $uvZip (Join-Path $Tools 'uv') }
$ffZip = Join-Path $Downloads 'ffmpeg.zip'
Get-Verified $Files.Ffmpeg $ffZip
if (-not (Test-Path (Join-Path $Tools 'ffmpeg\bin\ffmpeg.exe'))) {
    $tmp = Join-Path $Downloads 'ffmpeg-unpack'
    Expand-Zip $ffZip $tmp
    if (Test-Path (Join-Path $Tools 'ffmpeg')) { Remove-Item -Recurse -Force (Join-Path $Tools 'ffmpeg') }
    Move-Item (Get-ChildItem $tmp | Select-Object -First 1).FullName (Join-Path $Tools 'ffmpeg')
    Remove-Item -Recurse -Force $tmp
}
$fsZip = Join-Path $Downloads 'fluidsynth.zip'
Get-Verified $Files.Fluidsynth $fsZip
if (-not (Test-Path (Join-Path $Tools 'fluidsynth\bin\fluidsynth.exe'))) {
    $tmp = Join-Path $Downloads 'fluidsynth-unpack'
    Expand-Zip $fsZip $tmp
    if (Test-Path (Join-Path $Tools 'fluidsynth')) { Remove-Item -Recurse -Force (Join-Path $Tools 'fluidsynth') }
    Move-Item (Get-ChildItem $tmp | Select-Object -First 1).FullName (Join-Path $Tools 'fluidsynth')
    Remove-Item -Recurse -Force $tmp
}
$uv = Join-Path $Tools 'uv\uv.exe'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $InstallDir 'python'
$env:UV_CACHE_DIR = Join-Path $Downloads 'uv-cache'

# ------------------------------------------------------------------- engine
if ($Cpp) {
    Step 'The engine (yue2.cpp)'
    $server = $CppPrograms.Server
    $serverZip = Join-Path $Downloads (Split-Path $server.Url -Leaf)
    $serverMark = 'yue2cpp-' + [System.IO.Path]::GetFileNameWithoutExtension($serverZip)
    if (-not (IsDone $serverMark) -or -not (Test-Path (Join-Path $CppDir 'yue2cpp\yue-server.exe'))) {
        Get-Verified $server $serverZip
        Expand-Zip $serverZip (Join-Path $CppDir 'yue2cpp')
        Done $serverMark
        Remove-Item -Force -ErrorAction SilentlyContinue $serverZip, "$serverZip.sha256ok"
    }
    foreach ($sub in @('yue2cpp', 'loras', 'text_encoders', 'diffusion_models', 'vae')) {
        New-Item -ItemType Directory -Force -Path (Join-Path $Models $sub) | Out-Null
    }
    if ($Pictures) {
        Say 'The picture server (stable-diffusion.cpp)'
        $sdMark = 'sdcpp-' + [System.IO.Path]::GetFileNameWithoutExtension((Split-Path $CppPrograms.Sdcpp.Url -Leaf))
        if (-not (IsDone $sdMark) -or -not (Test-Path (Join-Path $CppDir 'sdcpp\sd-server.exe'))) {
            $sdZip = Join-Path $Downloads (Split-Path $CppPrograms.Sdcpp.Url -Leaf)
            $rtZip = Join-Path $Downloads (Split-Path $CppPrograms.SdCudart.Url -Leaf)
            Get-Verified $CppPrograms.Sdcpp $sdZip
            Get-Verified $CppPrograms.SdCudart $rtZip
            Expand-Zip $sdZip (Join-Path $CppDir 'sdcpp')
            Expand-Archive -Path $rtZip -DestinationPath (Join-Path $CppDir 'sdcpp') -Force
            # The server may sit one folder down in the archive.
            $exe = Get-ChildItem -Recurse (Join-Path $CppDir 'sdcpp') -Filter 'sd-server.exe' | Select-Object -First 1
            if (-not $exe) { Stop-Setup "the picture server's archive has no sd-server.exe" }
            if ($exe.DirectoryName -ne (Join-Path $CppDir 'sdcpp')) {
                Get-ChildItem $exe.DirectoryName | Move-Item -Destination (Join-Path $CppDir 'sdcpp') -Force
            }
            Done $sdMark
            Remove-Item -Force -ErrorAction SilentlyContinue $sdZip, "$sdZip.sha256ok", $rtZip, "$rtZip.sha256ok"
        }
    }
    if (-not $NoLyrics) {
        Say 'Ollama, which runs Gemma beside the engine'
        $olMark = 'ollama-' + ($CppPrograms.Ollama.Url -replace '.*/download/([^/]+)/.*', '$1')
        if (-not (IsDone $olMark) -or -not (Test-Path (Join-Path $CppDir 'ollama\ollama.exe'))) {
            $olZip = Join-Path $Downloads (Split-Path $CppPrograms.Ollama.Url -Leaf)
            Get-Verified $CppPrograms.Ollama $olZip
            Expand-Zip $olZip (Join-Path $CppDir 'ollama')
            Done $olMark
            Remove-Item -Force -ErrorAction SilentlyContinue $olZip, "$olZip.sha256ok"
        }
    }
}
if (-not $Cpp) {
Step 'The engine (ComfyUI)'
$engineMark = "engine-$variant-$($Pins.ComfyCommit.Substring(0, 8))"
if (-not (IsDone $engineMark)) {
    $portable = $Portables[$variant]
    $archive = Join-Path $Downloads (Split-Path $portable.Url -Leaf)
    Get-Verified $portable $archive
    Say 'Unpacking the engine (a few minutes)'
    $tmp = Join-Path $InstallDir 'engine-unpack'
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
    Invoke-Checked 'Unpacking the engine' (Join-Path $Tools '7zr.exe') @('x', $archive, "-o$tmp", '-y', '-bso0', '-bsp1')
    $unpacked = Get-ChildItem $tmp -Directory | Select-Object -First 1
    # Keep the models and anything made with the engine when it is replaced.
    $keep = Join-Path $InstallDir 'engine-keep'
    if (Test-Path $ComfyDir) {
        New-Item -ItemType Directory -Force -Path $keep | Out-Null
        foreach ($sub in @('models', 'input', 'output', 'user')) {
            if (Test-Path (Join-Path $ComfyDir $sub)) { Move-Item (Join-Path $ComfyDir $sub) (Join-Path $keep $sub) }
        }
    }
    if (Test-Path $Engine) { Remove-Item -Recurse -Force $Engine }
    Move-Item $unpacked.FullName $Engine
    Remove-Item -Recurse -Force $tmp

    # The portable build brings a newer ComfyUI than the one tested here; that one is
    # put in its place, over the same Python.
    Get-Commit 'Comfy-Org/ComfyUI' $Pins.ComfyCommit $ComfyDir
    if (Test-Path $keep) {
        foreach ($sub in @('models', 'input', 'output', 'user')) {
            $saved = Join-Path $keep $sub
            if (Test-Path $saved) {
                if (Test-Path (Join-Path $ComfyDir $sub)) { Remove-Item -Recurse -Force (Join-Path $ComfyDir $sub) }
                Move-Item $saved (Join-Path $ComfyDir $sub)
            }
        }
        Remove-Item -Recurse -Force $keep
    }
    $py = Join-Path $Engine 'python_embeded\python.exe'
    Say "Installing the engine's packages"
    Invoke-Checked "The engine's packages" $py @('-s', '-m', 'pip', 'install', '--no-warn-script-location', '-r', (Join-Path $ComfyDir 'requirements.txt'))
    Done $engineMark
    # Unpacked and working: the 1.8 GB archive is not needed again.
    Remove-Item -Force -ErrorAction SilentlyContinue $archive, "$archive.sha256ok"
}
$py = Join-Path $Engine 'python_embeded\python.exe'

# 0.0.25 put torch 2.9.1 on CUDA 12.8 into the engine, to chase a training problem it did not
# fix.  On that build the low-memory model renders several times slower than on CUDA 13, which is
# what the portable build ships and what that model was tested on.  An install that has the
# 0.0.25 pair is put back on the portable's own.  A step of its own, so an update does it
# without unpacking the engine again.
if ($variant -eq 'cu130') {
    $torchHave = (& $py -s -c 'import torch; print(torch.__version__)' 2>$null | Select-Object -First 1)
    if ($torchHave -and "$torchHave".Trim() -eq '2.9.1+cu128') {
        Say "Putting the engine's torch back (a large download)"
        Invoke-Checked "The engine's torch" $py @('-s', '-m', 'pip', 'install', '--no-warn-script-location',
            'torch==2.13.0', 'torchvision==0.28.0', 'torchaudio==2.11.0',
            '--index-url', 'https://download.pytorch.org/whl/cu130')
    }
    Get-ChildItem $State -Filter 'torch-2.9.1-cu128-*.done' -ErrorAction SilentlyContinue | Remove-Item -Force
}

$nodes = Join-Path $ComfyDir 'custom_nodes'
if (-not (IsDone "yue2_trainer-$($Pins.Yue2TrainerCommit.Substring(0, 8))") -or -not (Test-Path (Join-Path $nodes 'ComfyUI-YuE2-Trainer'))) {
    Get-Commit 'yeufonic/ComfyUI-YuE2-Trainer' $Pins.Yue2TrainerCommit (Join-Path $nodes 'ComfyUI-YuE2-Trainer')
    Invoke-Checked "The trainer's packages" $py @('-s', '-m', 'pip', 'install', '--no-warn-script-location', 'soundfile>=0.12', 'librosa>=0.10', 'scipy', 'mutagen', 'einops')
    Done "yue2_trainer-$($Pins.Yue2TrainerCommit.Substring(0, 8))"
}
# Stem separation on the GPU: the engine's CUDA torch runs Demucs, so a vocal is separated in the engine's queue
# beside plans and renders. It adds demucs and a few small packages and leaves torch alone. Without it the node is
# not there and the app separates on the CPU as before. A step of its own, so an update does it without more.
if (-not (IsDone 'engine-demucs')) {
    Invoke-Checked "Demucs for the engine" $py @('-s', '-m', 'pip', 'install', '--no-warn-script-location', 'demucs==4.1.0')
    Done 'engine-demucs'
}
# Whisper on the GPU, for the words of a separated vocal: faster-whisper with CTranslate2. CTranslate2's Windows build
# wants the CUDA 12 cuBLAS and cuDNN, which the engine's CUDA 13 PyTorch does not carry, so they come as their own
# packages (a little over a gigabyte); the node puts their folders on PATH. faster-whisper goes in without its
# dependencies, which would hold PyAV to a version of their choosing. Without all this the node is not there and the app
# hears words on the CPU as before.
if (-not (IsDone 'engine-whisper')) {
    # --no-warn-conflicts: pip would say in red that faster-whisper wants onnxruntime, which is only for the voice detector
    # that is switched off, and the line looks like a failure.
    Invoke-Checked 'Whisper for the engine' $py @('-s', '-m', 'pip', 'install', '--no-warn-script-location', '--no-warn-conflicts', '--no-deps', 'faster-whisper==1.2.1')
    Invoke-Checked "Whisper's GPU libraries" $py @('-s', '-m', 'pip', 'install', '--no-warn-script-location', '--no-warn-conflicts', 'ctranslate2>=4.5,<5', 'tokenizers', 'nvidia-cublas-cu12', 'nvidia-cudnn-cu12')
    Done 'engine-whisper'
}
# Our own node, carried by the installer.
$harmony = Join-Path $nodes 'yue2_harmony'
if (Test-Path $harmony) { Remove-Item -Recurse -Force $harmony }
Copy-Item -Recurse (Join-Path $InstallDir 'studio\engine-nodes\yue2_harmony') $harmony
foreach ($sub in @('checkpoints', 'audio_encoders', 'text_encoders', 'loras', 'fs_audio')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $Models $sub) | Out-Null
}
}   # the ComfyUI engine
# Models kept by an uninstall come back, with the LoRAs trained here.
$kept = Join-Path $InstallDir 'models-kept'
if (Test-Path $kept) {
    Say 'Putting back the models kept by the last uninstall'
    Get-ChildItem $kept -Recurse -File | ForEach-Object {
        $target = Join-Path $Models $_.FullName.Substring($kept.Length + 1)
        New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
        if (-not (Test-Path $target)) { Move-Item $_.FullName $target }
    }
    Remove-Item -Recurse -Force $kept
}

# ---------------------------------------------------------------------- app
Step 'The app'
$venv = Join-Path $InstallDir 'venv'
$appPy = Join-Path $venv 'Scripts\python.exe'
$reqs = Join-Path $InstallDir 'studio\requirements.txt'
$appMark = 'app-' + (Get-FileHash -Algorithm SHA256 $reqs).Hash.Substring(0, 12).ToLower()
if (-not (IsDone $appMark) -or -not (Test-Path $appPy)) {
    # --no-bin: uv would also put a python3.13.exe in the user's own .local\bin, outside this folder, where
    # the uninstaller never looks and where an existing one of the user's makes it warn.
    Invoke-Checked 'Python for the app' $uv @('python', 'install', '--no-bin', $Pins.AppPython)
    if (-not (Test-Path $appPy)) { Invoke-Checked 'The app environment' $uv @('venv', '--python', $Pins.AppPython, $venv) }
    Invoke-Checked "The app's packages" $uv @('pip', 'install', '--python', $appPy, '-r', $reqs)
    # Stems run on the CPU, as in the app container: the GPU belongs to YuE2.
    Invoke-Checked 'Torch for stems' $uv @('pip', 'install', '--python', $appPy, 'torch==2.9.1', 'torchaudio==2.9.1', '--index-url', 'https://download.pytorch.org/whl/cpu')
    Invoke-Checked 'demucs' $uv @('pip', 'install', '--python', $appPy, 'demucs==4.1.0')
    Done $appMark
}
New-Item -ItemType Directory -Force -Path (Join-Path $InstallDir 'data') | Out-Null

# ------------------------------------------------------------------- models
if (-not $SkipModels) {
    Step 'The models (the long part)'
    $total = 0
    foreach ($m in $ModelFiles) { $total += $m.Size }
    Say ("{0} files, {1:N1} GB in all. Downloads resume if they break off." -f $ModelFiles.Count, ($total / 1e9))
    foreach ($m in $ModelFiles) {
        Say ''
        Say $m.Name 'White'
        New-Item -ItemType Directory -Force -Path (Join-Path $Models $m.Dir) | Out-Null
        Get-Verified $m (Join-Path (Join-Path $Models $m.Dir) $m.File)
    }
    # One size only: with the chosen one in place, the other is taken away, so the app uses what was chosen.
    $unchosen = Join-Path (Join-Path $Models 'checkpoints') $(if ($Int8) { $FullModel } else { $SmallModel })
    if (-not $Cpp -and (Test-Path $unchosen)) {
        Say ''
        Say ("Removing {0}: this install uses the {1} model." -f (Split-Path $unchosen -Leaf), $(if ($Int8) { 'low-memory' } else { 'full-quality' }))
        Remove-Item -Force $unchosen
    }
}

# ------------------------------------------------------ the app's own models
$dataDir = Join-Path $InstallDir 'data'
$ini = Join-Path $InstallDir 'settings.ini'
if (Test-Path $ini) {
    $line = Get-Content $ini | Where-Object { $_ -match '^\s*data_dir\s*=\s*(.+?)\s*$' } | Select-Object -First 1
    if ($line -and $Matches[1]) { $dataDir = $Matches[1] }
}

# Whisper (times the lyric lines of a cover) and demucs (separates the vocal) would
# otherwise download the first time a cover or stems are made, and leave that first
# go sitting on a 1.6 GB download.  Fetched with the app's own Python, by the same
# calls the app makes, so they land where it looks.
if (-not $SkipModels -and -not (IsDone 'app-models')) {
    Step "The app's own models (lyric timing and stems)"
    # As the launcher sets them for the app: demucs 4.1 fetches from Hugging Face, so
    # its model goes where HF_HOME says, and Whisper is given its folder directly.
    $env:TORCH_HOME = Join-Path $dataDir 'models\torch'
    $env:HF_HOME = Join-Path $dataDir 'models\whisper'
    $env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
    Say 'Whisper large-v3-turbo (about 1.6 GB)'
    $whisperDir = Join-Path $dataDir 'models\whisper'
    Invoke-Checked 'Whisper' $appPy @('-c', "from faster_whisper import download_model; download_model('large-v3-turbo', cache_dir=r'$whisperDir')")
    Say 'demucs htdemucs (about 80 MB)'
    Invoke-Checked 'demucs' $appPy @('-c', "from demucs.pretrained import get_model; get_model('htdemucs')")
    Done 'app-models'
}

# The engine's own copy of the Whisper model (the app keeps its own, for the CPU), as a plain folder the node uses as it
# stands. Fetched with the same download as the other models, so it shows its progress, resumes if it breaks off and is
# checked, and the first lyric hearing does not wait on 1.6 GB.
if (-not $Cpp -and -not $SkipModels -and -not (IsDone 'engine-whisper-model')) {
    Step 'Whisper for the engine (about 1.6 GB)'
    $whisperUrl = 'https://huggingface.co/dropbox-dash/faster-whisper-large-v3-turbo/resolve/main'
    $engineWhisper = Join-Path $Models 'whisper\large-v3-turbo'
    New-Item -ItemType Directory -Force -Path $engineWhisper | Out-Null
    $whisperFiles = @(
        @{ File = 'config.json'; Size = 2263 },
        @{ File = 'preprocessor_config.json'; Size = 340 },
        @{ File = 'tokenizer.json'; Size = 2710337 },
        @{ File = 'vocabulary.json'; Size = 1068114 },
        @{ File = 'model.bin'; Size = 1617884929; Sha = 'e76620f83d5f5b69efd3d87e3dc180c1bd21df9fbebacfd4335e5e1efcc018da' }
    )
    foreach ($f in $whisperFiles) {
        Get-Verified @{ Url = "$whisperUrl/$($f.File)"; Size = $f.Size; Sha = $f.Sha } (Join-Path $engineWhisper $f.File)
    }
    Done 'engine-whisper-model'
}

# The engine's own copy of the Demucs model (it keeps it with its models, found again after an update). Fetched now so
# the first separation does not wait on it; if this fails the node fetches it when it first runs.
if (-not $Cpp -and -not $SkipModels -and -not (IsDone 'engine-demucs-model')) {
    Say 'demucs htdemucs for the engine (about 80 MB)'
    $demucsDir = Join-Path $Models 'demucs'
    try {
        Invoke-Checked 'The engine demucs model' $py @('-s', '-c', "import torch; torch.hub.set_dir(r'$demucsDir'); from huggingface_hub import constants; constants.HF_HUB_CACHE = r'$demucsDir\hub'; from demucs.pretrained import get_model; get_model('htdemucs')")
        Done 'engine-demucs-model'
    } catch {
        Say "Could not fetch it now ($($_.Exception.Message)); the engine will when it first separates a vocal."
    }
}

# Gemma for the yue2.cpp engine, fetched by Ollama itself into the models folder: Ollama checks what it fetches.  A
# server of its own is started for it, on a port nothing else uses, and stopped again.
if ($Cpp -and -not $NoLyrics -and -not $SkipModels -and -not (IsDone "gemma-$($GemmaModel -replace '[:]', '-')")) {
    Step "Gemma for lyric drafts ($GemmaModel, about 6.1 GB)"
    $ollama = Join-Path $CppDir 'ollama\ollama.exe'
    $env:OLLAMA_MODELS = Join-Path $Models 'ollama'
    $env:OLLAMA_HOST = '127.0.0.1:11439'
    New-Item -ItemType Directory -Force -Path $env:OLLAMA_MODELS | Out-Null
    $serve = Start-Process -FilePath $ollama -ArgumentList 'serve' -WindowStyle Hidden -PassThru
    try {
        $up = $false
        for ($i = 0; $i -lt 60 -and -not $up; $i++) {
            Start-Sleep -Seconds 1
            & curl.exe -s -o NUL --max-time 2 "http://$($env:OLLAMA_HOST)/api/tags"
            $up = $LASTEXITCODE -eq 0
        }
        if (-not $up) { Stop-Setup 'Ollama did not start, so Gemma could not be fetched' }
        & $ollama pull $GemmaModel
        if ($LASTEXITCODE -ne 0) { Stop-Setup 'Gemma could not be fetched; run the installer again to carry on' }
        Done "gemma-$($GemmaModel -replace '[:]', '-')"
    } finally {
        if ($serve -and -not $serve.HasExited) { Stop-Process -Id $serve.Id -Force -ErrorAction SilentlyContinue }
        Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like (Join-Path $CppDir 'ollama\*') } |
            ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Remove-Item Env:OLLAMA_HOST, Env:OLLAMA_MODELS -ErrorAction SilentlyContinue
    }
}

# Which engine the launcher starts: remembered in settings.ini, where Repair reads it back.
Set-IniValue $settingsIni 'engine' $EngineKind
if ($Cpp) { Set-IniValue $settingsIni 'gemma_model' $GemmaModel }

# ---------------------------------------------------------------- soundfonts
if (-not $SkipModels) {
    Step "SoundFonts for MIDI playback"
    $sf2Dir = Join-Path $dataDir 'models\soundfonts\sf2'
    New-Item -ItemType Directory -Force -Path $sf2Dir | Out-Null
    foreach ($sf in $SoundFontFiles) {
        Say ''
        Say $sf.Name 'White'
        Get-Verified $sf (Join-Path $sf2Dir $sf.File)
    }
}

# -------------------------------------------------------------------- done
# uv's download cache is only needed while installing.
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $env:UV_CACHE_DIR
Step 'Finished'
Say ("Yeufonic is set up, with the {0} engine. Start it from the Start menu or the desktop." -f $(if ($Cpp) { 'yue2.cpp' } else { 'ComfyUI' })) 'Green'
Stop-Transcript | Out-Null
exit 0
