{
    'name': 'Face & Mood Attendance',
    'version': '17.0.1.0.5',
    'category': 'Human Resources/Attendances',
    'summary': 'Face-recognition check-in/out with mood detection and wellbeing alerts',
    'description': """
Face & Mood Attendance
=======================

Adds a camera-based kiosk to Odoo Attendances:

* Employees check in / check out by having their face recognized in the
  browser (no external service required, in-browser AI models).
* At the same moment, the dominant facial expression (happy, sad, angry,
  neutral, ...) is captured and stored against the attendance record.
* A daily job looks for employees whose mood has been dominantly "sad"
  for a configurable number of consecutive attended days (20 by default)
  and, when that streak is hit:

  - raises an activity / notification for HR and the employee's manager
    so a human reviews the situation,
  - can create a draft leave request for the employee to review,
  - can log a small wellbeing incentive for payroll/HR to action.

IMPORTANT - read before deploying
----------------------------------
Face images and any inferred emotional state are sensitive personal /
biometric data under most data protection laws (e.g. the Saudi PDPL,
GDPR-alike regimes). This module:

* never enrolls or scores anyone without an explicit, timestamped
  consent flag on the employee record,
* never sends face data to any third party - matching and expression
  detection run entirely in the employee's / kiosk's browser,
* stores only a mathematical face descriptor (128 numbers), not the
  photo itself.

You are still responsible for: a written privacy notice, a lawful
basis / consent process suited to your jurisdiction, retention limits,
and legal sign-off before using this for real HR decisions (leave,
pay, discipline). Treat the "20 sad days" workflow as a *human review
trigger*, not an automated decision - a person must confirm any leave
or incentive before it is finalized.
""",
    'author': 'Allam Bushra',
    'website': 'https://www.linkedin.com/in/lomixyz/',
    'license': 'LGPL-3',
    'depends': ['hr_attendance', 'hr_holidays', 'mail'],
    'data': [
        'security/hr_face_mood_security.xml',
        'security/ir.model.access.csv',
        'data/hr_mood_data.xml',
        'data/ir_cron.xml',
        'views/hr_employee_views.xml',
        'views/hr_attendance_views.xml',
        'views/hr_mood_incentive_views.xml',
        'views/res_company_views.xml',
        'views/kiosk_templates.xml',
        'views/menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
