class TaskStatus():
  @property
  def status(self):
    return self.__status

  @status.setter
  def status(self, value):
    self.__status = value

  def __init__(self, status=False, reason=None):
    self.status = status
    self.reason = reason
  
  def has_suceedeed(self):
    self.status == True