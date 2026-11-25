from datetime import date,datetime,time
from typing import Optional
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError,DataError
from db import engine

app=FastAPI(title="Conference and Paper Review System")

STATUSES=["submitted","under review","accepted","rejected","withdrawn"]
RECOMMENDATIONS=["accept","reject"]

def db_error(e):
    msg=str(e.orig).split("\n")[0]
    if isinstance(e,IntegrityError):
        return HTTPException(409,msg)
    return HTTPException(422,msg)

def to_list(result):
    out=[]
    for row in result.mappings():
        out.append(dict(row))
    return out

def first_column(result):
    out=[]
    for row in result:
        out.append(row[0])
    return out

@app.get("/health")
def health():
    with engine.connect() as c:
        n=c.execute(text("SELECT COUNT(*) FROM paper")).scalar()
    return {"papers":n}

class AuthorIn(BaseModel):
    orcid:Optional[str]=None
    research_areas:list[str]=[]

class ReviewerIn(BaseModel):
    years_experience:int
    expertise:list[str]=[]

class UserIn(BaseModel):
    given_name:str
    surname:str
    email:str
    affiliation:str
    country:str
    phone_number:str
    author:Optional[AuthorIn]=None
    reviewer:Optional[ReviewerIn]=None

def user_params(u):
    return {"given_name":u.given_name,"surname":u.surname,"email":u.email,
            "affiliation":u.affiliation,"country":u.country,"phone_number":u.phone_number}

def save_profiles(c,uid,u):
    if u.author is not None:
        c.execute(text(
            "INSERT INTO author (author_id, orcid) VALUES (:i, :o) "
            "ON CONFLICT (author_id) DO UPDATE SET orcid = EXCLUDED.orcid"),
            {"i":uid,"o":u.author.orcid})
        c.execute(text("DELETE FROM author_research_area WHERE author_id = :i"),{"i":uid})
        for a in set(u.author.research_areas):
            c.execute(text("INSERT INTO author_research_area (author_id, area_label) VALUES (:i, :a)"),
                      {"i":uid,"a":a})
    else:
        c.execute(text("DELETE FROM author WHERE author_id = :i"),{"i":uid})
    if u.reviewer is not None:
        c.execute(text(
            "INSERT INTO reviewer (reviewer_id, years_experience) VALUES (:i, :y) "
            "ON CONFLICT (reviewer_id) DO UPDATE SET years_experience = EXCLUDED.years_experience"),
            {"i":uid,"y":u.reviewer.years_experience})
        c.execute(text("DELETE FROM reviewer_expertise WHERE reviewer_id = :i"),{"i":uid})
        for a in set(u.reviewer.expertise):
            c.execute(text("INSERT INTO reviewer_expertise (reviewer_id, area_label) VALUES (:i, :a)"),
                      {"i":uid,"a":a})
    else:
        c.execute(text("DELETE FROM reviewer WHERE reviewer_id = :i"),{"i":uid})

def fetch_user(c,uid):
    row=c.execute(text("SELECT * FROM app_user WHERE user_id = :i"),{"i":uid}).mappings().first()
    if row is None:
        return None
    out=dict(row)
    a=c.execute(text("SELECT orcid FROM author WHERE author_id = :i"),{"i":uid}).first()
    if a is None:
        out["author"]=None
    else:
        areas=first_column(c.execute(text(
            "SELECT area_label FROM author_research_area WHERE author_id = :i ORDER BY area_label"),{"i":uid}))
        out["author"]={"orcid":a[0],"research_areas":areas}
    r=c.execute(text("SELECT years_experience FROM reviewer WHERE reviewer_id = :i"),{"i":uid}).first()
    if r is None:
        out["reviewer"]=None
    else:
        exp=first_column(c.execute(text(
            "SELECT area_label FROM reviewer_expertise WHERE reviewer_id = :i ORDER BY area_label"),{"i":uid}))
        out["reviewer"]={"years_experience":r[0],"expertise":exp}
    return out

@app.post("/users",status_code=201)
def create_user(u:UserIn):
    try:
        with engine.begin() as c:
            uid=c.execute(text(
                "INSERT INTO app_user (given_name, surname, email, affiliation, country, phone_number) "
                "VALUES (:given_name, :surname, :email, :affiliation, :country, :phone_number) "
                "RETURNING user_id"),user_params(u)).scalar()
            save_profiles(c,uid,u)
            return fetch_user(c,uid)
    except (IntegrityError,DataError) as e:
        raise db_error(e)

