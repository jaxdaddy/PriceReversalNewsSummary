import re
import os
import datetime
import json
import pandas as pd
import pypdf
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# --- Helper Functions ---
def _footer_callback(canvas_obj, doc):
    """
    Draws the footer on each page.
    """
    canvas_obj.saveState()
    # Footer content
    advisory = "<i>This content was created with Artificial Intelligence</i>"
    generated_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp = f"<i>Generated on: {generated_time}</i>"

    # Define a style for the footer
    styles = getSampleStyleSheet()
    footer_style = ParagraphStyle(
        'footer',
        parent=styles['Normal'],
        alignment=1, # TA_CENTER
        fontSize=8,
        leading=10,
        textColor=colors.gray,
    )

    # Page number
    page_num_text = f"Page {doc.page}"
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(colors.gray)
    canvas_obj.drawString(inch, 0.75 * inch, page_num_text) # Left aligned page number

    # Advisory text
    p_advisory = Paragraph(advisory, footer_style)
    # Calculate width of the advisory paragraph
    text_width, text_height = p_advisory.wrapOn(canvas_obj, doc.width, doc.bottomMargin)
    # Center the advisory
    p_advisory.drawOn(canvas_obj, doc.leftMargin + (doc.width - text_width) / 2.0, 0.85 * inch)
    
    # Timestamp text
    p_timestamp = Paragraph(timestamp, footer_style)
    # Calculate width of the timestamp paragraph
    text_width, text_height = p_timestamp.wrapOn(canvas_obj, doc.width, doc.bottomMargin)
    # Center the timestamp
    p_timestamp.drawOn(canvas_obj, doc.leftMargin + (doc.width - text_width) / 2.0, 0.75 * inch)
    
    canvas_obj.restoreState()

