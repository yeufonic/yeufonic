<p align="center">
  <img src="docs/readme/banner.svg" alt="Yeufonic" width="100%">
</p>

<p align="center"><b>带可编辑乐谱的完整歌曲，由 YuE2 在你自己的 GPU 上生成。</b></p>

<p align="center">
  <img src="docs/readme/chips-zh-CN.svg" alt="从提示词写歌 · 翻唱你的录音 · 纯音乐 · 风格 LoRA：自己训练或导入 · 嗓音：自己训练或导入 · 分轨与母带"><br>
  <img src="docs/readme/chip-engines-zh-CN.svg" alt="两种引擎：ComfyUI 或 yue2.cpp"><a href="https://yeufonic.com/examples/"><img src="docs/readme/chip-examples-zh-CN.svg" alt="yeufonic.com 上的示例"></a>
</p>

<p align="center">
  <a href="https://github.com/yeufonic/yeufonic/releases/latest"><img src="docs/readme/windows.svg" alt="Windows" height="44"></a>
  <a href="https://yeufonic.com/macos/"><img src="docs/readme/macos.svg" alt="macOS" height="44"></a>
  <a href="#用-docker-快速开始"><img src="docs/readme/docker.svg" alt="Docker" height="44"></a>
  <a href="https://yeufonic.com"><img src="docs/readme/website.svg" alt="yeufonic.com" height="44"></a>
</p>

<p align="center">
  <a href="https://github.com/yeufonic/yeufonic/releases/latest"><img src="https://img.shields.io/github/v/release/yeufonic/yeufonic?style=flat-square&label=%E7%89%88%E6%9C%AC&labelColor=17121f&color=7b5cff" alt="版本"></a>
  <a href="https://github.com/yeufonic/yeufonic/releases"><img src="https://img.shields.io/github/downloads/yeufonic/yeufonic/total?style=flat-square&label=%E4%B8%8B%E8%BD%BD&labelColor=17121f&color=b04dff" alt="下载"></a>
  <a href="https://github.com/yeufonic/yeufonic/stargazers"><img src="https://img.shields.io/github/stars/yeufonic/yeufonic?style=flat-square&label=%E6%98%9F%E6%A0%87&labelColor=17121f&color=d94dc4" alt="星标"></a>
  <a href="https://github.com/yeufonic/yeufonic/commits/main"><img src="https://img.shields.io/github/last-commit/yeufonic/yeufonic?style=flat-square&label=%E6%9C%80%E8%BF%91%E6%8F%90%E4%BA%A4&labelColor=17121f&color=ff4d94" alt="最近提交"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/%E8%AE%B8%E5%8F%AF-%E4%B8%AA%E4%BA%BA%E9%9D%9E%E5%95%86%E4%B8%9A-fb923c?style=flat-square&labelColor=17121f" alt="许可: 个人非商业"></a>
</p>

<p align="center"><a href="README.md">English</a> · <a href="README.de.md">Deutsch</a> · <a href="README.es.md">Español</a> · <a href="README.fr.md">Français</a> · <a href="README.it.md">Italiano</a> · <a href="README.nl.md">Nederlands</a> · <a href="README.pt.md">Português</a> · <a href="README.ru.md">Русский</a> · <a href="README.ja.md">日本語</a> · <a href="README.ko.md">한국어</a> · <b>简体中文</b> · <a href="README.zh-TW.md">繁體中文</a></p>

---

> 本页为机器翻译，比包含全部细节的[英文 README](README.md) 更简短。完整的中文指南在应用内（帮助）以及这里：**[中文指南](app/static/guides/zh-CN.md)**。

