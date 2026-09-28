{
    'name': 'Face & Mood Attendance',
    'version': '20.0.1.0.7',
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
  - HR can then create and link a leave for the employee if appropriate
    (this build does not auto-create the leave - see the note below),
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

NOTE ON THIS 20.0 BUILD: Odoo 20 had not reached general availability at
the time this build was prepared, so it targets the 18.0/19.0 view
conventions Odoo has been converging on (list views, <chatter/>) as the
closest known approximation. It also does NOT auto-create a leave
request: hr_holidays' "leave type" concept (hr.leave.type) was being
restructured in Odoo 20 dev builds, so this build only notifies HR/the
manager and lets them create and link the leave themselves. On top of
that, real-install testing found that Odoo 20 dev builds have merged
the classic ir.model.access / ir.rule security models into a single
new ir.access model. This module's security data was rewritten against
that new model and cross-checked against Odoo's own official "account"
(Invoicing) module source from a real Odoo 20 install, which confirmed
the exact security/ir.access.csv format used here. Both of these are
internal, pre-GA Odoo 20 APIs and may still change before the official
release. See the module's README for details and what to check first
if an install error appears.

This 20.0 build's technical module name is the same as the 17.0 build
(hr_face_mood_attendance) - matching how Odoo's own official modules
never encode the Odoo series in the technical name, only in the
manifest 'version' field. Keep the 17.0 and 20.0 builds in separate
addons paths / git branches, never installed side by side under the
same name on one database.
""",
    'author': 'Allam Bushra',
    'website': 'https://www.linkedin.com/in/lomixyz/',
    'license': 'LGPL-3',
    'depends': ['hr_attendance', 'hr_holidays', 'mail'],
    'data': [
        'security/hr_face_mood_security.xml',
        'security/ir.access.csv',
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
