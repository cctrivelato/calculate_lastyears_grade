import pandas as pd

# --- 1. File Path ---
grades_filepath = 'grades2.0.csv' # Your new space-separated file

# --- 2. Load the Data ---
try:
    print(f"Loading grades data from: {grades_filepath}")
    # The file now has a header, so we let pandas read it automatically.
    grades_df = pd.read_csv(grades_filepath, encoding='latin1')
    
    # --- Check if the DataFrame is empty after loading ---
    if grades_df.empty:
        print("\n--- ERROR ---")
        print("No data was found in the input file. Please check that the file is not empty.")
        exit()

    print(f"Data loaded successfully. Processed {len(grades_df)} records.\n")

except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please make sure the file name and path are correct.")
    exit()
except Exception as e:
    print(f"An unexpected error occurred during file loading: {e}")
    exit()

# --- 3. Assign Column Names and Clean Data ---
# We select and rename the columns to work with the rest of the script.
# This makes it easy to change if your source column names change.
grades_clean_df = grades_df[['Student_Number', 'LastFirst', 'Grade_level', 'Grade', 'Gradescaleid']].copy()
grades_clean_df.columns = ['student_id', 'student_name', 'grade_level', 'grade', 'description']

# --- 4. Clean and Filter for Valid Grades ---
print("Normalizing and filtering for valid grades (A, B, C, D, F)...")
valid_grades = ['A', 'B', 'C', 'D', 'F']

grades_clean_df['grade'] = grades_clean_df['grade'].astype(str).str.strip()
grades_clean_df['grade'] = grades_clean_df['grade'].str[0]

original_rows = len(grades_clean_df)
grades_clean_df = grades_clean_df[grades_clean_df['grade'].isin(valid_grades)]
print(f"Removed {original_rows - len(grades_clean_df)} rows with non-standard or invalid grades.\n")


# --- 5. Define Grade Point and Calculation Logic ---
def calculate_grade_points(row):
    """
    Calculates points for a grade. Adds a +1 bonus if the description
    is 'AP Grades'.
    """
    grade_map = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}
    grade = row['grade']
    description = str(row['description']).strip()
    
    points = grade_map.get(grade, 0) # Use .get() for safety in case of unexpected data
    
    # Check if the course is an honors course and the grade is not an 'F'
    if description == 'AP Grades' and grade != 'F':
        points += 1
        
    return points

print("Calculating grade points for each course...")
grades_clean_df['points'] = grades_clean_df.apply(calculate_grade_points, axis=1)
print("Points calculation complete.\n")

# --- 6. Calculate Final GPA for Each Student ---
print("Calculating final GPAs...")
# Group by the new, consistent column names, including grade_level
gpa_results = grades_clean_df.groupby(['student_id', 'student_name', 'grade_level']).agg(
    total_points=('points', 'sum'),
    course_count=('grade', 'count')
).reset_index()

gpa_results['gpa'] = 0.0
gpa_results.loc[gpa_results['course_count'] > 0, 'gpa'] = gpa_results['total_points'] / gpa_results['course_count']

# --- 7. Display and Save the Final Results ---
print("Final GPA Results:")
gpa_results['gpa'] = gpa_results['gpa'].round(2)
print(gpa_results[['student_id', 'student_name', 'grade_level', 'gpa']])

output_filename = 'student_gpas_withgradelevel.csv'
gpa_results.to_csv(output_filename, index=False)
print(f"\nResults have been saved to {output_filename}")