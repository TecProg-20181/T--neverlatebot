import db
from db import Task , Association

# TODO(Lucas) Retirar o import abaixo quando a send_message estiver neste arquivo.
from taskbot import send_message

def split_msg(msg):
    text = ''
    if msg != '':
        if len(msg.split(' ', 1)) > 1:
            text = msg.split(' ', 1)[1]
        msg = msg.split(' ', 1)[0]
    return msg, text

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

        query = db.session.query(Association).filter_by(parents_id=task_id)
        query_row = query.one()
        for query_row in query.all():
            duplicated_association = Association(id=query_row.id , parents_id=duplicated_task.id)
            print(type(duplicated_association))
            print(duplicated_association.parents_id)
            db.session.add(duplicated_association)
            db.session.commit()

        send_message("New task *TODO* [[{}]] {}".format(duplicated_task.id, duplicated_task.name), chat)
