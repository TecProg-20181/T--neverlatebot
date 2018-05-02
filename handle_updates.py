import sqlalchemy
import json
import requests
import db
import time
import urllib

from db import Task ,Association
from get_token import get_token

TOKEN = get_token()
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)

    js = get_json_from_url(url)
    return js

def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)

    get_url(url)

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))

    return max(update_ids)

def split_msg(msg):
    text = ''
    if msg != '':
        if len(msg.split(' ', 1)) > 1:
            text = msg.split(' ', 1)[1]
        msg = msg.split(' ', 1)[0]
    return msg, text

def deps_text(task, chat, preceed=''):
    text = ''

    i = 1
    dependencies_count = db.session.query(Association).filter_by(parents_id=task.id).count()
    query = db.session.query(Association).filter_by(parents_id=task.id)

    for row in query.all():
        line = preceed

        try:
            dependency = db.session.query(Task).get(row.id)
            icon = '\U0001F195'
            if dependency.status == 'DOING':
                icon = '\U000023FA'

            elif dependency.status == 'DONE':
                icon = '\U00002611'

            if i == dependencies_count:
                line += '└── [[{}]] {} {}\n'.format(dependency.id, icon, dependency.name)
                line += deps_text(dependency, chat, preceed + '    ')

            else:
                line += '├── [[{}]] {} {}\n'.format(dependency.id, icon, dependency.name)
                line += deps_text(dependency, chat, preceed + '│   ')

            i += 1
            text += line

        except:
            pass

    return text

def new_task(chat, msg):

    from datetime import datetime
    task = Task(chat=chat, name=msg, status='TODO', description='No description.',
                priority='None', duedate='')

    task.duedate = datetime.strptime(task.duedate, '')
    db.session.add(task)
    db.session.commit()

    send_message("New task *TODO* [[{}]] {}".format(task.id, task.name), chat)

def rename_task(chat, msg):
    msg, text = split_msg(msg)

    if not msg.isdigit():
        send_message("You must inform the task id", chat)

    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)

        try:
            task = query.one()

        except sqlalchemy.orm.exc.NoResultFound:
            send_message(
                "_404_ Task {} not found x.x".format(task_id), chat)
            return

        if text == '':
            send_message(
                "You want to modify task {}, but you didn't provide any new text".format(task_id), chat)
            return

        old_text = task.name
        task.name = text
        db.session.commit()
        send_message("Task {} redefined from {} to {}".format(task_id, old_text, text), chat)

def duplicate_task(chat, msg):
    if not msg.isdigit():
        send_message("You must inform the task id", chat)

    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)

        try:
            task = query.one()

        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return

        duplicated_task = Task(chat=task.chat, name=task.name, status=task.status,
                     priority=task.priority, duedate=task.duedate,
                     description=task.description)

        db.session.add(duplicated_task)
        db.session.commit()

        try:
            query = db.session.query(Association).filter_by(parents_id=task_id)
            query_row = query.one()

            for query_row in query.all():
                duplicated_association = Association(id=query_row.id , parents_id=duplicated_task.id)
                print(type(duplicated_association))
                print(duplicated_association.parents_id)
                db.session.add(duplicated_association)
                db.session.commit()

        except sqlalchemy.orm.exc.NoResultFound:
            pass

        send_message("New task *TODO* [[{}]] {}".format(duplicated_task.id, duplicated_task.name), chat)


def delete_task(chat, msg):
    if not msg.isdigit():
        send_message("You must inform the task id", chat)

    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)

        try:
            task = query.one()

        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return

        query_dependencies = db.session.query(
            Association).filter_by(parents_id=task_id)
        for rows in query_dependencies.all():
            try:
                deleted_query = rows
                db.session.delete(deleted_query)

            except sqlalchemy.orm.exc.NoResultFound:
                send_message("No dependencies".format(task_id), chat)

        query = db.session.query(Association).filter_by(id=task_id)

        for rows in query.all():
            try:
                deleted_query = rows
                db.session.delete(deleted_query)

            except sqlalchemy.orm.exc.NoResultFound:
                send_message("No dependencies".format(task_id), chat)

        db.session.delete(task)
        db.session.commit()
        send_message("Task [[{}]] deleted".format(task_id), chat)

def to_do_task(chat, msg):

    if not msg.isdigit():
        send_message("You must inform the task id", chat)

    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()

        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return

        task.status = 'TODO'
        db.session.commit()
        send_message("*TODO* task [[{}]] {}".format(task.id, task.name), chat)

def doing_task(chat, msg):

    if not msg.isdigit():
        send_message("You must inform the task id", chat)

    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()

        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return

        task.status = 'DOING'
        db.session.commit()
        send_message("*DOING* task [[{}]] {}".format(task.id, task.name), chat)

def done_task(chat, msg):
    if not msg.isdigit():
        send_message("You must inform the task id", chat)

    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()

        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return

        task.status = 'DONE'
        db.session.commit()
        send_message("*DONE* task [[{}]] {}".format(task.id, task.name), chat)

