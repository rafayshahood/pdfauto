import re
from docx import Document


def process_cell(cell, replacement_dict, dynamic_counters):
    """
    Recursively processes a cell:
      - Replaces text in the paragraphs using the provided replacement dictionary.
      - Handles dynamic (list‑based) replacements using dynamic_counters.
      - Recursively processes any nested tables within the cell.
    """
    # Process paragraphs in the current cell.
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            for old_text, new_val in replacement_dict.items():
                if old_text in run.text:
                    if isinstance(new_val, list):
                        if not new_val:  # Skip if the list is empty.
                            continue
                        idx = dynamic_counters.get(old_text, 0)
                        replacement_str = new_val[idx] if idx < len(new_val) else new_val[-1]
                        run.text = run.text.replace(old_text, replacement_str)
                        dynamic_counters[old_text] = idx + 1
                    else:
                        run.text = run.text.replace(old_text, new_val)
    # Recursively process any nested tables in this cell.
    for nested_table in cell.tables:
        for row in nested_table.rows:
            for nested_cell in row.cells:
                process_cell(nested_cell, replacement_dict, dynamic_counters)

# --------------------------
# Process document function.
def process_document_full(file_path, newHeader, replacement1, replacement2, 
                          allSafetyMeasures, dm2_value, edemaResults, depressed_value, iteration_index):
    """
    Processes the Word document and performs the following tasks:
      1. Header text replacement.
      2. Table cell replacements in the first and second columns using dynamic (list‑based) replacements.
      3. Updates safety measure checkboxes.
      4. Updates the DM II checkbox.
      5. Updates the Edema section checkboxes.
      6. Updates the Depressed checkbox.
    The modified document is saved as "merged_modiftotal37.docx".
    """

    # Load the document.
    doc = Document(file_path)
    
    # 1. Header Text Replacement.
    old_header_text = "MINT HOME HEALTH CARE"
    for section in doc.sections:
        header = section.header
        for paragraph in header.paragraphs:
            for run in paragraph.runs:
                if old_header_text in run.text:
                    run.text = run.text.replace(old_header_text, newHeader)
    
    # 2. Table Cell Replacements.
    # Setup dynamic counters for list-based replacements.
    dynamic_counters1 = { key: 0 for key, val in replacement1.items() if isinstance(val, list) }
    dynamic_counters2 = { key: 0 for key, val in replacement2.items() if isinstance(val, list) }
    
    # 2. Table Cell Replacements.
    # Process first column (cell index 0)
    for table in doc.tables:
        for row in table.rows:
            cell = row.cells[0]
            process_cell(cell, replacement1, dynamic_counters1)
    
    # Process second column (cell index 1), including nested tables.
    for table in doc.tables:
        for row in table.rows:
            cell = row.cells[1]
            process_cell(cell, replacement2, dynamic_counters2)
                                
    
    # 3. Safety Measures Checkboxes Update.
    measures = [s.strip().lower() for s in allSafetyMeasures.split(",")]
    safety_measures_mapping = {
        "Bleeding Precautions": "bleeding precautions",
        "Fall Precautions": "fall precautions",
        "Clear pathways": "clear pathways",
        "Infection control measures": "infection control measures",
        "Cane, walker Precautions": ("cane", "walker"),
        "Universal Precautions": "universal precautions",
        "Other:911 protocols": "911 protocol"
    }
    # Uncheck all safety measure checkboxes.
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        for label in safety_measures_mapping.keys():
                            if label in run.text:
                                pattern = r"(☒|☐)(" + re.escape(label) + r")"
                                run.text = re.sub(pattern, r"☐\2", run.text)
    # Check safety measure checkboxes based on provided measures.
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        for label, expected in safety_measures_mapping.items():
                            if label in run.text:
                                should_check = False
                                if isinstance(expected, tuple):
                                    for item in expected:
                                        if item in measures:
                                            should_check = True
                                            break
                                else:
                                    if expected in measures:
                                        should_check = True
                                
                                pattern = r"(☒|☐)(" + re.escape(label) + r")"
                                run.text = re.sub(pattern, r"☒\2" if should_check else r"☐\2", run.text)
    
    # 4. DM II Checkbox Update.
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if "DM II" in run.text:
                            run.text = run.text.replace("☒", "☐")
                            if dm2_value:
                                run.text = run.text.replace("☐", "☒", 1)
                            else:
                                run.text = run.text.replace("☒", "☐")
    
    # 5. Edema Section Checkboxes Update.
    edema_results_lower = edemaResults.lower()
    edema_mapping = {
        "Pitting": "pitting",
        "Non-pitting": "non-pitting",
        "Pacer": "pacer",
        "1+": "+1",
        "2+": "+2",
        "3+": "+3",
        "4+": "+4",
        "Dependent": "dependent",
        "Pedal R/L": "pedal r/l",
        "Dorsum R/L": "dorsum r/l"
    }
    # Uncheck all Edema checkboxes.
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        for label in edema_mapping.keys():
                            if label in run.text:
                                pattern = r"(☒|☐)(" + re.escape(label) + r")"
                                run.text = re.sub(pattern, r"☐\2", run.text)
    # Check Edema checkboxes.
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        for label, expected in edema_mapping.items():
                            if label in run.text and expected in edema_results_lower:
                                pattern = r"(☒|☐)(" + re.escape(label) + r")"
                                run.text = re.sub(pattern, r"☒\2", run.text)
    
    # 6. Depressed Checkbox Update.
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if "Depressed" in run.text:
                            run.text = run.text.replace("☒", "☐")
                            if depressed_value:
                                run.text = run.text.replace("☐", "☒", 1)
                            else:
                                run.text = run.text.replace("☒", "☐")
    
    # Save the modified document with a name based on iteration (e.g., "page1.docx", "page2.docx", etc.)
    output_file = f"page{iteration_index+1}.docx"
    doc.save(output_file)
    return output_file