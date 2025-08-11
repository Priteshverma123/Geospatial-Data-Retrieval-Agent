import operator
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, START
from langgraph.graph import StateGraph, END
from langsmith import traceable


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

memory = MemorySaver()
# session_id = 
class Agent:
    def __init__(self, model, tools, system=""):
        self.system = system
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

        # Define the state graph
        self.graph = StateGraph(MessagesState)

        # Define nodes
        self.graph.add_node("agent", self.call_openai)
        self.graph.add_node("action", self.take_action)

        # Define edges
        self.graph.add_edge(START, "agent")
        self.graph.add_conditional_edges(
            "agent", self.should_continue, ["action", END]
        )
        self.graph.add_edge("action", "agent")

        # Compile with memory saver for persistence
        self.app = self.graph.compile(checkpointer=memory)

    def should_continue(self, state: MessagesState):
        # """Determine if agent should continue to action or end."""
        last_message = state["messages"][-1]
        return "action" if last_message.tool_calls else END

    @traceable
    def call_openai(self, state: MessagesState):
        messages = state["messages"]
        if self.system:
            messages = [HumanMessage(content=self.system)] + messages
        response = self.model.invoke(messages)
        return {"messages": response}


    @traceable
    def take_action(self, state: MessagesState):
        """Executes actions based on tool calls and returns responses with tool_call_ids."""
        tool_calls = state["messages"][-1].tool_calls
        results = []
        
        for t in tool_calls:
            print(f"Calling: {t}")
            tool_name = t["name"]
            tool_id = t["id"]
            if tool_name in self.tools:
                result = self.tools[tool_name].invoke(t["args"])
                print(result)
            else:
                result = "Invalid tool name; retry."

            # Ensure each tool call has a corresponding ToolMessage with tool_call_id
            results.append(
                ToolMessage(tool_call_id=tool_id, name=tool_name, content=str(result))
            )
        print("Back to the model!")
        return {"messages": results}
