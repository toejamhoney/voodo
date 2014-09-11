import os
from time import sleep


def run(task):
    """
    :type task: vo2.work.task.Task
    :param task:
    :return:
    """
    task.find_vm()


def callback(arg):
    print('Callback: %s' % arg)
