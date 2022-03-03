def matcher(node: str) -> str:
    match 5 + 2:
        case k if k == 2:
            return "empty"
        case _:
            return "base"

"""
 Match(
    subject=Name(id='node', ctx=Load()),
    cases=[
        match_case(
            pattern=MatchAs(name='k'),
            guard=Compare(
                left=Name(id='node', ctx=Load()),
                ops=[
                    Eq()],
                comparators=[
                    Constant(value='')]),
            body=[
                Return(
                    value=Constant(value='empty'))]),
        match_case(
            pattern=MatchAs(name='n'),
            body=[
                Return(
                    value=Name(id='n', ctx=Load()))])])


"""