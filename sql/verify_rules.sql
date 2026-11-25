SELECT rule,violations FROM(

  SELECT 1 AS n,'A reviewer never reviews a paper they authored' AS rule,
         COUNT(*) AS violations
  FROM review r
  JOIN paper_author pa ON pa.paper_id=r.paper_id AND pa.author_id=r.reviewer_id

  UNION ALL
  SELECT 2,'A paper in a session is accepted',COUNT(*)
  FROM paper WHERE session_id IS NOT NULL AND status<>'accepted'

  UNION ALL
  SELECT 3,'A paper''s track and session belong to the same conference',COUNT(*)
  FROM paper p
  JOIN track t ON t.track_id=p.track_id
  JOIN conference_session s ON s.session_id=p.session_id
  WHERE t.conference_id<>s.conference_id

  UNION ALL
  SELECT 4,'Every user is an author, a reviewer, or both',COUNT(*)
  FROM app_user u
  WHERE NOT EXISTS(SELECT 1 FROM author a WHERE a.author_id=u.user_id)
    AND NOT EXISTS(SELECT 1 FROM reviewer r WHERE r.reviewer_id=u.user_id)

  UNION ALL
  SELECT 5,'Every paper has exactly one corresponding author',COUNT(*)
  FROM paper p
  WHERE(SELECT COUNT(*) FROM paper_author pa
         WHERE pa.paper_id=p.paper_id AND pa.is_corresponding)<>1

  UNION ALL
  SELECT 6,'Every paper has at least one author',COUNT(*)
  FROM paper p
  WHERE NOT EXISTS(SELECT 1 FROM paper_author pa WHERE pa.paper_id=p.paper_id)

  UNION ALL
  SELECT 7,'Every paper has at least one version',COUNT(*)
  FROM paper p
  WHERE NOT EXISTS(SELECT 1 FROM paper_version v WHERE v.paper_id=p.paper_id)

  UNION ALL
  SELECT 8,'Every paper has at least one keyword',COUNT(*)
  FROM paper p
  WHERE NOT EXISTS(SELECT 1 FROM paper_keyword k WHERE k.paper_id=p.paper_id)

  UNION ALL
  SELECT 9,'Every author has at least one research area',COUNT(*)
  FROM author a
  WHERE NOT EXISTS(SELECT 1 FROM author_research_area x WHERE x.author_id=a.author_id)

  UNION ALL
  SELECT 10,'Every reviewer has at least one expertise area',COUNT(*)
  FROM reviewer r
  WHERE NOT EXISTS(SELECT 1 FROM reviewer_expertise x WHERE x.reviewer_id=r.reviewer_id)

  UNION ALL
  SELECT 11,'Every conference has at least one host institution',COUNT(*)
  FROM conference c
  WHERE NOT EXISTS(SELECT 1 FROM conference_host h WHERE h.conference_id=c.conference_id)

  UNION ALL
  SELECT 12,'Every conference has at least one track',COUNT(*)
  FROM conference c
  WHERE NOT EXISTS(SELECT 1 FROM track t WHERE t.conference_id=c.conference_id)

  UNION ALL
  SELECT 13,'Track coordinator is in the conference reviewer pool',COUNT(*)
  FROM track t
  WHERE NOT EXISTS(SELECT 1 FROM conference_reviewer cr
                    WHERE cr.conference_id=t.conference_id AND cr.reviewer_id=t.coordinator_id)

  UNION ALL
  SELECT 14,'Session chair is in the conference reviewer pool',COUNT(*)
  FROM conference_session s
  WHERE NOT EXISTS(SELECT 1 FROM conference_reviewer cr
                    WHERE cr.conference_id=s.conference_id AND cr.reviewer_id=s.chair_id)

  UNION ALL
  SELECT 15,'A reviewer only reviews papers of conferences whose pool they are in',COUNT(*)
  FROM review r
  JOIN paper p ON p.paper_id=r.paper_id
  JOIN track t ON t.track_id=p.track_id
  WHERE NOT EXISTS(SELECT 1 FROM conference_reviewer cr
                    WHERE cr.conference_id=t.conference_id AND cr.reviewer_id=r.reviewer_id)

  UNION ALL
  SELECT 16,'A session date is within its conference dates',COUNT(*)
  FROM conference_session s
  JOIN conference c ON c.conference_id=s.conference_id
  WHERE s.session_date NOT BETWEEN c.start_date AND c.end_date

  UNION ALL
  SELECT 17,'A paper is submitted on or before its conference submission deadline',COUNT(*)
  FROM paper p
  JOIN track t ON t.track_id=p.track_id
  JOIN conference c ON c.conference_id=t.conference_id
  WHERE p.submission_date>c.submission_deadline

  UNION ALL
  SELECT 18,'A review is not dated before the paper was submitted',COUNT(*)
  FROM review r
  JOIN paper p ON p.paper_id=r.paper_id
  WHERE r.review_submission_date<p.submission_date

  UNION ALL
  SELECT 19,'A version is not uploaded before the paper submission date',COUNT(*)
  FROM paper_version v
  JOIN paper p ON p.paper_id=v.paper_id
  WHERE v.uploaded_at::date<p.submission_date

  UNION ALL
  SELECT 20,'Author positions of a paper are 1, 2, ..., n with no gaps',COUNT(*)
  FROM(SELECT paper_id FROM paper_author
        GROUP BY paper_id
        HAVING MAX(author_position)<>COUNT(*)) g

) checks
ORDER BY n;