一个为开放音乐模型 [YuE2](https://github.com/multimodal-art-projection/YuE) 打造的网页界面。用提示词写歌，或翻唱你自己的录音。用一组音乐在本地训练 LoRA。两种方式都能编辑乐谱，然后从成品中分离出分轨。

## 它能做什么

- **从提示词写歌：**根据风格和歌词写出乐谱方案，编辑后渲染。
- **选择引擎：**带 YuE2 节点的 ComfyUI，或适合小显卡的 yue2.cpp（GGUF）。
- **翻唱录音：**把你的歌转成乐谱，修改旋律与和弦，渲染出新版本。
- **纯音乐：**逐段搭建结构，或演奏一段录音的乐谱。
- **录一段旋律：**唱、哼或用乐器弹，把几个小节扩展成整首歌。
- **MIDI 导入**，用于翻唱和纯音乐，带钢琴卷帘和 SF2 音色。
- **风格 LoRA：**使用已发布的，或用 ComfyUI 引擎从一个歌曲文件夹训练你自己的。
- **录制的嗓音：**用你自己的歌声训练嗓音，让任何版本都用它来唱。
- **歌词与对唱：**一句话起草歌词，或从录音中听写；为男声、女声或合唱指定歌词行。
- **复古母带机架与 3D Space：**实时 EQ、压缩器和限制器；耳机空间声与 5.1。
- **分轨与 DAW：**把版本拆成音轨，或存为包含音频、分轨、MIDI 和乐谱的 zip。
- **资料库：**空间、星标、备注，以及可连同录音一起分享的版本文件。
- **歌曲配图**可用本地模型或你自己的外部 LLM，还有面向 AI 代理的 **MCP 服务器**。
- **版本面板和编辑器：**左侧面板显示所选版本是如何做出来的；一个大窗口（三栏或分步显示）是制作和修改版本的地方。
- **十五种语言：**应用和指南均为机器翻译。
- 用 Yeufonic 制作的**示例 LoRA 和歌曲**：**[示例](https://yeufonic.com/examples/)**。

一切都在一台电脑上运行，分为两部分：应用和引擎。不用云端，也不用账号；写歌词的外部 LLM 是可选的。

## 需求

- 建议使用 12 GB 显存以上的 NVIDIA 显卡和 16 GB 内存。8 GB 显卡也值得一试；更小的显卡可用 INT8 模型或 yue2.cpp 引擎。
- 在本地训练 LoRA 实际需要 16 GB 显存和 32 GB 内存（INT8 模型只需 8 GB 显存）。
- 约 30 GB 可用磁盘空间，资料库变大后需要更多。
- Apple 芯片的 Mac 也能完成所有功能，包括训练 LoRA，但比 NVIDIA 显卡慢得多：见 **[yeufonic.com/macos](https://yeufonic.com/macos/)**。

## 在 Windows 上，无需 Docker

一个小安装程序可在 Windows 上原生安装 Yeufonic，无需 Docker、WSL 或管理员权限。从**[最新版本](https://github.com/yeufonic/yeufonic/releases/latest)**下载并运行：它会先检查电脑，再下载约 27 GB（大部分是模型）。新版安装程序会更新已有的安装。需要 Windows 10 22H2 或 Windows 11（64 位），以及 NVIDIA RTX 30 系列或更新的显卡。

## 用 Docker 快速开始

在 Linux，或装有 WSL2 的 Windows 上，配合 Docker 和 NVIDIA Container Toolkit：

```sh
git clone https://github.com/yeufonic/yeufonic.git
cd yeufonic
sh scripts/fetch-models.sh          # 约 19 GB，同时创建文件夹
docker compose up -d --build
```

然后打开 <http://localhost:8090>。各种选项（较小的模型、yue2.cpp、图像模型、风格 LoRA）见[英文 README](README.md#quick-start)。

## 更多

- **[完整的中文指南](app/static/guides/zh-CN.md)**，也可在应用的帮助中阅读。
- 用 Yeufonic 制作的**[示例歌曲和 LoRA](https://yeufonic.com/examples/)**。
- 问题与建议：[GitHub Issues](https://github.com/yeufonic/yeufonic/issues)（最好用英文）。

## 许可

Yeufonic 采用个人非商业使用许可：见 [LICENSE](LICENSE)。模型、LoRA 和其他组件各有其许可，[英文 README](README.md#credits) 中有列出。
