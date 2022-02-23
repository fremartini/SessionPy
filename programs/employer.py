from typing import Union
class Employee: ...
class Manager(Employee): ...

worker = Employee()
worker = Manager() # OK since Manager >: Employee


x : Union[Employee, Manager, int] = Employee()

reveal_type(x)


