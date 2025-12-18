import pymysql
import re
import datetime

# =============================================================================
# SECURITY & VALIDATION HELPER
# =============================================================================

def validate_identifier(identifier):
    """
    Security Check: Prevents SQL Injection in table/column names.
    Ensures the string contains only alphanumeric characters and underscores.
    """
    if not identifier:
        raise ValueError("Identifier cannot be empty.")
    # Strict regex: Only letters, numbers, and underscores allowed
    if not re.match(r'^[a-zA-Z0-9_]+$', identifier):
        raise ValueError(f"Security Alert: Invalid identifier detected: {identifier}")
    return identifier

# =============================================================================
# CONNECTION & ID GENERATION
# =============================================================================

def get_db_connection(host, user, password, db_name):
    """Establishes a connection to the MySQL database."""
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        return connection
    except pymysql.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def increment_alpha_part(alpha_str):
    chars = list(alpha_str)
    i = len(chars) - 1
    while i >= 0:
        if chars[i] == 'Z':
            chars[i] = 'A'
            i -= 1
        else:
            chars[i] = chr(ord(chars[i]) + 1)
            return "".join(chars)
    return 'A' + "".join(chars)

def get_next_id(connection, table_name, id_column, prefix):
    """
    Generates the next ID. 
    SECURE: Validates table/column names, Parameterizes the LIKE clause.
    """
    # 1. Validate Identifiers (Cannot be parameterized)
    clean_table = validate_identifier(table_name)
    clean_col = validate_identifier(id_column)

    try:
        with connection.cursor() as cursor:
            # 2. Parameterize Values (%s)
            sql = f"SELECT {clean_col} FROM {clean_table} WHERE {clean_col} LIKE %s ORDER BY {clean_col} DESC LIMIT 1"
            cursor.execute(sql, (f"{prefix}%",))
            result = cursor.fetchone()

            if not result:
                return f"{prefix}AAA001"
            
            current_id = result[clean_col]
            match = re.search(r'([A-Z]+)(\d{3})$', current_id[len(prefix):])
            
            if not match:
                return f"{prefix}AAA001"

            alpha_part = match.group(1)
            number_part = int(match.group(2))
            
            next_number = number_part + 1
            next_alpha = alpha_part
            
            if next_number > 999:
                next_number = 1
                next_alpha = increment_alpha_part(alpha_part)
            
            return f"{prefix}{next_alpha}{next_number:03d}"
            
    except pymysql.Error as e:
        print(f"Error generating ID: {e}")
        return None
    except ValueError as ve:
        print(ve)
        return None

# =============================================================================
# VIEW, SEARCH & RECENT FUNCTIONALITY
# =============================================================================

