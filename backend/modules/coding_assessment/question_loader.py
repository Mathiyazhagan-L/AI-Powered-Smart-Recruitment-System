import os
import re
import xlrd
from typing import Dict, List, Any

# Locate Excel question bank
EXCEL_PATH = r"c:\Recruitment\data\question_bank\coding\coding_questions.xlsx"

class QuestionLoader:
    _cached_questions: List[Dict[str, Any]] = []
    _grouped_questions: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def load_all_questions(cls) -> List[Dict[str, Any]]:
        """Loads and parses questions from Excel, filtering for standard Python questions."""
        if cls._cached_questions:
            return cls._cached_questions

        if not os.path.exists(EXCEL_PATH):
            raise FileNotFoundError(f"Coding questions bank not found at {EXCEL_PATH}")

        questions = []
        workbook = xlrd.open_workbook(EXCEL_PATH)
        sheet = workbook.sheet_by_index(0)

        # Columns mapping based on sheet layout:
        # Title, Difficulty, Category, Problem Statement, Constraints, Sample Input, Sample Output, Test Cases, Hidden Test Cases, Marks
        headers = [str(sheet.cell_value(0, c)).strip() for c in range(sheet.ncols)]
        
        for r in range(1, sheet.nrows):
            row_data = {}
            for c in range(sheet.ncols):
                row_data[headers[c]] = sheet.cell_value(r, c)
            
            # Use 1-indexed row number as question_id (ensures direct Excel mapping)
            row_data['question_id'] = r
            
            # Clean difficulty
            diff = str(row_data.get('Difficulty', '')).strip().capitalize()
            if diff not in ['Easy', 'Medium', 'Hard']:
                continue
            row_data['Difficulty'] = diff

            # Validate standard executable test case structure (must have '->')
            tc = str(row_data.get('Test Cases', '')).strip()
            htc = str(row_data.get('Hidden Test Cases', '')).strip()
            if not tc or ' -> ' not in tc or not htc or ' -> ' not in htc:
                # Skip non-executable (e.g. SQL descriptive) questions
                continue

            # Parse constraints, inputs, outputs
            row_data['Problem Statement'] = str(row_data.get('Problem Statement', '')).strip()
            row_data['Constraints'] = str(row_data.get('Constraints', '')).strip()
            row_data['Sample Input'] = str(row_data.get('Sample Input', '')).strip()
            row_data['Sample Output'] = str(row_data.get('Sample Output', '')).strip()
            
            try:
                row_data['Marks'] = float(row_data.get('Marks', 10.0))
            except (ValueError, TypeError):
                row_data['Marks'] = 10.0

            # Generate default template code
            params = cls._extract_params(row_data['Sample Input'])
            param_str = ", ".join(params)
            template_code = ""
            category = str(row_data.get('Category', '')).strip()
            if "Tree" in category:
                template_code += (
                    "# Definition for a binary tree node.\n"
                    "# class TreeNode:\n"
                    "#     def __init__(self, val=0, left=None, right=None):\n"
                    "#         self.val = val\n"
                    "#         self.left = left\n"
                    "#         self.right = right\n\n"
                )
            elif "List" in category:
                template_code += (
                    "# Definition for singly-linked list.\n"
                    "# class ListNode:\n"
                    "#     def __init__(self, val=0, next=None):\n"
                    "#         self.val = val\n"
                    "#         self.next = next\n\n"
                )
            template_code += f"def solve({param_str}):\n    # Write your Python 3 code here\n    pass\n"
            row_data['template'] = template_code

            questions.append(row_data)

        cls._cached_questions = questions
        
        # Group by difficulty
        cls._grouped_questions = {
            'Easy': [q for q in questions if q['Difficulty'] == 'Easy'],
            'Medium': [q for q in questions if q['Difficulty'] == 'Medium'],
            'Hard': [q for q in questions if q['Difficulty'] == 'Hard']
        }

        return questions

    @classmethod
    def _extract_params(cls, sample_input: str) -> List[str]:
        """Helper to extract parameter names from sample input string."""
        sample_input = sample_input.strip()
        if not sample_input:
            return ["x"]
        
        # Match pattern of variable name before =
        matches = re.findall(r'\b([a-zA-Z_]\w*)\s*=', sample_input)
        if matches:
            return matches
        
        # Fallback if it's just raw values
        return ["x"]

    @classmethod
    def get_by_id(cls, question_id: int) -> Dict[str, Any]:
        """Retrieve question by row ID."""
        all_q = cls.load_all_questions()
        for q in all_q:
            if q['question_id'] == question_id:
                return q
        raise ValueError(f"Question with ID {question_id} not found or not executable.")

    @classmethod
    def get_grouped(cls) -> Dict[str, List[Dict[str, Any]]]:
        """Gets questions grouped by difficulty level."""
        if not cls._grouped_questions:
            cls.load_all_questions()
        return cls._grouped_questions
