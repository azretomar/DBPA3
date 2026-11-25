import os
import sys
from textwrap import dedent

import sqlalchemy
from sqlalchemy import create_engine,text
from sqlalchemy.engine import URL

PASSWORD="postgres"

db_url=URL.create("postgresql+psycopg2",username="postgres",password=PASSWORD,
                    host="localhost",port=5432,database="OmarData")
if os.environ.get("DATABASE_URL"):
    db_url=os.environ["DATABASE_URL"]

engine=create_engine(db_url)
folder=os.path.dirname(os.path.abspath(__file__))

tables=["app_user","author","author_research_area","reviewer","reviewer_expertise",
          "conference","conference_host","conference_reviewer","track","conference_session",
          "paper","paper_keyword","paper_author","paper_version","review"]

def title(s):
    print()
    print("="*75)
    print(s)
    print("="*75)

def print_rows(cols,rows):
    data=[["NULL" if v is None else str(v) for v in r] for r in rows]
    w=[len(c) for c in cols]
    for r in data:
        for i in range(len(r)):
            if len(r[i])>w[i]:
                w[i]=len(r[i])
    print(" | ".join(cols[i].ljust(w[i]) for i in range(len(cols))))
    print("-+-".join("-"*x for x in w))
    for r in data:
        print(" | ".join(r[i].ljust(w[i]) for i in range(len(r))))
    print("("+str(len(rows))+" rows)")

def run(conn,sql,params=None,label=""):
    sql=dedent(sql).strip()
    print()
    if label:
        print("--",label)
    print(sql)
    if params:
        print("params:",params)
    print()
    res=conn.execute(text(sql),params or {})
    if res.returns_rows:
        cols=list(res.keys())
        print_rows(cols,res.fetchall())
    elif res.rowcount>=0:
        print("rows affected:",res.rowcount)
    else:
        print("ok")
    return res

def run_file(name):
    with open(os.path.join(folder,"sql",name),encoding="utf-8") as f:
        script=f.read()
    print("running sql/"+name)
    with engine.begin() as conn:
        conn.exec_driver_sql(script)

count_all="\nUNION ALL\n".join("SELECT '"+t+"' AS table_name, COUNT(*) AS rows FROM "+t for t in tables)

counts="""
SELECT (SELECT COUNT(*) FROM app_user) AS users,
       (SELECT COUNT(*) FROM conference) AS conferences,
       (SELECT COUNT(*) FROM track) AS tracks,
       (SELECT COUNT(*) FROM paper) AS papers,
       (SELECT COUNT(*) FROM paper_author) AS paper_authors,
       (SELECT COUNT(*) FROM paper_keyword) AS keywords,
       (SELECT COUNT(*) FROM paper_version) AS versions,
       (SELECT COUNT(*) FROM review) AS reviews
"""

def task1():
    title("1. Create tables")
    run_file("schema.sql")
    with engine.connect() as conn:
        run(conn,"""
            SELECT c.relname AS table_name,
                   COUNT(*) FILTER (WHERE con.contype = 'p') AS pk,
                   COUNT(*) FILTER (WHERE con.contype = 'f') AS fk,
                   COUNT(*) FILTER (WHERE con.contype = 'u') AS uniq,
                   COUNT(*) FILTER (WHERE con.contype = 'c') AS checks
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            LEFT JOIN pg_constraint con ON con.conrelid = c.oid
            WHERE n.nspname = 'public' AND c.relkind = 'r'
            GROUP BY c.relname
            ORDER BY c.relname
        """,label="tables and constraints")
        run(conn,"""
            SELECT CAST(conrelid AS regclass) AS table_name, conname, pg_get_constraintdef(oid) AS definition
            FROM pg_constraint
            WHERE contype = 'c' AND connamespace = CAST('public' AS regnamespace)
            ORDER BY 1, 2
        """,label="check constraints")
        run(conn,"""
            SELECT indexname, indexdef FROM pg_indexes
            WHERE schemaname = 'public' AND indexname = 'uq_one_corresponding_author'
        """,label="one corresponding author per paper")

def task2():
    title("2. Insert data")
    run_file("seed.sql")
    with engine.connect() as conn:
        run(conn,count_all,label="row count of every table")

