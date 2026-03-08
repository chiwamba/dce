import os
import io
import json
import requests
from flask import Flask, request, render_template, redirect, url_for, session, flash, send_file, abort
import pandas as pd
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import time
import re 

application = Flask(__name__)

# Path to store PDFs
pdf_folder = 'reports'
if not os.path.exists(pdf_folder):
    os.makedirs(pdf_folder)

# Google Sheets Configuration
SHEETS_CONFIG = {
    # Domasi Demo Details
    '1n15V4NogwMxP69R4_7Npeay49iCSiwBnYg8wE6BT4bM': {'gid': '280165131'}, # form 1 day
    '1PNBgH3HsSNcKgIQJxY0O2ply55uEOMVVNcCokwWXieg': {'gid': '1388779181'}, # form 2 day
    '13Au17YTBjgzJYTDfZ1leXmSobnNBdEPC9rqNms05fTY': {'gid': '900409288'}, # form 4 day
    '1YxyXxn_-8CQuGXjdx0AvwA99YldHiBh-gHZdnJcEN80': {'gid': '1859605198'},# form 3 day
    '1zSt-ea0mBphg6-NbKViHG1goQ_5-9eYz4rrJYK7Cf-M': {'gid': '1172957593'}, # Open form 4
    '1h_n99ROFIFvvlpX3f4WfOmeeVin5KU2Eps7bs2VUnfs': {'gid': '1970292484'}, # Open form 2 
    '1AK3KtSoXx0g9LeJV-UtRBgd1o6XtOjYFrV8v5V1tzWU': {'gid': '124926488'}, # Open form 3
    '1alplXh4f3V28iRLvrgSqI1ra7y6XkgqleETp1Z-1R74': {'gid': '534889396'}, # Open form 1
    #End of Domasi Demo Details
    # Below are details for Zenith Private Secondary Schoool
    '1R7Efn18ez58q9AFAX_rB_NJvsR-KsN5TycTHg4HPdZ0': {'gid': '2064965368'}, # Form 1 Zenith Private
    '1g6GzWoKLXNGzaB1N8ZZY-sIGZolZ-0oV_UtGDp95kQI': {'gid': '1289426634'}, # Form 2 Zenith Private
    '1LTZhZ5AgOCPmpZigGi3uJNyDvkLj5qdzBDK-O6lblps': {'gid': '364013426'}, # Form 3 Zenith Private
    '1M4rSL8U0fav2YPKwryIrIMyBiSVa_i84i6zNqz0jric': {'gid': '100678175'},
    # Form 4 Zenith Private
    # End of Zenith Private Secondary School Details
}

# Google Drive API credentials
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = '/home/smarbpfr/sis.smartscorecenter.com/venv/progress_report.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

sheets_service = build('sheets', 'v4', credentials=credentials)
drive_service = build('drive', 'v3', credentials=credentials)

