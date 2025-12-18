-- Drop database if it exists to start fresh
DROP DATABASE IF EXISTS football_league_db;
CREATE DATABASE football_league_db;
USE football_league_db;

-- ---------------------------------------------------
-- INDEPENDENT TABLES (Level 0)
-- ---------------------------------------------------

-- LEAGUE/FEDERATION
CREATE TABLE League (
    league_id VARCHAR(25) PRIMARY KEY, 
    league_name VARCHAR(100) NOT NULL,
    main_city VARCHAR(100),
    country VARCHAR(100),
    CONSTRAINT chk_league_id CHECK (league_id REGEXP '^L[A-Z]{3,16}[0-9]{3}$')
);

-- POSITION (Goalkeeper, Defender, Midfielder, Forward)
CREATE TABLE Position (
    position_id VARCHAR(25) PRIMARY KEY,
    position_name VARCHAR(50) NOT NULL UNIQUE,
    CONSTRAINT chk_position_id CHECK (position_id REGEXP '^P[A-Z]{3,16}[0-9]{3}$')
);

-- SKILL/TRAIT
CREATE TABLE Skill (
    skill_id VARCHAR(25) PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL,
    effect_description TEXT,
    CONSTRAINT chk_skill_id CHECK (skill_id REGEXP '^K[A-Z]{3,16}[0-9]{3}$')
);

-- ---------------------------------------------------
-- LEVEL 1 TABLES (Dependencies on Level 0)
-- ---------------------------------------------------

