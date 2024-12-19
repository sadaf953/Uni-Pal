from langgraph.graph import StateGraph, END
from src.agents.student_info_agent import collect_student_info
# from src.agents.university_recommendation_agent import recommend_universities # Removed the import
# from src.agents.visa_info_agent import fetch_visa_info
# from src.agents.scholarship_info_agent import fetch_scholarship_info
from src.agents.management_agent import manage_state
# from src.agents.document_management_agent import manage_documents
from src.models import StudentInfo, University, VisaInfo, ScholarshipInfo, Document
from typing import Dict, List, Optional
import logging
import streamlit as st

def handle_error(state, error):
    """
    Handles errors in the graph and provides a human in the loop fallback.

    Args:
        state: The current state of the graph.
        error: The error that occurred.

    Returns:
        The updated state.
    """
    logging.error(f"Error in graph: {error}")
    st.error(f"An error occurred: {error}. Please check the logs for more details: {error}")
    st.error(f"Error Details: {str(error)}")
    return state

def update_state(state, updates):
    """
    Updates the state dictionary with new values
    
    Args:
      state: The current state of the graph.
      updates: The updates to be applied to the state.
    
    Returns:
      The updated state.
    """
    if isinstance(updates, dict):
        state.update(updates)
    return state

def get_workflow():
    """
    Defines and returns the LangGraph workflow for the application.
    """
    builder = StateGraph(StudentInfo)

    # Define the nodes with state update
    builder.add_node("student_info", lambda state: update_state(state, collect_student_info()))

    def university_recommendations_node(state):
       st.info("Running university_recommendations_node")
       return update_state(state, {"universities": []})
    

    builder.add_node("university_recommendations", university_recommendations_node)

    # def visa_info_node(state):
    #   if state and state.get('universities'):
    #     try:
    #         country = state['universities'][0].name.split(",")[-1].strip()
    #         visa_info = fetch_visa_info(country)
    #         return update_state(state, {"visa_info": visa_info})
    #     except Exception as e:
    #         logging.error(f"Error in visa_info_node: {e}")
    #         st.error(f"Error getting visa information: {e}")
    #         return state
    #
    #   else:
    #     st.error("University information not available.")
    #     return state
    #
    # builder.add_node("visa_info", visa_info_node)
    #
    # def scholarship_info_node(state):
    #   if state:
    #     try:
    #         scholarship_info = fetch_scholarship_info(state)
    #         return update_state(state, {"scholarships": scholarship_info})
    #     except Exception as e:
    #         logging.error(f"Error in scholarship_info_node: {e}")
    #         st.error(f"Error getting scholarship information: {e}")
    #         return state
    #   else:
    #     st.error("Student information not available.")
    #     return state
    #
    # builder.add_node("scholarship_info", scholarship_info_node)
    #
    # builder.add_node("document_management", lambda state: update_state(state, manage_documents(state)))
    builder.add_node("management", lambda state: manage_state(**state))

    # Set the entry point
    builder.set_entry_point("student_info")

    # Define the edges
    builder.add_edge("student_info", "university_recommendations")

    # builder.add_edge("university_recommendations", "visa_info")
    # builder.add_edge("university_recommendations", "scholarship_info")
    #
    # builder.add_edge("visa_info", "document_management")
    # builder.add_edge("scholarship_info", "document_management")

    builder.add_edge("university_recommendations", "management")
    builder.add_edge("management", END)


    # Add error handling
    builder.add_exception_handler("*", handle_error)

    return builder.compile()