# A dictionary to map teachers to subjects
teachers_subjects = {
    'tinda': 'AGR',
    'jamali1': 'AGR',
    'mithande': 'AGR',
    'agriteacher': 'AGR',
    'inno': 'AGR',
    'NJ1': 'AGR',
    'kamwendo1': 'AGR',
    'mchacha': 'BIK',
    'bik2teacher': 'BIK',
    'MBA1': 'BIK',
    'bikteacher': 'BIK',
    'bioteacher': 'BIO',
    'kasenda': 'BIO',
    'mithande1': 'BIO',
    'tinda1': 'BIO',
    'inno1': 'BIO',
    'bio4teacher': 'BIO',
    'kalonga1': 'BIO',
    'cheteacher': 'CHE',
    'kasenda1': 'CHE',
    'che2teacher': 'CHE', # Zuze
    'che3teacher': 'CHE',
    'che4teacher': 'CHE',
    'chiteacher': 'CHI',
    'ENRIQUE': 'CHI',
    'mmillho1': 'CHI',
    'alistair': 'CHI',
    'kavina': 'CHI',
    'chi20': 'CHI',
    'emment': 'CHI',
    'kamanga1': 'CHI',
    'comteacher': 'COM',
    'maulidi': 'COM',
    'com2teacher': 'COM',
    'jesman': 'COM',
     'chiwamba1': 'COM',
    'freteacher': 'FRE',
    'engteacher': 'ENG',
    'kamwendo': 'ENG',
    'enrique': 'ENG',
    'losani': 'ENG',
    'mmillho': 'ENG',
    'mussa': 'ENG',
    'mchacha1': 'ENG',
    'kamanga': 'ENG',
    'julio': 'ENG',
    'eng20': 'ENG',
    'jaysh': 'ENG',
    'emment1': 'ENG',
    'histeacher': 'HIS',
    'lado': 'HIS',
    'mbewe': 'HIS',
    'msukwa': 'HIS',
    'banda': 'HIS',
    'mussa1': 'HIS',
    'asante': 'HIS',
    'chilumpha': 'HEC',
    'hec1teacher': 'HEC',
    'hecteacher': 'HEC',
    'hec2teacher': 'HEC',
    'salimu': 'GEO',
    'geoteacher': 'GEO',
    'BLEYA': 'GEO',
    'phiri': 'GEO',
    'chilumpha1': 'GEO',
    'geo3teacher': 'GEO',
    'julio1': 'GEO',
    'geo4teacher': 'GEO',
    'matteacher': 'MAT',
    'bleya': 'MAT',
    'zuze': 'MAT',
    'maulidi1': 'MAT',
    'kalonga': 'MAT',
    'jesman1': 'MAT',
    'jamali': 'MAT',
    'NJ': 'MAT',
    'SA1': 'MAT',
    'table': 'MAT',
    'SA': 'PHY',
    'kasenda2': 'PHY',
    'phyteacher': 'PHY',
    'phy2teacher': 'PHY', #Zuze
    'kabuthu': 'PHY',
    'chiwamba': 'PHY',
    'table1': 'SOS',
    'alistair1': 'SOS',
    'sosteacher': 'SOS',
    'hkbanda': 'SOS',
    'MBA': 'SOS',
    'jaysh1': 'SOS',
    'asante1': 'SOS',
    'ngwazi': 'SOS',
    'pedu': 'PED',
    'arts': 'CRE',
    # Add other teachers and their subject mappings
}

# Route for teacher login
@application.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        teacher_id = request.form['teacher_id']
        if teacher_id in teachers_subjects:
            session['teacher_id'] = teacher_id
            session['subject_column'] = teachers_subjects.get(teacher_id)
            return redirect(url_for('teacher_input_score'))
        else:
            flash("Invalid Teacher ID.", "danger")
    return render_template('login.html')
    
# Function to read data from Google Sheets

def read_google_sheet(sheet_id, range_name):
    sheet = sheets_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
    values = result.get('values', [])
    
    if values:
        # Clean up values to remove empty rows
        values = [row for row in values if any(cell for cell in row)]  # Remove empty rows

        # Check if there is a header
        if len(values) > 1:
            # Ensure all rows have the same length
            max_length = max(len(row) for row in values)
            values = [row + [''] * (max_length - len(row)) for row in values]  # Pad shorter rows
            
            return pd.DataFrame(values[1:], columns=values[0])  # Use first row as headers
        else:
            return pd.DataFrame()  # Only header or empty
        
    return pd.DataFrame()  # Return empty DataFrame if no values

# Function to get the relevant sheet ID based on student ID
def get_relevant_sheet(student_id):
    for sheet_id in SHEETS_CONFIG.keys():
        df = read_google_sheet(sheet_id, 'DATA ENTRY SECTION')
        if not df[df['STUDENT ID'] == student_id].empty:
            return sheet_id  # Return the first matching sheet ID
    return None  # Return None if no sheet matches

# Function to trigger progress report
def trigger_progress_report(student_id):
    sheet_id = get_relevant_sheet(student_id)
    if not sheet_id:
        print(f"Student ID {student_id} not found in any sheets.")
        return

    df = read_google_sheet(sheet_id, 'DATA ENTRY SECTION')
    student_row = df[df['STUDENT ID'] == student_id]
    
    if not student_row.empty:
        student_name = student_row['NAME'].iloc[0]
        progress_report_data = [[student_name]]
        
        # Update cell B6 in the PROGRESSREPORT sheet
        sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='PROGRESSREPORT!B6',
            valueInputOption='USER_ENTERED',
            body={'values': progress_report_data}
        ).execute()
    else:
        print(f"Student ID {student_id} not found.")