def get_all_tables(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            return [list(row.values())[0] for row in cursor.fetchall()]
    except pymysql.Error as e:
        print(f"Error fetching tables: {e}")
        return []

def get_text_columns(conn, table_name):
    # Validate table name before passing to query
    try:
        clean_table = validate_identifier(table_name)
        with conn.cursor() as cursor:
            sql = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = %s 
                AND data_type IN ('char', 'varchar', 'text', 'mediumtext', 'longtext', 'enum')
            """
            cursor.execute(sql, (clean_table,))
            rows = cursor.fetchall()
            return [row.get('COLUMN_NAME') or row.get('column_name') for row in rows]
            
    except pymysql.Error as e:
        print(f"Error fetching columns for {table_name}: {e}")
        return []
    except ValueError as ve:
        print(ve)
        return []


def get_searchable_columns(conn, table_name):
    """Return list of (column_name, data_type) for columns we can search across.
    This includes text, numeric and date/time types so the application can
    decide whether to use LIKE or equality comparisons based on the search term.
    """
    try:
        clean_table = validate_identifier(table_name)
        with conn.cursor() as cursor:
            sql = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = %s
            """
            cursor.execute(sql, (clean_table,))
            rows = cursor.fetchall()
            return [(row.get('COLUMN_NAME') or row.get('column_name'), (row.get('DATA_TYPE') or row.get('data_type')).lower()) for row in rows]
    except pymysql.Error as e:
        print(f"Error fetching searchable columns for {table_name}: {e}")
        return []
    except ValueError as ve:
        print(ve)
        return []

def view_table(conn, table_name, limit=100):
    try:
        clean_table = validate_identifier(table_name)
        with conn.cursor() as cursor:
            # Table name is validated f-string, Limit is parameterized
            sql = f"SELECT * FROM {clean_table} LIMIT %s"
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
    except (pymysql.Error, ValueError) as e:
        print(f"Error viewing table: {e}")
        return []

def search_table(conn, table_name, search_term):
    try:
        clean_table = validate_identifier(table_name)

        # Retrieve searchable columns and types
        cols = get_searchable_columns(conn, clean_table)

        if not cols:
            return []

        # Attempt to interpret search term as int/float/date to enable numeric/date searches
        is_int = False
        is_float = False
        is_date = False
        num_val = None
        date_val = None
        try:
            num_val = int(search_term)
            is_int = True
        except Exception:
            try:
                num_val = float(search_term)
                is_float = True
            except Exception:
                num_val = None

        # parse date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS or YYYY)
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y"):
            try:
                dt = datetime.datetime.strptime(search_term, fmt)
                is_date = True
                # normalize to YYYY-MM-DD for DATE comparisons; if format was year only, keep year
                date_val = dt.date().isoformat() if fmt != "%Y" else dt.year
                break
            except Exception:
                continue

        clauses = []
        params = []

        text_types = {'char', 'varchar', 'text', 'mediumtext', 'longtext', 'enum'}
        numeric_types = {'int', 'bigint', 'smallint', 'mediumint', 'decimal', 'float', 'double', 'tinyint'}
        date_types = {'date', 'datetime', 'timestamp', 'year', 'time'}

        for col, dtype in cols:
            try:
                clean_col = validate_identifier(col)
            except ValueError:
                continue

            if dtype in text_types:
                clauses.append(f"LOWER({clean_col}) LIKE LOWER(%s)")
                params.append(f"%{search_term}%")

            if dtype in numeric_types and (is_int or is_float):
                clauses.append(f"{clean_col} = %s")
                params.append(num_val)

            if dtype in date_types and is_date:
                # If search was year-only, compare YEAR(), else DATE()
                if isinstance(date_val, int):
                    clauses.append(f"YEAR({clean_col}) = %s")
                    params.append(date_val)
                else:
                    clauses.append(f"DATE({clean_col}) = %s")
                    params.append(date_val)

        if not clauses:
            return []

        where_clause = " OR ".join(clauses)
        sql = f"SELECT * FROM {clean_table} WHERE {where_clause}"

        with conn.cursor() as cursor:
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()

    except (pymysql.Error, ValueError) as e:
        print(f"Error searching table: {e}")
        return []

def search_global(conn, search_term):
    tables = get_all_tables(conn)
    results = {}
    for table in tables:
        matches = search_table(conn, table, search_term)
        if matches:
            results[table] = matches
    return results

def get_recent_records(conn, table_name, pk_col=None, limit=5):
    try:
        clean_table = validate_identifier(table_name)
        with conn.cursor() as cursor:
            if pk_col:
                clean_pk = validate_identifier(pk_col)
                sql = f"SELECT * FROM {clean_table} ORDER BY {clean_pk} DESC LIMIT %s"
            else:
                sql = f"SELECT * FROM {clean_table} LIMIT %s"
                
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
    except (pymysql.Error, ValueError) as e:
        print(f"Error fetching recent records: {e}")
        return []

# =============================================================================
# UPDATE & DELETE FUNCTIONALITY (SECURE)
# =============================================================================

def update_record(conn, table_name, pk_dict, updates_dict):
    if not updates_dict or not pk_dict:
        return False

    try:
        clean_table = validate_identifier(table_name)
        
        # Validate Column Names (Identifiers)
        clean_set_cols = [validate_identifier(col) for col in updates_dict.keys()]
        clean_pk_cols = [validate_identifier(col) for col in pk_dict.keys()]

        # Build Query Strings
        set_clauses = [f"{col} = %s" for col in clean_set_cols]
        set_str = ", ".join(set_clauses)
        
        where_clauses = [f"{col} = %s" for col in clean_pk_cols]
        where_str = " AND ".join(where_clauses)

        sql = f"UPDATE {clean_table} SET {set_str} WHERE {where_str}"
        
        # Combine Values into Tuple
        params = tuple(list(updates_dict.values()) + list(pk_dict.values()))
        
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return True # Return True even if 0 rows updated (query succeeded)
            
    except (pymysql.Error, ValueError) as e:
        print(f"Error updating record: {e}")
        return False

def delete_record(conn, table_name, pk_dict):
    if not pk_dict:
        return False

    try:
        clean_table = validate_identifier(table_name)
        clean_pk_cols = [validate_identifier(col) for col in pk_dict.keys()]

        where_clauses = [f"{col} = %s" for col in clean_pk_cols]
        where_str = " AND ".join(where_clauses)
        
        sql = f"DELETE FROM {clean_table} WHERE {where_str}"
        params = tuple(pk_dict.values())
        
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return True
            
    except pymysql.Error as e:
        if e.args[0] == 1451:
            print("Cannot delete: This record is referenced by other tables.")
        else:
            print(f"Error deleting record: {e}")
        return False
    except ValueError as ve:
        print(ve)
        return False

# =============================================================================
# COMPLEX RELATIONSHIP QUERIES (Static SQL is safe)
# =============================================================================

def get_league_management_report(conn):
    sql = """
        SELECT L.league_name, LS.theme, T.tournament_name, C.club_name
        FROM League L
        JOIN LeagueSeason LS ON L.league_id = LS.league_id
        JOIN Tournament T ON LS.season_id = T.season_id
        JOIN City CT ON T.city_id = CT.city_id 
        JOIN Club C ON CT.city_id = C.city_id
        ORDER BY L.league_name, LS.year;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

def get_club_assignments_report(conn):
    sql = """
        SELECT LS.year, LS.theme, L.league_name, C.club_name, M.name
        FROM ClubSeasonRegistry CSR
        JOIN LeagueSeason LS ON CSR.season_id = LS.season_id
        JOIN Club C ON CSR.club_id = C.club_id
        JOIN ClubManager CM ON CSR.manager_id = CM.manager_id
        JOIN Manager M ON CM.manager_id = M.manager_id
        JOIN City CT ON C.city_id = CT.city_id
        JOIN League L ON CT.league_id = L.league_id
        ORDER BY LS.year DESC, L.league_name;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

def get_player_skills_report(conn):
    sql = """
        SELECT P.player_name, A.archetype_name, S.skill_name, S.effect_description
        FROM Player P
        JOIN PlayerArchetype A ON P.archetype_id = A.archetype_id
        JOIN PlayerArchetypeSkill PAS ON A.archetype_id = PAS.archetype_id
        JOIN Skill S ON PAS.skill_id = S.skill_id
        LIMIT 50;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

def get_manager_performance_sheet(conn, limit=15):
    sql = """
        SELECT 
            C.club_name,
            CM.manager_id,
            M.manager_id AS opponent_manager_id,
            M.name AS opponent_name,
            COUNT(CH.match_id) AS matches_played,
            SUM(CASE WHEN CH.result = 'Home Win' THEN 1 ELSE 0 END) AS home_wins,
            SUM(CASE WHEN CH.result = 'Away Win' THEN 1 ELSE 0 END) AS away_wins,
            ROUND(
                SUM(CASE WHEN CH.result = 'Home Win' THEN 1 ELSE 0 END) / NULLIF(COUNT(CH.match_id), 0),
                2
            ) AS win_rate,
            GROUP_CONCAT(DISTINCT CONCAT(A.archetype_name, ' (', COALESCE(POS.position_name, 'Unknown'), ')')
                         ORDER BY A.archetype_name SEPARATOR ', ') AS signature_players
        FROM ClubMatch CH
        JOIN Club C ON CH.home_club_id = C.club_id
        JOIN ClubManager CM ON CH.home_manager_id = CM.manager_id
        JOIN Manager M ON CH.away_manager_id = M.manager_id
        LEFT JOIN Player P ON P.manager_id = M.manager_id
        LEFT JOIN PlayerArchetype A ON P.archetype_id = A.archetype_id
        LEFT JOIN Position POS ON A.primary_position_id = POS.position_id
        GROUP BY C.club_name, CM.manager_id, M.manager_id, M.name
        ORDER BY matches_played DESC, win_rate DESC
        LIMIT %s;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET SESSION group_concat_max_len = 4096")
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

def get_tournament_snapshot(conn):
    sql = """
        WITH archetype_usage AS (
            SELECT 
                T.tournament_id,
                T.tournament_name,
                T.start_date,
                A.archetype_name,
                COUNT(*) AS usage_count,
                ROW_NUMBER() OVER (PARTITION BY T.tournament_id ORDER BY COUNT(*) DESC) AS rank_in_tournament
            FROM Tournament T
            JOIN TournamentEntry TE ON T.tournament_id = TE.tournament_id
            JOIN Player P ON P.manager_id = TE.manager_id
            JOIN PlayerArchetype A ON P.archetype_id = A.archetype_id
            WHERE T.start_date >= CURDATE()
            GROUP BY T.tournament_id, T.tournament_name, T.start_date, A.archetype_name
        )
        SELECT tournament_name, start_date, archetype_name, usage_count, rank_in_tournament
        FROM archetype_usage
        WHERE rank_in_tournament <= 5
        ORDER BY start_date, rank_in_tournament;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

def get_underrated_manager_report(conn):
    sql = """
        WITH match_stats AS (
            SELECT manager_id,
                   SUM(win_flag) AS wins,
                   COUNT(*) AS matches_played
            FROM (
                SELECT manager1_id AS manager_id,
                       CASE WHEN winner_id = manager1_id THEN 1 ELSE 0 END AS win_flag
                FROM TournamentMatch
                UNION ALL
                SELECT manager2_id AS manager_id,
                       CASE WHEN winner_id = manager2_id THEN 1 ELSE 0 END AS win_flag
                FROM TournamentMatch
            ) s
            WHERE manager_id IS NOT NULL
            GROUP BY manager_id
        ),
        tour_counts AS (
            SELECT manager_id, COUNT(*) AS tournaments_entered
            FROM TournamentEntry
            GROUP BY manager_id
        )
        SELECT 
            M.manager_id,
            M.name,
            COALESCE(MS.wins, 0) AS wins,
            COALESCE(MS.matches_played, 0) AS matches_played,
            COALESCE(TC.tournaments_entered, 0) AS tournaments_entered,
            ROUND(COALESCE(MS.wins, 0) / NULLIF(COALESCE(MS.matches_played, 0), 0), 3) AS win_ratio
        FROM Manager M
        LEFT JOIN match_stats MS ON M.manager_id = MS.manager_id
        LEFT JOIN tour_counts TC ON M.manager_id = TC.manager_id
        WHERE COALESCE(MS.matches_played, 0) >= 10
          AND COALESCE(MS.wins, 0) / NULLIF(COALESCE(MS.matches_played, 0), 0) >= 0.6
          AND COALESCE(TC.tournaments_entered, 0) <= 3
        ORDER BY win_ratio DESC, tournaments_entered ASC
        LIMIT 25;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

def get_league_power_report(conn):
    sql = """
        WITH match_wins AS (
            SELECT M.league_id, COUNT(*) AS match_wins
            FROM TournamentMatch TM
            JOIN Manager M ON TM.winner_id = M.manager_id
            GROUP BY M.league_id
        ),
        trophy_totals AS (
            SELECT L.league_id, COUNT(*) AS trophies_awarded
            FROM Trophy TR
            JOIN Club C ON TR.club_id = C.club_id
            JOIN City CT ON C.city_id = CT.city_id
            JOIN League L ON CT.league_id = L.league_id
            GROUP BY L.league_id
        ),
        tournament_hosting AS (
            SELECT L.league_id, COUNT(DISTINCT T.tournament_id) AS tournaments_hosted
            FROM League L
            JOIN City CT ON CT.league_id = L.league_id
            JOIN Tournament T ON T.city_id = CT.city_id
            GROUP BY L.league_id
        )
        SELECT 
            L.league_name,
            COALESCE(MW.match_wins, 0) AS match_wins,
            COALESCE(TT.trophies_awarded, 0) AS trophies_awarded,
            COALESCE(TH.tournaments_hosted, 0) AS tournaments_hosted
        FROM League L
        LEFT JOIN match_wins MW ON L.league_id = MW.league_id
        LEFT JOIN trophy_totals TT ON L.league_id = TT.league_id
        LEFT JOIN tournament_hosting TH ON L.league_id = TH.league_id
        ORDER BY match_wins DESC, tournaments_hosted DESC;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

def get_archetype_mvp_report(conn, limit=15):
    sql = """
        SELECT 
            A.archetype_name,
            COUNT(*) AS registered_count,
            ROUND(AVG(P.overall_rating), 2) AS avg_rating,
            MAX(P.overall_rating) AS max_rating
        FROM Player P
        JOIN PlayerArchetype A ON P.archetype_id = A.archetype_id
        GROUP BY A.archetype_id, A.archetype_name
        HAVING COUNT(*) >= 5
        ORDER BY avg_rating DESC, registered_count DESC
        LIMIT %s;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Report Error: {e}")
        return []

# =============================================================================
# PARAMETERIZED QUERY LIBRARY
# =============================================================================

def query_managers_with_min_wins(conn, tournament_name, min_wins=50):
    sql = """
        SELECT 
            M.manager_id,
            M.name,
            TE.registration_date,
            COALESCE(W.total_wins, 0) AS total_wins
        FROM TournamentEntry TE
        JOIN Tournament T ON TE.tournament_id = T.tournament_id
        JOIN Manager M ON TE.manager_id = M.manager_id
        LEFT JOIN (
            SELECT winner_id, COUNT(*) AS total_wins
            FROM TournamentMatch
            WHERE winner_id IS NOT NULL
            GROUP BY winner_id
        ) W ON M.manager_id = W.winner_id
        WHERE T.tournament_name = %s
          AND COALESCE(W.total_wins, 0) > %s
        ORDER BY total_wins DESC;
    """
    try:
        with conn.cursor() as cursor:
            try:
                print("Executing SQL (Selection):\n" + sql.strip())
                print("Params:", (tournament_name, min_wins))
            except Exception:
                pass
            cursor.execute(sql, (tournament_name, min_wins))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
        return []

def query_players_by_manager(conn, manager_id):
    sql = """
        SELECT P.player_id, P.player_name, P.overall_rating, A.archetype_name
        FROM Player P
        JOIN PlayerArchetype A ON P.archetype_id = A.archetype_id
        WHERE P.manager_id = %s
        ORDER BY P.overall_rating DESC;
    """
    try:
        with conn.cursor() as cursor:
            try:
                print("Executing SQL (Projection):\n" + sql.strip())
                print("Params:", (manager_id,))
            except Exception:
                pass
            cursor.execute(sql, (manager_id,))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
        return []

def query_average_rating_for_tournament(conn, tournament_name):
    sql = """
        SELECT 
            T.tournament_name,
            ROUND(AVG(P.overall_rating), 2) AS average_rating,
            COUNT(*) AS player_count
        FROM Tournament T
        JOIN TournamentEntry TE ON T.tournament_id = TE.tournament_id
        JOIN Player P ON P.manager_id = TE.manager_id
        WHERE T.tournament_name = %s
        GROUP BY T.tournament_id, T.tournament_name;
    """
    try:
        with conn.cursor() as cursor:
            try:
                print("Executing SQL (Aggregate):\n" + sql.strip())
                print("Params:", (tournament_name,))
            except Exception:
                pass
            cursor.execute(sql, (tournament_name,))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
        return []

def query_archetype_by_prefix(conn, prefix):
    sql = """
        SELECT archetype_id, archetype_name, base_pace, base_shooting, base_passing
        FROM PlayerArchetype
        WHERE archetype_name LIKE %s
        ORDER BY archetype_name;
    """
    try:
        with conn.cursor() as cursor:
            try:
                print("Executing SQL (Search):\n" + sql.strip())
                print("Params:", (f"{prefix}%",))
            except Exception:
                pass
            cursor.execute(sql, (f"{prefix}%",))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
        return []

def query_trophy_leaderboard(conn, limit=10):
    sql = """
        SELECT 
            M.manager_id,
            M.name,
            COUNT(*) AS trophies_collected,
            COUNT(DISTINCT TR.club_id) AS clubs_conquered
        FROM Trophy TR
        JOIN Manager M ON TR.manager_id = M.manager_id
        GROUP BY M.manager_id, M.name
        ORDER BY trophies_collected DESC, clubs_conquered DESC
        LIMIT %s;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
        return []

def query_elite_players(conn, min_rating=85):
    sql = """
        SELECT 
            P.player_id,
            P.player_name,
            A.archetype_name,
            P.overall_rating,
            M.name AS manager_name
        FROM Player P
        JOIN PlayerArchetype A ON P.archetype_id = A.archetype_id
        JOIN Manager M ON P.manager_id = M.manager_id
        WHERE P.overall_rating >= %s
        ORDER BY P.overall_rating DESC
        LIMIT 50;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (min_rating,))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
        return []

