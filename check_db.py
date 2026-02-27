from app import app
from project.models import User

with app.app_context():
    for u in User.query.limit(5).all():
        print(u.username, "->", u.image_file)