@app.get("/users")
def list_users():
    with engine.connect() as c:
        return to_list(c.execute(text(
            "SELECT user_id, given_name, surname, email FROM app_user ORDER BY user_id")))

@app.get("/users/{user_id}")
def get_user(user_id:int):
    with engine.connect() as c:
        u=fetch_user(c,user_id)
    if u is None:
        raise HTTPException(404,"User not found")
    return u

@app.put("/users/{user_id}")
def update_user(user_id:int,u:UserIn):
    try:
        with engine.begin() as c:
            params=user_params(u)
            params["uid"]=user_id
            hit=c.execute(text(
                "UPDATE app_user SET given_name = :given_name, surname = :surname, email = :email, "
                "affiliation = :affiliation, country = :country, phone_number = :phone_number "
                "WHERE user_id = :uid RETURNING user_id"),params).first()
            if hit is None:
                raise HTTPException(404,"User not found")
            save_profiles(c,user_id,u)
            return fetch_user(c,user_id)
    except (IntegrityError,DataError) as e:
        raise db_error(e)

@app.delete("/users/{user_id}")
def delete_user(user_id:int):
    try:
        with engine.begin() as c:
            hit=c.execute(text("DELETE FROM app_user WHERE user_id = :i RETURNING user_id"),
                            {"i":user_id}).first()
            if hit is None:
                raise HTTPException(404,"User not found")
    except IntegrityError as e:
        raise db_error(e)
    return {"deleted_user_id":user_id}

class AuthorLink(BaseModel):
    author_id:int
    author_position:int
    is_corresponding:bool=False

class VersionIn(BaseModel):
    version_no:int
    file_location:str
    uploaded_at:datetime
    change_note:Optional[str]=None

class PaperUpdate(BaseModel):
    track_id:int
    title:str
    abstract:str
    submission_date:date
    status:str="submitted"
    session_id:Optional[int]=None
    keywords:list[str]=[]
    authors:list[AuthorLink]

class PaperIn(PaperUpdate):
    versions:list[VersionIn]=[]

def paper_params(p):
    return {"track_id":p.track_id,"title":p.title,"abstract":p.abstract,
            "submission_date":p.submission_date,"status":p.status,"session_id":p.session_id}

def version_params(paper_id,version_no,v):
    return {"p":paper_id,"n":version_no,"f":v.file_location,"u":v.uploaded_at,"c":v.change_note}

def check_paper_input(p):
    if p.status not in STATUSES:
        raise HTTPException(422,"Invalid status, must be one of "+str(STATUSES))
    if len(p.authors)==0:
        raise HTTPException(422,"A paper must have at least one author")
    corresponding=0
    for a in p.authors:
        if a.is_corresponding:
            corresponding=corresponding+1
    if corresponding!=1:
        raise HTTPException(422,"A paper must have exactly one corresponding author")

def check_authors(c,paper_id,authors):
    for a in authors:
        hit=c.execute(text("SELECT 1 FROM review WHERE paper_id = :p AND reviewer_id = :r"),
                        {"p":paper_id,"r":a.author_id}).first()
        if hit is not None:
            raise HTTPException(409,"Self-review not allowed: user "+str(a.author_id)+
                                " already reviewed this paper and cannot be its author")

def check_session(c,track_id,status,session_id):
    if session_id is None:
        return
    if status!="accepted":
        raise HTTPException(409,"Invalid session assignment: only accepted papers can be scheduled")
    tc=c.execute(text("SELECT conference_id FROM track WHERE track_id = :t"),{"t":track_id}).scalar()
    sc=c.execute(text("SELECT conference_id FROM conference_session WHERE session_id = :s"),
                   {"s":session_id}).scalar()
    if tc is None:
        raise HTTPException(404,"Track not found")
    if sc is None:
        raise HTTPException(404,"Session not found")
    if tc!=sc:
        raise HTTPException(409,"Invalid session assignment: track and session belong to different conferences")

