# Session types in Python

## Getting started

Use the verify_channels decorator on functions that contains Channel definitions to statically check their use. 

```python
from channel import *
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
  ch = Channel[Recv[int, Recv[int, Send[int, End]]]]()
  x = ch.recv()
  print(f"Received {x}")
  ch.send(5)
```

## Primitives

### Send
Send a message on a channel
```python
@verify_channels
def main():
  ch = Channel[Send[int, End]]()
  ch.send(1)
```

### Recv
Receive a message from a channel
```python
@verify_channels
def main():
  ch = Channel[Recv[int, End]]()
  x = ch.recv()
  print(f"Received {x}")
```

### Offer
Offer the recipient two choices
```python
@verify_channels
def main():
  ch = Channel[Offer[Send[str, Recv[int, End]], Send[int, End]]]()
  match ch.offer():
    case Branch.LEFT:
        ch.send("foo")

    case Branch.RIGHT:
        ch.send(42)
```

### Choose
Choose a path received from 'Offer'
```python
@verify_channels
def main():
  ch = Channel[Choose[Send[str, End], Send[int, End]]]()
  if 2 > 1:
    ch.choose(Branch.LEFT)
    ch.send("foo")
  else:
    ch.choose(Branch.RIGHT)
    ch.send(42)
```
