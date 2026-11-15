# Windows 无 Mac 用 Pinky 连接 iPhone（iOS 27+）

一句话：**Windows 上 Pinky 连 iPhone 唯一的真坑是开发者磁盘映像（iOS_DDI）下不下来**。
镜像没失效，是 Pinky 直连 `raw.githubusercontent.com` 超时。换条 CDN 线路把文件放到指定目录即可。
iOS 27 及以上**不需要 Mac、不需要 Xcode、不需要在手机上装任何 App、不需要 TestFlight 邀请链接**。

> 实测环境：Windows 11 / iPhone 15 Pro Max / iOS 27.2 / Pinky 2026-1115 版。

## 快速开始（三选一）

| 方式 | 做法 | 适合 |
|---|---|---|
| **A. 一键脚本（推荐）** | `python fetch_pinky_ddi.py` | 想从上游拉取并逐个校验，最干净 |
| **B. 现成压缩包** | 到 [Releases](https://github.com/miaopasi677/pinky-windows-ddi-guide/releases) 下载 `pinky-ios-ddi-27A5228h.zip`，解压后把 `iOS_DDI` 放到 `%LOCALAPPDATA%\Pinky\DeveloperDiskImages\` | 网络实在拉不到 CDN |
| **C. 手动** | 按下方「方案 B」逐文件下载、改名、校验 | 想完全掌控每一步 |

脚本会自动：并发从 jsDelivr 拉取 → 失败切 fastly / ghfast / raw → 按 Pinky 源码固钉的
**size + SHA-256 逐个校验** → 检查 `BuildManifest.plist` 里 `Personalize=true` 的路径齐全 →
组装成 Pinky 下载成功后应有的目录。任何一个文件校验不过就**不会**安装。

## 仓库文件

| 文件 | 说明 |
|---|---|
| `README.md` | 完整教程（含三个坑、错误速查表、7 文件校验清单） |
| `fetch_pinky_ddi.py` | 一键下载 + 校验 + 安装脚本，仅依赖 Python 标准库和 `curl` |
| `SHA256SUMS.txt` | `iOS_DDI` 内 8 个文件的 SHA-256 |
| `NOTICE.md` | 来源与版权声明 |
| Releases 里的 zip | 现成的 `iOS_DDI` 文件夹（Apple 的文件，见 NOTICE） |

---

> 适用：Windows 10/11 + Pinky 桌面端 + iOS 27 及以上 iPhone，没有 Mac、拿不到 Xcode。
> 不适用：iOS 17.4–26 的 iPhone —— 那个版本区间的"辅助应用"目前**必须**用 Mac + Xcode 构建，本文的 DDI 方案只能解决一半（能看画面、不能点按）。
> 本文实测环境：Windows 11 / iPhone 15 Pro Max / iOS 27.2 / Pinky 2026-1115 版。

---

## 0. 一句话结论

Windows 上 Pinky 连 iPhone 只有**一个真坑**：Apple 开发者磁盘映像（iOS_DDI）下不下来。
把映像放到 Pinky 指定目录后，**iOS 27 及以上不需要在手机上装任何 App**，也不需要 Mac、不需要 TestFlight 邀请链接。

---

## 1. 前置准备（手机侧，只需一次）

1. 数据线连接 iPhone 与电脑，解锁，弹窗点「信任此电脑」并输入锁屏密码。
2. Windows 从 Microsoft Store 安装「Apple 设备」App（或苹果官网的 iTunes）。
3. 手机「设置 › 隐私与安全性 › 开发者模式」打开开关 → 重启 → 解锁 → 点「打开」→ 输入锁屏密码。
4. 全程保持手机**解锁**。

---

## 2. 坑一：开发者磁盘映像下载失败（最常见）

### 现象

「添加手机 › iPhone」提示"这台电脑上还没有开发者磁盘映像"，点「下载（32MB）」后报：

```
下载没有成功。
downloading Xcode_iOS_DDI_Cryptex/BuildManifest.plist:
Get "https://raw.githubusercontent.com/doronz88/DeveloperDiskImage/
e2aaeac89ca8fa56c2fa1f144d182994e07a525b/...":
net/http: TLS handshake timeout
```

有时错误后半段是 `wsarecv: A connection attempt failed...`，本质是同一件事。

### 根因：**不是镜像失效，是网络**

- Pinky 用 Go 的 `net/http` 直连 `raw.githubusercontent.com`，**不读本机代理**，在国内网络下经常 TLS 握手超时或只下载到几百 KB 就断。
- 镜像仓库 `github.com/doronz88/DeveloperDiskImage` 的 pinned commit `e2aaeac89ca8fa56c2fa1f144d182994e07a525b` 里的文件**一个都没少**，逐个核对过大小与 SHA-256。
- 所以正解是：**同一份文件，换一条能到达的线路**，而不是换仓库、更不是找"网盘转存"。

### 三条可用线路实测（同一台机器）

| 线路 | 结果 |
|---|---|
| `cdn.jsdelivr.net/gh/...` | ✅ 最快，30.9 MB 约 1 分钟下完 |
| `fastly.jsdelivr.net/gh/...` | ✅ 可用（脚本里的备用） |
| `ghfast.top/https://raw.githubusercontent.com/...` | ✅ 可用（脚本里的备用） |
| `raw.githubusercontent.com` | ❌ 40 秒只下到 753 KB，超时 |
| `github.com/.../raw`、GitHub blob API | ❌ 连接被重置 / 极慢 |

把 raw 域名替换成 CDN 即可，路径完全一致：

```
https://cdn.jsdelivr.net/gh/doronz88/DeveloperDiskImage@<COMMIT>/PersonalizedImages/<子路径>
```

### 方案 A：一键脚本（推荐）

用随本文附带的 `fetch_pinky_ddi.py`，它会：

1. 并发从 jsDelivr 拉取 7 个文件，失败自动切 fastly / ghfast / raw；
2. **逐个按 Pinky 源码里固钉的 size + SHA-256 校验**，任何一个不匹配就不安装；
3. 按 `BuildManifest.plist` 里 `Personalize=true` 的 `Info.Path` 检查文件齐全；
4. 自动组装成 Pinky 下载成功后应有的目录，写入两个位置。

```bash
python fetch_pinky_ddi.py
```

脚本顶部常量可改：`COMMIT` / `BUILD` / `ROOT`（Pinky 数据目录）。

### 方案 B：手动下载（不想跑脚本）

7 个文件，源路径都在 `PersonalizedImages/` 下，目标路径都在 `iOS_DDI/Restore/` 下：

| 源路径 | 目标路径 | 字节 | SHA-256 |
|---|---|---:|---|
| `Xcode_iOS_DDI_Cryptex/BuildManifest.plist` | `BuildManifest.plist` | 804946 | `27385d7582b03b36bb3104e22b520aee0c47d72fecb4e8ecfe12ef5d966c7012` |
| `Xcode_iOS_DDI_Cryptex/Image.dmg` | `Image.dmg` | 15895040 | `873097f695a8b9734e2abc54f795a8874d40ff6fd11208ecb01ef29534c7c176` |
| `Xcode_iOS_DDI_Cryptex/Image.dmg.cryptex_info` | `Image.dmg.cryptex_info` | 430 | `edf49aef55aacc063d4d7be05b713bb545ce2993b3f62bcc15eccd75e610ee6c` |
| `Xcode_iOS_DDI_Cryptex/Image.dmg.root_hash` | `Image.dmg.root_hash` | 229 | `3543fad2805b88119695c417e12679380b3b5a2742994bbcc839c8e2de5d7302` |
| `Xcode_iOS_DDI_Cryptex/Image.dmg.trustcache` | `Image.dmg.trustcache` | 1895 | `f7f21986074eee03a215aca16ecfc78d6bf183600d8a0d2fb691f9896782e6f0` |
| `Xcode_iOS_DDI_Personalized/Image.dmg` | `022-22070-072.dmg` | 15733248 | `05fd807da5e19f030fa4941f24800c965c6c77982ab572dd5d1ef778fb69f9ca` |
| `Xcode_iOS_DDI_Personalized/Image.dmg.trustcache` | `Firmware/022-22070-072.dmg.trustcache` | 1895 | `36af60889ff5a737874a26daeb8e1a0139ebfebec6ec2e4d8f6a3c1bf1dce35c` |

注意最后两个「personalized 半边」要**改名**：镜像仓库里的扁平文件名是 `Image.dmg` / `Image.dmg.trustcache`，Pinky 要的是 Apple 原名 `022-22070-072.dmg` 和 `Firmware/022-22070-072.dmg.trustcache`。漏了这两个，`BuildManifest.plist` 检查会报"incomplete"。

### 方案 C：直接用现成压缩包

`pinky-ios-ddi-27A5228h.zip`（31.6 MB）解压后把 `iOS_DDI` 整个文件夹放到下面目录即可，包内附 `SHA256SUMS.txt` 和安装说明。

### 目标目录（照抄）

```
C:\Users\<你的用户名>\AppData\Local\Pinky\DeveloperDiskImages\
├── iOS_DDI\                 ← 界面上「从 Mac 复制」对应的位置，主用
│   ├── version.plist
│   └── Restore\
│       ├── BuildManifest.plist
│       ├── Image.dmg
│       ├── Image.dmg.cryptex_info
│       ├── Image.dmg.root_hash
│       ├── Image.dmg.trustcache
│       ├── 022-22070-072.dmg
│       └── Firmware\022-22070-072.dmg.trustcache
└── iOS_DDI-mirror\         ← Pinky 自己下载成功后会放的目录（同样内容，建议一并放）
```

`version.plist` 内容（XML plist，三个键）：

```xml
ProductBuildVersion = 27A5228h
Source              = https://github.com/doronz88/DeveloperDiskImage
SourceCommit        = e2aaeac89ca8fa56c2fa1f144d182994e07a525b
```

> 为什么放两份：`iOS_DDI` 是官方拷贝路径，优先级最高；`iOS_DDI-mirror` 是 Pinky 判定"Apple 拒签官方映像"后的回退路径。两个都放，覆盖所有分支。

### 验证是否成功

不用重启 Pinky（它每轮发现设备都会重新扫描目录），看日志
`%LOCALAPPDATA%\Pinky\pinky.log`：

```
INFO  iphone: mounting the developer disk image ... image="the image in Pinky's folder 27A5228h"
INFO  iphone: developer disk image ready ... way=cryptex
INFO  device online ... connection=usb
INFO  pinky: mirror ...: stream opened
```

看到 `developer disk image ready` 就成了。

---

## 3. 坑二：误以为还要装「iPhone 上的 Pinky（WebDriverAgent）」

### 现象

在「选择连接方式」页面看到：

> 支持 iOS 17.4 及以上，而且不共享屏幕，拒绝屏幕共享的银行 App 照常能用。需要先在装有 Xcode 的 Mac 上装一次 iPhone 上的 Pinky……这台 iPhone 还没装 Pinky。

### 真相

这是**选项卡里的一个可选项**，不是待办步骤。README 原文：**iOS 27 及以上无需在手机上安装任何 App**；WDA 辅助应用只在 iOS 17.4–26 是必需的，在 iOS 27 上属于"你的选择"。

| 连接方式 | 要装 App | 要 Mac | 效果 |
|---|---|---|---|
| **自动（推荐）** | 否 | 否 | iOS 27+ 全功能（除双指缩放），读屏 <0.5 秒 |
| CoreDevice | 否 | 否 | 同上，画面最流畅；部分银行 App 会因"屏幕共享"拒绝运行 |
| iPhone 上的 Pinky（WDA） | 是 | 首次必须 | 不共享屏幕、可双指缩放；但读屏约 7 秒、画面慢、iOS 不时讨密码、免费 Apple ID 每 7 天重签 |

**操作**：「设置 › 手机」把连接方式选成 **「自动」**，回手机页即为"已就绪"。

### 关于"找 TestFlight 邀请链接"

这条路原理上不存在，教程里应写明，免得读者白找：

- 官方开发笔记原话：*"It is sideloaded only: it uses Apple's developer services, which App Review never allows."* —— 用私有开发者服务的 App 过不了 Apple 审核，不会有 App Store 版，也不会有 TestFlight 公开邀请链接。
- Release 里的 `pinky-iphone-<版本>.tar.gz` 是**源码包**（Xcode 工程 + Swift + Go core），不是签名 IPA，仍需 Xcode 构建。
- WDA 必须用**本人 Apple ID 证书 + 含本机 UDID 的描述文件**签名，别人签的 IPA 装不上；网上"共享企业证书/在线签名"要交 Apple ID 密码，证书随时会被吊销，不建议。
- 源码 `internal/driver/ios/helperinstall.go` 里写死了 `installing Pinky on the iPhone needs a Mac with Xcode`。
- 补充：Pinky 默认安全策略本就把银行、钱包、密码管理器类 App 对 AI 隐身，装了 WDA 也不代表能让 AI 操作它们。

无 Mac 又一定要这个可选增强的话，只能借 Mac 或用云 macOS（GitHub Actions 的 macOS runner）构建 IPA，再在 Windows 侧用 Sideloadly / SideStore 侧载；官方不支持这条路，7 天续签问题依旧。性价比很低。

---

## 4. 坑三：`the iPhone is locked`

```
WARN iphone: could not mount the developer disk image ... err="the iPhone is locked" retry_in=3s
```

纯手机侧问题：**解锁 iPhone、保持屏幕亮着、线插着**。Pinky 每 3 秒自动重试，解锁后约 8 秒完成挂载。这一步不需要改电脑上的任何东西。

---

## 5. 常见错误速查

| 报错 / 现象 | 原因 | 处理 |
|---|---|---|
| `TLS handshake timeout` / `wsarecv` | Pinky 直连 raw.githubusercontent.com 超时 | 用 CDN 通道下载，见第 2 节 |
| 下载到一半 `schannel: server closed abruptly` | 同上，连接被掐 | 换 jsDelivr，脚本已自动重试 |
| `the downloaded developer disk image is incomplete` | 少了 personalized 半边或没改名 | 核对第 2 节 7 文件表 |
| `the iPhone is locked` | 手机锁屏 | 解锁并保持亮屏 |
| `Apple 不再为这个开发者磁盘映像签名` | iOS 太新，27A5228h（beta 4）已不被签名 | 需更新的 Xcode 27 正式版 DDI，或等 Pinky 更新固钉版本 |
| 界面说"这台 iPhone 还没装 Pinky" | 停在 WDA 选项卡上 | 连接方式改「自动」 |
| 镜像流打不开 / 相机黑屏 | 手机正在使用相机或麦克风 | 关掉通话/相机，Pinky 会自动重连 |

---

## 6. 附录

- **版权与来源**：DDI 是 Apple 随 Xcode 分发的文件，由 pymobiledevice3 作者 doronz88 在 `DeveloperDiskImage` 仓库转存，仅供 Windows/Linux 互操作使用，不是 Apple 官方发布。推荐教程引导读者**用脚本从上游仓库拉取并校验**，而不是传播打包文件。
- **Pinky 源码参考**：`internal/driver/ios/mirror.go`（文件清单、size、SHA-256、下载后目录布局）、`internal/driver/ios/ddi.go`（目录优先级、`checkManifestFiles`）、`cmd/pinky/locales/zh-Hans.json`（中文界面文案）。
- **本文附带文件**：`fetch_pinky_ddi.py`（下载+校验+安装脚本）、`pinky-ios-ddi-27A5228h.zip`（现成压缩包，含 SHA256SUMS）。
- **实测结论**：iOS 27 的 DDI 以 cryptex 方式挂载，重启后仍在；Pinky 也支持随后拔线走 Wi-Fi。

---

# 来源与版权声明

- 本仓库的 **教程文字与脚本** 由整理者编写，采用 MIT 许可。
- `pinky-ios-ddi-27A5228h.zip` 及其中的 `Image.dmg`、`BuildManifest.plist` 等文件是
  **Apple 随 Xcode 分发的开发者磁盘映像**，Apple 保留全部权利。本仓库不主张其所有权，
  也未修改这些文件（仅重新打包并附校验值）。
- 原始转存来源：[github.com/doronz88/DeveloperDiskImage](https://github.com/doronz88/DeveloperDiskImage)，
  由 pymobiledevice3 作者维护，**不是 Apple 官方**；固定 commit
  `e2aaeac89ca8fa56c2fa1f144d182994e07a525b`（Xcode 27.0 beta 4 / build `27A5228h`）。
- 这些文件仅用于 **Windows / Linux 上与本人设备的互操作**（Apple 未提供这些平台的 Xcode）。
  使用它们仍需 iOS 开发者模式、Apple 对每台设备的签名，不绕过 Apple 的任何保护机制。
- [Pinky](https://github.com/DIYgod/pinky) 本身不附带、不托管 Apple 的文件。
- **推荐优先使用 `fetch_pinky_ddi.py` 从上游仓库自行拉取**，而不是依赖本仓库的二进制副本。
- 权利人如要求移除，请提 issue，我们会尽快删除对应的 Release 附件。

本仓库与 Apple Inc.、Pinky 项目、doronz88 均无隶属或背书关系。
