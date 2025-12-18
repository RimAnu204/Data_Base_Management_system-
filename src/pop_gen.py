import random
import datetime

# Try to import faker, else fallback
try:
    from faker import Faker
    fake = Faker()
except ImportError:
    fake = None

# ---------------------------------------------------------
# CONFIGURATION & CONSTANTS
# ---------------------------------------------------------
NUM_MANAGERS = 150
NUM_PLAYERS = 700
NUM_MATCHES = 1200
FILE_NAME = "populate.sql"

# Real World Data for Coherence
LEAGUES = [
    ("Premier League", "London", "England"), 
    ("La Liga", "Madrid", "Spain"), 
    ("Bundesliga", "Munich", "Germany"), 
    ("Serie A", "Milan", "Italy"), 
    ("Ligue 1", "Paris", "France"), 
    ("Eredivisie", "Amsterdam", "Netherlands"),
    ("Primeira Liga", "Lisbon", "Portugal"), 
    ("MLS", "New York", "USA")
]

POSITIONS = [
    "Goalkeeper", "Center Back", "Left Back", "Right Back", 
    "Defensive Midfielder", "Central Midfielder", "Attacking Midfielder",
    "Left Winger", "Right Winger", "Striker", "Forward"
]

# (Name, Pace, Shooting, Passing, Defending, Position1, Position2)
ARCHETYPE_DATA = [
    ("Classic Goalkeeper", 40, 30, 45, 70, "Goalkeeper", None),
    ("Ball-Playing Defender", 55, 35, 65, 85, "Center Back", None),
    ("Wing Back", 80, 45, 70, 65, "Right Back", "Left Back"),
    ("Deep-Lying Playmaker", 50, 55, 90, 70, "Defensive Midfielder", None),
    ("Box-to-Box Midfielder", 75, 65, 80, 70, "Central Midfielder", None),
    ("Classic Number 10", 70, 75, 90, 45, "Attacking Midfielder", None),
    ("Pace Winger", 95, 70, 65, 35, "Left Winger", "Right Winger"),
    ("Target Man", 50, 85, 55, 30, "Striker", None),
    ("Poacher", 75, 90, 50, 25, "Striker", "Forward"),
    ("False Nine", 75, 80, 85, 40, "Forward", "Attacking Midfielder"),
    ("Sweeper Keeper", 60, 25, 70, 55, "Goalkeeper", None),
    ("Pressing Forward", 85, 75, 60, 55, "Forward", None),
    ("Regista", 45, 40, 95, 75, "Defensive Midfielder", "Central Midfielder"),
    ("Inverted Winger", 85, 80, 75, 40, "Left Winger", "Right Winger"),
    ("Complete Striker", 80, 88, 75, 50, "Striker", None),
    ("Anchor Man", 40, 30, 60, 90, "Defensive Midfielder", None),
    ("Trequartista", 65, 85, 90, 30, "Attacking Midfielder", None),
    ("Shadow Striker", 80, 85, 70, 45, "Attacking Midfielder", "Forward"),
    ("Ball Winner", 70, 40, 55, 88, "Defensive Midfielder", "Central Midfielder"),
    ("Wide Playmaker", 75, 60, 90, 50, "Left Winger", "Right Winger")
]

SPECIAL_MOVES_DATA = [
    ("Step Over", 3, 75, 10, "Dribbling"),
    ("Rabona Cross", 8, 60, 25, "Passing"),
    ("Bicycle Kick", 9, 50, 30, "Shooting"),
    ("Rainbow Flick", 7, 65, 15, "Dribbling"),
    ("Elastico", 8, 70, 20, "Dribbling"),
    ("Trivela Pass", 6, 80, 15, "Passing"),
    ("Knuckleball Shot", 7, 65, 25, "Shooting"),
    ("McGeady Spin", 6, 75, 15, "Dribbling"),
    ("Cruyff Turn", 5, 80, 10, "Dribbling"),
    ("Panenka Penalty", 9, 55, 20, "Shooting"),
    ("Slide Tackle", 4, 85, 15, "Defensive"),
    ("Chip Shot", 6, 70, 20, "Shooting"),
    ("Roulette", 7, 75, 15, "Dribbling"),
    ("Driven Pass", 4, 90, 10, "Passing")
]

