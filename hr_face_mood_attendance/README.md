# Face & Mood Attendance (Odoo 20 build, technical name: hr_face_mood_attendance)

> **Status of this build - please read first.** At the time this build
> was prepared, Odoo 20 had just been announced at Odoo Experience and
> had not reached general availability; there was no official,
> confirmed developer changelog to verify against yet. This release
> was ported on a **best-effort basis** from the working Odoo 17
> module, applying the concrete, already-documented conventions Odoo
> has been converging on since 18.0/19.0:
> - `<tree>` view tags and `view_mode: 'tree,...'` renamed to `<list>` / `'list,...'`.
> - The verbose `oe_chatter` div replaced with the `<chatter/>` tag.
> - No `attrs=`/`states=` remnants (this module already used the
>   modern `invisible="..."` syntax throughout).
>
> **One real risk remains and is called out inline in
> `views/hr_attendance_views.xml`**: this module inherits two of
> `hr_attendance`'s own views (its attendance list and form), and their
> exact external IDs may have changed by 20.0 the same way they moved
> from `view_attendance_tree` in 17.0 towards a `..._list` naming
> pattern in 18.0/19.0. If installing this module errors with an
> "external ID not found" on one of those two `<record>`s, open
> **Settings > Technical > Views**, search "Attendances", find the
> actual list/form view IDs on your instance, and swap them into the
> `ref="..."` in that file - everything else in the module is
> self-contained and does not depend on core view internals.
>
> Once Odoo 20 reaches general availability, it would be worth a
> quick real install-and-test pass rather than trusting this note
> alone.
>
> **Update 1:** a real install against an Odoo 20 dev build surfaced a
> second, confirmed issue: `hr_holidays`' `hr.leave.type` model (and
> `hr.leave.holiday_status_id`) appears to have been removed/restructured
> in Odoo 20 (replaced by an in-flux `hr.time.rule` concept), so this
> build's earlier "company-configured wellbeing leave type" field and
> its auto-created **draft leave** have both been **removed**. This
> build no longer creates any `hr.leave` automatically - see "How it
> works" and the `leave_id` field below.
>
> **Update 2 - bigger one:** the same real-install testing then hit a
> `KeyError: 'ir.rule'` while loading this module's security data, even
> after a full server restart. Digging into the Odoo 20 dev source
> confirmed this is not a corrupted install: **Odoo 20 has merged the
> classic `ir.model.access` (CRUD access rights) and `ir.rule` (record
> rules) models into a single new model, `ir.access`**, with fields
> `model_id`, `group_id` (empty = a global restriction, like an old
> `ir.rule` with no groups; set = a permission grant, like an old
> `ir.model.access.csv` row), `operation` (a short code such as `crud`,
> `cru`, `cr`, ... for which of Create/Read/Update/Delete it applies
> to), and `domain` (replacing `domain_force`). This module's
> `security/hr_face_mood_security.xml` was rewritten against `ir.access`
> and `security/ir.model.access.csv` was removed entirely (folded into
> the same XML file). **This is deep, pre-GA internal Odoo 20 API and
> is exactly the kind of thing that can still change again before
> Odoo 20's official release** - if you hit another security-related
> error (e.g. about `ir.access` itself, or a field on it), that's why,
> and it's the first place to check.
>
> **Update 3:** cross-checked the `ir.access` approach above against
> Odoo's own official `account` (Invoicing) module source pulled from a
> real Odoo 20 install, which confirmed the exact working format:
> access/rule rows now live in a CSV file named after the model itself
> (`security/ir.access.csv`, columns `id,name,model_id,group_id/id,
> operation,domain` - note `model_id` takes the plain model name like
> `hr.mood.incentive`, not an external-id-style `model_xxx` reference),
> and `res.groups` records stay in a plain XML file as before. This
> module's security files were rewritten to match that confirmed,
> real-world format exactly. Also: **this build's technical module
> name is `hr_face_mood_attendance`, the same as the 17.0 build** -
> matching how Odoo's own official addons never encode the Odoo series
> in the technical (folder) name, only in the manifest `version` field
> (e.g. `20.0.1.0.3`). Keep the two builds in separate addons paths so
> they never both try to install under the same technical name on one
> database.
>
> **Update 4:** installing past the security fix hit one more confirmed
> break: `ir.cron`'s `numbercall` field is gone in this Odoo 20 build
> (cross-checked against the official `account` module's own
> `data/service_cron.xml`, which no longer sets it either). Removed
> `numbercall` from `data/ir_cron.xml` - the cron still runs daily via
> `interval_number`/`interval_type` as before.
>
> **Update 5:** confirmed directly on the user's real Odoo 20.0.20260924
> build: `hr_attendance`'s standard attendance list view external ID is
> **`hr_attendance.view_attendance_tree`**, NOT `view_attendance_list`
> as earlier guessed by analogy with the 18.0/19.0 tree-to-list
> renaming. `views/hr_attendance_views.xml` was corrected accordingly.

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
  **Attendances > Wellbeing Triggers**) and schedules an activity for
  HR + the manager. **No leave is created automatically.** If HR/the
  manager decides time off is appropriate, they create the `hr.leave`
  themselves (any leave type - this build has no dependency on the
  `hr.leave.type` model) and can link it on the wellbeing record's
  **Linked Leave** field for traceability.

## Setup

1. Install the module (`hr_attendance`, `hr_holidays`, `mail` are
   pulled in automatically).
2. **Settings > Companies > (your company)**: a "Face & Mood
   Attendance" section holds the sad-streak threshold, confidence
   threshold, suggested incentive amount, and the face/mood model URL.
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