def save_children(c,pid,p):
    c.execute(text("DELETE FROM paper_keyword WHERE paper_id = :p"),{"p":pid})
    c.execute(text("DELETE FROM paper_author WHERE paper_id = :p"),{"p":pid})
    for k in set(p.keywords):
        c.execute(text("INSERT INTO paper_keyword (paper_id, keyword) VALUES (:p, :k)"),{"p":pid,"k":k})
    for a in p.authors:
        c.execute(text(
            "INSERT INTO paper_author (paper_id, author_id, author_position, is_corresponding) "
            "VALUES (:p, :a, :pos, :c)"),
            {"p":pid,"a":a.author_id,"pos":a.author_position,"c":a.is_corresponding})

def paper_exists(c,pid):
    row=c.execute(text("SELECT 1 FROM paper WHERE paper_id = :p"),{"p":pid}).first()
    return row is not None

def fetch_paper(c,pid):
    row=c.execute(text("SELECT * FROM paper WHERE paper_id = :p"),{"p":pid}).mappings().first()
    if row is None:
        return None
    out=dict(row)
    out["keywords"]=first_column(c.execute(text(
        "SELECT keyword FROM paper_keyword WHERE paper_id = :p ORDER BY keyword"),{"p":pid}))
    out["authors"]=to_list(c.execute(text(
        "SELECT pa.author_id, u.given_name, u.surname, pa.author_position, pa.is_corresponding "
        "FROM paper_author pa JOIN app_user u ON u.user_id = pa.author_id "
        "WHERE pa.paper_id = :p ORDER BY pa.author_position"),{"p":pid}))
    out["versions"]=to_list(c.execute(text(
        "SELECT version_no, file_location, uploaded_at, change_note FROM paper_version "
        "WHERE paper_id = :p ORDER BY version_no DESC"),{"p":pid}))
    return out

@app.post("/papers",status_code=201)
def create_paper(p:PaperIn):
    check_paper_input(p)
    try:
        with engine.begin() as c:
            check_session(c,p.track_id,p.status,p.session_id)
            pid=c.execute(text(
                "INSERT INTO paper (track_id, title, abstract, submission_date, status, session_id) "
                "VALUES (:track_id, :title, :abstract, :submission_date, :status, :session_id) "
                "RETURNING paper_id"),paper_params(p)).scalar()
            save_children(c,pid,p)
            for v in p.versions:
                c.execute(text(
                    "INSERT INTO paper_version (paper_id, version_no, file_location, uploaded_at, change_note) "
                    "VALUES (:p, :n, :f, :u, :c)"),version_params(pid,v.version_no,v))
            return fetch_paper(c,pid)
    except (IntegrityError,DataError) as e:
        raise db_error(e)

@app.get("/papers")
def list_papers():
    with engine.connect() as c:
        return to_list(c.execute(text(
            "SELECT paper_id, title, status, track_id, session_id FROM paper ORDER BY paper_id")))

@app.get("/papers/{paper_id}")
def get_paper(paper_id:int):
    with engine.connect() as c:
        out=fetch_paper(c,paper_id)
    if out is None:
        raise HTTPException(404,"Paper not found")
    return out

@app.put("/papers/{paper_id}")
def update_paper(paper_id:int,p:PaperUpdate):
    check_paper_input(p)
    try:
        with engine.begin() as c:
            if not paper_exists(c,paper_id):
                raise HTTPException(404,"Paper not found")
            check_authors(c,paper_id,p.authors)
            check_session(c,p.track_id,p.status,p.session_id)
            params=paper_params(p)
            params["pid"]=paper_id
            c.execute(text(
                "UPDATE paper SET track_id = :track_id, title = :title, abstract = :abstract, "
                "submission_date = :submission_date, status = :status, session_id = :session_id "
                "WHERE paper_id = :pid"),params)
            save_children(c,paper_id,p)
            return fetch_paper(c,paper_id)
    except (IntegrityError,DataError) as e:
        raise db_error(e)

@app.delete("/papers/{paper_id}")
def delete_paper(paper_id:int):
    try:
        with engine.begin() as c:
            hit=c.execute(text("DELETE FROM paper WHERE paper_id = :p RETURNING paper_id"),
                            {"p":paper_id}).first()
            if hit is None:
                raise HTTPException(404,"Paper not found")
    except IntegrityError as e:
        raise db_error(e)
    return {"deleted_paper_id":paper_id}