def list_tasks(chat, msg):

    from datetime import datetime

    response = ''
    response += '\U0001F4CB Task List\n'
    query = db.session.query(Task).filter_by(chat=chat).order_by(Task.id)
    for task in query.all():
        icon = '\U0001F195'
        if task.status == 'DOING':
            icon = '\U000023FA'

        elif task.status == 'DONE':
            icon = '\U00002611'

        duedate = ' '
        duedate = task.duedate
        duedate = duedate.strftime('%d/%m/%Y')
        if duedate == '01/01/1900':
            duedate = ' '

        response += '\n[[{}]] {} {}\n`{}`'.format(task.id, icon, task.name, duedate)
        response += deps_text(task, chat)

    send_message(response, chat)

    priority = ' '
    response = ''
    response += '\U0001F4DD _Status_\n'
    query = db.session.query(Task).filter_by(status='TODO', chat=chat).order_by(Task.id)
    response += '\n\U0001F195 *TODO*\n'
    for task in query.all():
        priority = task.priority
        if priority == 'None':
            priority = ' '

        response += '[[{}]] {}  `{}`\n'.format(task.id, task.name, priority)

    query = db.session.query(Task).filter_by(status='DOING', chat=chat).order_by(Task.id)
    response += '\n\U000023FA *DOING*\n'
    for task in query.all():
        priority = task.priority
        if priority == 'None':
            priority = ' '

        response += '[[{}]] {}  `{}`\n'.format(task.id, task.name, priority)

    query = db.session.query(Task).filter_by(status='DONE', chat=chat).order_by(Task.id)
    response += '\n\U00002611 *DONE*\n'
    for task in query.all():
        priority = task.priority
        if priority == 'None':
            priority = ' '

        response += '[[{}]] {}  `{}`\n'.format(task.id, task.name, priority)

    send_message(response, chat)

    response = ''
    aux = ''
    response += '\U0001F4C6 Task List by duedate\n\n'
    query = db.session.query(Task).filter_by(chat=chat).order_by(Task.duedate)
    for task in query.all():
        icon = '\U0001F195'
        if task.status == 'DOING':
            icon = '\U000023FA'

        elif task.status == 'DONE':
            icon = '\U00002611'

        duedate = ' '
        duedate = task.duedate
        duedate = duedate.strftime('%d/%m/%Y')

        if duedate == '01/01/1900':
            duedate = ' '
            aux += '[[{}]] {} {} `{}`\n'.format(task.id, icon, task.name, duedate)
            aux += deps_text(task, chat)
            aux += '\n'

        else:
            response += '[[{}]] {} {} `{}`\n'.format(task.id, icon, task.name, duedate)
            response += deps_text(task, chat)
            response += '\n'

    response += aux
    send_message(response, chat)

def task_dependencies(chat, msg):

    msg, text = split_msg(msg)

    if not msg.isdigit():
        send_message("You must inform the task id", chat)

    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()

        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return

        if not text:
            try:
                query_dependencies = db.session.query(Association).filter_by(parents_id=task_id)
                db.session.delete(query_dependencies)

            except sqlalchemy.orm.exc.NoResultFound:
                send_message("No dependencies to delete from task {}.".format(task_id), chat)

            send_message("Dependencies removed from task {}".format(task_id), chat)

        else:
            for dependency_id in text.split(' '):
                if not dependency_id.isdigit():
                    send_message("All dependencies ids must be numeric, and not {}".format(dependency_id), chat)

                else:
                    dependency_id = int(dependency_id)
                    query = db.session.query(Task).filter_by(id=dependency_id, chat=chat)

                    try:
                        dependent_task = query.one()
                        dependency = Association(id=dependent_task.id, parents_id=task.id)

                        try:
                            query_dependency = db.session.query(Association).filter_by(parents_id=dependent_task.id)
                            query_aux = query_dependency.one()
                            send_message("Tasks can't be co-dependents", chat)
                            return

                        except:
                            db.session.add(dependency)

                    except sqlalchemy.orm.exc.NoResultFound:
                        send_message("_404_ Task {} not found x.x".format(dependency_id), chat)
                        continue

        db.session.commit()
        send_message("Task {} dependencies up to date".format(task_id), chat)

def task_priority(chat, msg):

    msg, text = split_msg(msg)

    if not msg.isdigit():
        send_message("You must inform the task id", chat)

    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()

        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return

        if text == '':
            task.priority = ''
            send_message(
                "_Cleared_ all priorities from task {}".format(task_id), chat)

        else:
            if text.lower() not in ['high', 'medium', 'low']:
                send_message("The priority *must be* one of the following: high, medium, low", chat)

            else:
                task.priority = text.lower()
                send_message("*Task {}* priority has priority *{}*".format(task_id, text.lower()), chat)

        db.session.commit()
