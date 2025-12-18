# Football League Management System

---

## Project Overview

<span style="color:#2b6cb0;font-weight:bold;">Football League Management System</span> is a comprehensive, terminal-based application for managing, querying, and analyzing a relational database of football tournaments, clubs, managers, players, and related entities. Developed in Python using the Textual TUI framework, it provides a robust, secure, and visually appealing interface for all database operations, analytics, and data integrity enforcement.

---

## Features and Functionality

### 1. Table Browser and CRUD Operations

<span style="color:#3182ce;font-weight:bold;">Table Listing and Browsing</span>  
All tables in the database are listed in a sidebar. Selecting a table displays its contents in a scrollable, filterable data grid. By default, the first 100 rows are shown for performance. Table-specific search returns all matching records, regardless of count.

<span style="color:#3182ce;font-weight:bold;">Add, Update, Delete Records</span>  
Users can add new records, update existing ones, or delete records using auto-generated forms that respect schema constraints. All operations use parameterized SQL (`INSERT`, `UPDATE`, `DELETE`) to ensure security and correctness.

<span style="color:#3182ce;font-weight:bold;">Table Navigation and Cell-to-Cell Jumping</span>  
Navigate seamlessly through table cells using keyboard shortcuts (arrow keys: <kbd>j</kbd>, <kbd>k</kbd>, <kbd>h</kbd>, <kbd>l</kbd> or arrow keys). The active cell is highlighted for clarity. Selecting a foreign key cell allows instant navigation ("table junction") to the referenced table and record, making relational exploration intuitive and efficient.

<span style="color:#3182ce;font-weight:bold;">Referential Integrity and Constraints</span>  
All foreign key relationships are enforced at the database level. Attempts to insert or update with invalid references are rejected. Cascading actions (`ON DELETE CASCADE`, `ON UPDATE CASCADE`) are used where appropriate to maintain data consistency. Unique constraints and check constraints are enforced as defined in the schema.

### 2. Search and Filtering

<span style="color:#38a169;font-weight:bold;">Table Search</span>  
Each table view includes a search bar for filtering records by any field. Results are not limited to the initial 100-row display.  
<span style="color:#718096;">SQL: <code>SELECT ... WHERE ... LIKE ...</code></span>

<span style="color:#38a169;font-weight:bold;">Global Search</span>  
A dedicated tab allows searching for a keyword across all tables and fields. Results display the table name and matching record details.  
<span style="color:#718096;">SQL: Iterates over all tables with <code>SELECT ... WHERE ... LIKE ...</code> for each.</span>

### 3. Reports Tab

<span style="color:#d69e2e;font-weight:bold;">Predefined Analytical Reports</span>  
The Reports tab provides a set of curated, complex SQL reports (e.g., top managers by win percentage, league power index, player archetype MVP leaderboard). Users select a report and view results with a single action. Reports use advanced SQL features such as <code>JOIN</code>, <code>GROUP BY</code>, <code>WITH</code> (CTEs), and aggregation. Results can be filtered using a search bar within the report view.

### 4. Queries Tab

<span style="color:#805ad5;font-weight:bold;">Parameterized Queries</span>  
The Queries tab offers a set of interactive queries where users provide input parameters (e.g., minimum wins, manager ID, tournament name). All queries are parameterized to prevent SQL injection and ensure safe execution. The exact SQL statement and parameters are displayed after each query for transparency.

**Example Query Usage:**

1. **Managers with more than N wins in a tournament**
   - Enter a tournament name and minimum win count, then run the query to see all qualifying managers.
   - SQL: Uses <code>SELECT ... WHERE tournament_name = ? AND total_wins > ?</code>

2. **Players owned by a specific manager**
   - Enter a manager ID to list all players registered to that manager.
   - SQL: Uses <code>SELECT ... WHERE manager_id = ?</code>

3. **Average rating of players in a tournament**
   - Enter a tournament name to compute the average rating of all players used in that tournament.
   - SQL: Uses <code>SELECT ... AVG(overall_rating) ... WHERE tournament_name = ?</code>

4. **Trophy leaderboard (top N managers by trophies)**
   - Enter a number N to see the top N managers with the most trophies.
   - SQL: Uses <code>SELECT ... ORDER BY trophies_collected DESC LIMIT ?</code>