@app.post("/papers/{paper_id}/versions",status_code=201)
def add_version(paper_id:int,v:VersionIn):
    try:
        with engine.begin() as c:
            if not paper_exists(c,paper_id):
                raise HTTPException(404,"Paper not found")
            c.execute(text(
                "INSERT INTO paper_version (paper_id, version_no, file_location, uploaded_at, change_note) "
                "VALUES (:p, :n, :f, :u, :c)"),version_params(paper_id,v.version_no,v))
            return fetch_paper(c,paper_id)
    except (IntegrityError,DataError) as e:
        raise db_error(e)

@app.put("/papers/{paper_id}/versions/{version_no}")
def update_version(paper_id:int,version_no:int,v:VersionIn):
    try:
        with engine.begin() as c:
            hit=c.execute(text(
                "UPDATE paper_version SET file_location = :f, uploaded_at = :u, change_note = :c "
                "WHERE paper_id = :p AND version_no = :n RETURNING version_no"),
                version_params(paper_id,version_no,v)).first()
            if hit is None:
                raise HTTPException(404,"Version not found")
            return fetch_paper(c,paper_id)
    except (IntegrityError,DataError) as e:
        raise db_error(e)

@app.delete("/papers/{paper_id}/versions/{version_no}")
def delete_version(paper_id:int,version_no:int):
    with engine.begin() as c:
        hit=c.execute(text(
            "DELETE FROM paper_version WHERE paper_id = :p AND version_no = :n RETURNING version_no"),
            {"p":paper_id,"n":version_no}).first()
        if hit is None:
            raise HTTPException(404,"Version not found")
    return {"deleted_version":version_no}

class SessionIn(BaseModel):
    conference_id:int
    title:str
    session_date:date
    start_time:time
    end_time:time
    room_label:str
    chair_id:int

def session_params(s):
    return {"conference_id":s.conference_id,"title":s.title,"session_date":s.session_date,
            "start_time":s.start_time,"end_time":s.end_time,"room_label":s.room_label,
            "chair_id":s.chair_id}

def fetch_session(c,sid):
    row=c.execute(text("SELECT * FROM conference_session WHERE session_id = :s"),
                    {"s":sid}).mappings().first()
    if row is None:
        return None
    out=dict(row)
    out["papers"]=to_list(c.execute(text(
        "SELECT paper_id, title, status FROM paper WHERE session_id = :s ORDER BY paper_id"),{"s":sid}))
    return out

@app.post("/sessions",status_code=201)
def create_session(s:SessionIn):
    try:
        with engine.begin() as c:
            sid=c.execute(text(
                "INSERT INTO conference_session (conference_id, title, session_date, start_time, end_time, "
                "room_label, chair_id) VALUES (:conference_id, :title, :session_date, :start_time, "
                ":end_time, :room_label, :chair_id) RETURNING session_id"),session_params(s)).scalar()
            return fetch_session(c,sid)
    except (IntegrityError,DataError) as e:
        raise db_error(e)

@app.get("/sessions")
def list_sessions():
    with engine.connect() as c:
        return to_list(c.execute(text(
            "SELECT session_id, conference_id, title, session_date, start_time, end_time, room_label, chair_id "
            "FROM conference_session ORDER BY session_id")))

@app.get("/sessions/{session_id}")
def get_session(session_id:int):
    with engine.connect() as c:
        out=fetch_session(c,session_id)
    if out is None:
        raise HTTPException(404,"Session not found")
    return out

@app.put("/sessions/{session_id}")
def update_session(session_id:int,s:SessionIn):
    try:
        with engine.begin() as c:
            found=c.execute(text("SELECT 1 FROM conference_session WHERE session_id = :s"),
                              {"s":session_id}).first()
            if found is None:
                raise HTTPException(404,"Session not found")
            bad=first_column(c.execute(text(
                "SELECT p.paper_id FROM paper p JOIN track t ON t.track_id = p.track_id "
                "WHERE p.session_id = :s AND t.conference_id <> :conf"),
                {"s":session_id,"conf":s.conference_id}))
            if len(bad)>0:
                raise HTTPException(409,"Invalid session change: paper(s) "+str(bad)+
                                    " assigned to this session belong to a different conference")
            params=session_params(s)
            params["sid"]=session_id
            c.execute(text(
                "UPDATE conference_session SET conference_id = :conference_id, title = :title, "
                "session_date = :session_date, start_time = :start_time, end_time = :end_time, "
                "room_label = :room_label, chair_id = :chair_id WHERE session_id = :sid"),params)
            return fetch_session(c,session_id)
    except (IntegrityError,DataError) as e:
        raise db_error(e)

