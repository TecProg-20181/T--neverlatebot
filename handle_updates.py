import sqlalchemy

import db
from db import Task

# TODO(Lucas) Retirar o import abaixo quando a send_message estiver neste arquivo.
from taskbot import send_message


def new_task(chat, msg):

    from datetime import datetime
    task = Task(chat=chat, name=msg, status='TODO', description='No description.',
                priority='None', duedate='')

    task.duedate = datetime.strptime(task.duedate, '')
    db.session.add(task)
    db.session.commit()

    send_message("New task *TODO* [[{}]] {}".format(task.id, task.name), chat)


def rename_task(chat, msg):
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
            send_message(
                "You want to modify task {}, but you didn't provide any new text".format(task_id), chat)
            return

        old_text = task.name
        task.name = text
        db.session.commit()
        send_message("Task {} redefined from {} to {}".format(
            task_id, old_text, text), chat)
