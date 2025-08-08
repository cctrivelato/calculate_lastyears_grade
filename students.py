class Student:
    def __init__(self, firstname, lastname, id_number, grade_level):
        self.firstname = firstname
        self.lastname = lastname
        self.id_number = id_number
        self.grade_level = grade_level

    def add_course(self, letter_grade, grade_scale):
        self.courses.append((letter_grade, grade_scale))

    def calculate_weighted_gpa(self):
        grade_points = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}
        total_points = 0
        total_classes = 0

        for grade, scale in self.courses:
            if grade.upper() == "P":
                continue
            points = grade_points.get(grade.upper(), 0)

            # Apply +1 if grade scale is AP or Honors
            if scale and scale.lower() in ("ap", "honors"):
                points += 1

            total_points += points
            total_classes += 1

        return round(total_points / total_classes, 2) if total_classes > 0 else None