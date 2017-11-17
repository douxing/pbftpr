from datetime import datetime

def pprint_task(task):
    if __debug__:
        print('''(utc: {utcdt}) --- new task {task.type.name}:
{task.item}
'''.format(utcdt = str(datetime.utcnow()), task = task))
    
