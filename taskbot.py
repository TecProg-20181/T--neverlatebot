#!/usr/bin/env python3
from handle_updates import *

HELP = """
 /new NOME
 /todo ID ID...
 /doing ID ID...
 /done ID ID...
 /delete ID
 /list
 /rename ID NOME
 /dependson ID ID...
 /duplicate ID
 /priority ID PRIORITY{low, medium, high}
 /duedate ID DUEDATE{DD/MM/YYYY}
 /setdescription ID DESCRIPTION
 /taskdetail ID
 /help
"""

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
            task_priority(chat, msg)

        elif command == '/duedate':
            set_due_date(chat, msg)
            
        elif command == '/setdescription':
            set_description(chat, msg)

        elif command == '/taskdetail':
            task_detail(chat, msg)

        elif command == '/start':
            start_chat(chat)
            send_message("Welcome! Here is a list of things you can do.", chat)
            send_message(HELP, chat)

        elif command == '/help':
            send_message("Here is a list of things you can do.", chat)
            send_message(HELP, chat)

        else:
            send_message("I'm sorry dave. I'm afraid I can't do that.", chat)


def main():
    last_update_id = None

    # Search for update every half second.
    while True:
        print("Updates")
        updates = get_updates(last_update_id)

        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)

        time.sleep(0.5)


if __name__ == '__main__':
    main()