# Function to convert the sheet to a PDF
def convert_sheet_to_pdf(sheet_id, student_name, sheet_name='PROGRESSREPORT'):
    gid = SHEETS_CONFIG[sheet_id]['gid']  # Get the GID for the specified sheet
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=pdf&size=A4&sheetnames=true&printtitle=true&pagenumbers=false&gridlines=false&fzr=false&portrait=false&fitw=true&gid={gid}"

    pdf_file = io.BytesIO()
    response = requests.get(export_url)
    pdf_file.write(response.content)
    pdf_file.seek(0)

# Save the PDF to the local directory
    pdf_filename = os.path.join(pdf_folder, f'{student_name}.pdf')
    with open(pdf_filename, 'wb') as f:
        f.write(pdf_file.read())

    return pdf_filename
   
# Define the folder to store PDFs
pdf_folder = "Exam_Results"
os.makedirs(pdf_folder, exist_ok=True)

# Function to convert the sheet to a PDF
def summary_sheet(sheet_id, gid, sheet_name):
    # Construct the export URL with `headers=true` to repeat the frozen rows
    export_url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=pdf&size=A4"
        f"&sheetnames=true&printtitle=true&headers=true&pagenumbers=false&gridlines=false"
        f"&fzr=true&portrait=false&fitw=true&gid={gid}"
    )

    # Fetch the PDF data from Google Sheets
    response = requests.get(export_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download PDF: {response.status_code}")

    # Save the PDF to the local directory
    pdf_filename = os.path.join(pdf_folder, f"{sheet_name}.pdf")
    with open(pdf_filename, "wb") as f:
        f.write(response.content)

    return pdf_filename

# Route for the home page
@application.route("/")
def home():
    return render_template("teacher_input_score.html")
#
# Route for Form 1 results
@application.route("/form1_results", methods=["POST"])
def form1_results():
    sheet_id = "1n15V4NogwMxP69R4_7Npeay49iCSiwBnYg8wE6BT4bM"  # Demo
    sheet_id ="1R7Efn18ez58q9AFAX_rB_NJvsR-KsN5TycTHg4HPdZ0" # Zenith
    gid = "1584058578"  # Demo
    gid = "2064965368" # Zenith
    sheet_name = "Form 1 Results"  # Name of the sheet
    pdf_filename = summary_sheet(sheet_id, gid, sheet_name)

    # Send the PDF file to the user
    return send_file(pdf_filename, as_attachment=True)

# Route for Form 2 results
@application.route("/form2_results", methods=["POST"])
def form2_results():
    sheet_id = "1PNBgH3HsSNcKgIQJxY0O2ply55uEOMVVNcCokwWXieg"  # Demo
    sheet_id = "1g6GzWoKLXNGzaB1N8ZZY-sIGZolZ-0oV_UtGDp95kQI"  # Zenith
    gid = "1242835144"  # Demo
    gid = "1289426634"  # Zenith
    sheet_name = "Form 2 Results"  # Name of the sheet
    pdf_filename = summary_sheet(sheet_id, gid, sheet_name)

    # Send the PDF file to the user
    return send_file(pdf_filename, as_attachment=True)
    
# Route for Form 3 results
@application.route("/form3_results", methods=["POST"])
def form3_results():
    sheet_id = "1YxyXxn_-8CQuGXjdx0AvwA99YldHiBh-gHZdnJcEN80"  # Demo
    sheet_id = "1LTZhZ5AgOCPmpZigGi3uJNyDvkLj5qdzBDK-O6lblps" # Zenith
    gid = "138762849" # Demo 
    gid = "364013426" # Zenith
    sheet_name = "Form 3 Results"  # Name of the sheet
    pdf_filename = summary_sheet(sheet_id, gid, sheet_name)

    # Send the PDF file to the user
    return send_file(pdf_filename, as_attachment=True)

# Route for Form 4 results
@application.route("/form4_results", methods=["POST"])
def form4_results():
    sheet_id = "13Au17YTBjgzJYTDfZ1leXmSobnNBdEPC9rqNms05fTY"  # Demo
    sheet_id = "1M4rSL8U0fav2YPKwryIrIMyBiSVa_i84i6zNqz0jric" # Zenith
    gid = "1377545223"  # Demo
    gid = "100678175" #Zenith
    sheet_name = "Form 4 Results"  # Name of the sheet
    pdf_filename = summary_sheet(sheet_id, gid, sheet_name)

    # Send the PDF file to the user
    return send_file(pdf_filename, as_attachment=True)


def get_student_name_by_id(student_id, df):
    # Filter the dataframe for the matching student ID
    student_row = df[df['STUDENT ID'].str.strip() == student_id.strip()]
    
    # Ensure there's exactly one match
    if len(student_row) == 1:
        return student_row['NAME'].iloc[0]
    elif len(student_row) > 1:
        print(f"Warning: Multiple students found with ID {student_id}. Returning the first match.")
        return student_row['NAME'].iloc[0] # Return the first match
    else:
        return None # Return None if no match is found

@application.route('/view_report/<student_id>', methods=['GET'])
def view_report(student_id):
    """
    Allow access for:
    - Admins logged in via session.
    - Students directly using the student_id.
    """
    # Check if the user is an admin or a valid student
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    username = session['username']
    student_found = False
    student_name = None
    sheet_id = None

    # Check if the logged-in user is a student and verify if the student ID exists
    for sid in SHEETS_CONFIG.keys():
        df = read_google_sheet(sid, 'DATA ENTRY SECTION')
        student_name = get_student_name_by_id(student_id, df)
        if student_name:
            sheet_id = sid
            student_found = True
            break

    if not student_found:
        return "Unauthorized or Student not found.", 403

    # Trigger the progress report and convert to PDF
    try:
        trigger_progress_report(student_id)
    except Exception as e:
        print(f"Error triggering progress report: {e}")
        return "Error updating the progress report."

    try:
        pdf_file = convert_sheet_to_pdf(sheet_id, student_name)
        if pdf_file:
            return send_file(pdf_file, as_attachment=True)
    except Exception as e:
        print(f"Error converting sheet to PDF: {e}")
        return "Error generating the progress report."

    return "Student report generated successfully."

@application.route('/teacher', methods=['GET', 'POST'])
def teacher_input_score():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))

    teacher_id = session['teacher_id']
    subject_column = session['subject_column']

    student_data = []
    scores_to_update = {}
    submitted_by_teacher = False

    # Safely fetch data from Google Sheets with retries
    def fetch_sheet_data_with_retries(sheet_id, range_name, retries=3):
        for attempt in range(retries):
            try:
                return read_google_sheet(sheet_id, range_name)
            except HttpError as e:
                if e.resp.status in [500, 503]:  # Retry on server errors
                    if attempt < retries - 1:
                        time.sleep((2 ** attempt) + 1)  # Exponential backoff
                        continue
                raise e  # Raise the exception if retries are exhausted

    data_entry_section_dfs = {}
    for sheet_id in SHEETS_CONFIG.keys():
        try:
            data_entry_section_dfs[sheet_id] = fetch_sheet_data_with_retries(sheet_id, 'DATA ENTRY SECTION')
        except HttpError as e:
            flash(f"Error fetching data for sheet {sheet_id}: {e}", "error")

    subject_columns = {
        'AGR': 'AG',
        'BIK': 'AL',
        'BIO': 'AQ',
        'CHE': 'AV',
        'CHI': 'BA',
        'COM': 'BF',
        'FRE': 'BK',
        'ENG': 'BP',
        'HIS': 'BU',
        'HEC': 'BZ',
        'GEO': 'CE',
        'PED': 'CJ',
        'MAT': 'CO',
        'PHY': 'CT',
        'SOS': 'CY',
        'CRE': 'CZ',
    }

    if request.method == 'POST':
        if 'student_ids' in request.form:
            student_ids = request.form.getlist('student_ids')
            for student_id in student_ids:
                for sheet_id, df in data_entry_section_dfs.items():
                    student_name = get_student_name_by_id(student_id, df)
                    if student_name:
                        score = request.form.get(f'score_{student_id}', type=float)
                        if score is not None:
                            scores_to_update[student_id] = (sheet_id, score)
                        student_data.append((student_id, student_name))

        if 'submit_scores' in request.form:
            if scores_to_update:
                batch_requests = []
                for student_id, (sheet_id, score) in scores_to_update.items():
                    column = subject_columns.get(subject_column)
                    if column:
                        row_number = get_row_number(student_id, sheet_id)
                        if row_number:
                            range_notation = f'DATA ENTRY SECTION!{column}{row_number}'
                            batch_requests.append({
                                'range': range_notation,
                                'values': [[score]]
                            })
                        else:
                            flash(f"Could not find row for student ID: {student_id}. Score not updated.", "error")

                    # Send batch requests in chunks to avoid exceeding quota limits
                    if len(batch_requests) >= 50:
                        try:
                            send_batch_update(sheet_id, batch_requests)
                        except HttpError as e:
                            flash(f"Error updating sheet {sheet_id}: {e}", "error")
                        batch_requests = []
                        time.sleep(1)  # Pause to respect API quota limits

                # Send remaining batch requests
                if batch_requests:
                    try:
                        send_batch_update(sheet_id, batch_requests)
                    except HttpError as e:
                        flash(f"Error updating sheet {sheet_id}: {e}", "error")

                # Trigger progress reports and PDFs after batch updates
                for student_id, (sheet_id, _) in scores_to_update.items():
                    trigger_progress_report(student_id)
                    convert_sheet_to_pdf(sheet_id, get_student_name_by_id(student_id, data_entry_section_dfs[sheet_id]))

                flash("All scores updated successfully.", "success")
            else:
                flash("No scores to update.", "warning")

            submitted_by_teacher = True

    return render_template('teacher_input_score.html', teacher_id=teacher_id, subject_column=subject_column, student_data=student_data, submitted=submitted_by_teacher)

