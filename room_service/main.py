import logging

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from room_service.agent.graph import create_graph
from room_service.agent.chat import SYSTEM_PROMPT

def chat() -> None:
  """Run an interactive chat session with the room service agent."""
  
  # Create the agent graph
  thread_id, graph = create_graph()

  messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]

  print("Welcome to Room Service! Type 'quit' to exit.")
  print("How may I assist you today?")

  while True:
    # Get user input
    user_input = input("\nYou: ").strip()
    
    # Check for quit command
    if user_input.lower() in ['quit', 'exit', 'bye']:
      print("\nThank you for using Room Service. Have a great day!")
      break
    
    # Skip empty inputs
    if not user_input:
      continue
    
    try:
      # Add user message to state
      messages.append(HumanMessage(content=user_input))
      
      # Run the agent graph
      response = graph.invoke(
        {"messages": messages},
        config={
          "configurable": {
            "thread_id": thread_id
          }
        }
      )

      response = response["messages"][-1]
      if isinstance(response, AIMessage):
        print(f"\nAgent: {response.content}")
      else:
        print(f"\nAgent: {response}")
        
    except Exception as e:
      print(f"\nError: {str(e)}")
      print("Please try again.")

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  chat()
