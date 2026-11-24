# CSCI 341 Assignment 3 - Conference and Paper Review System

## Versions

- PostgreSQL 18.6 (local), PostgreSQL 18.7 on Neon (deployed)
- Python 3.13.9 (Part 2), Python 3.12 (web app, locally and on Render)
- SQLAlchemy 2.1.9, psycopg2-binary 2.9.13, FastAPI 0.165.0, uvicorn 0.54.0 (requirements.txt)

## Files

- `sql/schema.sql` - creates all tables and constraints (drops old ones first)
- `sql/seed.sql` - deletes all rows and inserts the sample data
- `sql/verify_rules.sql` - checks the business rules on the data, all numbers should be 0
- `part2_queries.py` - Part 2, runs tasks 1 to 8 with SQLAlchemy
- `main.py` - Part 3, the FastAPI web app
- `db.py` - creates the SQLAlchemy engine from DATABASE_URL, used by main.py
- `requirements.txt`

## Database setup and restore

The database is called `OmarData`. Because of the capital letters it has to be created with quotes:

```
CREATE DATABASE "OmarData";
```

Then either run the Python program (tasks 1 and 2 create the tables and load the data):

```
python part2_queries.py 1 2
```

or use psql:

```
psql -U postgres -d OmarData -f sql/schema.sql
psql -U postgres -d OmarData -1 -f sql/seed.sql
psql -U postgres -d OmarData -f sql/verify_rules.sql
```

To restore the initial data at any time run seed.sql again (or `python part2_queries.py 2`). It truncates all tables and inserts the same rows with the same ids.

---

# Part 1

## Tables and keys

We used the reference schema from Appendix A.

| Table | Primary key | Foreign keys | Unique |
|---|---|---|---|
| app_user | user_id | | email |
| author | author_id | author_id -> app_user | orcid |
| author_research_area | (author_id, area_label) | author_id -> author | |
| reviewer | reviewer_id | reviewer_id -> app_user | |
| reviewer_expertise | (reviewer_id, area_label) | reviewer_id -> reviewer | |
| conference | conference_id | | acronym |
| conference_host | (conference_id, host_name) | conference_id -> conference | |
| conference_reviewer | (conference_id, reviewer_id) | conference_id -> conference, reviewer_id -> reviewer | |
| track | track_id | conference_id -> conference, coordinator_id -> reviewer, (conference_id, coordinator_id) -> conference_reviewer | (conference_id, name) |
| conference_session | session_id | conference_id -> conference, chair_id -> reviewer, (conference_id, chair_id) -> conference_reviewer | |
| paper | paper_id | track_id -> track, session_id -> conference_session | |
| paper_keyword | (paper_id, keyword) | paper_id -> paper | |
| paper_author | (paper_id, author_id) | paper_id -> paper, author_id -> author | (paper_id, author_position) |
| paper_version | (paper_id, version_no) | paper_id -> paper | |
| review | review_id | paper_id -> paper, reviewer_id -> reviewer | (paper_id, reviewer_id) |

- Author and reviewer use the same id as app_user (overlapping specialization, a user can be both).
- Research areas, expertise, hosts and keywords are in their own tables, no comma separated lists.
- paper_version is a weak entity, key is (paper_id, version_no). Gaps are allowed and the current version is the max version_no, so we don't store it.
- paper.session_id is NULL when the paper is not in a session, so a paper can have at most one session.
- Only orcid, session_id, change_note and confidential_comments can be NULL. Everything else is NOT NULL.

## Constraints

- Unique: user email, (paper_id, author_position), (paper_id, reviewer_id) in review.
- Only completed reviews: all review columns except confidential_comments are NOT NULL.
- CHECK: paper status (5 values), score 1 to 5, recommendation accept/reject, author_position > 0, version_no > 0, years_experience >= 0, conference end_date >= start_date, session end_time > start_time.
- Extra checks we added: email must have @, orcid format, review_deadline >= submission_deadline.
- chk_session_only_accepted: a paper can have a session only if its status is accepted.
- Unique index uq_one_corresponding_author: at most one corresponding author per paper.

## Delete actions

