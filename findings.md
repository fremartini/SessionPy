# Findings

### What have I done

So far, traversing the AST and finding where assigning of channels happens and what information I could get it.

### Problem

Ultimately, the line:
```py
ch = Channel[Send[int, Recv[bool, End]]]()
```
breaks down to a `ast.Assign` object with all these properties:

```py
obj.__class__ = <class 'ast.Assign'>
obj.__delattr__ = <method-wrapper '__delattr__' of Assign object at 0x104da7940>
obj.__dict__ = {'targets': [<ast.Name object at 0x104da7850>], 'value': <ast.Call object at 0x104da7730>, 'type_comment': None, 'lineno': 4, 'col_offset': 4, 'end_lineno': 4, 'end_col_offset': 17}
obj.__dir__ = <built-in method __dir__ of Assign object at 0x104da7940>
obj.__doc__ = 'Assign(expr* targets, expr value, string? type_comment)'
obj.__eq__ = <method-wrapper '__eq__' of Assign object at 0x104da7940>
obj.__format__ = <built-in method __format__ of Assign object at 0x104da7940>
obj.__ge__ = <method-wrapper '__ge__' of Assign object at 0x104da7940>
obj.__getattribute__ = <method-wrapper '__getattribute__' of Assign object at 0x104da7940>
obj.__gt__ = <method-wrapper '__gt__' of Assign object at 0x104da7940>
obj.__hash__ = <method-wrapper '__hash__' of Assign object at 0x104da7940>
obj.__init__ = <method-wrapper '__init__' of Assign object at 0x104da7940>
obj.__init_subclass__ = <built-in method __init_subclass__ of type object at 0x12e626220>
obj.__le__ = <method-wrapper '__le__' of Assign object at 0x104da7940>
obj.__lt__ = <method-wrapper '__lt__' of Assign object at 0x104da7940>
obj.__match_args__ = ('targets', 'value', 'type_comment')
obj.__module__ = 'ast'
obj.__ne__ = <method-wrapper '__ne__' of Assign object at 0x104da7940>
obj.__new__ = <built-in method __new__ of type object at 0x12e61b840>
obj.__reduce__ = <built-in method __reduce__ of Assign object at 0x104da7940>
obj.__reduce_ex__ = <built-in method __reduce_ex__ of Assign object at 0x104da7940>
obj.__repr__ = <method-wrapper '__repr__' of Assign object at 0x104da7940>
obj.__setattr__ = <method-wrapper '__setattr__' of Assign object at 0x104da7940>
obj.__sizeof__ = <built-in method __sizeof__ of Assign object at 0x104da7940>
obj.__str__ = <method-wrapper '__str__' of Assign object at 0x104da7940>
obj.__subclasshook__ = <built-in method __subclasshook__ of type object at 0x12e626220>
obj.__weakref__ = None
obj._attributes = ('lineno', 'col_offset', 'end_lineno', 'end_col_offset')
obj._fields = ('targets', 'value', 'type_comment')
obj.col_offset = 4
obj.end_col_offset = 17
obj.end_lineno = 4
obj.lineno = 4
obj.targets = [<ast.Name object at 0x104da7850>]
obj.type_comment = None
obj.value = <ast.Call object at 0x104da7730>
```

As I see it, the interesting information happens on line 49 and 51: `obj.targets` (to retrieve name of channel variable) but more importantly `obj.value` that has the actual channel. As can be seen, this is something being *called* at this point. And a dump of that... reveals nothing:

```


