from nopf.core.errors import flatten_error_tree


def test_flatten_error_tree():
    tree = ExceptionGroup(
        "group1",
        [
            ExceptionGroup(
                "group2",
                [
                    ValueError("1"),
                    ExceptionGroup(
                        "group3",
                        [
                            ValueError("2"),
                            ValueError("3"),
                        ],
                    ),
                ],
            ),
            ValueError("4"),
        ],
    )

    errors = list(flatten_error_tree(tree))
    assert len(errors) == 4
    assert [str(err) for err in errors] == ["1", "2", "3", "4"]
