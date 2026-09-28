# Face & Mood Attendance (Odoo 17)

Camera-based check-in/out that recognizes an employee's face in the
browser and reads their dominant facial expression at that moment. A
daily job watches for employees whose mood has been dominantly "sad"
for a configurable number of consecutive attended days (default: 20)
and, when that streak is hit, raises a human-review workflow: a
notification/activity for HR and the manager, an optional **draft**
leave request, and a suggested wellbeing incentive. Nothing is
auto-approved - a person always confirms the leave/incentive.

## How it works

- **Recognition & expression detection run entirely in the browser**
  using [face-api.js](https://github.com/justadudewhohacks/face-api.js)
  (loaded from a CDN by default, or self-hosted - see below). Odoo
  never receives a photo, only: the matched employee id, the dominant
  mood label, its confidence score, and the match distance.
- Each employee enrolls their **own** face descriptor (a 128-number
  vector, not an image) from **Attendances > My Face ID**, and only
  after ticking consent on their employee record.
- A shared kiosk device (tablet at the entrance) opens
  **Attendances > Face & Mood Kiosk**, logged in as a dedicated
  internal user in the *Mood Attendance Kiosk Device* group (or any HR
  officer). It recognizes whoever stands in front of it among
  consenting, enrolled employees and toggles their check-in/check-out.
- `hr.attendance` gets 4 new fields: mood + confidence at check-in and
  at check-out.
- The `_cron_check_mood_streaks` daily cron recomputes each consenting
  employee's consecutive sad-day streak and, once it crosses the
  threshold, creates an `hr.mood.incentive` record (menu:
  **Attendances > Wellbeing Triggers**), schedules an activity for HR
  + the manager, and (if a wellbeing leave type is configured in
  Settings) a **draft** leave request.

## Setup

1. Install the module (`hr_attendance`, `hr_holidays`, `mail` are
   pulled in automatically).
2. **Settings > Companies > (your company)**: a "Face & Mood
   Attendance" section holds the sad-streak threshold, confidence
   threshold, wellbeing leave type, suggested incentive amount, and
   the face/mood model URL.
3. Create a dedicated internal user for each kiosk tablet, add it to
   *Mood Attendance Kiosk Device*, and leave it logged in at
   `/hr_face_mood/kiosk` on that device.
4. Each employee: HR ticks **Face ID & Mood > Consent** on their
   employee record, then the employee opens
   **Attendances > My Face ID** themselves and captures their face.

## Offline / self-hosted AI models

By default the kiosk loads face-api.js's model weights from a public
CDN (`https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights`).
For a fully offline deployment, download that `weights/` folder,
serve it from your own web server (or drop it under this module's
`static/src/models/` and expose it via a static route), and change
**Face/Mood Model URL** in Settings to point at it.

## Read before you switch this on for real employees

Face descriptors and inferred mood are sensitive / biometric personal
data under most data-protection regimes (Saudi PDPL, GDPR-alike laws
elsewhere). This module is a technical scaffold, not a compliance
package:

- Get written legal sign-off and a proper privacy notice before
  deploying. Consent must be freely given, specific, and revocable -
  the module deletes the stored face descriptor the moment consent is
  unticked, but you still need a documented process around that.
- The client-side matching in this scaffold trusts the browser's
  reported match distance; for a security-critical deployment, verify
  the match server-side too (e.g. re-run distance comparison in
  Python against the stored descriptor) rather than trusting the
  kiosk page alone.
- Treat the 20-day "sad streak" workflow strictly as a prompt for a
  human conversation, never as an automated basis for pay, discipline,
  or performance decisions.
