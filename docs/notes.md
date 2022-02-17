# Random thoughts on thesis

We want (gradual) session types in Python. Our smaller research project had only focus on static checks on a channel abstraction with a recursive type definition:

```py
c1 = Channel[Send[int, Recv[float, End]]]
```

Problem is that to enforce correct usage, we had to do preinspection. We did this to a small extend, using the built-in `type(obj)`, but only worked for atomical values like strings, integers, booleans, etc.

```py
greeting = "hello there"
c1.send(greeting) # this failed since type(greeting) => type("hello there") => str != int
```

Now, we want to extend upon the static type system by defining environments that contains [variable -> type] associations and enforce their usage. However, there are vastly many AST nodes to handle, and hundres, if not thousands, of corner cases. Take the binary node as an example (`ast.BinOp`). Python allows numerics to be added and unionised:

```py
2 + 2 		# => 4 (OK, type int)
2 + 2.5	 	# => 4.5 (OK, type float)
2.5 + 2.5 	# => 5.0 (OK, type float)
```

But not strings:

```py
2 + "hi"	# Runtime TypeError: unsupported operand type(s) for +: 'int' and 'str'
```

But it does allow strings to be replicated under `*`:

```py
2 * "hi"	# => 'hihi' (OK)
"hello" * 5	# => 'hellohellohellohellohello' (OK)
"world" * 0	# => '' (OK)
```

Two cents: it's hard/time consuming to go into details about what's statically, Pythonically sound and what isn't. Also, with 50+ AST nodes in Python, there are many cases to handle (BinOp being just one).

In terms of our thesis, we'd like to have part static checks, part dynamic, but we find it hard where to draw the line. 

## Design decisions

### Starting the static checker: use decorators or not
Pros:
* can be provided with data (@typecheck_all(metadata))
* can be method specific (@typecheck_method)





