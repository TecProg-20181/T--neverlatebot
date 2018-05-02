#!/usr/bin/env python3

import json
import requests
import time
import urllib

import sqlalchemy

import db
from handle_updates import *
from db import Task, Association
from get_token import get_token

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
            new_task(chat, msg)

        elif command == '/rename':
            rename_task(chat, msg)

        elif command == '/duplicate':
            duplicate_task(chat, msg)

        elif command == '/delete':
            delete_task(chat, msg)

        elif command == '/todo':
            to_do_task(chat, msg)

        elif command == '/doing':
            doing_task(chat, msg)

        elif command == '/done':
            done_task(chat, msg)

        elif command == '/list':
            list_tasks(chat, msg)

        elif command == '/dependson':
            task_dependencies(chat, msg)

        elif command == '/priority':
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

        elif command == '/duedate':
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
                    task.duedate = ''
                    send_message(
                        "_Cleared_ due date from task {}".format(task_id), chat)

                else:
                    text = text.split("/")
                    text.reverse()
                    if not (1 <= int(text[2]) <= 31 and 1 <= int(text[1]) <= 12 and 1970 <= int(text[0]) <= 2100):
                        send_message(
                            "The due date *must be* of the following format: DD/MM/YYYY (including '/')", chat)

                    else:
                        from datetime import datetime
                        task.duedate = datetime.strptime(" ".join(text), '%Y %m %d')
                        send_message(
                            "*Task {}* due date has due date *{}*".format(task_id, task.duedate), chat)

                db.session.commit()

        elif command == '/setdescription':
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

                response = ''
                response += '\U0001F4D1 Task Detail\n'
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

                response += '[[{}]] {} {} \t`{}`\nData de entrega:\n>{}\nDescrição:\n{}\n'.format(
                    task.id, icon, task.name, priority, duedate, task.description)
                response += deps_text(task, chat)

                send_message(response, chat)

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
