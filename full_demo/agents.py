from autogen_core import MessageContext, RoutedAgent, message_handler, AgentId
from autogen_core.models import SystemMessage, LLMMessage, UserMessage
from full_demo.messages import RequestMsg, VacationSpecificationMsg, VacationBudgetMsg, VacationItineraryMsg
from typing import List
from autogen_core.tool_agent import tool_agent_caller_loop
from autogen_core import  AgentId
from full_demo.utils import model_client, create_document

class RetrievalAgent(RoutedAgent):
    def __init__(self, tool_schema) -> None:
        super().__init__("A RetrievalAgent with tools")
        self._tool_schema = tool_schema

    @message_handler
    async def handle_start_message(self, message: RequestMsg, ctx: MessageContext) -> None:
        print("Getting vacation specifications from user")
        system_messages: List[LLMMessage] = [SystemMessage(content='''You are a retrieval agent. You are to access the external dataset 
                                                                      and get the information and format it.
                                                                Step 1: Use the `df` variable to access the dataset to find ALL the specifications on the vacation. Dont forget anything.
                                                                Step 2: I want you to include everything. 
                                                                Step 3: Format, I want you to return 5 sections. Destination, Departure City, Length of Stay, Total Budget and Wants. 
                                                                        Put all the information you get into the categories and dont forget any information for df variable.
                                                                        Also do not use markdown language to create bolded, headers or anything. Just uses spaces and new lines''')]
        messages = await tool_agent_caller_loop(
            self,
            tool_agent_id = AgentId("tool_agent", "default"),
            model_client =model_client,
            input_messages =system_messages,
            tool_schema =self._tool_schema,
            cancellation_token =ctx.cancellation_token,
        )
        await self.send_message(VacationSpecificationMsg(request = message.request, 
                                                         specification = messages[-1].content), 
                                AgentId("BudgetAgent", "default"))

class BudgetAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("A BudgetAgent")

    @message_handler
    async def handle_start_message(self, message: VacationSpecificationMsg, ctx: MessageContext) -> None:
        print("Vacation specifications sent to the BudgetAgent")
        system_message = SystemMessage(content=('''You are to make a budget. 
                                                Step 1: You will be given vacation specifications and it is your job to come up with an appropriate budget. 
                                                    Use all the money given and create a budget given the context of the destination. If the destination 
                                                    is a cheaper location then consider that but if the destination has very high cost of living or high cost of
                                                    transportation then consider that as well and cater the budget given the specifications.
                                                Step 2: Only create amounts for areas of Flights, Accommodation, Food & Drinks, 
                                                    Transportation, Entertainment/Activities and Shopping & Souvenirs.
                                                Step 3: 
                                                    The user will tell you how much money they have to spend. If you think they dont 
                                                    have enough money to spend on a particular vacation given the length of stay and 
                                                    destination then reply with 'The budget given for this vacation is not sufficient for your requests'.
                                                Format: I want you to return a simple budget that contains amounts for the sections already mentioned.
                                                    Keep it simple and only include the section name and totals each on its own line like this 'Food & Drinks = $50'.
                                                    If one section is $0 then still include.'''))

        llm_result = await model_client.create(messages=[system_message, UserMessage(content=message.request + message.specification, source=self.id.key)],
                                                cancellation_token=ctx.cancellation_token)
        await self.send_message(VacationBudgetMsg(request = message.request, 
                                                  specification =  message.specification, 
                                                  budget = llm_result.content), 
                                AgentId("ItineraryAgent", "default"))
    

class ItineraryAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("A ItineraryAgent")

    @message_handler
    async def handle_start_message(self, message: VacationBudgetMsg, ctx: MessageContext) -> None:
        print("Vacation budget sent to the ItineraryAgent")
        system_message = SystemMessage(content=('''You are to make an itinerary.
                                                Step 1: Use all the information given to you such as the request from the user, any additional specifications and budget. 
                                                    I want you  to understand all three of these components.
                                                Step 2: Create an itnerary for the user. For each day I want you to give things to do in the morning, afternoon and evening.
                                                    Make sure to consider their specifications on how they most want to spend their time or things to do.
                                                Step 3: Look for popular things to do in the particular destination and ensure to include those. As the users will want 
                                                    to do things that are popular for tourists in their destination location.
                                                Step 4: Do not include a budget. 
                                                Format: I want as many sections as there are days in the vacation. I want you to make three subsections per day for morning, 
                                                    afternoon and evening and include a small description of all the things to do. I do not want to see any other details besides 
                                                    the days sections and the subsections of morning, evening and night. Also do not use markdown language to create 
                                                    bolded, headers or anything. Just uses spaces and new lines'''))

        llm_result = await model_client.create(messages=[system_message, UserMessage(content=message.request + message.specification + message.budget, source=self.id.key)],
                                                cancellation_token=ctx.cancellation_token)
        await self.send_message(VacationItineraryMsg(request = message.request, 
                                                  specification =  message.specification, 
                                                  budget = message.budget,
                                                  itinerary = llm_result.content), 
                                AgentId("FormatterAgent", "default"))
        
class FormatterAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("A FormatterAgent")

    @message_handler
    async def handle_start_message(self, message: VacationItineraryMsg, ctx: MessageContext) -> None:
        print("Vacation budget and itinerary sent to the FormatterAgent")
        system_message = SystemMessage(content=('''I want you to return a single word or two if needed to tell me where the vacation is happening. No spaces or extra lines, just the words.'''))
        llm_result = await model_client.create(messages=[system_message, UserMessage(content=message.request + message.specification, source=self.id.key)],
                                                cancellation_token=ctx.cancellation_token)
        create_document(message, "full_demo/word_docs", f"{llm_result.content}_Vacation.docx")