def task3_1():
    title("3.1 Update phone number of Arman Armanov")
    q="SELECT user_id, given_name, surname, email, phone_number FROM app_user WHERE email = :email"
    email="arman.armanov@example.com"
    with engine.connect() as conn:
        tr=conn.begin()
        run(conn,q,{"email":email},"before")
        run(conn,"UPDATE app_user SET phone_number = :phone WHERE email = :email",
            {"phone":"+77773414141","email":email},"update")
        run(conn,q,{"email":email},"after")
        tr.rollback()
    print("\nrolled back")

def task3_2():
    title("3.2 Extend review deadlines (Astana +7 days, others +3 days)")
    q="SELECT conference_id, acronym, city, review_deadline FROM conference ORDER BY conference_id"
    with engine.connect() as conn:
        tr=conn.begin()
        run(conn,q,label="before")
        run(conn,"""
            UPDATE conference
            SET review_deadline = review_deadline + CASE WHEN city = :city THEN :days1 ELSE :days2 END
        """,{"city":"Astana","days1":7,"days2":3},"update")
        run(conn,q,label="after")
        tr.rollback()
    print("\nrolled back")

def task4_1():
    title("4.1 Delete withdrawn papers where Amina Aminova is corresponding author")
    p={"email":"amina.aminova@example.com","status":"withdrawn"}
    amina="""
        SELECT p.paper_id, p.title, p.status, pa.is_corresponding
        FROM paper p
        JOIN paper_author pa ON pa.paper_id = p.paper_id
        JOIN app_user u ON u.user_id = pa.author_id
        WHERE u.email = :email
        ORDER BY p.paper_id
    """
    with engine.connect() as conn:
        tr=conn.begin()
        run(conn,amina,{"email":p["email"]},"before: papers of Amina")
        run(conn,"""
            SELECT p.paper_id,
                   (SELECT COUNT(*) FROM paper_author x WHERE x.paper_id = p.paper_id) AS authors,
                   (SELECT COUNT(*) FROM paper_keyword x WHERE x.paper_id = p.paper_id) AS keywords,
                   (SELECT COUNT(*) FROM paper_version x WHERE x.paper_id = p.paper_id) AS versions,
                   (SELECT COUNT(*) FROM review x WHERE x.paper_id = p.paper_id) AS reviews
            FROM paper p
            WHERE p.status = :status
              AND EXISTS (SELECT 1 FROM paper_author pa JOIN app_user u ON u.user_id = pa.author_id
                          WHERE pa.paper_id = p.paper_id AND pa.is_corresponding AND u.email = :email)
            ORDER BY p.paper_id
        """,p,"before: papers that will be deleted and their rows")
        run(conn,counts,label="before: counts")
        run(conn,"""
            DELETE FROM paper p
            WHERE p.status = :status
              AND EXISTS (SELECT 1 FROM paper_author pa JOIN app_user u ON u.user_id = pa.author_id
                          WHERE pa.paper_id = p.paper_id AND pa.is_corresponding AND u.email = :email)
            RETURNING p.paper_id, p.title
        """,p,"delete (authors, keywords, versions, reviews are deleted by ON DELETE CASCADE)")
        run(conn,amina,{"email":p["email"]},"after: papers of Amina")
        run(conn,counts,label="after: counts")
        tr.rollback()
    print("\nrolled back")

def task4_2():
    title("4.2 Delete empty sessions of conferences in Astana")
    q="""
        SELECT s.session_id, s.title, c.acronym, c.city, COUNT(p.paper_id) AS papers
        FROM conference_session s
        JOIN conference c ON c.conference_id = s.conference_id
        LEFT JOIN paper p ON p.session_id = s.session_id
        GROUP BY s.session_id, s.title, c.acronym, c.city
        ORDER BY s.session_id
    """
    with engine.connect() as conn:
        tr=conn.begin()
        run(conn,q,label="before")
        run(conn,"""
            DELETE FROM conference_session s
            USING conference c
            WHERE c.conference_id = s.conference_id
              AND c.city = :city
              AND NOT EXISTS (SELECT 1 FROM paper p WHERE p.session_id = s.session_id)
            RETURNING s.session_id, s.title
        """,{"city":"Astana"},"delete")
        run(conn,q,label="after")
        run(conn,"SELECT conference_id, acronym, city FROM conference ORDER BY conference_id",
            label="after: conferences")
        tr.rollback()
    print("\nrolled back")

