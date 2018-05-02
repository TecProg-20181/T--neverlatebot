import db
from db import Task , Association

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