def extract_pdf_text(pdf_path: str) -> str:
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def markdown_to_paragraphs(markdown_text: str, styles: dict) -> list:
    """
    Converts a simple markdown text to a list of ReportLab Flowables.
    Handles headings, bold, italic, lists, and basic tables as formatted ReportLab tables.
    """
    story = []
    lines = markdown_text.split('\n')
    in_table_block = False
    table_lines = []

    for line_idx, line in enumerate(lines):
        # Detect markdown table lines (starts with '|' and contains other '|' or is a separator)
        is_table_related_line = line.strip().startswith('|')
        
        if is_table_related_line:
            table_lines.append(line)
            in_table_block = True
            continue
        
        if in_table_block and not is_table_related_line:
            # End of table block, process collected table_lines
            if table_lines:
                processed_table_data = []
                # First, determine if there's a separator line and process header/body separately
                header_row = []
                separator_idx = -1

                # Find separator line (e.g., |---|---|) 
                for i, t_line in enumerate(table_lines):
                    # Check for a line consisting primarily of hyphens and pipes
                    if re.match(r'^\|[\s\-\:|]*$', t_line.strip()):
                        separator_idx = i
                        break
                
                if separator_idx != -1:
                    # Process header row
                    header_row_str = table_lines[0]
                    header_cells = [cell.strip() for cell in header_row_str.split('|') if cell.strip()]
                    processed_table_data.append([Paragraph(f"<b>{cell}</b>", styles['Normal']) for cell in header_cells])

                    # Process body rows (skip separator line)
                    for b_line_str in table_lines[separator_idx + 1:]:
                        body_cells = [cell.strip() for cell in b_line_str.split('|') if cell.strip()]
                        processed_table_data.append([Paragraph(cell, styles['Normal']) for cell in body_cells])
                else: # No explicit separator, treat all rows as body (no bold header)
                    for t_line in table_lines:
                        row_cells = [cell.strip() for cell in t_line.split('|')]
                        processed_table_data.append([Paragraph(cell, styles['Normal']) for cell in row_cells if cell])
                
                if processed_table_data:
                    # Ensure all rows have the same number of columns for ReportLab Table
                    max_cols = max(len(row) for row in processed_table_data) if processed_table_data else 0
                    max_cols = max(1, max_cols) # Ensure max_cols is at least 1
                    processed_table_data = [row + [Paragraph('', styles['Normal'])] * (max_cols - len(row)) for row in processed_table_data]
                    
                    # Calculate column widths based on page size
                    page_width = letter[0]
                    left_right_margin = 0.5 * inch # Assuming 0.5 inch margin on each side
                    available_width = page_width - (2 * left_right_margin)
                    
                    col_widths = [available_width / max_cols] * max_cols if max_cols > 0 else [None]
                    
                    table_style = TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica'), # Use Helvetica for general text
                        ('BOTTOMPADDING', (0,0), (-1,0), 6),
                        ('BACKGROUND', (0,1), (-1,-1), colors.white),
                        ('GRID', (0,0), (-1,-1), 1, colors.black),
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('WORDWRAP', (0,0), (-1,-1), True), # Enable word wrapping
                        ('FONTNAME', (0,0), (max_cols - 1,0), 'Helvetica-Bold'), # Header text is bold
                    ])
                    
                    t = Table(processed_table_data, colWidths=col_widths)
                    t.setStyle(table_style)
                    story.append(t)
                    story.append(Spacer(1, 12)) # Add spacing after table
                
                table_lines = [] # Clear for next table
            in_table_block = False
        
        # If still in table block, continue to next line
        if in_table_block:
            continue

        # Process non-table lines
        if line.startswith('# '):
            story.append(Paragraph(line[2:], styles['CustomH1']))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], styles['CustomH2']))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], styles['CustomH3']))
        elif line.startswith('* '):
            story.append(Paragraph(f"• {line[2:]}", styles['Normal']))
        elif line.strip() == '':
            story.append(Spacer(1, 12))
        else:
            # Simple bold and italic using regex
            line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', line)
            story.append(Paragraph(line, styles['Normal']))
    
    # Process any remaining table lines if file ends with a table
    if in_table_block and table_lines:
        processed_table_data = []
        header_row = []
        separator_idx = -1

        for i, t_line in enumerate(table_lines):
            if re.match(r'^\|[\s\-\:|]*$', t_line.strip()):
                separator_idx = i
                break
        
        if separator_idx != -1:
            header_row_str = table_lines[0]
            header_cells = [cell.strip() for cell in header_row_str.split('|') if cell.strip()]
            processed_table_data.append([Paragraph(f"<b>{cell}</b>", styles['Normal']) for cell in header_cells])

            for b_line_str in table_lines[separator_idx + 1:]:
                body_cells = [cell.strip() for cell in b_line_str.split('|') if cell.strip()]
                processed_table_data.append([Paragraph(cell, styles['Normal']) for cell in body_cells])
        else:
            for t_line in table_lines:
                row_cells = [cell.strip() for cell in t_line.split('|')]
                processed_table_data.append([Paragraph(cell, styles['Normal']) for cell in row_cells if cell])
        
        if processed_table_data:
            max_cols = max(len(row) for row in processed_table_data) if processed_table_data else 0
            max_cols = max(1, max_cols)
            processed_table_data = [row + [Paragraph('', styles['Normal'])] * (max_cols - len(row)) for row in processed_table_data]

            page_width = letter[0]
            left_right_margin = 0.5 * inch
            available_width = page_width - (2 * left_right_margin)
            col_widths = [available_width / max_cols] * max_cols if max_cols > 0 else [None]

            table_style = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica'), # Use Helvetica for general text
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('BACKGROUND', (0,1), (-1,-1), colors.white),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('WORDWRAP', (0,0), (-1,-1), True), # Enable word wrapping
                ('FONTNAME', (0,0), (max_cols - 1,0), 'Helvetica-Bold'), # Header text is bold
            ])
                
            t = Table(processed_table_data, colWidths=col_widths)
            t.setStyle(table_style)
            story.append(t)
            story.append(Spacer(1, 12)) # Add spacing after table
            
    return story

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type((ResourceExhausted, InternalServerError, ServiceUnavailable)),
    reraise=True
)
def _generate_response_with_retry(model, full_prompt: str) -> str:
    """Internal function to call the Gemini API for report generation with retry logic."""
    return model.generate_content(full_prompt).text

