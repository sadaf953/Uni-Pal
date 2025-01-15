from langgraph.graph import StateGraph, END
from src.agents.student_info_agent import collect_student_info
from src.utils import search_universities, build_query, save_links_to_csv, process_csv
from src.models import StudentInfo
from typing import Dict, List, Optional, TypedDict, Annotated
import logging
import streamlit as st
from typing import Annotated
import typing
from src.llm_interface import query_llm
import pandas as pd

class WorkflowState(TypedDict):
    student_info: Optional[Dict]
    search_results: Optional[List]
    processed_universities: Optional[List]
    recommendations: Optional[List]
    error: Optional[str]

def handle_error(state: WorkflowState, error: Exception) -> WorkflowState:
    """
    Handles errors in the graph and provides a human in the loop fallback.
    """
    logging.error(f"Error in graph: {error}")
    state["error"] = str(error)
    st.error(f"An error occurred: {error}")
    return state

def update_state(state: WorkflowState, updates: Dict) -> WorkflowState:
    """
    Updates the state dictionary with new values
    """
    if isinstance(updates, dict):
        state.update(updates)
    return state

def search_universities_node(state: WorkflowState) -> WorkflowState:
    """
    Node for searching universities based on student preferences
    """
    try:
        if not state.get("student_info"):
            raise ValueError("Student information not available")
        
        program_field = state["student_info"].get("interested_field_for_masters")
        countries = state["student_info"].get("preferred_countries", [])
        
        query = build_query(program_field, countries)
        search_results = search_universities(query)
        save_links_to_csv(search_results)
        
        return update_state(state, {"search_results": search_results})
    except Exception as e:
        return handle_error(state, e)

def process_universities_node(state: WorkflowState) -> WorkflowState:
    """
    Node for processing and filtering university links
    """
    try:
        if not state.get("search_results"):
            raise ValueError("No search results available")
        
        process_csv('university.csv', 'processed_universities.csv')
        
        # Import here to avoid circular import
        from src.agents.university_recommendation_agent import process_all_university_links
        processed_results = process_all_university_links()
        
        return update_state(state, {"processed_universities": processed_results})
    except Exception as e:
        return handle_error(state, e)

def generate_recommendations_node(state: WorkflowState) -> WorkflowState:
    """
    Node for generating final university recommendations
    """
    try:
        if not state.get("processed_universities"):
            raise ValueError("No processed university data available")
        
        # Import here to avoid circular import
        from src.agents.university_recommendation_agent import recommend_top_universities
        recommendations = recommend_top_universities(state.get("student_info", {}))
        return update_state(state, {"recommendations": recommendations})
    except Exception as e:
        return handle_error(state, e)

def should_continue(state: WorkflowState) -> bool:
    """
    Determines if the workflow should continue based on state
    """
    return not state.get("error") and state.get("student_info") is not None

def get_workflow() -> StateGraph:
    """
    Defines and returns the LangGraph workflow for the application.
    """
    # Initialize the workflow graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes to the graph
    workflow.add_node("collect_student_info", collect_student_info)
    workflow.add_node("search_universities", search_universities_node)
    workflow.add_node("process_universities", process_universities_node)
    workflow.add_node("generate_recommendations", generate_recommendations_node)
    
    # Define the workflow edges
    workflow.add_edge("collect_student_info", "search_universities")
    workflow.add_edge("search_universities", "process_universities")
    workflow.add_edge("process_universities", "generate_recommendations")
    workflow.add_edge("generate_recommendations", END)
    
    # Set conditional edges
    workflow.add_conditional_edges(
        "collect_student_info",
        should_continue,
        {
            True: "search_universities",
            False: END
        }
    )
    
    # Set the entry point
    workflow.set_entry_point("collect_student_info")
    
    return workflow.compile()