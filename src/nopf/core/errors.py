from typing import Generator


def flatten_error_tree(excgroup: ExceptionGroup) -> Generator[Exception, None, None]:
    for exc in excgroup.exceptions:
        if isinstance(exc, ExceptionGroup):
            yield from flatten_error_tree(exc)

        else:
            yield exc
