from StudentApp.models import Attendance, ExamResult

def calculate_attendance_percentage(student):
    total_classes = Attendance.objects.filter(student=student).count()
    if total_classes == 0:
        return 0

    present_classes = Attendance.objects.filter(
        student=student,
        status='Present'
    ).count()

    return round((present_classes / total_classes) * 100, 2)


def check_exam_eligibility(student):
    attendance_percentage = calculate_attendance_percentage(student)

    academics_passed = ExamResult.objects.filter(
        student=student,
        is_passed=True
    ).exists()

    reasons = []

    if not student.is_fee_paid:
        reasons.append("Fees not paid")

    if attendance_percentage < 75:
        reasons.append("Attendance below 75%")

    if not academics_passed:
        reasons.append("Academic requirements not met")

    eligible = len(reasons) == 0

    return {
        "eligible": eligible,
        "attendance": attendance_percentage,
        "academics": academics_passed,
        "reasons": reasons
    }
