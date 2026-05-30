def greeting(name: str = "Python project") -> str:
    return f"Hello from {name}"


def main() -> None:
    print(greeting())