- Delete user: author/reviewer rows, areas, expertise and pool rows are deleted (cascade). It is rejected if the user wrote a paper or a review, or is a coordinator or chair.
- Delete paper: versions, keywords, authors and reviews are deleted (cascade).
- Delete session: papers stay, their session_id becomes NULL.
- Delete track: rejected if it has papers.
- Delete conference: hosts, pool, tracks and sessions are deleted. Rejected if a track has papers. Users and reviewers are never deleted.

We never turn off foreign keys.

## Required checks (done in the web app, Part 3)

1. No self review. Before saving a review we check the reviewer is not an author of the paper. When the authors of a paper change we check none of the new authors already reviewed it.
2. Session assignment. A paper in a session must be accepted (also checked by the database), and its track and the session must be in the same conference. If a change breaks this (status not accepted, track in another conference, or a session moved to another conference while it has papers) it is rejected with 409.

## Other business rules

verify_rules.sql checks all of them, on our data all are 0.

| Rule | Enforced? |
|---|---|
| Track coordinator is in the conference pool | yes, composite FK |
| Session chair is in the conference pool | yes, composite FK |
| Exactly one corresponding author | at most one by unique index, at least one by the app |
| Every user is author or reviewer or both | only in data |
| Every paper has at least one author, keyword, version | at least one author by the app, keyword and version only in data |
| Every author has a research area, every reviewer has an expertise | only in data |
| A reviewer only reviews papers of conferences where he is in the pool | only in data |
| Every conference has a host and a track | only in data |
| Session date is inside the conference dates | only in data |
| Paper submitted before the submission deadline | only in data |
| Author positions are 1..n without gaps | only in data |

## Assumptions

- The conference of a paper is found through its track (paper -> track -> conference).
- A reviewer can be in the pool of more than one conference.
- Deadlines are dates without time.
- file_location is just a path, no real files.
- Phone number is required.

## Changes from Assignment 1
 We used Azamat's assignment 1, but made some changes according to feedback received from professor (score was 92.5/100)
- Paper Version: version_no is the partial key, key is (paper_id, version_no). HAS_VERSION is 1:N with total participation of Paper Version. Removed the current version attribute (it is derived).
- Status and recommendation values were drawn as attributes, now they are CHECK constraints.
- Exactly one corresponding author was missing in UML, now it is enforced as above.
- Reviewer-Track multiplicity fixed: a track has exactly one coordinator, a reviewer can coordinate 0 or more tracks.

## Sample data

All data is test data. Only Arman Armanov and Amina Aminova are from the assignment, the other users are Person 3 to Person 14.

Row counts: app_user 14, author 9, author_research_area 16, reviewer 9, reviewer_expertise 17, conference 3, conference_host 5, conference_reviewer 14, track 6, conference_session 5, paper 13, paper_keyword 28, paper_author 26, paper_version 18, review 20.

- Author only: Amina, Person 7, 8, 11, 14. Reviewer only: Person 4, 5, 9, 10, 13. Both: Arman, Person 3, 6, 12.
- Statuses: accepted 1, 2, 3, 4, 9; rejected 5, 11, 13; under review 6; withdrawn 7, 8, 12; submitted 10.
- Multiple versions: paper 1 (v1, v2, v3), paper 2 and 7 (v1, v2), paper 9 (v1, v3, gap).
- Empty track: Track 3 and Track 6. Conference with no papers: CONF-C (Tashkent).
- Reviewer with no reviews: Person 13.
- Accepted with session: 1, 2, 3, 9. Accepted without session: 4.
- Amina is corresponding author of withdrawn papers 7 and 8. Paper 12 is also withdrawn but Person 11 is corresponding, so it should stay.
- Empty session in Astana: Session 3 (CONF-A). Session 5 is empty too but in Almaty.
- Conferences: CONF-A Astana, CONF-B Almaty, CONF-C Tashkent.
- Reviews per reviewer: Person 4 has 5, Arman, Person 3 and Person 5 have 3, Person 6 and 10 have 2, Person 9 and 12 have 1, Person 13 has 0. Average is 20/9 = 2.22.

## Query parameters

