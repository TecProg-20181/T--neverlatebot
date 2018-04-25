#!/usr/bin/env python3

import json
import requests
import time
import urllib

import sqlalchemy

import db
from db import Task
from get_token import *

TOKEN = get_token()
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

HELP = """
 /new NOME
 /todo ID
 /doing ID
 /done ID
 /delete ID
 /list
 /rename ID NOME
 /dependson ID ID...
 /duplicate ID
 /priority ID PRIORITY{low, medium, high}
 /duedate ID DUEDATE{AAAA/MM/DD}
 /setdescription ID DESCRIPTION
 /taskdetail ID
 /help
"""

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

def deps_text(task, chat, preceed=''):
    text = ''

    for i in range(len(task.dependencies.split(',')[:-1])):
        line = preceed
        query = db.session.query(Task).filter_by(id=int(task.dependencies.split(',')[:-1][i]), chat=chat)
        dep = query.one()

        icon = '\U0001F195'
        if dep.status == 'DOING':
            icon = '\U000023FA'
        elif dep.status == 'DONE':
            icon = '\U00002611'

        if i + 1 == len(task.dependencies.split(',')[:-1]):
            line += '└── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
            line += deps_text(dep, chat, preceed + '    ')
        else:
            line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
            line += deps_text(dep, chat, preceed + '│   ')

        text += line

    return text


