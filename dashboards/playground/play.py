def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before the function runs")
        result = func(*args, **kwargs)
        print("After the function runs")
        return result
    return wrapper

@my_decorator
def greet(name):
    print(f"Hello, {name}!")


if __name__ == "__main__":
    greet("Lauren")
    