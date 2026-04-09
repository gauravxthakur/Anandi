import asyncio
import os
from dotenv import load_dotenv
import json
from typing import List, TypedDict, Annotated, Optional
from langchain_core.messages import HumanMessage, AnyMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from IPython.display import Image, display
from langgraph.types import interrupt # For HITL
from langgraph.types import Command
from langchain_core.messages import ToolMessage

load_dotenv()


# -----------------------------------STATE SCHEMA-------------------------------------------
class AgentState(TypedDict):
    
    # Conversation History
    messages: Annotated[list[AnyMessage], add_messages]
 
#--------------------------------------------------------------------------------------------


#-------------------------------------TOOLS---------------------------------------------
local_tools = []


# Initialise the LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# System Message
sys_msg = SystemMessage(content=f"""
You are an AI assistant that helps to analyze fetal biometry measurements from ultrasound images.
""")


#--------------------------------Build the Graph -----------------------------------------------------
async def build_graph():
    
    builder = StateGraph(AgentState)
    
    llm_with_tools = llm.bind_tools(local_tools)
    
    #------------------------------------AI ASSISTANT---------------------------------------
    async def assistant(state: AgentState):
        
        response = await llm_with_tools.ainvoke([sys_msg] + state["messages"])    
        return{
            "messages": [response],
        }

    # 2. Nodes & Edges
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(local_tools))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")
           
    app = builder.compile()
    
    # Generate PNG image of the graph
    image_data = app.get_graph().draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(image_data)
        
    return app


# ----------------------------------------RUN----------------------------------------------    
async def run_app():
   
    graph = await build_graph()


if __name__ == "__main__":
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        print("\nSession ended.")