import sqlalchemy

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

        query = db.session.query(Association).filter_by(parents_id=task_id)
        query_row = query.one()
        for query_row in query.all():
            duplicated_association = Association(id=query_row.id , parents_id=duplicated_task.id)
            print(type(duplicated_association))
            print(duplicated_association.parents_id)
            db.session.add(duplicated_association)
            db.session.commit()

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
