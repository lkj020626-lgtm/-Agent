# 基于大模型的代码辅助开发 Agent（完整项目代码）

这是一个可直接运行的「代码辅助开发 Agent」项目，支持：

* 多轮对话
* 文件读写
* Shell 命令执行
* 自动生成代码
* 自动修复 Bug
* 项目结构分析
* 基于大模型的 Agent 调度
* Web API
* 简单前端页面

技术栈：

* Python 3.11+
* FastAPI
* OpenAI API（兼容 DeepSeek / Qwen / OpenRouter）
* React（可选）
* LangChain（轻量使用）

---

# 一、项目结构

```bash
code-agent/
│
├── backend/
│   ├── app.py
│   ├── agent.py
│   ├── tools.py
│   ├── memory.py
│   ├── config.py
│   ├── requirements.txt
│   └── workspace/
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
│
└── README.md
```

---

# 二、安装依赖

## backend/requirements.txt

```txt
fastapi
uvicorn
openai
langchain
python-dotenv
pydantic
```

安装：

```bash
pip install -r requirements.txt
```

---

# 三、配置文件

## backend/config.py

```python
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
WORKSPACE = "workspace"
```

---

# 四、记忆模块

## backend/memory.py

```python
class ConversationMemory:
    def __init__(self):
        self.messages = []

    def add(self, role, content):
        self.messages.append({
            "role": role,
            "content": content
        })

    def get(self):
        return self.messages

    def clear(self):
        self.messages = []
```

---

# 五、工具系统

## backend/tools.py

```python
import os
import subprocess
from config import WORKSPACE


class ToolManager:

    @staticmethod
    def read_file(path):
        full_path = os.path.join(WORKSPACE, path)

        if not os.path.exists(full_path):
            return "文件不存在"

        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def write_file(path, content):
        full_path = os.path.join(WORKSPACE, path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"文件已写入: {path}"

    @staticmethod
    def list_files():
        result = []

        for root, dirs, files in os.walk(WORKSPACE):
            for file in files:
                result.append(os.path.join(root, file))

        return "\n".join(result)

    @staticmethod
    def run_command(command):
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=WORKSPACE,
                timeout=30
            )

            return result.stdout + "\n" + result.stderr

        except Exception as e:
            return str(e)
```

---

# 六、Agent 核心

## backend/agent.py

```python
import json
from openai import OpenAI

from config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    MODEL_NAME
)

from memory import ConversationMemory
from tools import ToolManager


client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)


memory = ConversationMemory()


SYSTEM_PROMPT = """
你是一个专业代码开发 Agent。

你的能力：
1. 编写代码
2. 修复 bug
3. 自动创建文件
4. 自动分析项目
5. 自动执行 shell 命令
6. 自动生成完整项目

你可以调用以下工具：

read_file(path)
write_file(path, content)
list_files()
run_command(command)

当你需要调用工具时，必须返回如下 JSON：

{
  "tool": "tool_name",
  "args": {
    "path": "xxx"
  }
}

否则直接输出普通文本。
"""


class CodeAgent:

    def __init__(self):
        memory.add("system", SYSTEM_PROMPT)

    def ask_llm(self, user_input):

        memory.add("user", user_input)

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=memory.get(),
            temperature=0.2
        )

        content = response.choices[0].message.content

        memory.add("assistant", content)

        return content

    def handle_tool(self, tool_json):

        tool_name = tool_json.get("tool")
        args = tool_json.get("args", {})

        if tool_name == "read_file":
            return ToolManager.read_file(args.get("path"))

        elif tool_name == "write_file":
            return ToolManager.write_file(
                args.get("path"),
                args.get("content")
            )

        elif tool_name == "list_files":
            return ToolManager.list_files()

        elif tool_name == "run_command":
            return ToolManager.run_command(
                args.get("command")
            )

        return "未知工具"

    def run(self, user_input):

        result = self.ask_llm(user_input)

        try:
            tool_json = json.loads(result)

            tool_result = self.handle_tool(tool_json)

            memory.add(
                "tool",
                tool_result
            )

            final_answer = self.ask_llm(
                f"工具执行结果:\n{tool_result}"
            )

            return {
                "type": "tool",
                "tool": tool_json,
                "tool_result": tool_result,
                "final_answer": final_answer
            }

        except:
            return {
                "type": "text",
                "content": result
            }
```

---

# 七、FastAPI 服务

## backend/app.py

