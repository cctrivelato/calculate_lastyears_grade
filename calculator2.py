import pandas as pd
import numpy as np

# --- 1. File Path ---
grades_filepath = 'grades2.csv' # Your CSV file with a header

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
grades_clean_df = grades_df[['Student_Number', 'LastFirst', 'Grade_level', 'Grade', 'Gradescaleid', 'Earned_Credits']].copy()
grades_clean_df.columns = ['student_id', 'student_name', 'grade_level', 'grade', 'gpa_added_value', 'credits']

# --- 4. Normalize and Filter Grades ---
print("Normalizing and filtering for valid grades (A, B, C, D, F)...")
valid_grades = ['A', 'B', 'C', 'D', 'F']

grades_clean_df['grade'] = grades_clean_df['grade'].astype(str).str.strip().str[0]

original_rows = len(grades_clean_df)
grades_clean_df = grades_clean_df[grades_clean_df['grade'].isin(valid_grades)]
print(f"Removed {original_rows - len(grades_clean_df)} rows with non-standard or invalid grades.\n")


# --- 5. Calculate GPA Components for Each Course (UPDATED LOGIC) ---
print("Calculating GPA components for each course...")
grade_map = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}
grades_clean_df['base_points'] = grades_clean_df['grade'].map(grade_map)

grades_clean_df['gpa_added_value'] = pd.to_numeric(grades_clean_df['gpa_added_value'], errors='coerce').fillna(0)
grades_clean_df.loc[grades_clean_df['grade'] == 'F', 'gpa_added_value'] = 0

grades_clean_df['total_points_per_course'] = grades_clean_df['base_points'] + grades_clean_df['gpa_added_value']

# Calculate a multiplier based on credits.
# A 1.0 credit course will have its points doubled (multiplier of 2).
# All other courses (0.5, 0, etc.) will have a standard weight (multiplier of 1).
grades_clean_df['point_multiplier'] = np.where(grades_clean_df['credits'] == 1.0, 2, 1)

# Calculate the final points for the course using the multiplier.
grades_clean_df['custom_weighted_points'] = grades_clean_df['total_points_per_course'] * grades_clean_df['point_multiplier']
print("Component calculation complete.\n")


# --- 6. Calculate Final Custom GPA for Each Student ---
print("Calculating final custom GPAs...")
# Group by student and aggregate based on the new logic.
gpa_agg = grades_clean_df.groupby(['student_id', 'student_name', 'grade_level']).agg(
    # Sum the custom points for the numerator
    total_custom_points=('custom_weighted_points', 'sum'),
    # Count the number of courses for the denominator
    course_count=('grade', 'count')
).reset_index()

# Calculate the final GPA using the custom formula
gpa_agg['gpa'] = 0.0
gpa_agg.loc[gpa_agg['course_count'] > 0, 'gpa'] = gpa_agg['total_custom_points'] / gpa_agg['course_count']


# --- 7. Display and Save the Final Results ---
# First, save the detailed grades file with the new columns
detailed_output_filename = 'grades_with_details.csv'
# We need to merge our calculated data back to the original to get all columns
final_detailed_df = grades_df.merge(
    grades_clean_df[['gpa_added_value', 'custom_weighted_points']],
    left_index=True,
    right_index=True,
    how='left'
).fillna(0) # Fill non-graded courses with 0 for added columns

# To avoid duplicate columns if script is run multiple times on its own output
final_detailed_df = final_detailed_df.loc[:,~final_detailed_df.columns.duplicated()]

print(f"Saving detailed grade-by-grade data to {detailed_output_filename}...")
final_detailed_df.to_csv(detailed_output_filename, index=False)
print("Detailed file saved.\n")


# Second, save the final student GPA summary
summary_output_filename = 'student_gpas.csv'
print("Final Student GPA Summary:")
gpa_agg['gpa'] = gpa_agg['gpa'].round(2)
print(gpa_agg[['student_id', 'student_name', 'grade_level', 'gpa']])

print(f"\nSaving final GPA summary to {summary_output_filename}...")
gpa_agg.to_csv(summary_output_filename, index=False)
print("Summary file saved.")