def handle_updates(updates):
    for update in updates["result"]:
        if 'message' in update:
            message = update['message']
        elif 'edited_message' in update:
            message = update['edited_message']
        else:
            print('Can\'t process! {}'.format(update))
            return

        msg = ''
        if 'text' in message:
            command = message["text"].split(" ", 1)[0]
            if len(message["text"].split(" ", 1)) > 1:
                msg = message["text"].split(" ", 1)[1].strip()
        else:
            command = '/start'

        chat = message["chat"]["id"]
        print(command, msg, chat)

        if command == '/new':
            task = Task(chat=chat, name=msg, status='TODO', description='No description.', dependencies='None', parents='', priority='None', duedate='')
            from datetime import datetime
            task.duedate = datetime.strptime(task.duedate, '')
            db.session.add(task)
            db.session.commit()
            send_message("New task *TODO* [[{}]] {}".format(task.id, task.name), chat)

        elif command == '/rename':
            text = ''
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]

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
                    send_message("You want to modify task {}, but you didn't provide any new text".format(task_id), chat)
                    return

                old_text = task.name
                task.name = text
                db.session.commit()
                send_message("Task {} redefined from {} to {}".format(task_id, old_text, text), chat)
      
        elif command == '/duplicate':
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

                dtask = Task(chat=task.chat, name=task.name, status=task.status, dependencies=task.dependencies,
                             parents=task.parents, priority=task.priority, duedate=task.duedate, description=task.description)
                db.session.add(dtask)

                for t in task.dependencies.split(',')[:-1]:
                    qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
                    t = qy.one()
                    t.parents += '{},'.format(dtask.id)

                db.session.commit()
                send_message("New task *TODO* [[{}]] {}".format(dtask.id, dtask.name), chat)

        elif command == '/delete':
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
                for t in task.dependencies.split(',')[:-1]:
                    qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
                    t = qy.one()
                    t.parents = t.parents.replace('{},'.format(task.id), '')
                db.session.delete(task)
                db.session.commit()
                send_message("Task [[{}]] deleted".format(task_id), chat)

        elif command == '/todo':
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

        elif command == '/doing':
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

        elif command == '/done':
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

        elif command == '/list':
            from datetime import datetime
            a = ''

            a += '\U0001F4CB Task List\n'
            query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.id)
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

                a += '[[{}]] {} {}\n`{}`\n\n'.format(task.id, icon, task.name, duedate)
                a += deps_text(task, chat)

            send_message(a, chat)

            priority = ' '
            priority = task.priority
            if priority == 'None':
                priority = ' '
            a = ''
            a += '\U0001F4DD _Status_\n'
            query = db.session.query(Task).filter_by(status='TODO', chat=chat).order_by(Task.id)
            a += '\n\U0001F195 *TODO*\n'
            for task in query.all():
                a += '[[{}]] {}  `{}`\n'.format(task.id, task.name, priority)
            query = db.session.query(Task).filter_by(status='DOING', chat=chat).order_by(Task.id)
            a += '\n\U000023FA *DOING*\n'
            for task in query.all():
                a += '[[{}]] {}  `{}`\n'.format(task.id, task.name, priority)
            query = db.session.query(Task).filter_by(status='DONE', chat=chat).order_by(Task.id)
            a += '\n\U00002611 *DONE*\n'
            for task in query.all():
                a += '[[{}]] {}  `{}`\n'.format(task.id, task.name, priority)

            send_message(a, chat)

            a = ''
            aux = ''
            a += '\U0001F4C6 Task List by duedate\n'
            query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.duedate)
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
                    aux += '[[{}]] {} {}\n`{}`\n\n'.format(task.id, icon, task.name, duedate)
                    aux += deps_text(task, chat)
                else:
                    duedate = duedate.strftime('%d/%m/%Y')
                    a += '[[{}]] {} {}\n`{}`\n\n'.format(task.id, icon, task.name, duedate)
                    a += deps_text(task, chat)

            a += aux
            send_message(a, chat)

        elif command == '/dependson':
            text = ''
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]

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
                    for i in task.dependencies.split(',')[:-1]:
                        i = int(i)
                        q = db.session.query(Task).filter_by(id=i, chat=chat)
                        t = q.one()
                        t.parents = t.parents.replace('{},'.format(task.id), '')

                    task.dependencies = ''
                    send_message("Dependencies removed from task {}".format(task_id), chat)
                else:
                    for depid in text.split(' '):
                        if not depid.isdigit():
                            send_message("All dependencies ids must be numeric, and not {}".format(depid), chat)
                        else:
                            depid = int(depid)
                            query = db.session.query(Task).filter_by(id=depid, chat=chat)
                            try:
                                taskdep = query.one()
                                taskdep.parents += str(task.id) + ','
                            except sqlalchemy.orm.exc.NoResultFound:
                                send_message("_404_ Task {} not found x.x".format(depid), chat)
                                continue

                            deplist = task.dependencies.split(',')
                            if str(depid) not in deplist:
                                task.dependencies += str(depid) + ','

                db.session.commit()
                send_message("Task {} dependencies up to date".format(task_id), chat)
       
        elif command == '/priority':
            text = ''
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]

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

        elif command == '/duedate':
            text = ''
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]

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
                    task.duedate = ''
                    send_message(
                        "_Cleared_ due date from task {}".format(task_id), chat)
                else:
                    text = text.split("/")
                    text.reverse()
                    print(text)
                    if not (1 <= int(text[2]) <= 31 and 1 <= int(text[1]) <= 12 and 1970 <= int(text[0]) <= 2100):
                        send_message(
                            "The due date *must be* of the following format: DD/MM/YYYY (including '/')", chat)
                    else:
                        from datetime import datetime
                        task.duedate = datetime.strptime(" ".join(text), '%Y %m %d')
                        send_message(
                            "*Task {}* due date has due date *{}*".format(task_id, task.duedate), chat)
                db.session.commit()
            print(msg)
            print(text)
       
        elif command == '/setdescription':
            text = ''
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]

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

                print(text)
                if text == '':
                    send_message(
                        "_Canceled_ Hey, you must inform a description\nTry Again.", chat)
                else:
                    if len(text) > 1000:
                        send_message("Hey, the description *must be* less of 1000 caracters.", chat)
                    else:
                        task.description = text
                        send_message("*Task {}*:Update successful. ´XD´".format(task_id), chat)
                db.session.commit()

        elif command == '/taskdetail':
            from datetime import datetime
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]

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

                a = ''
                a += '\U0001F4D1 Task Detail\n'
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

                priority = ' '
                priority = task.priority
                if priority == 'None':
                    priority = ' '

                a += '[[{}]] {} {} \t`{}`\nData de entrega:\n>{}\nDescrição:\n{}\n'.format(
                    task.id, icon, task.name, priority, duedate, task.description)
                a += deps_text(task, chat)

                send_message(a, chat)

        elif command == '/start':
            send_message("Welcome! Here is a list of things you can do.", chat)
            send_message(HELP, chat)

        elif command == '/help':
            send_message("Here is a list of things you can do.", chat)
            send_message(HELP, chat)

        else:
            send_message("I'm sorry dave. I'm afraid I can't do that.", chat)


def main():
    last_update_id = None

    while True:
        print("Updates")
        updates = get_updates(last_update_id)

        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)

        time.sleep(0.5)


if __name__ == '__main__':
    main()