def task5_1():
    title("5.1 Accepted papers")
    with engine.connect() as conn:
        run(conn,"""
            SELECT p.paper_id, p.title,
                   u.given_name || ' ' || u.surname AS corresponding_author,
                   u.email,
                   t.name AS track,
                   c.conference_id,
                   c.acronym
            FROM paper p
            JOIN track t ON t.track_id = p.track_id
            JOIN conference c ON c.conference_id = t.conference_id
            JOIN paper_author pa ON pa.paper_id = p.paper_id AND pa.is_corresponding
            JOIN app_user u ON u.user_id = pa.author_id
            WHERE p.status = :status
            ORDER BY p.paper_id
        """,{"status":"accepted"})

def task5_2():
    title("5.2 Abstract contains 'machine learning'")
    with engine.connect() as conn:
        run(conn,"""
            SELECT paper_id, title FROM paper
            WHERE abstract ILIKE '%' || :phrase || '%'
            ORDER BY paper_id
        """,{"phrase":"machine learning"})

def task5_3():
    title("5.3 Versions of a paper")
    with engine.connect() as conn:
        run(conn,"""
            SELECT version_no, file_location, uploaded_at
            FROM paper_version
            WHERE paper_id = :paper_id
            ORDER BY version_no DESC
        """,{"paper_id":1})

def task5_4():
    title("5.4 Reviewers in pool with Databases expertise and 3+ years")
    with engine.connect() as conn:
        run(conn,"""
            SELECT u.user_id, u.given_name || ' ' || u.surname AS full_name, u.email
            FROM conference_reviewer cr
            JOIN reviewer r ON r.reviewer_id = cr.reviewer_id
            JOIN app_user u ON u.user_id = r.reviewer_id
            WHERE cr.conference_id = :conf
              AND r.years_experience >= :years
              AND EXISTS (SELECT 1 FROM reviewer_expertise e
                          WHERE e.reviewer_id = r.reviewer_id AND e.area_label = :area)
            ORDER BY u.user_id
        """,{"conf":1,"years":3,"area":"Databases"})

def task6_1():
    title("6.1 Papers and authors per track")
    with engine.connect() as conn:
        run(conn,"""
            SELECT t.track_id, t.name, t.conference_id,
                   COUNT(DISTINCT p.paper_id) AS papers,
                   COUNT(DISTINCT pa.author_id) AS authors
            FROM track t
            LEFT JOIN paper p ON p.track_id = t.track_id
            LEFT JOIN paper_author pa ON pa.paper_id = p.paper_id
            GROUP BY t.track_id, t.name, t.conference_id
            ORDER BY t.track_id
        """)

def task6_2():
    title("6.2 Reviews per reviewer")
    with engine.connect() as conn:
        run(conn,"""
            SELECT r.reviewer_id, u.given_name || ' ' || u.surname AS full_name,
                   COUNT(rv.review_id) AS reviews,
                   ROUND(AVG(rv.overall_score), 2) AS avg_score
            FROM reviewer r
            JOIN app_user u ON u.user_id = r.reviewer_id
            LEFT JOIN review rv ON rv.reviewer_id = r.reviewer_id
            GROUP BY r.reviewer_id, u.given_name, u.surname
            ORDER BY r.reviewer_id
        """)

def task6_3():
    title("6.3 Papers and average score per conference")
    with engine.connect() as conn:
        run(conn,"""
            SELECT c.conference_id, c.acronym,
                   COALESCE(a.total, 0) AS total_papers,
                   COALESCE(a.accepted, 0) AS accepted_papers,
                   b.avg_score
            FROM conference c
            LEFT JOIN (SELECT t.conference_id, COUNT(*) AS total,
                              COUNT(*) FILTER (WHERE p.status = :st) AS accepted
                       FROM paper p JOIN track t ON t.track_id = p.track_id
                       GROUP BY t.conference_id) a ON a.conference_id = c.conference_id
            LEFT JOIN (SELECT t.conference_id, ROUND(AVG(rv.overall_score), 2) AS avg_score
                       FROM review rv
                       JOIN paper p ON p.paper_id = rv.paper_id
                       JOIN track t ON t.track_id = p.track_id
                       GROUP BY t.conference_id) b ON b.conference_id = c.conference_id
            ORDER BY c.conference_id
        """,{"st":"accepted"})

