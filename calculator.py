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
        print(student_id)
        for termid, storecode in [("3401", "S1"), ("3402", "S2")]:
            page = 1
            while True:
                grades_url = f"{base_url}/ws/schema/table/storedgrades"
                query = f"studentid=={student_id};termid=={termid};storecode=={storecode}"
                params = {
                    "q": query,
                    "page": page,
                    "pagesize": 100,
                    "projection": "grade,studentid,gradescale_name"
                }
                response = requests.get(grades_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                grades = data.get("data", [])
                if not grades:
                    break
                all_grades.extend(grades)
                page += 1

    # Add grades to students
    for g in all_grades:
        student = studentsclass.get(g["studentid"])
        if student:
            student.add_course(g["grade"], g["gradescale_name"])

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