@app.delete("/sessions/{session_id}")
def delete_session(session_id:int):
    try:
        with engine.begin() as c:
            hit=c.execute(text("DELETE FROM conference_session WHERE session_id = :s RETURNING session_id"),
                            {"s":session_id}).first()
            if hit is None:
                raise HTTPException(404,"Session not found")
    except IntegrityError as e:
        raise db_error(e)
    return {"deleted_session_id":session_id}

class ReviewIn(BaseModel):
    paper_id:int
    reviewer_id:int
    overall_score:int
    recommendation:str
    comments_for_authors:str
    confidential_comments:Optional[str]=None
    review_submission_date:date

def review_params(r):
    return {"paper_id":r.paper_id,"reviewer_id":r.reviewer_id,"overall_score":r.overall_score,
            "recommendation":r.recommendation,"comments_for_authors":r.comments_for_authors,
            "confidential_comments":r.confidential_comments,
            "review_submission_date":r.review_submission_date}

def check_review_input(r):
    if r.recommendation not in RECOMMENDATIONS:
        raise HTTPException(422,"Invalid recommendation, must be accept or reject")

def check_self_review(c,paper_id,reviewer_id):
    hit=c.execute(text("SELECT 1 FROM paper_author WHERE paper_id = :p AND author_id = :r"),
                    {"p":paper_id,"r":reviewer_id}).first()
    if hit is not None:
        raise HTTPException(409,"Self-review not allowed: the reviewer is an author of this paper")

@app.post("/reviews",status_code=201)
def create_review(r:ReviewIn):
    check_review_input(r)
    try:
        with engine.begin() as c:
            check_self_review(c,r.paper_id,r.reviewer_id)
            row=c.execute(text(
                "INSERT INTO review (paper_id, reviewer_id, overall_score, recommendation, "
                "comments_for_authors, confidential_comments, review_submission_date) VALUES "
                "(:paper_id, :reviewer_id, :overall_score, :recommendation, :comments_for_authors, "
                ":confidential_comments, :review_submission_date) RETURNING *"),review_params(r)).mappings().first()
            return dict(row)
    except (IntegrityError,DataError) as e:
        raise db_error(e)

@app.get("/reviews")
def list_reviews():
    with engine.connect() as c:
        return to_list(c.execute(text(
            "SELECT review_id, paper_id, reviewer_id, overall_score, recommendation FROM review "
            "ORDER BY review_id")))

@app.get("/reviews/{review_id}")
def get_review(review_id:int):
    with engine.connect() as c:
        row=c.execute(text("SELECT * FROM review WHERE review_id = :r"),{"r":review_id}).mappings().first()
    if row is None:
        raise HTTPException(404,"Review not found")
    return dict(row)

@app.put("/reviews/{review_id}")
def update_review(review_id:int,r:ReviewIn):
    check_review_input(r)
    try:
        with engine.begin() as c:
            found=c.execute(text("SELECT 1 FROM review WHERE review_id = :r"),{"r":review_id}).first()
            if found is None:
                raise HTTPException(404,"Review not found")
            check_self_review(c,r.paper_id,r.reviewer_id)
            params=review_params(r)
            params["rid"]=review_id
            row=c.execute(text(
                "UPDATE review SET paper_id = :paper_id, reviewer_id = :reviewer_id, "
                "overall_score = :overall_score, recommendation = :recommendation, "
                "comments_for_authors = :comments_for_authors, confidential_comments = :confidential_comments, "
                "review_submission_date = :review_submission_date WHERE review_id = :rid RETURNING *"),
                params).mappings().first()
            return dict(row)
    except (IntegrityError,DataError) as e:
        raise db_error(e)

@app.delete("/reviews/{review_id}")
def delete_review(review_id:int):
    with engine.begin() as c:
        hit=c.execute(text("DELETE FROM review WHERE review_id = :r RETURNING review_id"),
                        {"r":review_id}).first()
        if hit is None:
            raise HTTPException(404,"Review not found")
    return {"deleted_review_id":review_id}