SKILLS = [
    "Pace", "Dribbling", "Shooting", "Passing", "Defending", 
    "Physicality", "Vision", "Positioning", "Ball Control", "Stamina"
]

# (Club Name, Position Type, Trophy Name, Stadium)
CLUB_LORE_DATA = [
    ("Manchester United", "Attacking Midfielder", "Premier League Trophy", "Old Trafford"),
    ("Real Madrid", "Forward", "La Liga Trophy", "Santiago Bernabéu"),
    ("Bayern Munich", "Central Midfielder", "Bundesliga Trophy", "Allianz Arena"),
    ("Barcelona", "Attacking Midfielder", "La Liga Trophy", "Camp Nou"),
    ("Liverpool", "Left Winger", "Premier League Trophy", "Anfield"),
    ("Juventus", "Center Back", "Serie A Trophy", "Allianz Stadium"),
    ("Paris Saint-Germain", "Forward", "Ligue 1 Trophy", "Parc des Princes"),
    ("Chelsea", "Defensive Midfielder", "Premier League Trophy", "Stamford Bridge"),
    ("Arsenal", "Right Winger", "Premier League Trophy", "Emirates Stadium"),
    ("AC Milan", "Striker", "Serie A Trophy", "San Siro"),
    ("Inter Milan", "Box-to-Box Midfielder", "Serie A Trophy", "San Siro"),
    ("Atletico Madrid", "Defensive Midfielder", "La Liga Trophy", "Wanda Metropolitano")
]

TOURNAMENT_NAMES = [
    "UEFA Champions League",
    "FA Cup",
    "Copa del Rey",
    "DFB-Pokal",
    "Coppa Italia",
    "Coupe de France",
    "FIFA Club World Cup",
    "UEFA Europa League",
    "English League Cup",
    "Spanish Super Cup"
]

# Fallback city names
LORE_CITIES = [
    "Manchester", "London", "Madrid", "Barcelona", "Munich", "Milan",
    "Paris", "Liverpool", "Turin", "Rome", "Amsterdam", "Lisbon",
    "Porto", "Valencia", "Seville", "Dortmund", "Naples", "Florence"
]

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def get_id(prefix, name, index):
    """
    Generates an ID strictly matching ^Prefix[A-Z]{3,16}[0-9]{3}$
    """
    clean_name = "".join(c for c in name if c.isalpha()).upper()
    if len(clean_name) < 3:
        clean_name = (clean_name + "XXX")[:16]
    if len(clean_name) > 16:
        clean_name = clean_name[:16]
    return f"{prefix}{clean_name}{index:03d}"

def escape_sql(val):
    if val is None:
        return "NULL"
    if isinstance(val, int) or isinstance(val, float):
        return str(val)
    return f"'{str(val).replace("'", "''")}'"


def random_date_between(start_date, end_date):
    """Return an ISO date string between two datetime.date objects (inclusive)."""
    if isinstance(start_date, str):
        start_date = datetime.date.fromisoformat(start_date)
    if isinstance(end_date, str):
        end_date = datetime.date.fromisoformat(end_date)
    delta = (end_date - start_date).days
    if delta <= 0:
        return start_date.isoformat()
    pick = random.randint(0, delta)
    return (start_date + datetime.timedelta(days=pick)).isoformat()


def random_date_in_years(start_year=2000, end_year=2025):
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)
    return random_date_between(start, end)

# Storage for Referencing IDs
ids = {
    "league": [], "position": [], "skill": [], "city": [], 
    "move": [], "archetype": [], "manager": [], "season": [],
    "club": [], "club_manager": [], "player": [], "tournament": []
}

# ---------------------------------------------------------
# GENERATION LOGIC
# ---------------------------------------------------------