def send_batch_update(sheet_id, batch_requests):
    try:
        body = {
            'data': batch_requests,
            'valueInputOption': 'USER_ENTERED'
        }
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=sheet_id,
            body=body
        ).execute()
    except HttpError as e:
        flash(f"Error during batch update for sheet {sheet_id}: {e}", "error")

# Function to get the row number of a student in a specific sheet
def get_row_number(student_id, sheet_id):
    df = read_google_sheet(sheet_id, 'DATA ENTRY SECTION')
    student_row = df[df['STUDENT ID'].str.strip() == student_id.strip()]
    if not student_row.empty:
        return student_row.index[0] + 2  # +2 because Google Sheets is 1-indexed and we have a header row
    return None

# Route for admins to input student ID and scores
@application.route('/admin', methods=['GET', 'POST'])
def admin_input_score():
    # Check if the admin is logged in
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    student_data = []
    scores_to_update = {}
    submitted_by_admin = False  # Track if scores were submitted

    # Load the Google sheet as a DataFrame (for displaying purposes)
    data_entry_section_dfs = {sheet_id: read_google_sheet(sheet_id, 'DATA ENTRY SECTION') for sheet_id in SHEETS_CONFIG.keys()}

    # Define the subjects and their corresponding columns
    subject_columns = {
        'AGR': 'AG',
        'BIK': 'AL',
        'BIO': 'AQ',
        'CHE': 'AV',
        'CHI': 'BA',
        'COM': 'BF',
        'FRE': 'BK',
        'ENG': 'BP',
        'HIS': 'BU',
        'HEC': 'BZ',
        'GEO': 'CE',
        'MAT': 'CO',
        'PHY': 'CT',
        'SOS': 'CY',
    }

    # Pass the subjects to the template
    subjects = list(subject_columns.keys())

    if request.method == 'POST':
        # Collect student IDs and scores
        if 'student_ids' in request.form:
            student_ids = request.form.getlist('student_ids')
            for student_id in student_ids:
                for sheet_id, df in data_entry_section_dfs.items():
                    student_name = get_student_name_by_id(student_id, df)
                    
                    # Ensure student_name is valid (not None)
                    if student_name:  
                        score = request.form.get(f'score_{student_id}', type=float)
                        subject = request.form.get(f'subject_{student_id}')  # Get the selected subject for this student
                        
                        # Ensure both score and subject are provided
                        if score is not None and subject in subject_columns:
                            column = subject_columns[subject]  # Get the corresponding column for the subject
                            scores_to_update[student_id] = (sheet_id, column, score)  # Store the sheet ID, column, and score
                        student_data.append((student_id, student_name))  # Store student data for rendering

        # Process scores when submitting
        if 'submit_scores' in request.form:
            if scores_to_update:
                # Prepare to update the Google sheet with new scores
                for student_id, (sheet_id, column, score) in scores_to_update.items():
                    # Get the row number for the specific student ID
                    row_number = get_row_number(student_id, sheet_id)  
                    if row_number is not None:  # Ensure the row number is valid
                        # Prepare the data to update
                        body = {
                            'values': [[score]]  # Create a list of lists for the API call
                        }

                        # Update the Google Sheets cell
                        sheets_service.spreadsheets().values().update(
                            spreadsheetId=sheet_id,
                            range=f'DATA ENTRY SECTION!{column}{row_number}',  # Construct the cell range
                            valueInputOption='USER_ENTERED',
                            body=body
                        ).execute()

                # Trigger progress reports and PDF generation as before
                for student_id in scores_to_update.keys():
                    trigger_progress_report(student_id)  # Update the progress report for each student
                    student_name = get_student_name_by_id(student_id, data_entry_section_dfs[sheet_id])  # Get the student name again
                    if student_name:
                        convert_sheet_to_pdf(sheet_id, student_name)  # Convert the sheet to PDF for the student
                
                submitted_by_admin = True  # Mark that scores were submitted
                flash("All scores updated successfully.", "success")  # Success message
            else:
                flash("No scores to update.", "warning")  # Warning message if no scores are updated

    return render_template('admin_input_score.html', 
                           student_data=student_data, 
                           subjects=subjects,  # Pass subjects to the template
                           submitted_by_admin=submitted_by_admin)  # Pass necessary data to the template

