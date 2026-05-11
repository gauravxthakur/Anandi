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
from tools import fetal_biometry_calculator
from rag.retreiver import search, search_legal, search_guidelines

load_dotenv()


# -----------------------------------STATE SCHEMA-------------------------------------------
class AgentState(TypedDict):
    
    # Conversation History
    messages: Annotated[list[AnyMessage], add_messages]
 
#--------------------------------------------------------------------------------------------


#-------------------------------------TOOLS---------------------------------------------
local_tools = [fetal_biometry_calculator, search, search_legal, search_guidelines]


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
    
    print("Fetal Biometry Assistant (Type 'quit' to exit)")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
                
            if not user_input:
                continue
            
            # Run the graph with user input
            response = await graph.ainvoke({
                "messages": [HumanMessage(content=user_input)]
            })
            
            # Get the assistant's response
            assistant_message = response["messages"][-1]
            print(f"\nAssistant: {assistant_message.content}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        print("\nSession ended.")