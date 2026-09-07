# Call my Mac（打电话控制我的 Mac）

> 用 iPhone 打电话给自己的 Mac：本地 Agent 接听、理解意图、安全地操控本机。大脑稍后可换成本地 LLM。

面向用户：**大仁**。本仓库是可运行的脚手架（Phase 0 文本通路已通），不是空文档。

---

## 一句话产品

**iPhone 呼叫 → Tailscale 上的 Mac Companion → 可插拔 Agent → 白名单动作控制 Mac。**

相关先验（仅作参考，非本产品主线）：ChatGPT Codex Voice、官方 Remote 类方案。本项目强调 **本地 Agent + 可换模型后端 + 可控安全边界**。

---

## 架构一览

```
iPhone (SwiftUI)  --WebSocket/REST-->  Mac Companion (Python FastAPI)
                                           |
                                           v
                                    AgentBackend (可插拔)
                                      ├── StubAgent      (短语 → 白名单动作)
                                      └── LocalLLMAgent  (TODO: Ollama / llama.cpp)
                                           |
                                           v
                                    Capability stubs (allowlisted Mac actions, dry-run 默认)
```

详情见 [ARCHITECTURE.md](./ARCHITECTURE.md)、信令与消息见 [protocol/PROTOCOL.md](./protocol/PROTOCOL.md)。

---

## 阶段计划

| Phase | 目标 | 状态 |
|-------|------|------|
| **0** | 文本模拟通话：`demo-call-sim` → Companion → Agent 回路 | ✅ 本脚手架 |
| **1** | 真双工音频（WebRTC 目标；PCM 占位可过渡） | 文档 + 接口预留 |
| **2** | 接入本地 LLM（Ollama / llama.cpp OpenAI 兼容端点） | `LocalLLMAgent` stub |
| **3** | Wake-on-LAN / 远程唤醒 | 未实现 |

---

## 快速开始（Mac Companion）

在 **Mac** 上（本 Linux 脚手架也可跑文本通路）：

```bash
cd mac
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 生成配对 Token（首次）
export CALL_MY_MAC_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(24))')"
echo "你的配对 Token: $CALL_MY_MAC_TOKEN"

# 默认 dry-run（安全）；真执行需显式关闭
export CALL_MY_MAC_DRY_RUN=1
export CALL_MY_MAC_HOST=0.0.0.0
export CALL_MY_MAC_PORT=8742

uvicorn app:app --host "$CALL_MY_MAC_HOST" --port "$CALL_MY_MAC_PORT"
```

健康检查：

```bash
curl -s http://127.0.0.1:8742/health
curl -s -X POST -H "Authorization: Bearer $CALL_MY_MAC_TOKEN" \
  -H "Content-Type: application/json" -d '{}' \
  http://127.0.0.1:8742/v1/session
```

生产建议：只在 **Tailscale IP** 上监听（或防火墙限制），不要裸露公网。

---

## 跑通 Demo（文本「打电话」）

另开终端（同一 venv 或保证依赖可用）：

```bash
export CALL_MY_MAC_TOKEN='你的token'
export CALL_MY_MAC_BASE='http://127.0.0.1:8742'
./scripts/demo-call-sim.sh
```

脚本会：建会话 → 发送多条中英文 utterance → 打印 Agent 回复与拟执行动作。

---

## 目录

```
call-my-mac/
  README.md
  ARCHITECTURE.md
  protocol/PROTOCOL.md
  mac/                 # Python FastAPI Companion
  agent/               # 可插拔 Agent（也被 mac 引用）
  ios/CallMyMac/       # SwiftUI 骨架（需 Xcode）
  scripts/demo-call-sim.sh
```

---

## 你还需要准备的

| 项 | 说明 |
|----|------|
| **Tailscale** | iPhone ↔ Mac 私有组网；Companion 绑 Tailscale IP |
| **Xcode** | 编译 `ios/` SwiftUI 工程（本 Linux 箱无法真编 iOS） |
| **本地模型（Phase 2）** | Ollama 或 llama.cpp 的 OpenAI 兼容 `/v1/chat/completions` |
| **真音频（Phase 1）** | WebRTC / STT-TTS；当前为文本控制面 |
| **Cursor Origin** | 后续若用 Cloud Agent 做深度开发，需 Origin namespace；本仓库是 starter |

---

## 安全要点（务必读）

- 动作 **白名单**；禁止模型输出直接 `eval` / 任意 shell。
- 默认 **`CALL_MY_MAC_DRY_RUN=1`**：只记录拟执行命令，不真正跑。
- 需确认的危险类动作走 `needs_confirmation`；客户端应二次确认后再 `POST /v1/confirm`。
- Bearer **配对 Token** 等同设备密钥，勿提交到 Git。

---

## License / 状态

个人脚手架 · MVP Phase 0。接口会变，以 `protocol/PROTOCOL.md` 为准。