with open(FILE_NAME, "w") as f:
    f.write("-- AUTO-GENERATED POPULATION SCRIPT FOR FOOTBALL LEAGUE\n")
    f.write("USE football_league_db;\n\n")
    f.write("-- Disable checks for bulk loading\n")
    f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

    # =====================================================
    # LEVEL 0
    # =====================================================
    f.write("-- LEVEL 0: League, Position, Skill\n")
    
    for i, (lname, main_city, country) in enumerate(LEAGUES, 1):
        lid = get_id("L", lname, i)
        ids["league"].append(lid)
        f.write(f"INSERT INTO League VALUES ({escape_sql(lid)}, {escape_sql(lname)}, {escape_sql(main_city)}, {escape_sql(country)});\n")

    for i, pname in enumerate(POSITIONS, 1):
        pid = get_id("P", pname, i)
        ids["position"].append(pid)
        f.write(f"INSERT INTO Position VALUES ({escape_sql(pid)}, {escape_sql(pname)});\n")

    for i, sname in enumerate(SKILLS, 1):
        sid = get_id("K", sname, i)
        ids["skill"].append(sid)
        f.write(f"INSERT INTO Skill VALUES ({escape_sql(sid)}, {escape_sql(sname)}, 'Standard effect');\n")

    # =====================================================
    # LEVEL 1
    # =====================================================
    f.write("\n-- LEVEL 1: Dependent on Level 0\n")

    # City
    for i in range(1, 60):
        league_ref = random.choice(ids["league"])
        
        if fake:
            cname = fake.city()
        elif i <= len(LORE_CITIES):
            cname = LORE_CITIES[i-1]
        else:
            cname = f"City{i}"
            
        cid = get_id("C", cname, i)
        ids["city"].append(cid)
        f.write(f"INSERT INTO City VALUES ({escape_sql(cid)}, {escape_sql(cname)}, {escape_sql(league_ref)});\n")

    # SpecialMove
    for i, (mname, diff, succ, stam, cat) in enumerate(SPECIAL_MOVES_DATA, 1):
        mid = get_id("M", mname, i)
        ids["move"].append(mid)
        # Random position for move
        pid = random.choice(ids["position"])
        f.write(f"INSERT INTO SpecialMove VALUES ({escape_sql(mid)}, {escape_sql(mname)}, {diff}, {succ}, {stam}, {escape_sql(pid)}, {escape_sql(cat)});\n")

    # PositionStrength & Weakness
    for pid in ids["position"]:
        # 2 positions it is strong against
        targets = random.sample(ids["position"], min(2, len(ids["position"])))
        for t in targets:
            if t != pid:
                f.write(f"INSERT IGNORE INTO PositionStrength VALUES ({escape_sql(pid)}, {escape_sql(t)});\n")
        
        # 2 positions it is weak against
        weak_targets = random.sample(ids["position"], min(2, len(ids["position"])))
        for wt in weak_targets:
            if wt != pid:
                f.write(f"INSERT IGNORE INTO PositionWeakness VALUES ({escape_sql(pid)}, {escape_sql(wt)});\n")

    # PlayerArchetype
    for i, data in enumerate(ARCHETYPE_DATA, 1):
        aid = get_id("A", data[0], i)
        ids["archetype"].append({"id": aid, "name": data[0]})
        p1_idx = POSITIONS.index(data[5])
        p1_id = ids["position"][p1_idx]
        p2_id = "NULL"
        if data[6]:
            p2_idx = POSITIONS.index(data[6])
            p2_id = f"'{ids['position'][p2_idx]}'"
        f.write(f"INSERT INTO PlayerArchetype VALUES ({escape_sql(aid)}, {escape_sql(data[0])}, {data[1]}, {data[2]}, {data[3]}, {data[4]}, {escape_sql(p1_id)}, {p2_id});\n")

    # Manager
    for i in range(1, NUM_MANAGERS + 1):
        if fake:
            mname = fake.name()
        else:
            mname = f"Manager {i}"
        
        raw_fname = mname.split()[0]
        clean_fname = "".join(c for c in raw_fname if c.isalnum())
        
        mid = get_id("G", clean_fname, i)
        ids["manager"].append(mid)
        
        gender = random.choice(['Male', 'Female', 'Other'])
        
        if fake:
            bdate_obj = fake.date_of_birth(minimum_age=35, maximum_age=70)
            bdate = bdate_obj.isoformat()
        else:
            bdate = random_date_in_years(1955, 1985)
        
        email = f"{clean_fname}{i}@footballmail.com"
        phone = f"555-{i:04d}"
        lid = random.choice(ids["league"])
        
        if fake:
            nationality = fake.country()
        else:
            nationality = random.choice(["England", "Spain", "Germany", "Italy", "France", "Brazil", "Argentina"])
        
        f.write(f"INSERT INTO Manager VALUES ({escape_sql(mid)}, {escape_sql(mname)}, {escape_sql(gender)}, {escape_sql(bdate)}, {escape_sql(email)}, {escape_sql(phone)}, {escape_sql(lid)}, {escape_sql(nationality)});\n")

    # LeagueSeason
    for i in range(1, 6):
        sid = get_id("S", "SEASON", i)
        ids["season"].append(sid)
        lid = ids["league"][i-1] if i-1 < len(ids["league"]) else ids["league"][0]
        f.write(f"INSERT INTO LeagueSeason VALUES ({escape_sql(sid)}, {2020+i}, {escape_sql(lid)}, 'Official League Season');\n")

    # =====================================================
    # LEVEL 2
    # =====================================================
    f.write("\n-- LEVEL 2: Dependent on Level 1\n")

    # PlayerArchetypeSkill
    for a_obj in ids["archetype"]:
        aid = a_obj["id"]
        # Assign 2-3 random skills
        num_skills = random.randint(2, 3)
        chosen_skills = random.sample(ids["skill"], min(num_skills, len(ids["skill"])))
        for skill_id in chosen_skills:
            f.write(f"INSERT IGNORE INTO PlayerArchetypeSkill VALUES ({escape_sql(aid)}, {escape_sql(skill_id)});\n")

    # Club & ClubManager
    available_cities = ids["city"][:len(CLUB_LORE_DATA)]
    
    for i, city_id in enumerate(available_cities):
        c_name, c_position_name, c_trophy_name, c_stadium = CLUB_LORE_DATA[i]
        
        cid = get_id("B", c_name, i+1)
        ids["club"].append({"id": cid, "city": city_id})
        
        try:
            pos_idx = POSITIONS.index(c_position_name)
            spec_pos_id = ids["position"][pos_idx]
        except ValueError:
            spec_pos_id = ids["position"][0]

        founded_year = random.randint(1880, 1990)
        f.write(f"INSERT INTO Club VALUES ({escape_sql(cid)}, {escape_sql(c_name)}, {escape_sql(city_id)}, {escape_sql(spec_pos_id)}, {escape_sql(c_stadium)}, {founded_year});\n")
        
        # Assign Manager
        cmid = ids["manager"][i]
        ids["club_manager"].append({"mid": cmid, "cid": cid})
        
        formation = random.choice(["4-4-2", "4-3-3", "3-5-2", "4-2-3-1", "5-3-2"])
        f.write(f"INSERT INTO ClubManager VALUES ({escape_sql(cmid)}, {escape_sql(spec_pos_id)}, {random.randint(1,20)}, {escape_sql(formation)});\n")
        
        # Trophy Name
        f.write(f"INSERT INTO TrophyName VALUES ({escape_sql(cid)}, {escape_sql(c_trophy_name)});\n")

    # Champion
    for i in range(1, 4):
        champ_id = ids["manager"][-i]
        f.write(f"INSERT INTO Champion VALUES ({escape_sql(champ_id)}, {2020+i});\n")

    # Player
    for i in range(1, NUM_PLAYERS + 1):
        pid = get_id("R", "PLAYER", i)
        ids["player"].append(pid)
        arch_obj = random.choice(ids["archetype"])
        arch_id = arch_obj["id"]
        manager_id = random.choice(ids["manager"])
        
        if fake:
            player_name = fake.name()
        else:
            player_name = f"Player{i}"
            
        jersey_num = random.randint(1, 99)
        rating = random.randint(50, 99)
        
        contract_start = random_date_in_years(2018, 2023)
        cs_obj = datetime.date.fromisoformat(contract_start)
        ce_obj = cs_obj + datetime.timedelta(days=random.randint(365, 1825))
        contract_end = ce_obj.isoformat()
        
        market_value = round(random.uniform(100000, 150000000), 2)
        
        f.write(f"INSERT INTO Player VALUES ({escape_sql(pid)}, {escape_sql(arch_id)}, {escape_sql(manager_id)}, {escape_sql(player_name)}, {jersey_num}, {rating}, {escape_sql(contract_start)}, {escape_sql(contract_end)}, {market_value});\n")

    # Tournament
    for i in range(1, 6):
        tid = get_id("T", "TOURN", i)
        cid = random.choice(ids["city"])
        sid = random.choice(ids["season"])
        
        if i <= len(TOURNAMENT_NAMES):
            t_name = TOURNAMENT_NAMES[i-1]
        else:
            t_name = f"Cup Competition {i}"
            
        start_date = random_date_in_years(2023, 2025)
        sd_obj = datetime.date.fromisoformat(start_date)
        end_obj = sd_obj + datetime.timedelta(days=random.randint(3, 30))
        end_date = end_obj.isoformat()
        
        prize_money = round(random.uniform(1000000, 100000000), 2)
        
        ids["tournament"].append({"id": tid, "start": start_date, "end": end_date, "city": cid, "season": sid})
        f.write(f"INSERT INTO Tournament VALUES ({escape_sql(tid)}, {escape_sql(t_name)}, {escape_sql(start_date)}, {escape_sql(end_date)}, {escape_sql(cid)}, {escape_sql(sid)}, {prize_money});\n")

    # =====================================================
    # LEVEL 3
    # =====================================================
    f.write("\n-- LEVEL 3: Complex Intersections\n")

    # PlayerMove
    for pid in ids["player"]:
        num_moves = random.randint(1, 4)
        chosen_moves = random.sample(ids["move"], min(num_moves, len(ids["move"])))
        for mid in chosen_moves:
            f.write(f"INSERT INTO PlayerMove VALUES ({escape_sql(pid)}, {escape_sql(mid)});\n")

    # ClubSeasonRegistry
    registry_count = 1
    for season in ids["season"]:
        for cm_obj in ids["club_manager"]:
            rid = get_id("E", "REG", registry_count)
            f.write(f"INSERT INTO ClubSeasonRegistry VALUES ({escape_sql(rid)}, {escape_sql(season)}, {escape_sql(cm_obj['cid'])}, {escape_sql(cm_obj['mid'])});\n")
            registry_count += 1

    # ClubMatch & Trophy
    match_count = 1
    trophy_counters = {}
    for i in range(50):
        if len(ids["club"]) < 2:
            break
        home_club_obj, away_club_obj = random.sample(ids["club"], 2)
        home_cid = home_club_obj['id']
        away_cid = away_club_obj['id']
        
        # Find managers for these clubs
        home_manager = None
        away_manager = None
        for cm in ids["club_manager"]:
            if cm['cid'] == home_cid:
                home_manager = cm['mid']
            if cm['cid'] == away_cid:
                away_manager = cm['mid']
        
        if not home_manager or not away_manager:
            continue
            
        mid = get_id("H", "MATCH", match_count)
        match_date = random_date_in_years(2022, 2025)
        
        home_score = random.randint(0, 5)
        away_score = random.randint(0, 5)
        
        if home_score > away_score:
            result = 'Home Win'
            winner_manager = home_manager
            winner_club = home_cid
        elif away_score > home_score:
            result = 'Away Win'
            winner_manager = away_manager
            winner_club = away_cid
        else:
            result = 'Draw'
            winner_manager = None
            winner_club = None
        
        attendance = random.randint(5000, 80000)
        
        f.write(f"INSERT INTO ClubMatch VALUES ({escape_sql(mid)}, {escape_sql(home_cid)}, {escape_sql(away_cid)}, {escape_sql(home_manager)}, {escape_sql(away_manager)}, {escape_sql(match_date)}, {home_score}, {away_score}, {escape_sql(result)}, {attendance});\n")
        
        if result != 'Draw' and winner_club:
            trophy_number = trophy_counters.get(winner_club, 0) + 1
            trophy_counters[winner_club] = trophy_number
            trophy_type = random.choice(["League Title", "Cup Trophy", "Super Cup"])
            f.write(
                f"INSERT IGNORE INTO Trophy VALUES ({escape_sql(winner_club)}, {trophy_number}, {escape_sql(match_date)}, {escape_sql(winner_manager)}, {escape_sql(trophy_type)});\n"
            )
        
        match_count += 1

    # TournamentEntry & TournamentMatch
    total_matches = 0
    for tourn in ids["tournament"]:
        tourn_id = tourn["id"]
        t_start = tourn["start"]
        t_end = tourn["end"]
        start_dt = datetime.date.fromisoformat(t_start)
        end_dt = datetime.date.fromisoformat(t_end)
        participants = random.sample(ids["manager"], min(32, len(ids["manager"])))
        
        entry_window_start = start_dt - datetime.timedelta(days=30)
        for p in participants:
            entry_date = random_date_between(entry_window_start, start_dt)
            f.write(f"INSERT IGNORE INTO TournamentEntry VALUES ({escape_sql(tourn_id)}, {escape_sql(p)}, {escape_sql(entry_date)});\n")
        
        match_number = 1
        num_rounds = random.randint(4, 6)
        for round_no in range(1, num_rounds + 1):
            matches_this_round = random.randint(18, 32)
            for _ in range(matches_this_round):
                if total_matches >= NUM_MATCHES:
                    break
                if len(participants) < 2:
                    break
                m1, m2 = random.sample(participants, 2)
                
                score1 = random.randint(0, 5)
                score2 = random.randint(0, 5)
                
                if score1 > score2:
                    winner = m1
                elif score2 > score1:
                    winner = m2
                else:
                    winner = random.choice([m1, m2])
                
                match_date = random_date_between(start_dt, end_dt)
                f.write(
                    f"INSERT INTO TournamentMatch VALUES ("
                    f"{escape_sql(tourn_id)}, {match_number}, {escape_sql(m1)}, {escape_sql(m2)}, "
                    f"{escape_sql(winner)}, {escape_sql(match_date)}, {round_no}, {score1}, {score2});\n"
                )
                match_number += 1
                total_matches += 1
            if total_matches >= NUM_MATCHES:
                break
        if total_matches >= NUM_MATCHES:
            break

    # PlayerStatistics
    stat_count = 1
    for player_id in ids["player"][:100]:  # First 100 players get stats
        for season_id in ids["season"][:3]:  # First 3 seasons
            stat_id = get_id("X", "STAT", stat_count)
            goals = random.randint(0, 30)
            assists = random.randint(0, 20)
            yellow_cards = random.randint(0, 8)
            red_cards = random.randint(0, 2)
            minutes_played = random.randint(500, 3000)
            matches_played = random.randint(10, 38)
            
            f.write(f"INSERT INTO PlayerStatistics VALUES ({escape_sql(stat_id)}, {escape_sql(player_id)}, {escape_sql(season_id)}, {goals}, {assists}, {yellow_cards}, {red_cards}, {minutes_played}, {matches_played});\n")
            stat_count += 1

    # Transfer
    transfer_count = 1
    for _ in range(50):  # 50 random transfers
        player_id = random.choice(ids["player"])
        from_manager = random.choice(ids["manager"])
        to_manager = random.choice(ids["manager"])
        
        if from_manager == to_manager:
            continue
            
        transfer_id = get_id("F", "TRANSFER", transfer_count)
        transfer_date = random_date_in_years(2020, 2025)
        transfer_fee = round(random.uniform(1000000, 100000000), 2)
        
        f.write(f"INSERT INTO Transfer VALUES ({escape_sql(transfer_id)}, {escape_sql(player_id)}, {escape_sql(from_manager)}, {escape_sql(to_manager)}, {escape_sql(transfer_date)}, {transfer_fee});\n")
        transfer_count += 1

    f.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")

print(f"Successfully generated {FILE_NAME} for Football League Management System with all tables populated.")