```python
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from agent import CodeAgent


app = FastAPI()

agent = CodeAgent()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {
        "message": "Code Agent Running"
    }


@app.post("/chat")
def chat(req: ChatRequest):

    result = agent.run(req.message)

    return result
```

---

# 八、前端页面

## frontend/index.html

```html
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>Code Agent</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>

<div class="container">

    <h1>AI Code Agent</h1>

    <div id="chat-box"></div>

    <div class="input-area">
        <input id="message" placeholder="请输入需求...">
        <button onclick="sendMessage()">发送</button>
    </div>

</div>

<script src="app.js"></script>
</body>
</html>
```

---

## frontend/style.css

```css
body {
    font-family: Arial;
    background: #f5f5f5;
}

.container {
    width: 800px;
    margin: 50px auto;
    background: white;
    padding: 20px;
    border-radius: 10px;
}

#chat-box {
    height: 500px;
    overflow-y: auto;
    border: 1px solid #ddd;
    padding: 10px;
    margin-bottom: 20px;
}

.message {
    margin-bottom: 10px;
    padding: 10px;
    border-radius: 6px;
}

.user {
    background: #d8ecff;
}

.ai {
    background: #ececec;
}

.input-area {
    display: flex;
}

input {
    flex: 1;
    padding: 10px;
}

button {
    width: 100px;
}
```

---

## frontend/app.js

```javascript
async function sendMessage() {

    const input = document.getElementById("message")
    const text = input.value

    addMessage(text, "user")

    input.value = ""

    const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: text
        })
    })

    const data = await response.json()

    addMessage(JSON.stringify(data, null, 2), "ai")
}


function addMessage(text, role) {

    const box = document.getElementById("chat-box")

    const div = document.createElement("div")

    div.className = `message ${role}`

    div.innerText = text

    box.appendChild(div)
}
```

---

# 九、环境变量

## backend/.env

```env
OPENAI_API_KEY=你的KEY

# OpenAI 官方
OPENAI_BASE_URL=https://api.openai.com/v1

# DeepSeek
# OPENAI_BASE_URL=https://api.deepseek.com/v1

MODEL_NAME=gpt-4.1-mini
```

---

# 十、启动项目

## 启动后端

```bash
cd backend
uvicorn app:app --reload
```

---

## 启动前端

直接双击：

```bash
frontend/index.html
```

或者：

```bash
python -m http.server 5500
```

---

# 十一、测试示例

输入：

```text
帮我创建一个 Flask 博客项目
```

或者：

```text
读取 main.py 并修复报错
```

或者：

```text
创建一个 Vue3 登录页面
```

---

# 十二、Agent 升级方向（非常重要）

你可以继续升级：

## 1. 多 Agent 架构

例如：

* Planner Agent
* Coding Agent
* Review Agent
* Debug Agent
* Test Agent

---

## 2. 接入向量数据库

推荐：

* Chroma
* Milvus
* FAISS

实现：

* 项目长期记忆
* 代码检索
* RAG

---

## 3. 自动代码测试

加入：

```python
pytest
```

实现自动测试。

---

## 4. 自动 Git 提交

加入：

```bash
git add .
git commit -m "AI update"
```

---

## 5. Docker 化

## Dockerfile

```dockerfile
FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

# 十三、生产级架构建议

真正商业化时建议：

## 后端

* FastAPI
* Celery
* Redis
* PostgreSQL
* Docker
* Kubernetes

---

## Agent 框架

推荐：

* LangGraph
* AutoGen
* CrewAI
* OpenAI Agents SDK

---

## 模型推荐

代码能力：

* GPT-4.1
* Claude Sonnet
* DeepSeek-V3
* Qwen3-Coder

---

# 十四、推荐你继续做的功能

## 企业级代码 Agent

包括：

* PR Review
* 自动补全
* IDE 插件
* 项目理解
* 自动修复 CI/CD
* 自动生成接口文档
* 自动生成测试
* 自动生成数据库表

---

# 十五、最终效果

这个项目已经具备：

✅ 基础 Agent 能力

✅ 工具调用能力

✅ 文件系统操作

✅ Shell 执行

✅ 大模型接入

✅ Web API

✅ 前端交互

✅ 可扩展架构

已经属于：

“初级 AI 编程 Agent”

继续升级后，就可以接近：

* Cursor
* Devin
* Windsurf
* Trae

这一类 AI Coding Agent。