### 5. Data Integrity and Schema Enforcement

<span style="color:#e53e3e;font-weight:bold;">Foreign Keys</span>  
All relationships between tables are enforced using foreign key constraints. Invalid references are not permitted.

<span style="color:#e53e3e;font-weight:bold;">Cascading Actions</span>  
Where specified, deleting or updating a parent record cascades changes to dependent records (e.g., deleting a manager removes their players if <code>ON DELETE CASCADE</code> is set).

<span style="color:#e53e3e;font-weight:bold;">Unique and Check Constraints</span>  
Unique constraints ensure that key fields (such as IDs and emails) are not duplicated. Check constraints enforce value ranges and formats (e.g., overall_rating between 1 and 100, ID patterns).

<span style="color:#e53e3e;font-weight:bold;">Composite Keys and Junction Tables</span>  
Many-to-many relationships are managed using composite primary keys in junction tables, ensuring uniqueness and referential integrity.

---

## Database Schema

### Level 0 (Independent Tables)
- **League**: Football leagues (Premier League, La Liga, etc.)
- **Position**: Player positions (Goalkeeper, Defender, Midfielder, Forward)
- **Skill**: Player skills (Pace, Dribbling, Shooting, etc.)

### Level 1 (Dependent on Level 0)
- **City**: Cities within leagues
- **SpecialMove**: Skill moves (Step-over, Rabona, Bicycle Kick)
- **PositionStrength/Weakness**: Position matchup relationships
- **PlayerArchetype**: Player types (Playmaker, Target Man, Sweeper)
- **Manager**: Manager/coach profiles
- **LeagueSeason**: Annual league seasons

### Level 2 (Dependent on Level 1)
- **PlayerArchetypeSkill**: Archetype-skill mappings
- **Club**: Football clubs with stadiums
- **ClubManager**: Manager profiles for clubs
- **Champion**: League champions
- **Player**: Individual players with contracts and ratings
- **Tournament**: Cup competitions (Champions League, FA Cup)

### Level 3 (Complex Relationships)
- **PlayerMove**: Special moves learned by players
- **ClubSeasonRegistry**: Club-manager assignments per season
- **ClubMatch**: Match records with scores and attendance
- **Trophy**: Trophies won by clubs
- **TrophyName**: Trophy names per club
- **TournamentEntry**: Tournament registrations
- **TournamentMatch**: Tournament matches with scores
- **PlayerStatistics**: Goals, assists, cards, minutes played
- **Transfer**: Player transfer history with fees

---

## Usage Instructions

### Connecting to the Database

On startup, the application prompts for database credentials (host, user, password, database name). Upon successful connection, the schema is loaded and all features become available.

### Table Operations

1. **Viewing Data:** Select a table from the sidebar to view its data. The first 100 rows are shown by default.

2. **Adding Records:** Press <kbd>a</kbd> or click "Add New". Fill in the form (IDs are auto-generated). Save to insert.

3. **Updating Records:** Select a row in the table, then press <kbd>u</kbd> or click "Update". Primary keys are locked by default but can be unlocked. Modify fields and save.

4. **Deleting Records:** Select a row, press <kbd>d</kbd> or click "Delete". Confirm the deletion. Note: Deletions respect foreign key constraints and may fail if the record is referenced elsewhere.

5. **Searching:** Use the filter bar below the table to search within the current table. Use the "Global Search" tab to search across all tables.

6. **Foreign Key Navigation:** Click on any foreign key value (marked with 🔗) to instantly jump to the referenced table and row.

### Keyboard Shortcuts

- <kbd>a</kbd>: Add new record
- <kbd>u</kbd>: Update selected record
- <kbd>d</kbd>: Delete selected record
- <kbd>r</kbd>: Refresh table
- <kbd>j</kbd>/<kbd>k</kbd>/<kbd>h</kbd>/<kbd>l</kbd>: Navigate table cells (Vim-style)
- <kbd>q</kbd>: Quit application
- <kbd>t</kbd>: Toggle dark/light theme

---

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- MySQL Server 8.0 or higher
- pip package manager

### Install Dependencies

```bash
pip install pymysql textual faker
```

### Database Setup

1. **Create the database schema:**
```bash
mysql -u root -p < schema.sql
```

2. **Generate and populate data:**
```bash
python pop_gen.py
mysql -u root -p football_league_db < populate.sql
```

