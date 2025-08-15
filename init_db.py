import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Create source table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS source (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT
    )
    ''')

    # Create articles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        published_date TEXT,
        source_id INTEGER,
        FOREIGN KEY (source_id) REFERENCES source(id)
    )
    ''')

    # Insert dummy sources (if not exists)
    cursor.execute("INSERT OR IGNORE INTO source (id, name, url) VALUES (1, 'Health Daily', 'https://healthdaily.example.com')")
    cursor.execute("INSERT OR IGNORE INTO source (id, name, url) VALUES (2, 'Wellness News', 'https://wellnessnews.example.com')")

    # Articles data from your input, assigned all to Health Daily (source_id=1)
    articles_data = [
        ("5 Strength Training Tips for Beginners", 
         "If you’re just starting strength training, focus on compound movements like squats, deadlifts, and push-ups. Start with light weights, learn proper form, and build gradually. Aim for 2–3 full-body sessions per week. Rest 48 hours between sessions to recover.",
         "2025-08-01", 1),

        ("HIIT Workouts to Burn Fat Fast", 
         "High-Intensity Interval Training (HIIT) alternates short bursts of intense activity like sprinting or burpees with low-intensity recovery periods. A typical session lasts 20–30 minutes. HIIT raises your metabolism for hours after exercise.",
         "2025-08-02", 1),

        ("Yoga for Flexibility and Stress Relief", 
         "Practicing yoga 3–4 times a week improves flexibility and reduces stress. Focus on poses like downward dog, pigeon, and seated forward fold. Hold each pose for 30–60 seconds and breathe deeply.",
         "2025-08-03", 1),

        ("Nutrition Basics: Protein Intake for Muscle Gain", 
         "To support muscle growth, aim for 1.6–2.2 grams of protein per kilogram of body weight daily. Include lean meats, dairy, legumes, and whey. Spread intake across meals and train regularly.",
         "2025-08-04", 1),

        ("Beginner Runner: How to Start a 5K Training Plan", 
         "Begin with run-walk intervals like 1-minute run and 2-minute walk. Repeat 6 times, three days a week. Gradually increase running duration weekly. Add a steady long run each weekend and include cross-training for recovery.",
         "2025-08-05", 1),

        ("The Importance of Hydration in Fitness", 
         "Staying hydrated is crucial for optimal performance. Drink water before, during, and after workouts. Aim for at least 2–3 liters daily, more if exercising intensely or in hot weather. Monitor urine color to ensure proper hydration.",
         "2025-08-06", 1),

        ("Core Workouts: Building a Strong Foundation", 
         "Incorporate core exercises like planks, Russian twists, and bicycle crunches into your routine 3–4 times a week. Focus on form and gradually increase duration or repetitions to build strength.",
         "2025-08-07", 1),

        ("Cardio vs. Strength Training: What’s Best for You?", 
         "Both cardio and strength training have benefits. Cardio improves heart health and burns calories, while strength training builds muscle and boosts metabolism. A balanced routine includes both types of exercise.",
         "2025-08-08", 1),

        ("Sleep and Recovery: Key to Fitness Success", 
         "Aim for 7–9 hours of quality sleep per night to support recovery and performance. Establish a bedtime routine, keep a consistent sleep schedule, and create a restful environment.",
         "2025-08-09", 1),

        ("Setting Realistic Fitness Goals", 
         "Set SMART goals: Specific, Measurable, Achievable, Relevant, Time-bound. For example, aim to run 5K in under 30 minutes within three months. Track progress and adjust goals as needed.",
         "2025-08-10", 1)
    ]

    cursor.executemany(
        "INSERT INTO articles (title, content, published_date, source_id) VALUES (?, ?, ?, ?)",
        articles_data
    )

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized with articles and source tables including your health articles.")