def query_active_league_insights(conn):
    sql = """
        SELECT 
            L.league_name,
            COUNT(DISTINCT T.tournament_id) AS tournaments_hosted,
            COUNT(DISTINCT TE.manager_id) AS visiting_managers,
            ROUND(AVG(LS.year), 1) AS average_season_year
        FROM League L
        LEFT JOIN City CT ON CT.league_id = L.league_id
        LEFT JOIN Tournament T ON T.city_id = CT.city_id
        LEFT JOIN TournamentEntry TE ON TE.tournament_id = T.tournament_id
        LEFT JOIN LeagueSeason LS ON T.season_id = LS.season_id
        GROUP BY L.league_id, L.league_name
        ORDER BY tournaments_hosted DESC, visiting_managers DESC;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Query Error: {e}")
        return []

# =============================================================================
# MATCH HELPERS
# =============================================================================

def validate_match_winner(manager1_id, manager2_id, winner_id):
    if winner_id is None:
        return True
    if manager1_id is None and manager2_id is None:
        raise ValueError("Both managers are None")
    if winner_id != manager1_id and winner_id != manager2_id:
        raise ValueError("Winner must be one of the participants")
    return True

def insert_match(conn, match_record):
    required = ['tournament_id', 'match_number']
    for k in required:
        if k not in match_record:
            return False

    # Validation Logic
    try:
        validate_match_winner(match_record.get('manager1_id'), 
                              match_record.get('manager2_id'), 
                              match_record.get('winner_id'))
    except ValueError as e:
        print(e)
        return False

    # Secure Insert Logic
    cols = [validate_identifier(k) for k in match_record.keys()]
    vals = list(match_record.values())
    placeholders = ["%s"] * len(cols)

    sql = f"INSERT INTO TournamentMatch ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, vals)
            return True
    except pymysql.Error as e:
        print(f"Error inserting match: {e}")
        return False

def update_match_winner(conn, tournament_id, match_number, new_winner_id):
    try:
        with conn.cursor() as cursor:
            # Get participants
            cursor.execute(
                "SELECT manager1_id, manager2_id FROM TournamentMatch WHERE tournament_id = %s AND match_number = %s",
                (tournament_id, match_number)
            )
            row = cursor.fetchone()
            if not row:
                return False

            validate_match_winner(row['manager1_id'], row['manager2_id'], new_winner_id)

            # Secure Update
            cursor.execute(
                "UPDATE TournamentMatch SET winner_id = %s WHERE tournament_id = %s AND match_number = %s",
                (new_winner_id, tournament_id, match_number)
            )
            return cursor.rowcount > 0
    except (pymysql.Error, ValueError) as e:
        print(f"Error updating winner: {e}")
        return False