3. **Run the TUI:**
```bash
python tui.py
```

---

## System Architecture

### Files

- **schema.sql**: Complete database schema with all tables, constraints, and triggers
- **pop_gen.py**: Data generation script creating realistic test data
- **populate.sql**: Generated SQL insert statements (auto-created by pop_gen.py)
- **db_utils.py**: Database utility functions with security-first design
- **tui.py**: Terminal user interface application

### Security Features

- **SQL Injection Prevention**: All identifiers validated with regex, all values parameterized
- **No Dynamic SQL**: Column/table names validated before use in queries
- **Constraint Enforcement**: Database-level constraints prevent invalid data
- **Referential Integrity**: Foreign keys enforce relationships
- **Transaction Safety**: Autocommit enabled with proper error handling

### Advanced Features

- **Auto-ID Generation**: Custom ID format `PREFIX[A-Z]{3,16}[0-9]{3}` with intelligent incrementing
- **Intelligent Search**: Supports text (LIKE), numeric (=), and date comparisons automatically
- **Foreign Key Jumping**: Click FK cells to navigate to referenced tables
- **Complex Reports**: Pre-built analytical queries using CTEs and window functions
- **Real-time Validation**: Form validation before database submission

---

## Data Model Highlights

### Player Management
- Players have archetypes (playing styles) with base stats
- Contract management with start/end dates and market values
- Special moves and skills per player
- Comprehensive statistics tracking (goals, assists, cards, minutes)

### Club & Manager System
- Clubs have home stadiums and founding years
- Managers assigned to clubs per season
- Manager specializations and preferred formations
- Trophy tracking with types and dates

### Match System
- Club matches with home/away scores and attendance
- Tournament matches with rounds and knockout stages
- Match result tracking (Win/Draw/Loss)
- Winner validation through database triggers

### Transfer System
- Complete transfer history with fees
- From/To manager tracking
- Transfer date recording
- Market value trends

---

## Sample Queries

### Top Scorers
```sql
SELECT P.player_name, SUM(PS.goals) AS total_goals
FROM Player P
JOIN PlayerStatistics PS ON P.player_id = PS.player_id
GROUP BY P.player_id, P.player_name
ORDER BY total_goals DESC
LIMIT 10;
```

### Club Trophy Count
```sql
SELECT C.club_name, COUNT(*) AS trophy_count
FROM Club C
JOIN Trophy T ON C.club_id = T.club_id
GROUP BY C.club_id, C.club_name
ORDER BY trophy_count DESC;
```

### Manager Win Rate
```sql
SELECT M.name, 
       COUNT(*) AS matches,
       SUM(CASE WHEN TM.winner_id = M.manager_id THEN 1 ELSE 0 END) AS wins,
       ROUND(SUM(CASE WHEN TM.winner_id = M.manager_id THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS win_rate
FROM Manager M
JOIN TournamentMatch TM ON M.manager_id IN (TM.manager1_id, TM.manager2_id)
GROUP BY M.manager_id, M.name
HAVING matches >= 10
ORDER BY win_rate DESC;
```

---

## Troubleshooting

### Connection Issues
- Verify MySQL server is running
- Check credentials (username, password)
- Ensure database exists: `SHOW DATABASES;`

### Data Not Showing
- Run `python pop_gen.py` to regenerate data
- Import populate.sql: `mysql -u root -p football_league_db < populate.sql`

### Permission Errors
- Grant user privileges: `GRANT ALL ON football_league_db.* TO 'user'@'localhost';`
- Flush privileges: `FLUSH PRIVILEGES;`

---

## Future Enhancements

- Match event tracking (substitutions, goals by player, cards by player)
- League standings and points calculation
- Player injury tracking
- Financial management (club budgets, wages)
- Youth academy system
- Loan system for players
- International tournaments (World Cup, Euro)
- Manager tactics and formation builder
- Live match simulation
- Data visualization and charts

---

## Credits

**Developed by**: Your Name  
**Framework**: Textual (Python TUI Framework)  
**Database**: MySQL 8.0  
**License**: MIT

---

## Contact

For issues, questions, or contributions, please contact [your-email@example.com]

---

**Note**: This system is designed for educational and demonstration purposes. It showcases advanced database design, secure Python programming, and modern terminal UI development.
