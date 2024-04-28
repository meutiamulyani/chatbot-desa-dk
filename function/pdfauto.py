from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def create_pdf(file_path):
    # Create a SimpleDocTemplate
    pdf = SimpleDocTemplate(file_path, pagesize=letter)

    # Title
    title_text = "Student Information"

    # Sample data for the table
    student_data = [
        ["Name", "Class", "Age", "Hobby"],
        ["John", "10th", "16", "Football"],
        ["Emily", "11th", "17", "Reading"],
        ["Michael", "9th", "15", "Painting"],
        ["Sophia", "12th", "18", "Music"]
    ]

    # Table style
    style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.blue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])

    # Create the table
    table = Table(student_data)
    table.setStyle(style)

    # Title style
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title = Paragraph(title_text, title_style)

    # Add title and table to the PDF
    content = [title, table]

    # Build PDF
    pdf.build(content)

if __name__ == "__main__":
    create_pdf("student_info.pdf")