# Function to get the row number of a student in a specific sheet
def get_row_number(student_id, sheet_id):
    df = read_google_sheet(sheet_id, 'DATA ENTRY SECTION')
    student_row = df[df['STUDENT ID'].str.strip() == student_id.strip()]
    if not student_row.empty:
        # Assuming the first row corresponds to row 2 in the Google Sheets (considering headers)
        return df.index.get_loc(student_row.index[0]) + 2  # +2 to account for 0-indexing and header row
    return None  # Return None if student ID is not found

# New route for student to enter their ID and view their report
users = {
    'class1xA~': {'password': 'password1xQ#'}, # ADDED A~ ON USERNAME AND Q# ON PASSWORD
    'class1yA~': {'password': 'password1yQ#'},
    'mayeso#': {'password': 'mayeso'},
    'class1aA~': {'password': 'password1aQ#'},
    'class1bA~': {'password': 'password1bQ#'},
    'class2xA~': {'password': 'password2xQ#'},
    'class2yA~': {'password': 'password2yQ#'},
    'class2aA~': {'password': 'password2aQ#'},
    'class2bA~': {'password': 'password2bQ#'},
    'class3xA~': {'password': 'password3xQ#'},
    'class3yA~': {'password': 'password3yQ#'},
    'class3aA~': {'password': 'password3aQ#'},
    'class3bA~': {'password': 'password3bQ#'},
    'class4abA~': {'password': 'password4abQ#'},
    'openA~': {'password': 'openform4Q#'},
    'open1A~': {'password': 'openform1Q#'},
    'open2A~': {'password': 'openform2Q#'},
    'open3A~': {'password': 'openform3Q#'},
}

