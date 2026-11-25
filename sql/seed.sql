TRUNCATE app_user,author,author_research_area,reviewer,reviewer_expertise,
    conference,conference_host,conference_reviewer,track,conference_session,
    paper,paper_keyword,paper_author,paper_version,review
RESTART IDENTITY CASCADE;

INSERT INTO app_user(user_id,given_name,surname,email,affiliation,country,phone_number) VALUES
(1,'Arman','Armanov','arman.armanov@example.com','University A','Kazakhstan','+77010000001'),
(2,'Amina','Aminova','amina.aminova@example.com','University B','Kazakhstan','+77010000002'),
(3,'Person','3','person3@example.com','University C','Kazakhstan','+77010000003'),
(4,'Person','4','person4@example.com','University A','Kazakhstan','+77010000004'),
(5,'Person','5','person5@example.com','University D','Kazakhstan','+77010000005'),
(6,'Person','6','person6@example.com','University C','Kazakhstan','+77010000006'),
(7,'Person','7','person7@example.com','University E','Kazakhstan','+77010000007'),
(8,'Person','8','person8@example.com','University B','Kazakhstan','+77010000008'),
(9,'Person','9','person9@example.com','University F','Uzbekistan','+998900000009'),
(10,'Person','10','person10@example.com','University G','Kazakhstan','+77010000010'),
(11,'Person','11','person11@example.com','University C','Kazakhstan','+77010000011'),
(12,'Person','12','person12@example.com','University A','Kazakhstan','+77010000012'),
(13,'Person','13','person13@example.com','University H','Kazakhstan','+77010000013'),
(14,'Person','14','person14@example.com','University F','Uzbekistan','+998900000014');

INSERT INTO author(author_id,orcid) VALUES
(1,'0000-0000-0000-0001'),
(2,'0000-0000-0000-0002'),
(3,'0000-0000-0000-0003'),
(6,'0000-0000-0000-0006'),
(7,'0000-0000-0000-0007'),
(8,NULL),
(11,'0000-0000-0000-0011'),
(12,'0000-0000-0000-0012'),
(14,NULL);

INSERT INTO author_research_area VALUES
(1,'Databases'),(1,'Data Mining'),
(2,'Machine Learning'),(2,'Health Informatics'),
(3,'Natural Language Processing'),
(6,'Computer Vision'),(6,'Machine Learning'),
(7,'Data Mining'),(7,'Databases'),
(8,'Databases'),
(11,'Data Mining'),(11,'Natural Language Processing'),
(12,'Databases'),(12,'Cloud Computing'),
(14,'Databases'),(14,'Computer Vision');

INSERT INTO reviewer VALUES
(1,6),(3,4),(4,8),(5,2),(6,5),(9,3),(10,7),(12,1),(13,0);

INSERT INTO reviewer_expertise VALUES
(1,'Databases'),(1,'Data Mining'),
(3,'Machine Learning'),(3,'Natural Language Processing'),
(4,'Databases'),(4,'Distributed Systems'),
(5,'Databases'),(5,'Information Retrieval'),
(6,'Computer Vision'),(6,'Machine Learning'),
(9,'Software Engineering'),(9,'Databases'),
(10,'Software Engineering'),(10,'Human-Computer Interaction'),
(12,'Databases'),(12,'Cloud Computing'),
(13,'Machine Learning');

INSERT INTO conference(conference_id,name,acronym,description,city,country,start_date,end_date,submission_deadline,review_deadline) VALUES
(1,'Conference A','CONF-A','Test conference A','Astana','Kazakhstan','2027-03-16','2027-03-18','2026-09-15','2026-11-01'),
(2,'Conference B','CONF-B','Test conference B','Almaty','Kazakhstan','2027-04-21','2027-04-23','2026-09-30','2026-11-10'),
(3,'Conference C','CONF-C','Test conference C','Tashkent','Uzbekistan','2027-05-12','2027-05-13','2026-12-20','2027-02-15');

INSERT INTO conference_host VALUES
(1,'University A'),
(1,'University B'),
(2,'University C'),
(2,'University G'),
(3,'University F');

