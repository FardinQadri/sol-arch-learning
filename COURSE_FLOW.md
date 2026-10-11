# Course flow

One week at a time: concepts → drills → quiz → milestone → (optional) lab → review.

## Week 00 — Foundations & exam technique (no milestone)
- Concepts: `week_00_foundations_and_exam_technique/concepts/01 … 05` and both demos
- Drills: `python week_00_foundations_and_exam_technique/practice/exercises.py` → 10/10
- Quiz: `python quiz.py --week 0 -n 15` → ≥ 80 %
- Lab (optional): `week_00_…/lab/LAB.md` — account safety first

## Week 01 — IAM & multi-account governance
- Concepts: `week_01_iam_and_governance/concepts/01 … 05` and both demos
- Drills: `python week_01_iam_and_governance/practice/exercises.py` → 10/10
- Quiz: `python quiz.py --week 1 -n 30` → ≥ 80 %
- Milestone M01: `course_project/milestones/M01.md`
  - `python course_project/tools/start_milestone.py 1 --repo ~/code/shortly-infra`
  - in your repo: `<course>/.venv/Scripts/python.exe run_milestone.py 1` → 6/6 steps green, then commit
- Lab (optional): `week_01_…/lab/LAB.md`
- From now on, start each session with `python quiz.py --review`

## Week 02 — VPC networking
- Concepts: `week_02_vpc_networking/concepts/01 … 05` and both demos
- Drills: `python week_02_vpc_networking/practice/exercises.py` → 10/10
- Quiz: `python quiz.py --week 2 -n 30` → ≥ 80 %
- Milestone M02: `course_project/milestones/M02.md`
  - `python course_project/tools/start_milestone.py 2 --repo ~/code/shortly-infra`
  - in your repo: `<course>/.venv/Scripts/python.exe run_milestone.py 2` → 6/6 steps green, then commit
- Lab (optional): `week_02_…/lab/LAB.md` — tag everything `saa-course=lab`; delete the NAT gateway within 30 minutes
- Review: `python quiz.py --review`

## Week 03 — Compute & scaling
- Concepts: `week_03_compute_and_scaling/concepts/01 … 05` and both demos
- Drills: `python week_03_compute_and_scaling/practice/exercises.py` → 10/10
- Quiz: `python quiz.py --week 3 -n 30` → ≥ 80 %
- Milestone M03: `course_project/milestones/M03.md`
  - `python course_project/tools/start_milestone.py 3 --repo ~/code/shortly-infra` (also copies the course's app into `app/`)
  - in your repo: `<course>/.venv/Scripts/python.exe run_milestone.py 3` → 6/6 steps green, then commit
- Lab (optional): `week_03_…/lab/LAB.md` — default VPC, tag everything `saa-course=lab`, clean up within 90 minutes
- Review: `python quiz.py --review`

## Week 04 — Storage
- Concepts: `week_04_storage/concepts/01 … 05` and both demos
- Drills: `python week_04_storage/practice/exercises.py` → 10/10
- Quiz: `python quiz.py --week 4 -n 30` → ≥ 80 %
- Milestone M04: `course_project/milestones/M04.md`
  - `python course_project/tools/start_milestone.py 4 --repo ~/code/shortly-infra`
  - in your repo: `<course>/.venv/Scripts/python.exe run_milestone.py 4` → 5/5 steps green, then commit
- Lab (optional): `week_04_…/lab/LAB.md` — a versioned bucket, a lifecycle rule, a presigned URL, an EBS volume and snapshots; tag everything `saa-course=lab`
- Review: `python quiz.py --review`

## Week 05 — Databases & caching
- Concepts: `week_05_databases_and_caching/concepts/01 … 05` and both demos
- Drills: `python week_05_databases_and_caching/practice/exercises.py` → 10/10
- Quiz: `python quiz.py --week 5 -n 30` → ≥ 80 %
- Milestone M05: `course_project/milestones/M05.md`
  - `python course_project/tools/start_milestone.py 5 --repo ~/code/shortly-infra`
  - in your repo: `<course>/.venv/Scripts/python.exe run_milestone.py 5` → 6/6 steps green, then commit
- Lab (optional): `week_05_…/lab/LAB.md` — a DynamoDB table and a Single-AZ RDS PostgreSQL instance; never Multi-AZ in the lab
- Review: `python quiz.py --review`

## Weeks 06–12
Built one week at a time. See the README's week table and the design spec.