# Step 1: Login route for username and password
@application.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validate login credentials
        if username in users and users[username]['password'] == password:
            session['username'] = username  # Store username in session
            return redirect(url_for('student_view'))  # Redirect to the next step
        else:
            return "Invalid username or password, please try again."
    
    return render_template('student_login.html')  # Render login page

# Step 2: Student view route after login (enter student ID)
@application.route('/student', methods=['GET', 'POST'])
def student_view():
    if 'username' not in session:
        return redirect(url_for('student_login'))  # Redirect to login if not logged in
    
    if request.method == 'POST':
        student_id = request.form['student_id']  # Get the student ID
        return redirect(url_for('view_report', student_id=student_id))  # Redirect to view report route

    return render_template('student_view.html')  # Render student ID input page
    
# Route for admin login
@application.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Example admin credentials check (replace with your real authentication logic)
        if username == 'admin' and password == 'adminpassword':
            session['admin'] = True  # Set session for admin
            return redirect(url_for('admin_input_score'))
        else:
            flash("Invalid admin credentials.", "danger")
    
    return render_template('admin_login.html')
    
 #Adding a new code for my Android app
 # --- add this to passenger_wsgi.py ---
@application.route('/public/report/<student_id>', methods=['GET'])
def public_report(student_id):

    # Find which sheet this student belongs to
    sheet_id = None
    student_name = None
    for sid in SHEETS_CONFIG.keys():
        df = read_google_sheet(sid, 'DATA ENTRY SECTION')
        student_name = get_student_name_by_id(student_id, df)
        if student_name:
            sheet_id = sid
            break

    if not sheet_id:
        return ("Student not found", 404)

    try:
        # Update the sheet to point at this student and render the report
        trigger_progress_report(student_id)
    except Exception as e:
        print(f"Error triggering progress report: {e}")
        return ("Error updating the progress report", 500)

    try:
        pdf_file = convert_sheet_to_pdf(sheet_id, student_name)
        if pdf_file:
            # Set a friendly filename for the download
            return send_file(pdf_file, as_attachment=True, download_name=f"{student_name}.pdf")
    except Exception as e:
        print(f"Error converting sheet to PDF: {e}")
        return ("Error generating the progress report", 500)

    return ("Unexpected error", 500)
    
