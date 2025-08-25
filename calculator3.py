import pandas as pd
import numpy as np

# --- 1. File Path ---
grades_filepath = 'grades4.csv' # Your CSV file with a header

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

# --- 3. Clean and Prepare Data ---
# We select and rename the columns to work with the rest of the script.
grades_clean_df = grades_df[['Student_Number', 'First_Name', 'Last_Name', 'Grade_level', 'Grade', 'Gradescaleid', 'Earned_Credits']].copy()
grades_clean_df.columns = ['student_id', 'first_name', 'last_name', 'grade_level', 'grade', 'gpa_added_value', 'credits']

# --- 4. Normalize Data for Consistency ---
print("Normalizing data for consistent processing...")
# FIX: Normalize names to prevent grouping errors from spaces or capitalization.
grades_clean_df['first_name'] = grades_clean_df['first_name'].str.strip().str.title()
grades_clean_df['last_name'] = grades_clean_df['last_name'].str.strip().str.title()
# Normalize grades by taking the first character (e.g., 'A+' becomes 'A')
grades_clean_df['grade'] = grades_clean_df['grade'].astype(str).str.strip().str[0]
print("Data normalization complete.\n")


# --- 5. Calculate GPA Components for Each Course ---
print("Calculating GPA components for each course...")
grade_map = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}
# Use .get() to avoid errors if a grade is not in the map; it will result in NaN.
grades_clean_df['base_points'] = grades_clean_df['grade'].map(grade_map)

grades_clean_df['gpa_added_value'] = pd.to_numeric(grades_clean_df['gpa_added_value'], errors='coerce').fillna(0)
grades_clean_df.loc[grades_clean_df['grade'] == 'F', 'gpa_added_value'] = 0

grades_clean_df['total_points_per_course'] = grades_clean_df['base_points'] + grades_clean_df['gpa_added_value']

grades_clean_df['point_multiplier'] = np.where(grades_clean_df['credits'] == 1.0, 2, 1)
grades_clean_df['custom_weighted_points'] = grades_clean_df['total_points_per_course'] * grades_clean_df['point_multiplier']
print("Component calculation complete.\n")

# --- 6. Save Detailed File ---
# FIX: Save the detailed file BEFORE filtering, ensuring all rows are included.
detailed_output_filename = 'grades_with_details.csv'
print(f"Saving detailed grade-by-grade data to {detailed_output_filename}...")
# We can save the cleaned dataframe directly as it has all the info.
grades_clean_df.to_csv(detailed_output_filename, index=False)
print("Detailed file saved.\n")


# --- 7. Filter for Valid Grades for Final GPA Calculation ---
print("Filtering for valid grades (A, B, C, D, F) for final GPA calculation...")
valid_grades = ['A', 'B', 'C', 'D', 'F']
gpa_calc_df = grades_clean_df[grades_clean_df['grade'].isin(valid_grades)].copy()
print(f"Removed {len(grades_clean_df) - len(gpa_calc_df)} rows with non-standard or invalid grades.\n")


# --- 8. Calculate Final Custom GPA for Each Student ---
print("Calculating final custom GPAs...")
gpa_agg = gpa_calc_df.groupby(['student_id', 'first_name', 'last_name', 'grade_level']).agg(
    total_custom_points=('custom_weighted_points', 'sum'),
    course_count=('grade', 'count')
).reset_index()

gpa_agg['gpa'] = 0.0
gpa_agg.loc[gpa_agg['course_count'] > 0, 'gpa'] = gpa_agg['total_custom_points'] / gpa_agg['course_count']


# --- 9. Display and Save Final GPA Summary ---
summary_output_filename = 'student_gpas4.csv'
print("Final Student GPA Summary:")
gpa_agg['gpa'] = gpa_agg['gpa'].round(2)
print(gpa_agg[['student_id', 'first_name', 'last_name', 'grade_level', 'gpa']])

print(f"\nSaving final GPA summary to {summary_output_filename}...")
gpa_agg.to_csv(summary_output_filename, index=False)
print("Summary file saved.")
