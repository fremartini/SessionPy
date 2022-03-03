class A:
    class B:
        def inner(self):
            print("inner")

    def say_hello(self):
        print("hello")

    def say_twice(self):
        print("twice")


i = A()
i.say_hello()

"""

Module(
    body=[
        ClassDef(
            name='A',
            bases=[],
            keywords=[],
            body=[
                FunctionDef(
                    name='say_hello',
                    args=arguments(
                        posonlyargs=[],
                        args=[
                            arg(arg='self')],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[]),
                    body=[
                        Expr(
                            value=Call(
                                func=Name(id='print', ctx=Load()),
                                args=[
                                    Constant(value='hello')],
                                keywords=[]))],
                    decorator_list=[])],
            decorator_list=[]),
        Assign(
            targets=[
                Name(id='i', ctx=Store())],
            value=Call(
                func=Name(id='A', ctx=Load()),
                args=[],
                keywords=[])),
        Expr(
            value=Call(
                func=Attribute(
                    value=Name(id='i', ctx=Load()),
                    attr='say_hello',
                    ctx=Load()),
                args=[],
                keywords=[]))],
    type_ignores=[])


"""