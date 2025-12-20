"""
Complete Premier League Data Builder for Soccer-AI

Adds:
1. All 18 PL clubs as proper club nodes
2. All stadiums with links
3. Comprehensive facts per team
4. Legendary players
5. Club rivalries
6. Manager history
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "soccer_ai_architecture_kg.db"


class PLBuilder:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH))
        self.cursor = self.conn.cursor()
        self.stats = {"nodes": 0, "edges": 0, "facts": 0}

    def add_node(self, name: str, node_type: str, description: str, properties: dict = None) -> int:
        """Add node, return node_id."""
        self.cursor.execute("SELECT node_id FROM kg_nodes WHERE LOWER(name) = LOWER(?)", (name,))
        existing = self.cursor.fetchone()
        if existing:
            return existing[0]

        props_json = json.dumps(properties or {})
        self.cursor.execute("""
            INSERT INTO kg_nodes (name, type, description, properties)
            VALUES (?, ?, ?, ?)
        """, (name, node_type, description, props_json))
        self.stats["nodes"] += 1
        return self.cursor.lastrowid

    def add_edge(self, from_id: int, to_id: int, relationship: str, properties: dict = None):
        """Add edge between nodes."""
        self.cursor.execute("""
            SELECT 1 FROM kg_edges WHERE from_node=? AND to_node=? AND relationship=?
        """, (from_id, to_id, relationship))
        if self.cursor.fetchone():
            return

        props_json = json.dumps(properties or {})
        self.cursor.execute("""
            INSERT INTO kg_edges (from_node, to_node, relationship, properties)
            VALUES (?, ?, ?, ?)
        """, (from_id, to_id, relationship, props_json))
        self.stats["edges"] += 1

    def add_fact(self, content: str, fact_type: str, entities: list, confidence: float = 0.9):
        """Add fact to KB."""
        self.cursor.execute("SELECT 1 FROM kb_facts WHERE content = ?", (content,))
        if self.cursor.fetchone():
            return

        self.cursor.execute("""
            INSERT INTO kb_facts (content, fact_type, confidence, source_type, related_entities)
            VALUES (?, ?, ?, 'curated', ?)
        """, (content, fact_type, confidence, json.dumps(entities)))
        self.stats["facts"] += 1

    def build_all(self):
        """Build complete PL data."""

        # =============================================
        # PREMIER LEAGUE CLUBS
        # =============================================
        clubs_data = {
            "Arsenal": {
                "founded": 1886,
                "nickname": "The Gunners",
                "stadium": "Emirates Stadium",
                "stadium_capacity": 60704,
                "titles": 13,
                "fa_cups": 14,
                "legends": ["Thierry Henry", "Dennis Bergkamp", "Patrick Vieira", "Tony Adams", "Ian Wright"],
                "rivals": ["Tottenham Hotspur", "Chelsea", "Manchester United"],
                "facts": [
                    "Arsenal went unbeaten for the entire 2003-04 Premier League season, earning the nickname 'The Invincibles'",
                    "Thierry Henry is Arsenal's all-time top scorer with 228 goals",
                    "Arsenal moved from Highbury to Emirates Stadium in 2006",
                    "Arsene Wenger managed Arsenal for 22 years (1996-2018), winning 3 Premier League titles",
                    "Arsenal won the league and cup double in 1971, 1998, and 2002",
                ]
            },
            "Chelsea": {
                "founded": 1905,
                "nickname": "The Blues",
                "stadium": "Stamford Bridge",
                "stadium_capacity": 40343,
                "titles": 6,
                "fa_cups": 8,
                "legends": ["Frank Lampard", "John Terry", "Didier Drogba", "Gianfranco Zola", "Peter Osgood"],
                "rivals": ["Tottenham Hotspur", "Arsenal", "West Ham United"],
                "facts": [
                    "Chelsea won their first Champions League in 2012, beating Bayern Munich on penalties",
                    "Frank Lampard is Chelsea's all-time top scorer with 211 goals",
                    "Chelsea won back-to-back Premier League titles under Jose Mourinho in 2005 and 2006",
                    "Roman Abramovich's takeover in 2003 transformed Chelsea into a European powerhouse",
                    "Didier Drogba scored in 4 FA Cup finals, winning all of them",
                ]
            },
            "Liverpool": {
                "founded": 1892,
                "nickname": "The Reds",
                "stadium": "Anfield",
                "stadium_capacity": 61276,
                "titles": 19,
                "fa_cups": 8,
                "legends": ["Steven Gerrard", "Kenny Dalglish", "Ian Rush", "Robbie Fowler", "Mohamed Salah"],
                "rivals": ["Manchester United", "Everton"],
                "facts": [
                    "Liverpool have won 6 European Cups/Champions League titles",
                    "The Miracle of Istanbul 2005: Liverpool came back from 3-0 down to beat AC Milan on penalties",
                    "Liverpool ended their 30-year league title drought in 2020 under Jurgen Klopp",
                    "Steven Gerrard made 710 appearances for Liverpool, scoring 186 goals",
                    "The Kop at Anfield is one of the most famous stands in world football",
                ]
            },
            "Manchester United": {
                "founded": 1878,
                "nickname": "The Red Devils",
                "stadium": "Old Trafford",
                "stadium_capacity": 74310,
                "titles": 20,
                "fa_cups": 13,
                "legends": ["George Best", "Bobby Charlton", "Eric Cantona", "Ryan Giggs", "Cristiano Ronaldo"],
                "rivals": ["Liverpool", "Manchester City", "Leeds United"],
                "facts": [
                    "Manchester United won the treble in 1999: Premier League, FA Cup, and Champions League",
                    "Sir Alex Ferguson managed United for 26 years (1986-2013), winning 38 trophies",
                    "The Munich air disaster of 1958 killed 8 players of the 'Busby Babes'",
                    "Wayne Rooney is United's all-time top scorer with 253 goals",
                    "The Class of '92 included Beckham, Scholes, Giggs, Neville brothers, and Butt",
                ]
            },
            "Manchester City": {
                "founded": 1880,
                "nickname": "The Citizens",
                "stadium": "Etihad Stadium",
                "stadium_capacity": 53400,
                "titles": 8,
                "fa_cups": 7,
                "legends": ["Sergio Aguero", "Vincent Kompany", "David Silva", "Colin Bell", "Yaya Toure"],
                "rivals": ["Manchester United"],
                "facts": [
                    "Sergio Aguero's 93:20 goal against QPR in 2012 won City their first title in 44 years",
                    "City won the treble in 2023: Premier League, FA Cup, and Champions League",
                    "Pep Guardiola has won 6 Premier League titles with Manchester City",
                    "Sergio Aguero is City's all-time top scorer with 260 goals",
                    "Manchester City won 4 consecutive Premier League titles from 2021 to 2024",
                ]
            },
            "Tottenham Hotspur": {
                "founded": 1882,
                "nickname": "Spurs",
                "stadium": "Tottenham Hotspur Stadium",
                "stadium_capacity": 62850,
                "titles": 2,
                "fa_cups": 8,
                "legends": ["Jimmy Greaves", "Glenn Hoddle", "Gary Lineker", "Harry Kane", "Ossie Ardiles"],
                "rivals": ["Arsenal"],
                "facts": [
                    "Tottenham were the first English club to win a European trophy (Cup Winners' Cup 1963)",
                    "Spurs won the Double in 1961, the first club to do so in the 20th century",
                    "Harry Kane became Spurs' all-time top scorer with 280 goals before leaving in 2023",
                    "The new Tottenham Hotspur Stadium opened in 2019, costing £1 billion",
                    "Jimmy Greaves scored 266 goals for Spurs, a club record for decades",
                ]
            },
            "Newcastle United": {
                "founded": 1892,
                "nickname": "The Magpies",
                "stadium": "St James' Park",
                "stadium_capacity": 52305,
                "titles": 4,
                "fa_cups": 6,
                "legends": ["Alan Shearer", "Jackie Milburn", "Peter Beardsley", "Kevin Keegan", "Malcolm Macdonald"],
                "rivals": ["Sunderland"],
                "facts": [
                    "Alan Shearer is Newcastle's all-time top scorer with 206 goals",
                    "Kevin Keegan's 'I would love it' rant in 1996 is iconic Premier League moment",
                    "Newcastle won 3 consecutive league titles in 1905, 1907, and 1909",
                    "The Tyne-Wear derby against Sunderland is one of English football's fiercest rivalries",
                    "St James' Park has been Newcastle's home since 1892",
                ]
            },
            "West Ham United": {
                "founded": 1895,
                "nickname": "The Hammers",
                "stadium": "London Stadium",
                "stadium_capacity": 62500,
                "titles": 0,
                "fa_cups": 3,
                "legends": ["Bobby Moore", "Geoff Hurst", "Martin Peters", "Paolo Di Canio", "Mark Noble"],
                "rivals": ["Chelsea", "Millwall", "Tottenham Hotspur"],
                "facts": [
                    "West Ham produced three members of England's 1966 World Cup winning team: Moore, Hurst, Peters",
                    "Bobby Moore captained both West Ham and England to their greatest triumphs",
                    "The club moved from Upton Park to London Stadium in 2016",
                    "Paolo Di Canio's scissor kick vs Wimbledon is considered one of the greatest PL goals",
                    "West Ham won the FA Cup in 1964, 1975, and 1980",
                ]
            },
            "Aston Villa": {
                "founded": 1874,
                "nickname": "The Villans",
                "stadium": "Villa Park",
                "stadium_capacity": 42657,
                "titles": 7,
                "fa_cups": 7,
                "legends": ["Peter Withe", "Dennis Mortimer", "Paul McGrath", "Dwight Yorke", "Gabriel Agbonlahor"],
                "rivals": ["Birmingham City", "West Bromwich Albion"],
                "facts": [
                    "Aston Villa were founding members of the Football League in 1888",
                    "Villa won the European Cup in 1982, beating Bayern Munich 1-0",
                    "Villa Park has hosted more FA Cup semi-finals than any other stadium",
                    "Villa have won 7 league titles, putting them in the top 6 historically",
                    "The Second City Derby against Birmingham City is one of England's oldest rivalries",
                ]
            },
            "Everton": {
                "founded": 1878,
                "nickname": "The Toffees",
                "stadium": "Goodison Park",
                "stadium_capacity": 39414,
                "titles": 9,
                "fa_cups": 5,
                "legends": ["Dixie Dean", "Alan Ball", "Neville Southall", "Tim Cahill", "Leighton Baines"],
                "rivals": ["Liverpool"],
                "facts": [
                    "Dixie Dean scored 60 league goals in the 1927-28 season, a record that still stands",
                    "Everton are one of only 6 clubs to have played every season in the top flight",
                    "The Merseyside Derby against Liverpool is one of football's greatest rivalries",
                    "Everton won 9 league titles, making them the 4th most successful English club historically",
                    "Goodison Park has been Everton's home since 1892",
                ]
            },
            "Leicester City": {
                "founded": 1884,
                "nickname": "The Foxes",
                "stadium": "King Power Stadium",
                "stadium_capacity": 32312,
                "titles": 1,
                "fa_cups": 1,
                "legends": ["Gary Lineker", "Peter Shilton", "Jamie Vardy", "Riyad Mahrez", "Kasper Schmeichel"],
                "rivals": ["Nottingham Forest", "Derby County"],
                "facts": [
                    "Leicester City won the 2015-16 Premier League at 5000-1 odds, the greatest underdog story in sports",
                    "Jamie Vardy scored in 11 consecutive Premier League games in 2015-16",
                    "Leicester won their first FA Cup in 2021, beating Chelsea 1-0",
                    "Claudio Ranieri led Leicester to their historic title, dubbed 'The Impossible Dream'",
                    "Gary Lineker, Match of the Day host, started his career at Leicester",
                ]
            },
            "Leeds United": {
                "founded": 1919,
                "nickname": "The Whites",
                "stadium": "Elland Road",
                "stadium_capacity": 37890,
                "titles": 3,
                "fa_cups": 1,
                "legends": ["Billy Bremner", "Jack Charlton", "Eddie Gray", "John Charles", "Gordon Strachan"],
                "rivals": ["Manchester United", "Chelsea"],
                "facts": [
                    "Don Revie's Leeds were one of the most successful English teams of the late 1960s/early 70s",
                    "Leeds reached the Champions League semi-final in 2001 under David O'Leary",
                    "The rivalry with Manchester United is known as the Roses Derby",
                    "Leeds went into administration in 2007 and had to rebuild from League One",
                    "Elland Road's atmosphere is considered one of the best in English football",
                ]
            },
            "Wolverhampton Wanderers": {
                "founded": 1877,
                "nickname": "Wolves",
                "stadium": "Molineux Stadium",
                "stadium_capacity": 32050,
                "titles": 3,
                "fa_cups": 4,
                "legends": ["Billy Wright", "Steve Bull", "Derek Dougan", "Raul Jimenez", "Matt Doherty"],
                "rivals": ["West Bromwich Albion", "Aston Villa"],
                "facts": [
                    "Wolves were one of England's most successful clubs in the 1950s",
                    "Billy Wright was England's first player to reach 100 caps",
                    "The Black Country Derby against West Brom is one of England's oldest rivalries",
                    "Wolves' historic floodlit games in the 1950s helped inspire European competition",
                    "Steve Bull scored 306 goals for Wolves, a club record",
                ]
            },
            "Crystal Palace": {
                "founded": 1905,
                "nickname": "The Eagles",
                "stadium": "Selhurst Park",
                "stadium_capacity": 25486,
                "titles": 0,
                "fa_cups": 0,
                "legends": ["Ian Wright", "Wilfried Zaha", "Jim Cannon", "Mark Bright", "Geoff Thomas"],
                "rivals": ["Brighton & Hove Albion"],
                "facts": [
                    "Crystal Palace reached the FA Cup final in 1990 and 2016",
                    "Ian Wright started his career at Palace before becoming an Arsenal legend",
                    "The rivalry with Brighton is known as the M23 Derby",
                    "Wilfried Zaha has been Palace's talisman for over a decade",
                    "Selhurst Park's atmosphere is famous for its passionate fanbase",
                ]
            },
            "Brighton & Hove Albion": {
                "founded": 1901,
                "nickname": "The Seagulls",
                "stadium": "Amex Stadium",
                "stadium_capacity": 31800,
                "titles": 0,
                "fa_cups": 0,
                "legends": ["Bobby Zamora", "Peter Ward", "Mark Lawrenson", "Lewis Dunk", "Pascal Gross"],
                "rivals": ["Crystal Palace"],
                "facts": [
                    "Brighton reached the 1983 FA Cup Final, drawing with Manchester United before losing replay",
                    "The club played at Gillingham for two seasons (1997-99) during stadium crisis",
                    "The Amex Stadium opened in 2011, ending years of playing at temporary venues",
                    "Roberto De Zerbi's Brighton played some of the best football in the 2022-23 season",
                    "Brighton qualified for Europe for the first time in their history in 2023",
                ]
            },
            "Fulham": {
                "founded": 1879,
                "nickname": "The Cottagers",
                "stadium": "Craven Cottage",
                "stadium_capacity": 29600,
                "titles": 0,
                "fa_cups": 0,
                "legends": ["Johnny Haynes", "Bobby Moore", "Louis Saha", "Aleksandar Mitrovic", "John Collins"],
                "rivals": ["Chelsea", "Queens Park Rangers"],
                "facts": [
                    "Craven Cottage is one of the oldest and most iconic grounds in English football",
                    "Johnny Haynes was England's first £100-a-week footballer in 1961",
                    "Fulham reached the Europa League final in 2010 under Roy Hodgson",
                    "Bobby Moore finished his career at Fulham after leaving West Ham",
                    "The club has been a yo-yo club, promoted and relegated frequently",
                ]
            },
            "Nottingham Forest": {
                "founded": 1865,
                "nickname": "The Tricky Trees",
                "stadium": "City Ground",
                "stadium_capacity": 30445,
                "titles": 1,
                "fa_cups": 2,
                "legends": ["Brian Clough", "Peter Shilton", "Stuart Pearce", "Roy Keane", "Des Walker"],
                "rivals": ["Derby County", "Leicester City"],
                "facts": [
                    "Forest won back-to-back European Cups in 1979 and 1980 under Brian Clough",
                    "Brian Clough is a legendary figure in English football, managing Forest for 18 years",
                    "Forest won the league title just one year after promotion in 1978",
                    "Stuart Pearce 'Psycho' is one of Forest's greatest ever players",
                    "Forest returned to the Premier League in 2022 after 23 years absence",
                ]
            },
            "Brentford": {
                "founded": 1889,
                "nickname": "The Bees",
                "stadium": "Gtech Community Stadium",
                "stadium_capacity": 17250,
                "titles": 0,
                "fa_cups": 0,
                "legends": ["Jimmy Hill", "Ivan Toney", "Jim Towers", "Ken Coote", "Christian Eriksen"],
                "rivals": ["Fulham", "Queens Park Rangers"],
                "facts": [
                    "Brentford reached the top flight for the first time in 74 years in 2021",
                    "The club's data-driven approach revolutionized English football recruitment",
                    "Ivan Toney scored 20 goals in Brentford's first Premier League season",
                    "Brentford's new stadium opened in 2020, replacing historic Griffin Park",
                    "Thomas Frank has built one of the most efficient teams in the Premier League",
                ]
            },
            "AFC Bournemouth": {
                "founded": 1899,
                "nickname": "The Cherries",
                "stadium": "Vitality Stadium",
                "stadium_capacity": 11307,
                "titles": 0,
                "fa_cups": 0,
                "legends": ["Ted MacDougall", "Steve Fletcher", "Eddie Howe", "Callum Wilson", "Dominic Solanke"],
                "rivals": ["Southampton"],
                "facts": [
                    "Bournemouth rose from League Two to Premier League in just 6 years under Eddie Howe",
                    "The club almost went out of existence in 2008 before community saved them",
                    "Ted MacDougall scored 9 goals in one FA Cup game in 1971",
                    "Bournemouth have the smallest stadium capacity in the Premier League",
                    "Eddie Howe is the club's most successful manager in history",
                ]
            },
        }

        # Process all clubs
        for club_name, data in clubs_data.items():
            print(f"\n=== Building: {club_name} ===")

            # 1. Add club node
            club_id = self.add_node(
                club_name,
                "club",
                f"Premier League football club, {data['nickname']}",
                {
                    "founded": data["founded"],
                    "nickname": data["nickname"],
                    "titles": data["titles"],
                    "fa_cups": data["fa_cups"]
                }
            )

            # 2. Add/link stadium
            stadium_id = self.add_node(
                data["stadium"],
                "stadium",
                f"Home ground of {club_name}",
                {"capacity": data["stadium_capacity"]}
            )
            self.add_edge(club_id, stadium_id, "home_ground")

            # 3. Add legendary players
            for legend in data["legends"]:
                legend_id = self.add_node(
                    legend,
                    "person",
                    f"Legendary {club_name} player",
                    {"club": club_name, "role": "legend"}
                )
                self.add_edge(legend_id, club_id, "legend_of")

            # 4. Add rivalries
            for rival_name in data["rivals"]:
                # Get or create rival club
                self.cursor.execute("SELECT node_id FROM kg_nodes WHERE LOWER(name) = LOWER(?)", (rival_name,))
                rival = self.cursor.fetchone()
                if rival:
                    self.add_edge(club_id, rival[0], "rival_of")

            # 5. Add facts
            for fact in data["facts"]:
                self.add_fact(fact, "club_history", [club_name], 0.95)

            print(f"  + {len(data['legends'])} legends, {len(data['rivals'])} rivals, {len(data['facts'])} facts")

        self.conn.commit()
        print(f"\n=== BUILD COMPLETE ===")
        print(f"Nodes added: {self.stats['nodes']}")
        print(f"Edges added: {self.stats['edges']}")
        print(f"Facts added: {self.stats['facts']}")

        # Rebuild FTS
        self.cursor.execute("INSERT INTO kb_facts_fts(kb_facts_fts) VALUES('rebuild')")
        self.conn.commit()
        print("FTS index rebuilt")

        self.conn.close()


if __name__ == "__main__":
    builder = PLBuilder()
    builder.build_all()
