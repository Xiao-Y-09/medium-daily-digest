import sqlite3

def init_db(path="seen.db"):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE IF NOT EXISTS seen (id TEXT PRIMARY KEY)")
    return con

def filter_new(con, articles):
    return [a for a in articles
            if not con.execute("SELECT 1 FROM seen WHERE id=?", (a.id,)).fetchone()]

def mark_seen(con, articles):
    con.executemany("INSERT OR IGNORE INTO seen(id) VALUES (?)",
                    [(a.id,) for a in articles])
    con.commit()