INSERT INTO conference_reviewer VALUES
(1,1),(1,4),(1,5),(1,9),(1,10),(1,12),
(2,1),(2,3),(2,6),(2,10),(2,13),
(3,4),(3,9),(3,10);

INSERT INTO track(track_id,conference_id,name,description,research_area,coordinator_id) VALUES
(1,1,'Track 1','Test track 1','Databases',4),
(2,1,'Track 2','Test track 2','Data Mining',1),
(3,1,'Track 3','Test track 3','Databases',9),
(4,2,'Track 4','Test track 4','Machine Learning',6),
(5,2,'Track 5','Test track 5','Natural Language Processing',3),
(6,3,'Track 6','Test track 6','Software Engineering',10);

INSERT INTO conference_session(session_id,conference_id,title,session_date,start_time,end_time,room_label,chair_id) VALUES
(1,1,'Session 1','2027-03-16','10:00','11:30','Room 1',4),
(2,1,'Session 2','2027-03-16','14:00','15:30','Room 2',1),
(3,1,'Session 3','2027-03-17','11:00','12:30','Room 3',12),
(4,2,'Session 4','2027-04-21','09:30','11:00','Room 4',6),
(5,2,'Session 5','2027-04-22','13:00','14:30','Room 5',3);

INSERT INTO paper(paper_id,track_id,title,abstract,submission_date,status,session_id) VALUES
(1,1,'Paper 1','Abstract of paper 1.','2026-08-20','accepted',1),
(2,1,'Paper 2','Abstract of paper 2. It uses Machine Learning.','2026-09-02','accepted',1),
(3,2,'Paper 3','Abstract of paper 3.','2026-09-05','accepted',2),
(4,2,'Paper 4','Abstract of paper 4.','2026-09-10','accepted',NULL),
(5,1,'Paper 5','Abstract of paper 5 about machine learning.','2026-09-12','rejected',NULL),
(6,1,'Paper 6','Abstract of paper 6.','2026-09-14','under review',NULL),
(7,2,'Paper 7','Abstract of paper 7.','2026-09-01','withdrawn',NULL),
(8,4,'Paper 8','Machine learning paper 8.','2026-09-20','withdrawn',NULL),
(9,4,'Paper 9','Abstract of paper 9, machine learning.','2026-09-18','accepted',4),
(10,5,'Paper 10','Abstract of paper 10.','2026-09-28','submitted',NULL),
(11,4,'Paper 11','Abstract of paper 11.','2026-09-22','rejected',NULL),
(12,5,'Paper 12','Abstract of paper 12.','2026-09-25','withdrawn',NULL),
(13,5,'Paper 13','Abstract of paper 13.','2026-09-26','rejected',NULL);

INSERT INTO paper_keyword VALUES
(1,'keyword1'),(1,'keyword2'),(1,'keyword3'),
(2,'keyword1'),(2,'keyword2'),
(3,'keyword1'),(3,'keyword2'),
(4,'keyword1'),(4,'keyword2'),
(5,'keyword1'),(5,'keyword2'),
(6,'keyword1'),(6,'keyword2'),
(7,'keyword1'),(7,'keyword2'),
(8,'keyword1'),(8,'keyword2'),(8,'keyword3'),
(9,'keyword1'),(9,'keyword2'),
(10,'keyword1'),(10,'keyword2'),
(11,'keyword1'),(11,'keyword2'),
(12,'keyword1'),(12,'keyword2'),
(13,'keyword1'),(13,'keyword2');

INSERT INTO paper_author(paper_id,author_id,author_position,is_corresponding) VALUES
(1,1,1,TRUE),(1,7,2,FALSE),
(2,8,1,TRUE),(2,12,2,FALSE),
(3,11,1,TRUE),(3,3,2,FALSE),
(4,7,1,TRUE),(4,6,2,FALSE),
(5,12,1,TRUE),(5,14,2,FALSE),
(6,14,1,TRUE),
(7,2,1,TRUE),(7,6,2,FALSE),
(8,2,1,TRUE),(8,3,2,FALSE),
(9,6,1,TRUE),(9,2,2,FALSE),(9,1,3,FALSE),
(10,3,1,TRUE),(10,11,2,FALSE),
(11,14,1,TRUE),(11,12,2,FALSE),
(12,11,1,TRUE),(12,2,2,FALSE),
(13,7,1,TRUE),(13,11,2,FALSE);

