from flask import flash
from flask_login import login_user, current_user
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
import sqlalchemy

from .models import db, User, OAuth


google_oauth_blueprint = make_google_blueprint(
    scope=["profile", "email"],
    storage=SQLAlchemyStorage(OAuth, db.session, user=current_user)
)


@oauth_authorized.connect_via(google_oauth_blueprint)
def google_oauth_login(blueprint, token):
    if not token:
        flash("Failed to log in.", category="error")
        return False

    resp = blueprint.session.get("/oauth2/v1/userinfo")
    if not resp.ok:
        msg = "Failed to fetch user info."
        flash(msg, category="error")
        return False

    info = resp.json()
    user_id = info["id"]

    # find the OAuth token in the database, or create it
    query = OAuth.query.filter_by(provider=blueprint.name, provider_user_id=user_id)
    try:
        oauth = query.one()
    except sqlalchemy.orm.exc.NoResultFound:
        oauth = OAuth(provider=blueprint.name, provider_user_id=user_id, token=token)

    if oauth.user:
        login_user(oauth.user)
        flash("Successfully signed in.")

    else:
        # create a new local user account for this user
        user = User(email=info["email"])
        # associate the new local user account with the OAuth token
        oauth.user = user
        # save and commit our database models
        db.session.add_all([user, oauth])
        db.session.commit()
        # log in the new local user account
        login_user(user)
        flash("Successfully signed in.")

    # disable Flask-Dance's default behavior for saving the OAuth token
    return False


@oauth_error.connect_via(google_oauth_blueprint)
def google_oauth_error(blueprint, message, response):
    msg = ("OAuth error from {name}! " "message={message} response={response}").format(
        name=blueprint.name, message=message, response=response
    )
    flash(msg, category="error")