def generate_pdf_report(
    subset_data: List[Dict],
    news_summary_path: str,
    primer_pdf_path: str,
    prompts_path: str,
    output_dir: str = "files"
) -> str:
    
    with open(news_summary_path, "r") as f:
        news_summary = f.read()
    primer_text = extract_pdf_text(primer_pdf_path)
    with open(prompts_path, "r") as f:
        prompts_content = f.read()
    
    raw_prompts = [p.strip() for p in prompts_content.split('\n\n') if p.strip()]
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return "Error_GEMINI_API_KEY_not_found.pdf"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-pro-latest')
    
    responses = []
    subset_str = json.dumps(subset_data, default=str, indent=2)
    
    for prompt_text in raw_prompts:
        full_prompt = f"""
        You are a financial analyst.
        CONTEXT: {primer_text[:10000]}
        NEWS SUMMARY: {news_summary[:10000]}
        DATA: {subset_str}
        TASK: {prompt_text}
        """
        try:
            response_text = _generate_response_with_retry(model, full_prompt)
            responses.append({"prompt": prompt_text, "response": response_text})
        except (ResourceExhausted, InternalServerError, ServiceUnavailable) as e:
            print(f"LLM call failed after retries for prompt '{prompt_text[:50]}...': {e}")
            error_message = "Content generation failed due to API errors after multiple retries."
            responses.append({"prompt": prompt_text, "response": error_message})
        except Exception as e:
            print(f"An unexpected error occurred for prompt '{prompt_text[:50]}...': {e}")
            error_message = f"An unexpected error occurred: {str(e)}"
            responses.append({"prompt": prompt_text, "response": error_message})
            
    # --- PDF Creation Logic ---
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    output_filename = f"PRNS_Summary-{current_date}.pdf"
    output_path = os.path.join(output_dir, output_filename)
    
    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=inch/2, bottomMargin=inch)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CustomH1', fontSize=18, leading=22, spaceAfter=12))
    styles.add(ParagraphStyle(name='CustomH2', fontSize=16, leading=20, spaceAfter=10))
    styles.add(ParagraphStyle(name='CustomH3', fontSize=14, leading=18, spaceAfter=8))
    
    story = []
    
    # Title
    story.append(Paragraph(f"Price Reversal News Summary - {current_date}", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Subset Data Listing
    story.append(Paragraph("Subset Data Listing", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    # Create table data
    if subset_data:
        key_columns = ['Symbol', 'Company Name', 'Reversal Date', 'Direction', 'Reversal Price', 'HR1 Value', 'Last Close Price']
        table_data = [key_columns]
        
        for item in subset_data:
            row = [str(item.get(col, '')) for col in key_columns]
            table_data.append(row)
            
        # Ensure all rows have the same number of columns for ReportLab Table
        max_cols = max(len(row) for row in table_data) if table_data else 0
        max_cols = max(1, max_cols) # Ensure max_cols is at least 1
        processed_table_data = [row + [Paragraph('', styles['Normal'])] * (max_cols - len(row)) for row in table_data]

        page_width = letter[0]
        left_right_margin = 0.5 * inch # Assuming 0.5 inch margin on each side
        available_width = page_width - (2 * left_right_margin)
        col_widths = [available_width / max_cols] * max_cols if max_cols > 0 else [None]
            
        t = Table(processed_table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No data available.", styles['Normal']))
        
    story.append(Spacer(1, 24))
    
    # Gemini Responses
    story.append(Paragraph("Gemini Analysis", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    for item in responses:
        # Prompt Summary (First line of prompt)
        prompt_lines = item['prompt'].split('\n')
        prompt_title = prompt_lines[0] if prompt_lines else "Prompt"
        
        story.append(Paragraph(prompt_title, styles['CustomH3']))
        story.append(Spacer(1, 6))
        
        # Response (Handle markdown to some extent or just dump text)
        response_paragraphs = markdown_to_paragraphs(item['response'], styles)
        story.extend(response_paragraphs)
        story.append(Spacer(1, 12))
        
    doc.build(story, onFirstPage=_footer_callback, onLaterPages=_footer_callback)
    return output_path
