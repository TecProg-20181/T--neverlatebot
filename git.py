import requests
import json
import db
from handle_updates import*
from github import*


class GitApiHandlher:

    def authorize_git(chat):

        query = db.session.query(User).filter_by(chat_id=chat)
        user = query.one()

        if user.github_access_token is None:
            send_message("1-Please, go to the following link in a web browser such as chrome or firefox:[https://github.com/login/oauth/authorize?client_id=442951c7a24c1bba8e4e&scope=repo]\n\n2-After you have authorized the application, copy the code from the url you were redirected to.\n\nExample of url:https://telegram.me/Neverlatebot?code=XXXcodeXXX, copy only XXXcodeXXX.\n\n3-Send your code for us as a command: /code XXXcodeXXX\n\n", chat)
        else:
            send_message("you already authorized this app.", chat)

    def get_token_accsses(msg, chat):
        """This function is responsible to get the access token for github. """

        client_id='442951c7a24c1bba8e4e'
        client_secret='73c558ee531fe87ac2e0579d76a671edbdc540cd'
        code = msg
        url = "https://github.com/login/oauth/access_token?client_id={}&client_secret={}&code={}".format(client_id, client_secret, code)

        response = requests.post(url)
        content = response.content.decode("utf8")
        token_accsses = (content.split('='))[1].split('&')[0]

        if token_accsses == 'bad_verification_code':
            send_message("Your code is wrong or expired, please use the command /authorizegit, and follow the instructions. ", chat)
        else:
            query = db.session.query(User).filter_by(chat_id=chat)
            user = query.one()

            user.github_access_token = token_accsses
            db.session.commit()
            send_message("You have successfuly authorized this application.",chat)

    def list_repositories(github_access_token, chat):
        g = Github(github_access_token)
        user = g.get_user()
        message = ''
        for repo in g.get_user().get_repos():
            message += repo.name
            message +='\n'
        send_message(message, chat)

    def create_issue(msg, chat):
        data = msg.split(' ', 1)
        repository_name = data[0]
        task_id = int(data[1])

        query = db.session.query(User).filter_by(chat_id=chat)
        user = query.one()

        if user.github_access_token is None:
            send_message("You have to auhtorize the application first, please use the command: '/authorize_git' and follow the instructions.", chat)
        else:
            querytask = db.session.query(Task).filter_by(id=task_id, chat=chat)
            try:
                task = querytask.one()

            except sqlalchemy.orm.exc.NoResultFound:
                send_message("_404_ Task {} not found x.x".format(task_id), chat)
                return

            g = Github(user.github_access_token)
            git_user = g.get_user()

            repo_full_name = '{}/{}'.format(git_user.login, repository_name)

            try:
                repository = g.get_repo(repo_full_name)
            except:
                send_message("_404_ Repository {} not found x.x".format(repo_full_name), chat)

            label = GitApiHandlher.create_labels(repository, task)
            if label is None:
                repository.create_issue(task.name, body=task.description)
            else:
                repository.create_issue(task.name, body=task.description, labels=label)
            send_message("Issue created!", chat)

    def create_labels(repository, task):
        red = 'ff0000'
        orange = 'f58356'
        yellow = 'eabe1e'

        if task.priority == 'high':
            try:
                label_high = repository.get_label('high')
                labels = {'high': label_high}
            except:
                label_high = repository.create_label('high', color=orange)
                labels = {'high': label_high}
        elif task.priority == 'medium':
            try:
                label_medium = repository.get_label('medium')
                labels = {'medium': label_medium}
            except:
                label_medium = repository.create_label('medium', color=orange)
                labels = {'medium': label_medium}
        elif task.priority == 'low':
            try:
                label_low = repository.get_label('low')
                labels = {'low': label_low}
            except:
                label_low = repository.create_label('low', color=yellow)
                labels = {'low': label_low}
        else:
            labels = None

        return labels
