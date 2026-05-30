import sqlite3
import datetime
import os

DB_PATH = os.environ.get("DB_PATH", "ustaxona.db")

class Database:
    def __init__(self):
        self.path = DB_PATH

    def conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def init_db(self):
        with self.conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    lang TEXT DEFAULT 'uz',
                    tel TEXT
                );

                CREATE TABLE IF NOT EXISTS ustalar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ismi TEXT NOT NULL,
                    tel TEXT,
                    mutaxassis TEXT,
                    sana TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS buyurtmalar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mIsmi TEXT NOT NULL,
                    mTel TEXT NOT NULL,
                    model TEXT NOT NULL,
                    muammo TEXT,
                    narx INTEGER DEFAULT 0,
                    xarajat INTEGER DEFAULT 0,
                    usta_id INTEGER,
                    usta_ismi TEXT,
                    tayyor TEXT,
                    status TEXT DEFAULT 'Kutilmoqda',
                    sana TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (usta_id) REFERENCES ustalar(id)
                );
            """)
        print("✅ Ma'lumotlar bazasi tayyor.")

    # ── FOYDALANUVCHILAR ──────────────────────────────────────
    def set_user_lang(self, chat_id, lang):
        with self.conn() as c:
            c.execute("INSERT OR REPLACE INTO users (chat_id, lang) VALUES (?, ?)", (chat_id, lang))

    def get_user_lang(self, chat_id):
        with self.conn() as c:
            r = c.execute("SELECT lang FROM users WHERE chat_id=?", (chat_id,)).fetchone()
            return r["lang"] if r else "uz"

    def set_user_tel(self, chat_id, tel):
        with self.conn() as c:
            c.execute("UPDATE users SET tel=? WHERE chat_id=?", (tel, chat_id))

    def get_mijoz_chat_id(self, tel):
        # Telefon raqamini normalizatsiya qilish
        clean = tel.replace("+", "").replace(" ", "")
        with self.conn() as c:
            rows = c.execute("SELECT chat_id, tel FROM users WHERE tel IS NOT NULL").fetchall()
            for r in rows:
                if r["tel"] and r["tel"].replace("+", "").replace(" ", "") == clean:
                    return r["chat_id"]
        return None

    # ── USTALAR ──────────────────────────────────────────────
    def add_usta(self, ismi, tel, mutaxassis):
        with self.conn() as c:
            c.execute("INSERT INTO ustalar (ismi, tel, mutaxassis) VALUES (?,?,?)",
                      (ismi, tel, mutaxassis))

    def get_ustalar(self):
        with self.conn() as c:
            return [dict(r) for r in c.execute("SELECT * FROM ustalar ORDER BY id").fetchall()]

    def get_usta(self, usta_id):
        with self.conn() as c:
            r = c.execute("SELECT * FROM ustalar WHERE id=?", (usta_id,)).fetchone()
            return dict(r) if r else None

    def get_usta_stats(self, usta_id):
        with self.conn() as c:
            r = c.execute("""
                SELECT COUNT(*) as n,
                       COALESCE(SUM(narx),0) as jami,
                       COALESCE(SUM(xarajat),0) as xarajat
                FROM buyurtmalar WHERE usta_id=?
            """, (usta_id,)).fetchone()
            return dict(r) if r else {"n": 0, "jami": 0, "xarajat": 0}

    # ── BUYURTMALAR ──────────────────────────────────────────
    def add_buyurtma(self, mIsmi, mTel, model, muammo, narx, usta_id, usta_ismi, tayyor):
        with self.conn() as c:
            cur = c.execute("""
                INSERT INTO buyurtmalar (mIsmi, mTel, model, muammo, narx, usta_id, usta_ismi, tayyor)
                VALUES (?,?,?,?,?,?,?,?)
            """, (mIsmi, mTel, model, muammo, narx, usta_id, usta_ismi, tayyor))
            return cur.lastrowid

    def get_buyurtmalar(self, status=None):
        with self.conn() as c:
            if status:
                rows = c.execute("SELECT * FROM buyurtmalar WHERE status=? ORDER BY id DESC", (status,)).fetchall()
            else:
                rows = c.execute("SELECT * FROM buyurtmalar ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]

    def get_buyurtma(self, bid):
        with self.conn() as c:
            r = c.execute("SELECT * FROM buyurtmalar WHERE id=?", (bid,)).fetchone()
            return dict(r) if r else None

    def update_status(self, bid, status):
        with self.conn() as c:
            c.execute("UPDATE buyurtmalar SET status=? WHERE id=?", (status, bid))

    def add_xarajat(self, bid, summa):
        with self.conn() as c:
            c.execute("UPDATE buyurtmalar SET xarajat = xarajat + ? WHERE id=?", (summa, bid))

    # ── HISOBOT ──────────────────────────────────────────────
    def _davr_filter(self, davr):
        now = datetime.datetime.now()
        if davr == "bugun":
            start = now.strftime("%Y-%m-%d 00:00:00")
        elif davr == "hafta":
            start = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        elif davr == "oy":
            start = now.strftime("%Y-%m-01 00:00:00")
        else:
            start = "2000-01-01"
        return start

    def get_hisobot(self, davr):
        start = self._davr_filter(davr)
        with self.conn() as c:
            r = c.execute("""
                SELECT COUNT(*) as n,
                       COALESCE(SUM(narx),0) as jami,
                       COALESCE(SUM(xarajat),0) as xarajat
                FROM buyurtmalar WHERE sana >= ?
            """, (start,)).fetchone()
            return dict(r) if r else {"n": 0, "jami": 0, "xarajat": 0}

    def get_all_usta_stats(self, davr):
        start = self._davr_filter(davr)
        with self.conn() as c:
            rows = c.execute("""
                SELECT u.ismi,
                       COUNT(b.id) as n,
                       COALESCE(SUM(b.narx),0) as jami,
                       COALESCE(SUM(b.xarajat),0) as xarajat
                FROM ustalar u
                LEFT JOIN buyurtmalar b ON b.usta_id = u.id AND b.sana >= ?
                GROUP BY u.id
                HAVING n > 0
                ORDER BY jami DESC
            """, (start,)).fetchall()
            return [dict(r) for r in rows]

db = Database()
