from langgraph.graph import StateGraph, END
from src.agents.student_info_agent import collect_student_info
from src.agents.university_recommendation_agent import recommend_universities
from src.agents.visa_requirement_agent import fetch_visa_info
from src.agents.scholarship_search_agent import fetch_scholarship_info
from src.agents.document_management_agent import manage_documents
from src.agents.management_agent import manage_state
from src.models import StudentInfo, University, VisaInfo, ScholarshipInfo, Document

def get_workflow():
    builder = StateGraph(StudentInfo)

    builder.add_node("student_info", collect_student_info)
    builder.add_node("university_recommendations", recommend_universities)
    builder.add_node("visa_info", fetch_visa_info)
    builder.add_node("scholarship_info", fetch_scholarship_info)
    builder.add_node("document_management", manage_documents)
    builder.add_node("management", manage_state)


    builder.set_entry_point("student_info")
    builder.add_edge("student_info", "university_recommendations")
    builder.add_edge("university_recommendations", "visa_info")
    builder.add_edge("university_recommendations", "scholarship_info")
    builder.add_edge("scholarship_info", "document_management")
    builder.add_edge("visa_info", "document_management")

    builder.add_edge("document_management", "management")
    builder.add_edge("management", END)

    return builder.compile()