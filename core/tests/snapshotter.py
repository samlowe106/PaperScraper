from collections import defaultdict
from typing import Callable, DefaultDict, List

function_snaps: DefaultDict[str, DefaultDict[str: List[str]]]\
    = defaultdict(lambda : defaultdict(lambda : []))

def write_test_file(filename: str) -> None:
    """
    Writes test cases to a file
    """
    with open(filename, 'w', encoding='UTF-8') as snap_file:
        snap_file.dumps(function_snaps, indent=4)
        #snap_file.write("import unittest\n\n")
        #for class_name in function_snaps:
        #    snap_file.write("class Test{class_name}(unittest.TestCase):")
        #    for func_name in function_snaps[class_name]:
        #        snap_file.write("\tdef test_{func_name}(self):")
        #        for test_case in function_snaps[class_name][func_name]:
        #            snap_file.write((2 * "\t") + test_case)
        #        snap_file.write(2*"\n")
        #    snap_file.write(2*"\n")


def snapshot(filename: str) -> Callable:
    """
    Snapshots all calls of the decorated function and generates a test based on the returned value
    """
    def decorator(func: Callable) -> Callable:
        classkey = func.__qualname__.split(".")[0] if func.__class__=="method" else "function"

        def wrapper(*args, **kwargs):
            arg_dicts = [{"str" : str(arg), "vars": vars(arg)} for arg in args]
            output = func(*args, **kwargs)
            output_dict = {"str": str(output), "vars": vars(output)}

            function_snaps[classkey][func.__name__].append(
                {"inputs" : arg_dicts, "output": output_dict}
                )

            #arg_string = ",".join([str(a) for a in args] + [f'{k}={v}' for k, v in kwargs])
            write_test_file(filename)

            return output
        return wrapper
    return decorator
