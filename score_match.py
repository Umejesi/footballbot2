"""
Run this script manually after a match ends to award points.

Usage:
  python score_match.py "Arsenal" "Chelsea" 2 1

This will:
- Find all predictions for Arsenal vs Chelsea
- Award 50pts for exact score (2-1)
- Award 20pts for correct winner (Arsenal)
- Award 10pts for correct draw prediction
"""
import sys
from dotenv import load_dotenv
load_dotenv()

from db.models import init_db
from db.crud import score_predictions

def main():
    if len(sys.argv) != 5:
        print("Usage: python score_match.py 'Home Team' 'Away Team' home_goals away_goals")
        print("Example: python score_match.py 'Arsenal' 'Chelsea' 2 1")
        sys.exit(1)

    home_team = sys.argv[1]
    away_team = sys.argv[2]
    home_goals = int(sys.argv[3])
    away_goals = int(sys.argv[4])

    init_db()
    results = score_predictions(home_team, away_team, home_goals, away_goals)

    if not results:
        print(f"No predictions found for {home_team} vs {away_team}")
        return

    print(f"\nMatch: {home_team} {home_goals} - {away_goals} {away_team}")
    print(f"Scored {len(results)} predictions:\n")
    for telegram_id, pts in results:
        status = f"+{pts} pts" if pts > 0 else "no points"
        print(f"  User {telegram_id}: {status}")

if __name__ == "__main__":
    main()