# For Zenith
# Add this function to validate if a student already exists in a specific sheet
def student_exists_in_sheet(sheet_id, student_id):
    """Check if a student ID already exists in a specific sheet"""
    try:
        df = read_google_sheet(sheet_id, 'DATA ENTRY SECTION')
        if not df.empty and 'STUDENT ID' in df.columns:
            # Handle potential NaN values and convert to string
            existing_ids = df['STUDENT ID'].astype(str).str.strip()
            # Remove any 'nan' strings that might come from actual NaN values
            existing_ids = existing_ids[existing_ids.str.lower() != 'nan']
            return student_id.strip() in existing_ids.values
    except Exception as e:
        print(f"Error checking student existence in sheet {sheet_id}: {e}")
    return False

# Add this helper function to get the next available row
def get_next_available_row(sheet_id, sheet_name='DATA ENTRY SECTION'):
    """Find the next available (empty) row in the specified sheet"""
    try:
        # Get all values in column A
        range_name = f"{sheet_name}!A:A"
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            # If sheet is completely empty, start at row 1
            return 1
        
        # Find the first empty cell in column A
        for i, row in enumerate(values):
            if len(row) == 0 or not row[0].strip():
                # Return 1-indexed row number
                return i + 1
        
        # If no empty cells found, return next row after last
        return len(values) + 1
        
    except Exception as e:
        print(f"Error finding next available row: {e}")
        # Fallback: return a safe row number
        return 2  # Start from row 2 assuming row 1 is header

# Add this function to append student to Google Sheet
def add_student_to_zenith_sheet(form_level, student_id, student_name):
    """Add a new student to the DATA ENTRY SECTION in columns A and B of Zenith sheets"""
    
    # Map form levels to Zenith sheet IDs
    zenith_sheets = {
        'form1': '1R7Efn18ez58q9AFAX_rB_NJvsR-KsN5TycTHg4HPdZ0',
        'form2': '1g6GzWoKLXNGzaB1N8ZZY-sIGZolZ-0oV_UtGDp95kQI',
        'form3': '1LTZhZ5AgOCPmpZigGi3uJNyDvkLj5qdzBDK-O6lblps',
        'form4': '1M4rSL8U0fav2YPKwryIrIMyBiSVa_i84i6zNqz0jric'
    }
    
    if form_level not in zenith_sheets:
        return False, f"Invalid form level: {form_level}"
    
    sheet_id = zenith_sheets[form_level]
    
    try:
        # First, check if student already exists in this sheet
        if student_exists_in_sheet(sheet_id, student_id):
            return False, f"Student ID '{student_id}' already exists in Form {form_level[-1]} sheet!"
        
        # Get the next available row
        next_row = get_next_available_row(sheet_id, 'DATA ENTRY SECTION')
        
        # Check if we need to add headers
        if next_row == 1:
            # Sheet is empty, add headers first
            headers_range = 'DATA ENTRY SECTION!A1:B1'
            headers_body = {'values': [['STUDENT ID', 'NAME']]}
            sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=headers_range,
                valueInputOption='USER_ENTERED',
                body=headers_body
            ).execute()
            
            # Now add student data in row 2
            next_row = 2
        
        # Validate that the row number is within Google Sheets limits
        if next_row > 10000:  # Adjust this limit based on your needs
            return False, f"Cannot add student. Sheet may be full (row {next_row})."
        
        # Prepare the data to append
        range_name = f'DATA ENTRY SECTION!A{next_row}:B{next_row}'
        values = [[student_id.strip(), student_name.strip()]]
        
        # Update the sheet
        body = {'values': values}
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        return True, f"Student '{student_name}' (ID: {student_id}) added successfully to row {next_row} in Form {form_level[-1]}!"
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error adding student to Zenith sheet {sheet_id}: {error_msg}")
        
        # Handle specific error cases
        if "exceeds grid limits" in error_msg:
            return False, "Cannot add student. The sheet has reached its maximum row limit. Please contact the administrator."
        elif "Row limit" in error_msg:
            return False, "Sheet is full! Maximum row limit reached."
        elif "permissions" in error_msg.lower():
            return False, "Permission denied. Please check your Google Sheets API credentials."
        
        return False, f"Failed to add student. Error: {error_msg[:100]}..."