| Task | Parameters | Result on our data |
|---|---|---|
| 3.1 | email arman.armanov@example.com, phone +77773414141 | 1 row updated |
| 3.2 | city Astana, 7 days, others 3 days | CONF-A 2026-11-01 to 11-08, CONF-B 11-10 to 11-13, CONF-C 2027-02-15 to 02-18 |
| 4.1 | email amina.aminova@example.com, status withdrawn | papers 7 and 8 deleted with 4 author rows, 5 keywords, 3 versions, 3 reviews. Paper 12 stays |
| 4.2 | city Astana | Session 3 deleted, sessions 1, 2, 5 stay |
| 5.1 | status accepted | papers 1, 2, 3, 4, 9 |
| 5.2 | phrase machine learning | papers 2, 5, 8, 9 |
| 5.3 | paper_id 1 | versions 3, 2, 1 |
| 5.4 | conference 1, Databases, 3 years | Arman, Person 4, Person 9 |
| 6.4 | - | Person 4, Arman, Person 3, Person 5 |
| 7 | - | CONF-A 80.00, CONF-B 33.33, CONF-C NULL |
| 8 | - | papers 1, 2, 3, 9 (paper 4 is accepted but has no session) |

---

# Part 2

## Setup

```
pip install -r requirements.txt
```

Put your postgres password in `PASSWORD` at the top of part2_queries.py. Or set DATABASE_URL, for example
`postgresql+psycopg2://postgres:PASSWORD@localhost:5432/OmarData`.

## Run

```
python part2_queries.py                     (all tasks)
python part2_queries.py > part2_output.txt  (save output)
python part2_queries.py 5.1 6.4             (some tasks)
```

Running all tasks recreates the tables and data first (tasks 1 and 2).

## How it works

- All SQL is run with SQLAlchemy text() and bound parameters like :email. The program prints the task number, the SQL, the parameters and the result.
- Tasks 1 and 2 run schema.sql and seed.sql in a transaction and show the tables, constraints and row counts.
- Updates and deletes (3.1, 3.2, 4.1, 4.2) show the data before and after and then rollback, so every task uses the original data.
- 4.1 is one DELETE on paper, the other rows are removed by ON DELETE CASCADE.
- 6.1 uses COUNT(DISTINCT) so the author join does not count papers twice.
- 6.3 counts papers and averages reviews in two separate subqueries, so papers with many reviews are counted once.
- 6.4 uses a CTE, reviewers with 0 reviews are included in the average.
- 7 uses NULLIF so the rate is NULL when there are no accepted or rejected papers.
- 8 creates the view and commits it, so it stays in the database and in the dump.

## Export

```
pg_dump -U postgres --no-owner --no-privileges OmarData > OmarDBplain.sql
```

---

# Part 3

## Web application

- URL: https://dbpa3.onrender.com (API docs at /docs)
- FastAPI app in `main.py`, uses SQLAlchemy. Database is PostgreSQL on Neon, hosted on Render free plan.
- The free plan sleeps after 15 minutes, so the first request can take about a minute.
- The Neon database was created with schema.sql and seed.sql (same as Part 1).

## Run locally

```
pip install -r requirements.txt
export DATABASE_URL='postgresql+psycopg2://USER:PASS@HOST/DB'
uvicorn main:app --reload
```

## What it does

- CRUD for users, papers, sessions and reviews.
- Author and reviewer info is managed with the user. Authors, keywords and versions are managed with the paper.
- Paper versions have their own endpoints under /papers/{paper_id}/versions.
- Conferences, tracks, pools and labels come from the seed data and are read only.
- Every write runs in one transaction (`engine.begin()`), so if a check fails nothing is saved.
- Failed checks and duplicate values return 409, missing rows return 404, wrong input (like no corresponding author) returns 422.

## Demo of the checks

| Request | Result |
|---|---|
| POST /reviews, paper 1, reviewer 1 | 409, Arman is an author of paper 1 |
| PUT /papers/4 with session 4 | 409, track is in CONF-A, session is in CONF-B |
| PUT /papers/2 adding author 1 | 409, Arman already reviewed paper 2 |
| PUT /papers/1 with status rejected and session 1 | 409, only accepted papers can be in a session |