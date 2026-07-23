import sys
sys.path.insert(0, '.')
from core.database import SessionLocal
from sqlalchemy import text
import json

candidate_id = 11

def dump_table(db, table_name, user_col='user_id'):
    print(f"\n--- {table_name.upper()} ---")
    query = text(f"SELECT * FROM {table_name} WHERE {user_col} = :cid")
    rows = db.execute(query, {'cid': candidate_id}).fetchall()
    print(f"Total Rows: {len(rows)}")
    for row in rows:
        row_dict = dict(row._mapping)
        # Clean up long fields for readability
        if 'description' in row_dict and row_dict['description']:
            row_dict['description'] = row_dict['description'][:50] + "..."
        if 'raw_text' in row_dict:
            row_dict['raw_text'] = "<text>"
        if 'cleaned_text' in row_dict:
            row_dict['cleaned_text'] = "<text>"
        if 'parsed_json' in row_dict and isinstance(row_dict['parsed_json'], str):
            row_dict['parsed_json'] = "<json>"
        print(row_dict)

with SessionLocal() as db:
    dump_table(db, "resume_parser_results", user_col="candidate_id")
    dump_table(db, "candidate_profiles")
    dump_table(db, "candidate_skills")
    dump_table(db, "candidate_education")
    dump_table(db, "candidate_experience")
    dump_table(db, "candidate_projects")
