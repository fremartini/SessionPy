# Session Types in Python

Python implementation of gradual session types

This was a project completed as a Master’s Thesis at the IT University of Copenhagen in Spring 2022

## Projecting protocols

Global protocols written in Scribble-like syntax can be projected into a local protocol 
for each participant. The local protocols can then be projected into stub Python files 
the programmer can fill in. Below is a simple example of a protocol, see the Programs' folder for more examples. 

The main.py file contains functionality for running the entire pipeline.

```
type <List[int]> as payload;

global protocol SampleProtocol(role A, role B) {
    List(payload) from A to B;
    SumList(int) from B to A;
    ExitCode(int) from A to B;
    End;
}
```

Get projected into two local protocols, one for A and one for B:

```
# SampleProtocol_A.scr
type <List[int]> as payload;
local protocol SampleProtocol at A(role A,role B) {
    List(payload) to B;
    SumList(int) from B;
    ExitCode(int) to B;
    End;
}

# SampleProtocol_B.scr
type <List[int]> as payload;
local protocol SampleProtocol at B(role A,role B) {
    List(payload) from A;
    SumList(int) to A;
    ExitCode(int) from A;
    End;
}
```
That generates two Python files (imports omitted):

```python
# SampleProtocol_A.py
routing_table = {'self': ('localhost', 0), 'B': ('localhost', 0)}

ep = Endpoint(Send[List[int], 'B', Recv[int, 'B', Send[int, 'B', End]]], routing_table)

# SampleProtocol_B.py
routing_table = {'A': ('localhost', 0), 'self': ('localhost', 0)}

ep = Endpoint(Recv[List[int], 'A', Send[int, 'A', Recv[int, 'A', End]]], routing_table)
```

The programmer must fill in the implementation-specific details such as the routing table that maps roles to addresses, and the protocol itself using the operations defined below.

## Using the endpoints

The endpoints support four core operations: **Send**, **Recv**, **Choose** and **Offer**.

### Send
Send a message to the next role specified in the session type
```python
ep = Endpoint(Send[int, 'Someone', End], {})
ep.send(1) # send an int to 'Someone'
```

### Recv
Receive a message from the next role specified by the session type
```python
ep = Endpoint(Recv[int, 'Someone', End], {})
ep.recv() # recv an int from 'Someone'
```

### Offer
Offer several choices to the next role specified by the session type
```python
ep = Endpoint(Offer['Someone', {'add': Recv[int, 'Someone', Recv[int, 'Someone', Send[int, 'Someone', End]]], 'neg': Recv[int, 'Someone', Send[int, 'Someone', End]]}], {})
recipient_choice = ep.offer() # receive a choice from 'Someone'

match recipient_choice:
    case 'add':
        ...
    case 'neg':
        ...
```

### Choose
Choose an option received from 'Offer'
```python
ep = Endpoint(Choose['Someone', {'add': Send[int, 'Someone', Send[int, 'Someone', Recv[int, 'Someone', End]]], 'neg': Send[int, 'Someone', Recv[int, 'Someone', End]]}], {})
ep.choose('add') # choose the 'add' operation
```

## Checking modes

Optionally, the Endpoint supports static checking of the current file by toggling the ```static_check``` flag. This flag is set to **True**, by default

```python
ep = Endpoint(..., ..., static_check = False)
```
