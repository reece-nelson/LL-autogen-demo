import pandas as pd
import asyncio
from autogen_core import SingleThreadedAgentRuntime, AgentId
from autogen_ext.tools.langchain import LangChainToolAdapter
from langchain_experimental.tools.python.tool import PythonAstREPLTool
from full_demo.agents import RetrievalAgent, BudgetAgent, ItineraryAgent, FormatterAgent
from full_demo.messages import RequestMsg
from autogen_core.tool_agent import ToolAgent

async def main() -> None:

    async def get_tool():
        df = pd.read_csv("full_demo/data/vacation_specifications.txt", header=None)
        df.columns = ["items"]
        tool = LangChainToolAdapter(PythonAstREPLTool(locals={"df": df}))
        return tool
    
    runtime = SingleThreadedAgentRuntime()
    tool = await get_tool()
    await ToolAgent.register(runtime, "tool_agent", lambda: ToolAgent("tool agent", [tool]))
    await RetrievalAgent.register(runtime, type="RetrievalAgent", factory=lambda: RetrievalAgent([tool.schema]))
    await BudgetAgent.register(runtime, type="BudgetAgent", factory=lambda: BudgetAgent())
    await ItineraryAgent.register(runtime, type="ItineraryAgent", factory=lambda: ItineraryAgent())
    await FormatterAgent.register(runtime, type="FormatterAgent", factory=lambda: FormatterAgent())
    runtime.start()
    await runtime.send_message(RequestMsg(request='''Make me an itinerary and budget for my vacation. Please do not include any budget for Shopping/Souvenirs. I want to spend a lot of time outside.'''), 
                               AgentId("RetrievalAgent", "default"))
    await runtime.stop_when_idle()

asyncio.run(main())