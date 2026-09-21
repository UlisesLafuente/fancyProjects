class Task:
    def __init__(self, taskName: str, hours: int, id=None):
        self.id = id
        self.taskName = taskName
        self.hoursPredicted = hours
        self.hoursCompleted = 0
        self.hoursLeft = hours
        self.completedTask = False

    def __setTaskName(self, taskName: str):
        self.taskName = taskName

    def __setPredictedHours(self, hoursPredicted: int):
        self.hoursPredicted = hoursPredicted
        self.hoursLeft = hoursPredicted - self.hoursCompleted

    def __setHoursCompleted(self, hoursCompleted: int):
        if hoursCompleted <= self.hoursPredicted:
            self.hoursCompleted = hoursCompleted
            self.hoursLeft = self.hoursPredicted - hoursCompleted
        else:
            raise ValueError("Hours completed cannot exceed predicted hours")

    def __updateTaskStatus(self, status: bool):
        self.completedTask = status

    def updateTask(self, taskName: str, hoursPredicted: int, hoursCompleted: int, status: bool):
        try:
            self.__setTaskName(taskName)
            self.__setPredictedHours(hoursPredicted)
            self.__setHoursCompleted(hoursCompleted)
            self.__updateTaskStatus(status)
        except ValueError as e:
            print(e)

    def getTaskName(self):
        return self.taskName

    def getEstimatedHours(self):
        return self.hoursPredicted

    def getHoursPredicted(self):
        return self.hoursPredicted

    def getHoursCompleted(self):
        return self.hoursCompleted

    def getHoursLeft(self):
        return self.hoursLeft

    def getCompletedTask(self):
        return self.completedTask

    def __str__(self):
        return (
            "Task name: " + self.taskName +
            "\nTotal predicted hours: " + str(self.hoursPredicted) +
            "\nPredicted hours left to complete: " + str(self.hoursLeft) +
            "\nTask status: " + str(self.completedTask)
        )