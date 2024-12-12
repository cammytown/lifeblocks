from .models.database import init_database
from .ui.main_window import MainWindow


def main():
    # Initialize database and get session
    engine, session = init_database()

    # Create and run main window
    app = MainWindow(session)
    app.run()


if __name__ == "__main__":
    main()