INSERT INTO paper_version(paper_id,version_no,file_location,uploaded_at,change_note) VALUES
(1,1,'files/paper1_v1.pdf','2026-08-20 18:42',NULL),
(1,2,'files/paper1_v2.pdf','2026-09-03 11:15','change 1'),
(1,3,'files/paper1_v3.pdf','2026-11-20 09:05','change 2'),
(2,1,'files/paper2_v1.pdf','2026-09-02 22:10',NULL),
(2,2,'files/paper2_v2.pdf','2026-11-18 16:30','change 1'),
(3,1,'files/paper3_v1.pdf','2026-09-05 13:00',NULL),
(4,1,'files/paper4_v1.pdf','2026-09-10 08:45',NULL),
(5,1,'files/paper5_v1.pdf','2026-09-12 20:20',NULL),
(6,1,'files/paper6_v1.pdf','2026-09-14 23:55',NULL),
(7,1,'files/paper7_v1.pdf','2026-09-01 10:00',NULL),
(7,2,'files/paper7_v2.pdf','2026-09-09 10:30','change 1'),
(8,1,'files/paper8_v1.pdf','2026-09-20 15:40',NULL),
(9,1,'files/paper9_v1.pdf','2026-09-18 12:00',NULL),
(9,3,'files/paper9_v3.pdf','2026-11-21 19:25','change 2'),
(10,1,'files/paper10_v1.pdf','2026-09-28 17:05',NULL),
(11,1,'files/paper11_v1.pdf','2026-09-22 09:50',NULL),
(12,1,'files/paper12_v1.pdf','2026-09-25 14:15',NULL),
(13,1,'files/paper13_v1.pdf','2026-09-26 21:35',NULL);

INSERT INTO review(review_id,paper_id,reviewer_id,overall_score,recommendation,comments_for_authors,confidential_comments,review_submission_date) VALUES
(1,1,4,5,'accept','comment 1',NULL,'2026-10-05'),
(2,1,5,4,'accept','comment 2',NULL,'2026-10-12'),
(3,2,4,4,'accept','comment 3',NULL,'2026-10-08'),
(4,2,1,4,'accept','comment 4','note 1','2026-10-15'),
(5,3,1,5,'accept','comment 5',NULL,'2026-10-10'),
(6,3,5,4,'accept','comment 6',NULL,'2026-10-20'),
(7,4,4,4,'accept','comment 7',NULL,'2026-10-11'),
(8,4,10,3,'accept','comment 8',NULL,'2026-10-25'),
(9,5,4,2,'reject','comment 9',NULL,'2026-10-14'),
(10,5,5,1,'reject','comment 10','note 2','2026-10-22'),
(11,6,1,3,'accept','comment 11',NULL,'2026-10-18'),
(12,6,12,3,'reject','comment 12',NULL,'2026-10-28'),
(13,7,4,2,'reject','comment 13',NULL,'2026-09-25'),
(14,7,9,3,'reject','comment 14',NULL,'2026-09-28'),
(15,8,6,3,'accept','comment 15',NULL,'2026-10-16'),
(16,9,3,5,'accept','comment 16',NULL,'2026-10-21'),
(17,9,10,4,'accept','comment 17',NULL,'2026-10-30'),
(18,11,6,2,'reject','comment 18',NULL,'2026-10-19'),
(19,11,3,2,'reject','comment 19',NULL,'2026-10-27'),
(20,13,3,2,'reject','comment 20',NULL,'2026-11-02');

SELECT setval(pg_get_serial_sequence('app_user','user_id'),14);
SELECT setval(pg_get_serial_sequence('conference','conference_id'),3);
SELECT setval(pg_get_serial_sequence('track','track_id'),6);
SELECT setval(pg_get_serial_sequence('conference_session','session_id'),5);
SELECT setval(pg_get_serial_sequence('paper','paper_id'),13);
SELECT setval(pg_get_serial_sequence('review','review_id'),20);