-- CITY
CREATE TABLE City (
    city_id VARCHAR(25) PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    league_id VARCHAR(25),
    FOREIGN KEY (league_id) REFERENCES League(league_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_city_id CHECK (city_id REGEXP '^C[A-Z]{3,16}[0-9]{3}$')
);

-- SPECIAL MOVE (Skill moves like Step-over, Rabona, Bicycle Kick)
CREATE TABLE SpecialMove (
    move_id VARCHAR(25) PRIMARY KEY,
    move_name VARCHAR(100) NOT NULL,
    difficulty INT,
    success_rate INT,
    stamina_cost INT,
    position_id VARCHAR(25),
    category ENUM('Dribbling', 'Shooting', 'Passing', 'Defensive') NOT NULL,
    FOREIGN KEY (position_id) REFERENCES Position(position_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_move_id CHECK (move_id REGEXP '^M[A-Z]{3,16}[0-9]{3}$'),
    CONSTRAINT chk_success_rate CHECK (success_rate >= 0 AND success_rate <= 100),
    CONSTRAINT chk_difficulty CHECK (difficulty >= 0),
    CONSTRAINT chk_stamina_cost CHECK (stamina_cost > 0)
);

-- POSITION STRENGTH
CREATE TABLE PositionStrength (
    position_id VARCHAR(25),
    strong_against_position_id VARCHAR(25),
    PRIMARY KEY (position_id, strong_against_position_id),
    FOREIGN KEY (position_id) REFERENCES Position(position_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (strong_against_position_id) REFERENCES Position(position_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE PositionWeakness (
    position_id VARCHAR(25),
    weak_against_position_id VARCHAR(25),
    PRIMARY KEY (position_id, weak_against_position_id),
    FOREIGN KEY (position_id) REFERENCES Position(position_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (weak_against_position_id) REFERENCES Position(position_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- PLAYER ARCHETYPE (Playmaker, Target Man, Sweeper, Regista, etc.)
CREATE TABLE PlayerArchetype (
    archetype_id VARCHAR(25) PRIMARY KEY,
    archetype_name VARCHAR(100) NOT NULL,
    base_pace INT NOT NULL,
    base_shooting INT NOT NULL,
    base_passing INT NOT NULL,
    base_defending INT NOT NULL,
    primary_position_id VARCHAR(25),
    secondary_position_id VARCHAR(25),
    FOREIGN KEY (primary_position_id) REFERENCES Position(position_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (secondary_position_id) REFERENCES Position(position_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_archetype_id CHECK (archetype_id REGEXP '^A[A-Z]{3,16}[0-9]{3}$'),
    CONSTRAINT chk_base_stats CHECK (base_pace > 0 AND base_shooting > 0 AND base_passing > 0 AND base_defending > 0)
);

-- MANAGER/COACH (Supertype)
CREATE TABLE Manager (
    manager_id VARCHAR(25) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    birth_date DATE,
    contact_info_email VARCHAR(150) UNIQUE,
    contact_info_phone VARCHAR(50) UNIQUE,
    league_id VARCHAR(25),
    nationality VARCHAR(100),
    FOREIGN KEY (league_id) REFERENCES League(league_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_manager_id CHECK (manager_id REGEXP '^G[A-Z]{3,16}[0-9]{3}$')
);

-- LEAGUE SEASON
CREATE TABLE LeagueSeason (
    season_id VARCHAR(25) PRIMARY KEY,
    year INT NOT NULL,
    league_id VARCHAR(25),
    theme VARCHAR(100),
    FOREIGN KEY (league_id) REFERENCES League(league_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_season_id CHECK (season_id REGEXP '^S[A-Z]{3,16}[0-9]{3}$')
);

-- ---------------------------------------------------
-- LEVEL 2 TABLES (Dependencies on Level 1)
-- ---------------------------------------------------

-- PLAYER ARCHETYPE SKILL
CREATE TABLE PlayerArchetypeSkill (
    archetype_id VARCHAR(25),
    skill_id VARCHAR(25),
    PRIMARY KEY (archetype_id, skill_id),
    FOREIGN KEY (archetype_id) REFERENCES PlayerArchetype(archetype_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES Skill(skill_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- CLUB/TEAM
CREATE TABLE Club (
    club_id VARCHAR(25) PRIMARY KEY,
    club_name VARCHAR(100) NOT NULL,
    city_id VARCHAR(25),
    specialization_position_id VARCHAR(25),
    stadium_name VARCHAR(150),
    founded_year INT,
    FOREIGN KEY (city_id) REFERENCES City(city_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (specialization_position_id) REFERENCES Position(position_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_club_id CHECK (club_id REGEXP '^B[A-Z]{3,16}[0-9]{3}$')
);

-- CLUB MANAGER (Profile only)
CREATE TABLE ClubManager (
    manager_id VARCHAR(25) PRIMARY KEY,
    specialty_position_id VARCHAR(25),
    years_of_experience INT CHECK (years_of_experience >= 0),
    preferred_formation VARCHAR(20),
    FOREIGN KEY (manager_id) REFERENCES Manager(manager_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (specialty_position_id) REFERENCES Position(position_id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- LEAGUE CHAMPION
CREATE TABLE Champion (
    champion_id VARCHAR(25) PRIMARY KEY,
    title_year INT,
    FOREIGN KEY (champion_id) REFERENCES Manager(manager_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- REGISTERED PLAYER
CREATE TABLE Player (
    player_id VARCHAR(25) PRIMARY KEY,
    archetype_id VARCHAR(25),
    manager_id VARCHAR(25),
    player_name VARCHAR(100),
    jersey_number INT CHECK (jersey_number BETWEEN 1 AND 99),
    overall_rating INT CHECK (overall_rating BETWEEN 1 AND 100),
    contract_start_date DATE,
    contract_end_date DATE,
    market_value DECIMAL(15,2),
    FOREIGN KEY (archetype_id) REFERENCES PlayerArchetype(archetype_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (manager_id) REFERENCES Manager(manager_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_player_id CHECK (player_id REGEXP '^R[A-Z]{3,16}[0-9]{3}$'),
    CONSTRAINT chk_contract_dates CHECK (contract_end_date >= contract_start_date)
);

-- TOURNAMENT (Champions League, FA Cup, World Cup)
CREATE TABLE Tournament (
    tournament_id VARCHAR(25) PRIMARY KEY,
    tournament_name VARCHAR(150) NOT NULL,
    start_date DATE,
    end_date DATE,
    city_id VARCHAR(25),
    season_id VARCHAR(25),
    prize_money DECIMAL(15,2),
    FOREIGN KEY (city_id) REFERENCES City(city_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (season_id) REFERENCES LeagueSeason(season_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_tournament_id CHECK (tournament_id REGEXP '^T[A-Z]{3,16}[0-9]{3}$'),
    CONSTRAINT chk_dates CHECK (end_date >= start_date)
);

-- ---------------------------------------------------
-- LEVEL 3 TABLES (Dependencies on Level 2)
-- ---------------------------------------------------

-- PLAYER SPECIAL MOVE
CREATE TABLE PlayerMove (
    player_id VARCHAR(25),
    move_id VARCHAR(25),
    PRIMARY KEY (player_id, move_id),
    FOREIGN KEY (player_id) REFERENCES Player(player_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (move_id) REFERENCES SpecialMove(move_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- CLUB SEASON REGISTRY
CREATE TABLE ClubSeasonRegistry (
    registry_id VARCHAR(25) PRIMARY KEY,
    season_id VARCHAR(25),
    club_id VARCHAR(25),
    manager_id VARCHAR(25),
    FOREIGN KEY (season_id) REFERENCES LeagueSeason(season_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (club_id) REFERENCES Club(club_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (manager_id) REFERENCES ClubManager(manager_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_registry_id CHECK (registry_id REGEXP '^E[A-Z]{3,16}[0-9]{3}$')
);

-- CLUB MATCH
CREATE TABLE ClubMatch (
    match_id VARCHAR(25) PRIMARY KEY,
    home_club_id VARCHAR(25),
    away_club_id VARCHAR(25),
    home_manager_id VARCHAR(25),
    away_manager_id VARCHAR(25),
    match_date DATE,
    home_score INT DEFAULT 0,
    away_score INT DEFAULT 0,
    result ENUM('Home Win', 'Away Win', 'Draw') NOT NULL,
    attendance INT,
    FOREIGN KEY (home_club_id) REFERENCES Club(club_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (away_club_id) REFERENCES Club(club_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (home_manager_id) REFERENCES ClubManager(manager_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (away_manager_id) REFERENCES ClubManager(manager_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_match_id CHECK (match_id REGEXP '^H[A-Z]{3,16}[0-9]{3}$'),
    CONSTRAINT chk_scores CHECK (home_score >= 0 AND away_score >= 0)
);

-- TROPHY
CREATE TABLE Trophy (
    club_id VARCHAR(25),
    trophy_number INT,
    date_earned DATE,
    manager_id VARCHAR(25),
    trophy_type VARCHAR(100),
    FOREIGN KEY (club_id) REFERENCES Club(club_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (manager_id) REFERENCES Manager(manager_id) ON DELETE SET NULL ON UPDATE CASCADE,
    PRIMARY KEY (club_id, trophy_number)
);

-- TROPHY NAME (e.g., Premier League Trophy, FA Cup)
CREATE TABLE TrophyName (
    club_id VARCHAR(25) PRIMARY KEY,
    trophy_name VARCHAR(100) NOT NULL,
    FOREIGN KEY (club_id) REFERENCES Club(club_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- TOURNAMENT ENTRY
CREATE TABLE TournamentEntry (
    tournament_id VARCHAR(25),
    manager_id VARCHAR(25),
    registration_date DATE,
    PRIMARY KEY (tournament_id, manager_id),
    FOREIGN KEY (tournament_id) REFERENCES Tournament(tournament_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (manager_id) REFERENCES Manager(manager_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- TOURNAMENT MATCH
CREATE TABLE TournamentMatch (
    tournament_id VARCHAR(25),
    match_number INT,
    manager1_id VARCHAR(25),
    manager2_id VARCHAR(25),
    winner_id VARCHAR(25),
    match_date DATE,
    round_number INT,
    manager1_score INT DEFAULT 0,
    manager2_score INT DEFAULT 0,
    PRIMARY KEY (tournament_id, match_number),
    FOREIGN KEY (tournament_id) REFERENCES Tournament(tournament_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (manager1_id) REFERENCES Manager(manager_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (manager2_id) REFERENCES Manager(manager_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (winner_id) REFERENCES Manager(manager_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_tournament_scores CHECK (manager1_score >= 0 AND manager2_score >= 0)
);

-- PLAYER STATISTICS
CREATE TABLE PlayerStatistics (
    stat_id VARCHAR(25) PRIMARY KEY,
    player_id VARCHAR(25),
    season_id VARCHAR(25),
    goals INT DEFAULT 0,
    assists INT DEFAULT 0,
    yellow_cards INT DEFAULT 0,
    red_cards INT DEFAULT 0,
    minutes_played INT DEFAULT 0,
    matches_played INT DEFAULT 0,
    FOREIGN KEY (player_id) REFERENCES Player(player_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (season_id) REFERENCES LeagueSeason(season_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_stat_id CHECK (stat_id REGEXP '^X[A-Z]{3,16}[0-9]{3}$'),
    CONSTRAINT chk_stats CHECK (goals >= 0 AND assists >= 0 AND yellow_cards >= 0 AND red_cards >= 0 AND minutes_played >= 0 AND matches_played >= 0)
);

-- TRANSFER HISTORY
CREATE TABLE Transfer (
    transfer_id VARCHAR(25) PRIMARY KEY,
    player_id VARCHAR(25),
    from_manager_id VARCHAR(25),
    to_manager_id VARCHAR(25),
    transfer_date DATE,
    transfer_fee DECIMAL(15,2),
    FOREIGN KEY (player_id) REFERENCES Player(player_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (from_manager_id) REFERENCES Manager(manager_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (to_manager_id) REFERENCES Manager(manager_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_transfer_id CHECK (transfer_id REGEXP '^F[A-Z]{3,16}[0-9]{3}$')
);

-- ---------------------------------------------------
-- TRIGGERS: Ensure winner_id is one of the participants
-- ---------------------------------------------------
DELIMITER $$
CREATE TRIGGER trg_tournament_match_winner_check_before_insert
BEFORE INSERT ON TournamentMatch FOR EACH ROW
BEGIN
    IF NEW.winner_id IS NOT NULL AND NOT (NEW.winner_id = NEW.manager1_id OR NEW.winner_id = NEW.manager2_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'winner_id must be either manager1_id or manager2_id';
    END IF;
END$$

CREATE TRIGGER trg_tournament_match_winner_check_before_update
BEFORE UPDATE ON TournamentMatch FOR EACH ROW
BEGIN
    IF NEW.winner_id IS NOT NULL AND NOT (NEW.winner_id = NEW.manager1_id OR NEW.winner_id = NEW.manager2_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'winner_id must be either manager1_id or manager2_id';
    END IF;
END$$
DELIMITER ;
