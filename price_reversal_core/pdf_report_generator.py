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

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

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
    Converts a simple markdown text to a list of ReportLab Paragraphs.
    Handles headings, bold, italic, lists, and basic tables as formatted ReportLab tables.
    """
    story = []
    lines = markdown_text.split('\n')
    in_table_block = False
    table_lines = []

    for line in lines:
        # Detect start/continuation of table block
        # A table line typically starts and ends with '|' and contains pipes in between
        if line.strip().startswith('|') and '|' in line[1:-1]: # Simplified table row detection
            table_lines.append(line)
            in_table_block = True
            continue
        elif in_table_block: # End of table block or non-table line
            if table_lines:
                # Create a simple table from parsed lines
                table_data = []
                for t_line in table_lines:
                    # Split by '|' and clean up cells, then remove empty strings
                    # Wrap each cell content in a Paragraph for word wrapping
                    table_data.append([Paragraph(cell, styles['Normal']) for cell in t_line.split('|') if cell])
                
                # Basic table style
                table_style = TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0,0), (-1,0), 6),
                    ('BACKGROUND', (0,1), (-1,-1), colors.white),
                    ('GRID', (0,0), (-1,-1), 1, colors.black),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('WORDWRAP', (0,0), (-1,-1), True), # Enable word wrapping
                ])
                
                # Check if the table has at least a header and a separator
                if len(table_data) > 1 and re.match(r'[\s\-:]+', table_data[1][0].text if table_data[1] and table_data[1][0] else ''):
                    # It's likely a markdown table with a separator line
                    # Remove separator line for ReportLab Table
                    table_data.pop(1)
                
                # Ensure all rows have the same number of columns for ReportLab Table
                max_cols = max(len(row) for row in table_data) if table_data else 0
                max_cols = max(1, max_cols) # Ensure max_cols is at least 1 to prevent division by zero
                table_data = [row + [Paragraph('', styles['Normal'])] * (max_cols - len(row)) for row in table_data]
                
                # Calculate column widths based on page size
                page_width = letter[0]
                left_right_margin = 0.5 * inch # Assuming 0.5 inch margin on each side
                available_width = page_width - (2 * left_right_margin)
                
                col_widths = [available_width / max_cols] * max_cols if max_cols > 0 else [None]
                
                t = Table(table_data, colWidths=col_widths)
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
        story.append(Paragraph("", styles['Normal'])) # Add an empty paragraph for spacing before table
        table_data = []
        for t_line in table_lines:
            table_data.append([Paragraph(cell, styles['Normal']) for cell in t_line.split('|') if cell.strip()])
            
        table_style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('WORDWRAP', (0,0), (-1,-1), True), # Enable word wrapping
        ])
        
        if len(table_data) > 1 and re.match(r'[\s\-:]+', table_data[1][0].text if table_data[1] and table_data[1][0] else ''):
            table_data.pop(1)
            
        # Ensure all rows have the same number of columns for ReportLab Table
        max_cols = max(len(row) for row in table_data) if table_data else 0
        max_cols = max(1, max_cols) # Ensure max_cols is at least 1 to prevent division by zero
        table_data = [row + [Paragraph('', styles['Normal'])] * (max_cols - len(row)) for row in table_data]

        page_width = letter[0]
        left_right_margin = 0.5 * inch
        available_width = page_width - (2 * left_right_margin)
        
        col_widths = [available_width / max_cols] * max_cols if max_cols > 0 else [None]

        t = Table(table_data, colWidths=col_widths)
        t.setStyle(table_style)
        story.append(t)
        story.append(Spacer(1, 12)) # Add spacing after table
            
    return story

def generate_pdf_report(
    subset_data: List[Dict],
    news_summary_path: str,
    primer_pdf_path: str,
    prompts_path: str,
    output_dir: str = "files"
) -> str:
    
    # 1. Load Context
    with open(news_summary_path, "r") as f:
        news_summary = f.read()
        
    primer_text = extract_pdf_text(primer_pdf_path)
    
    with open(prompts_path, "r") as f:
        prompts_content = f.read()
    
    # Parse prompts (assuming they are separated by blank lines or numbered)
    # Simple parsing: split by double newlines and filter
    raw_prompts = [p.strip() for p in prompts_content.split('\n\n') if p.strip()]
    
    # 2. Configure Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-2.0-flash') # Or config model
    
    # 3. Generate Responses
    responses = []
    
    subset_str = json.dumps(subset_data, default=str, indent=2)
    
    for prompt_text in raw_prompts:
        full_prompt = f"""
        You are a financial analyst.
        
        CONTEXT:
        {primer_text[:10000]} # Truncate if too long, or use file API
        
        NEWS SUMMARY:
        {news_summary[:10000]}
        
        DATA:
        {subset_str}
        
        TASK:
        {prompt_text}
        """
        
        try:
            response = model.generate_content(full_prompt)
            responses.append({
                "prompt": prompt_text,
                "response": response.text
            })
        except Exception as e:
            responses.append({
                "prompt": prompt_text,
                "response": f"Error generating response: {str(e)}"
            })
            
    # 4. Create PDF
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    output_filename = f"PRNS_Summary-{current_date}.pdf"
    output_path = os.path.join(output_dir, output_filename)
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Add custom styles
    styles.add(ParagraphStyle(name='CustomH1', fontSize=18, leading=22, spaceAfter=12))
    styles.add(ParagraphStyle(name='CustomH2', fontSize=16, leading=20, spaceAfter=10))
    styles.add(ParagraphStyle(name='CustomH3', fontSize=14, leading=18, spaceAfter=8))
    styles.add(ParagraphStyle(name='Preformatted', fontName='Courier', fontSize=10, leading=12,
                                     spaceBefore=6, spaceAfter=6, borderWidth=0.5, borderColor=colors.black,
                                     backColor=colors.lightgrey))

    story = []
    
    # Title
    story.append(Paragraph(f"Price Reversal News Summary - {current_date}", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Subset Data Listing
    story.append(Paragraph("Subset Data Listing", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    # Create table data
    if subset_data:
        headers = list(subset_data[0].keys())
        key_columns = ['Symbol', 'Company Name', 'Reversal Date', 'Reversal Price', 'HR1 Value', 'Last Close Price']
        table_data = [key_columns]
        
        for item in subset_data:
            row = [str(item.get(col, '')) for col in key_columns]
            table_data.append(row)
            
        t = Table(table_data)
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
        
    doc.build(story)
    return output_path
