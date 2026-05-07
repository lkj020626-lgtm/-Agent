# AI Code Agent

## 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

## 配置环境变量

复制：

```bash
.env.example -> .env
```

填写你的 API Key。

## 启动后端

```bash
uvicorn app:app --reload
```

## 启动前端

直接打开：

frontend/index.html

或者：

```bash
python -m http.server 5500
```

## 功能

- AI 对话
- 文件读写
- Shell 执行
- 自动代码生成
- 自动修复 Bug
- Agent 工具调用
