import sys
from pathlib import Path
from database.database import init_database
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gameplay.gui.app import main


if __name__ == "__main__":
    init_database()
    main()
