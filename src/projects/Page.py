class Page:
    def __init__(self, tasks, id=None):
        self.id = id
        self.tasks = tasks

    def addTask(self, task):
        self.tasks.append(task)

    def getTotalEstimatedHours(self):
        totalEstimatedHours = 0
        for task in self.tasks:
            totalEstimatedHours += task.getEstimatedHours()
        return totalEstimatedHours

    def getTotalHoursLeft(self):
        totalHoursLeft = 0
        for task in self.tasks:
            totalHoursLeft += task.getHoursLeft()
        return totalHoursLeft

    def getTotalCompletedHours(self):
        return self.getTotalEstimatedHours() - self.getTotalHoursLeft()

    def getPercentileCompleted(self):
        estimatedHours = self.getTotalEstimatedHours()
        if estimatedHours == 0:
            return 0
        totalPercentileCompleted = (float(self.getTotalCompletedHours()) / estimatedHours) * 100
        return totalPercentileCompleted

    def getTasks(self):
        return self.tasks