def task6_4():
    title("6.4 Reviewers above average number of reviews")
    with engine.connect() as conn:
        run(conn,"""
            WITH cnt AS (
                SELECT r.reviewer_id, COUNT(rv.review_id) AS reviews
                FROM reviewer r
                LEFT JOIN review rv ON rv.reviewer_id = r.reviewer_id
                GROUP BY r.reviewer_id
            ),
            av AS (SELECT AVG(reviews) AS avg_reviews FROM cnt)
            SELECT cnt.reviewer_id, u.given_name || ' ' || u.surname AS full_name,
                   cnt.reviews, ROUND(av.avg_reviews, 2) AS avg_reviews
            FROM cnt
            CROSS JOIN av
            JOIN app_user u ON u.user_id = cnt.reviewer_id
            WHERE cnt.reviews > av.avg_reviews
            ORDER BY cnt.reviews DESC, cnt.reviewer_id
        """)

def task7():
    title("7. Acceptance rate")
    with engine.connect() as conn:
        run(conn,"""
            SELECT c.conference_id, c.acronym,
                   COUNT(p.paper_id) FILTER (WHERE p.status = :acc) AS accepted,
                   COUNT(p.paper_id) FILTER (WHERE p.status = :rej) AS rejected,
                   ROUND(100.0 * COUNT(p.paper_id) FILTER (WHERE p.status = :acc)
                         / NULLIF(COUNT(p.paper_id) FILTER (WHERE p.status IN (:acc, :rej)), 0), 2) AS acceptance_rate
            FROM conference c
            LEFT JOIN track t ON t.conference_id = c.conference_id
            LEFT JOIN paper p ON p.track_id = t.track_id
            GROUP BY c.conference_id, c.acronym
            ORDER BY c.conference_id
        """,{"acc":"accepted","rej":"rejected"})

def task8():
    title("8. View accepted_paper_schedule")
    with engine.begin() as conn:
        run(conn,"""
            CREATE OR REPLACE VIEW accepted_paper_schedule AS
            SELECT p.paper_id, p.title AS paper_title,
                   c.conference_id, c.acronym,
                   t.name AS track_name,
                   s.session_id, s.title AS session_title, s.session_date,
                   s.start_time, s.end_time, s.room_label,
                   ch.given_name || ' ' || ch.surname AS chair_name,
                   ca.given_name || ' ' || ca.surname AS corresponding_author,
                   ca.email AS corresponding_email
            FROM paper p
            JOIN conference_session s ON s.session_id = p.session_id
            JOIN conference c ON c.conference_id = s.conference_id
            JOIN track t ON t.track_id = p.track_id
            JOIN app_user ch ON ch.user_id = s.chair_id
            LEFT JOIN paper_author pa ON pa.paper_id = p.paper_id AND pa.is_corresponding
            LEFT JOIN app_user ca ON ca.user_id = pa.author_id
            WHERE p.status = 'accepted'
        """,label="create view")
    with engine.connect() as conn:
        run(conn,"SELECT table_name, table_type FROM information_schema.tables WHERE table_name = :t",
            {"t":"accepted_paper_schedule"},"it is a view")
        run(conn,"""
            SELECT * FROM accepted_paper_schedule
            ORDER BY conference_id, session_date, start_time, session_id, paper_id
        """,label="query view")
        run(conn,"SELECT paper_id, title, status, session_id FROM paper WHERE status = :s AND session_id IS NULL",
            {"s":"accepted"},"accepted papers with no session (not in view)")

tasks={
    "1":task1,"2":task2,
    "3.1":task3_1,"3.2":task3_2,
    "4.1":task4_1,"4.2":task4_2,
    "5.1":task5_1,"5.2":task5_2,"5.3":task5_3,"5.4":task5_4,
    "6.1":task6_1,"6.2":task6_2,"6.3":task6_3,"6.4":task6_4,
    "7":task7,"8":task8,
}

if __name__=="__main__":
    todo=sys.argv[1:] if len(sys.argv)>1 else list(tasks.keys())
    for t in todo:
        if t not in tasks:
            print("no task",t)
            sys.exit(1)

    with engine.connect() as conn:
        ver=conn.execute(text("SHOW server_version")).scalar()
    print("SQLAlchemy",sqlalchemy.__version__,"| PostgreSQL",ver,"| Python",sys.version.split()[0])

    for t in todo:
        tasks[t]()
