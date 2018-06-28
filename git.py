import requests
import json
import db
from handle_updates import *
from github import *

def connectAccount(msg, chat):
    """This function is responsible to connect with the github account via Oauth protocol. """

    client_id='442951c7a24c1bba8e4e'
    client_secret='73c558ee531fe87ac2e0579d76a671edbdc540cd'
    code = msg
    url = "https://github.com/login/oauth/access_token?client_id={}&client_secret={}&code={}".format(client_id, client_secret, code)
    print (url)
    response = requests.post(url)

    content = response.content.decode("utf8")

    new_content = (content.split('='))[1].split('&')[0]

    query = db.session.query(User).filter_by(chat_id=chat)
    user = query.one()

    user.github_access_token = new_content

    db.session.commit()

    return new_content

def login(github_access_token):
    g = Github(github_access_token)

    for repo in g.get_user().get_repos():
        print(repo.name)
