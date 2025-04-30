import asyncio
from autogen_core import SingleThreadedAgentRuntime, TypeSubscription, TopicId
from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_core.models import SystemMessage, UserMessage
from full_demo.utils import model_client
from pydantic import BaseModel

class MockMsg(BaseModel):
    content:str

class MockAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__(description="Mock Agent")

    @message_handler
    async def handle_start_message(self, message: MockMsg, ctx: MessageContext) -> None:
        system_message = SystemMessage(content = "tell me a joke about a certain topic about this topic:")  
        llm_result = await model_client.create(messages=[system_message, UserMessage(content=message.content, source=self.id.key)],
                                               cancellation_token=ctx.cancellation_token)
        print(llm_result.content)


async def main() -> None:
    runtime = SingleThreadedAgentRuntime() 
    mock_agent = await MockAgent.register(runtime, 
                                          type="MockAgent", 
                                          factory=lambda: MockAgent())
    
    await runtime.add_subscription(TypeSubscription(topic_type="MockAgent_type",
                                                    agent_type=mock_agent.type))  
    runtime.start()
    await runtime.publish_message(MockMsg(content="The topic is computers."), topic_id=TopicId("MockAgent_type", source="random") ) 
    await runtime.stop_when_idle()
if __name__ == "__main__":
    asyncio.run(main())