# Add this route to handle student addition
@application.route('/add_zenith_students', methods=['GET', 'POST'])
def add_zenith_students():
    """Admin route to add new students to Zenith Google Sheets"""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    success_message = None
    error_message = None
    
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        student_name = request.form.get('student_name', '').strip()
        form_level = request.form.get('form_level', '')
        
        # Validation
        if not student_id:
            error_message = "Student ID is required!"
        elif not student_name:
            error_message = "Student Name is required!"
        elif not form_level:
            error_message = "Please select a form level!"
        elif not re.match(r'^[A-Za-z0-9\-_]+$', student_id):
            error_message = "Student ID should contain only letters, numbers, hyphens, or underscores!"
        else:
            # Add student to the Zenith sheet
            success, message = add_student_to_zenith_sheet(form_level, student_id, student_name)
            
            if success:
                success_message = message
                # Clear form on success
                student_id = ''
                student_name = ''
            else:
                error_message = message
    
    return render_template('add_zenith_students.html', 
                         success_message=success_message,
                         error_message=error_message,
                         student_id=request.form.get('student_id', '') if request.method == 'POST' else '',
                         student_name=request.form.get('student_name', '') if request.method == 'POST' else '',
                         selected_form=request.form.get('form_level', ''))

# You can also add a batch upload functionality with improved error handling
@application.route('/batch_add_zenith_students', methods=['GET', 'POST'])
def batch_add_zenith_students():
    """Admin route to add multiple students at once"""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    results = []
    
    if request.method == 'POST':
        form_level = request.form.get('form_level', '')
        student_data = request.form.get('student_data', '').strip()
        
        if not form_level:
            flash("Please select a form level!", "error")
        elif not student_data:
            flash("Please enter student data!", "error")
        else:
            # Parse student data (format: ID,Name on each line)
            lines = student_data.split('\n')
            added_count = 0
            error_count = 0
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                # Parse ID and Name (comma-separated or tab-separated)
                if ',' in line:
                    parts = line.split(',', 1)
                elif '\t' in line:
                    parts = line.split('\t', 1)
                else:
                    results.append(f"Line {line_num}: ❌ Invalid format - '{line}'")
                    error_count += 1
                    continue
                
                if len(parts) != 2:
                    results.append(f"Line {line_num}: ❌ Invalid format - '{line}'")
                    error_count += 1
                    continue
                
                student_id = parts[0].strip()
                student_name = parts[1].strip()
                
                if not student_id or not student_name:
                    results.append(f"Line {line_num}: ❌ Missing ID or Name - '{line}'")
                    error_count += 1
                    continue
                
                # Validate student ID format using re module
                if not re.match(r'^[A-Za-z0-9\-_]+$', student_id):
                    results.append(f"Line {line_num}: ❌ Invalid Student ID format - '{student_id}'")
                    error_count += 1
                    continue
                
                # Add student
                success, message = add_student_to_zenith_sheet(form_level, student_id, student_name)
                
                if success:
                    results.append(f"Line {line_num}: ✅ Added {student_name} (ID: {student_id})")
                    added_count += 1
                else:
                    results.append(f"Line {line_num}: ❌ {message}")
                    error_count += 1
                    
                # Small delay to avoid rate limiting
                if line_num % 5 == 0:
                    import time
                    time.sleep(0.1)
            
            summary = f"Batch complete! Successfully added: {added_count}, Errors: {error_count}"
            if added_count > 0:
                flash(summary, "success")
            elif error_count > 0:
                flash(summary, "warning")
    
    return render_template('batch_add_zenith_students.html', results=results)
    
@application.route('/privacy')
def privacy_policy():
    return render_template('privacy_policy.html')

# Route for logging out
@application.route('/logout')
def logout():
    session.clear()  # Clear the session data
    return redirect(url_for('login'))
    
if __name__ == '__main__':
    application.run(debug=True)
