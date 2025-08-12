import requests
import csv
from students import Student

studentsclass = []

base_url = "https://usd470.powerschool.com"
client_id = "b3329d40-f8b2-47c8-96b6-2083262acc42"
client_secret = "3c788652-9442-4bba-9e4e-50bb7160c3ec"

def get_data(headers, page, url):

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Page {page} status: {response.status_code}")
        response.raise_for_status()
    except requests.exceptions.ConnectTimeout:
        print(f"⚠️ Connection timed out while requesting page {page}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return []

    data = response.json()
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return next((v for v in data.values() if isinstance(v, list)), [])
    else:
        return data.get('items', [])

def get_access_token():
    token_url = f"{base_url}/oauth/access_token"
    response = requests.post(token_url, data={
        'grant_type': 'client_credentials'
    }, auth=(client_id, client_secret))
    
    response.raise_for_status()
    token_data = response.json()
    return token_data['access_token']

def main():
    headers = {
        'Authorization': f'Bearer {get_access_token()}',
        'Accept': 'application/json',
    }

    studentsclass = {}
    all_students = []
    all_grades = []

    # Get all students (paginated)
    page = 1
    while True:
        user_package = f"{base_url}/ws/schema/table/students?q=enroll_status==0;schoolid==7456&page={page}&pagesize=100&projection=first_name,last_name,grade_level,id"
        students = get_data(headers, page, user_package)
        if not students:
            break
        all_students.extend(students)
        page += 1

    # Create Student objects indexed by ID
    for s in all_students:
        first_name = s.get("first_name", "Unknown")
        last_name = s.get("last_name", "Unknown")
        grade_level = s.get("grade_level", "Unknown")
        student_id = s.get("id", None)

        if student_id is None:
            print("Warning: student missing ID:", s)
        else:
            studentsclass[student_id] = Student(
                id_number=student_id,
                firstname=first_name,
                lastname=last_name,
                grade_level=grade_level
            )

    # Now get grades for each student for two terms
    for student_id in studentsclass.keys():
        print(f"--- Processing Student ID: {student_id} ---")
        
        # Loop through each term for the student
        for termid, storecode in [("3401", "S1"), ("3402", "S2")]:
            print(f"Checking Term: {termid}, Store Code: {storecode}")
            page = 1
            
            while True:
                # Construct the query string to filter results on the server
                query = f"studentid=={student_id};termid=={termid};storecode=={storecode}"
                
                grades_url = f"{base_url}/ws/schema/table/storedgrades"
                params = {
                    "q": query,           # ✅ FIXED: Pass the query to the API
                    "page": page,
                    "pagesize": 100,      # ✅ IMPROVED: Request more records at once for efficiency
                    "projection": "grade,studentid,gradescale_name"
                }
                
                try:
                    response = requests.get(grades_url, headers=headers, params=params)
                    response.raise_for_status() # Check for HTTP errors (e.g., 404, 500)
                    data = response.json()
                    
                    # NOTE: The key in the JSON response containing the list of data can vary.
                    # PowerSchool APIs often use 'record'. This code checks for 'record' first,
                    # then falls back to your original 'storedgrades'.
                    grades = data.get('record') or data.get('storedgrades')

                    # ✅ FIXED: If the API returns no records, we've reached the end.
                    if not grades:
                        print("No grades")
                        break # Exit the 'while' loop

                    # Process and display the grades you received
                    for grade_record in grades:
                        print(f"  - Grade: {grade_record.get('grade')}, Scale: {grade_record.get('gradescale_name')}")

                    # ✅ IMPROVED: If we got fewer records than we asked for, it's the last page.
                    if len(grades) < params["pagesize"]:
                        break # Exit the 'while' loop

                    # ✅ FIXED: Go to the next page for the next loop iteration.
                    page += 1

                except requests.exceptions.RequestException as e:
                    print(f"An error occurred: {e}")
                    break # Stop processing this term if an error occurs

    print("-" * 40) 

    # Write results to TSV
    with open("students_gpa.tsv", "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["FirstName", "LastName", "ID", "GradeLevel", "GPA"])
        for student in studentsclass.values():
            gpa = student.calculate_weighted_gpa()
            writer.writerow([
                student.first_name,
                student.last_name,
                student.student_id,
                student.grade_level,
                gpa if gpa is not None else ""
            ])

    print("✅ Tab-delimited file 'students_gpa.tsv' created.")

if __name__ == "__main__":
    main()