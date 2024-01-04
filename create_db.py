if __name__ == '__main__':
    from app import app, db
    app.app_context().push()
    db.create_all()
