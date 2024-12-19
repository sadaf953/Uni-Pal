from langgraph.graph import StateGraph, END
from src.agents.student_info_agent import collect_student_info
from src.agents.university_recommendation_agent import university_search_agent  # Import the agent
# from src.agents.visa_info_agent import fetch_visa_info
# from src.agents.scholarship_info_agent import fetch_scholarship_info
from src.agents.management_agent import manage_state
# from src.agents.document_management_agent import manage_documents
from src.models import StudentInfo # , University, VisaInfo, ScholarshipInfo, Document # Remove unused imports
from typing import Dict, List, Optional
import logging
import streamlit as st
from typing import Annotated
import typing
from src.utils import clean_search_results,scrape_website



def handle_error(state: typing.Dict, error: Exception) -> typing.Dict:
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

def update_state(state: typing.Dict, updates: Dict) -> typing.Dict:
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
    builder = StateGraph(StudentInfo) # Change the state to StudentInfo

    # Define the nodes with state update
    builder.add_node("student_info", collect_student_info) # remove the lambda function
    builder.add_node("raw data",scrape_website )
    builder.add_node("formatted data", clean_search_results)
    # Modify university_recommendations_node to use the university_search_agent
    builder.add_node("university_recommendations", university_search_agent)
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
    # Adding edges to connect the nodes
    builder.add_edge("student_info", "raw data")  # Connects student_info to raw data
    builder.add_edge("raw data", "formatted data")  # Connects raw data to formatted data


    # Define the edges
    # builder.add_edge("student_info", "university_recommendations")
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