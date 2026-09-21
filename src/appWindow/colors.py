COLOR_COUNT = 10


def task_color_indices(project):
    indices = {}
    for page in project.getPages():
        for task in page.getTasks():
            if task.getTaskName() not in indices:
                indices[task.getTaskName()] = len(indices)
    return indices


def most_advanced_completed_task(tasks):
    most = None
    for task in tasks:
        if (
            task.getHoursPredicted() > 0
            and task.getHoursCompleted() >= task.getHoursPredicted()
        ):
            most = task
    return most