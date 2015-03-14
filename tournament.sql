-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

CREATE TABLE tournaments (
	ID serial PRIMARY KEY,
	Name varchar(255) NOT NULL
);

CREATE TABLE players (
	ID serial PRIMARY KEY,
	Name varchar(255) NOT NULL
);

CREATE TABLE tournament_players ( 
	TournamentID int REFERENCES tournaments (ID) NOT NULL,
	PlayerID int REFERENCES players (ID) NOT NULL,
	HadBye int NOT NULL DEFAULT 0,
	PRIMARY KEY (TournamentID, PlayerID)
);

CREATE TABLE matches (
	ID serial PRIMARY KEY,
	TournamentID int REFERENCES tournaments (ID) NOT NULL,
	FirstPlayer int REFERENCES players (ID) NOT NULL,
	SecondPlayer int REFERENCES players (ID), -- can be null because of a bye
	Winner int REFERENCES players (ID)
);

CREATE VIEW player_matches AS
SELECT players.ID AS PlayerID, players.Name AS PlayerName, tournament_players.TournamentID, matches.ID AS MatchID,
CAST (
	CASE
		WHEN players.ID = matches.Winner
			THEN 1
		ELSE 0
	END AS int) AS Won
FROM players INNER JOIN tournament_players ON players.ID = tournament_players.PlayerID
LEFT JOIN matches ON matches.TournamentID = tournament_players.TournamentID AND (players.ID = matches.FirstPlayer OR players.ID = matches.SecondPlayer);

CREATE VIEW player_stats AS
SELECT TournamentID, PlayerID, PlayerName, count(MatchID) as Games, sum(Won) as Wins,
(
	SELECT COALESCE(sum(Won),0) as Wins FROM player_matches AS pm
	WHERE pm.TournamentID = player_matches.TournamentID AND pm.PlayerID IN 
	(
		SELECT FirstPlayer as Opponent FROM matches
		WHERE matches.TournamentID = pm.TournamentID  AND matches.SecondPlayer = player_matches.PlayerID
		UNION
		SELECT SecondPlayer as Opponent FROM matches
		WHERE matches.TournamentID = pm.TournamentID AND matches.FirstPlayer = player_matches.PlayerID
	)
) AS OMW
FROM player_matches
GROUP BY TournamentID, PlayerID, PlayerName 
ORDER BY Wins desc, OMW desc;
