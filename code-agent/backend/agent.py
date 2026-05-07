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
