import json
import os
import logging
from typing import Dict, Any

class JsonStorage:
    def __init__(self, file_path: str = "student_data.json"):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create the JSON file if it doesn't exist."""
        if not os.path.exists(self.file_path):
            self.save_data({"students": {}})

    def load_data(self) -> Dict[str, Any]:
        """Load data from the JSON file."""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning(f"File {self.file_path} not found. Creating new file.")
            return {"students": {}}
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from {self.file_path}")
            return {"students": {}}
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            return {"students": {}}

    def save_data(self, data: Dict[str, Any]) -> bool:
        """Save data to the JSON file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Error saving data: {e}")
            return False

    def clear_data(self) -> bool:
        """Clear all data from the JSON file."""
        return self.save_data({"students": {}})

    def update_student_info(self, student_data: Dict[str, Any], replace_existing: bool = True) -> bool:
        """Update or add student information.
        
        Args:
            student_data: The student data to save
            replace_existing: If True, replace existing data. If False, add as new entry.
        """
        try:
            data = self.load_data()
            student_id = student_data.get('contact_info')
            
            if not student_id:
                logging.error("No contact info provided in student data")
                return False
            
            if replace_existing:
                # Clear existing data
                data['students'] = {}
            
            # Add the new student data
            data['students'][student_id] = student_data
            return self.save_data(data)
        except Exception as e:
            logging.error(f"Error updating student info: {e}")
            return False

    def get_student_info(self, contact_info: str) -> Dict[str, Any]:
        """Retrieve student information by contact info."""
        try:
            data = self.load_data()
            return data.get('students', {}).get(contact_info, {})
        except Exception as e:
            logging.error(f"Error retrieving student info: {e}")
            return {}
