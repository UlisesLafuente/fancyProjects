class WorkflowType:
    CONTINUOUS = "continuous"
    BY_TASK = "by_task"


class Project:
    def __init__(self, name, pages, id=None, workflow_type=WorkflowType.CONTINUOUS):
        self.id = id
        self.projectName = name
        self.pages = pages
        self.workflow_type = workflow_type

    def addPage(self, page):
        self.pages.append(page)

    def removePage(self, page):
        if page in self.pages:
            self.pages.remove(page)

    def percentComplete(self):
        estimatedHours = self.getTotalEstimatedHours()
        if estimatedHours == 0:
            return 0
        completedHours = self.getTotalCompletedHours()

        return (float(completedHours) / estimatedHours) * 100

    def getTotalEstimatedHours(self):
        estimatedHours = 0
        for page in self.pages:
            estimatedHours += page.getTotalEstimatedHours()
        return estimatedHours

    def getTotalHoursLeft(self):
        hoursLeft = 0
        for page in self.pages:
            hoursLeft += page.getTotalHoursLeft()
        return hoursLeft

    def getTotalCompletedHours(self):
        return self.getTotalEstimatedHours() - self.getTotalHoursLeft()

    def getPages(self):
        return self.pages