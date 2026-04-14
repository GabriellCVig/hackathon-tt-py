"""Import mapper for TypeScript to Python translation.

Reads tt_import_map.json and provides mapping functions for constructors,
function calls, method calls, and types.
"""

import json
from pathlib import Path
from typing import Optional


class ImportMapper:
    """Maps TypeScript library calls to Python equivalents."""

    def __init__(self, map_path: Optional[Path] = None):
        """Initialize the import mapper.

        Args:
            map_path: Path to tt_import_map.json. Defaults to tt/tt_import_map.json
                     (one level up from tt/tt/).
        """
        if map_path is None:
            map_path = Path(__file__).parent.parent / "tt_import_map.json"
        
        with open(map_path) as f:
            data = json.load(f)
        
        self._libraries = data["libraries"]
        self._type_map = data["libraries"]["type_mappings"]
        self._needed_imports: set[str] = set()

    def map_constructor(self, class_name: str, args: str) -> str:
        """Map a TypeScript constructor call to Python.

        Args:
            class_name: TypeScript class name (e.g., "Big")
            args: Constructor arguments as string

        Returns:
            Python constructor call
        """
        # Search all libraries for the class
        for lib_name, lib_data in self._libraries.items():
            if lib_name == "type_mappings":
                continue
            mappings = lib_data.get("mappings", {})
            if class_name in mappings:
                mapping = mappings[class_name]
                python_name = mapping["python_name"]
                import_stmt = mapping.get("import_stmt", "")
                if import_stmt:
                    self._needed_imports.add(import_stmt)
                return f"{python_name}({args})"
        
        # No mapping found - return as-is
        return f"{class_name}({args})"

    def map_function_call(self, func_name: str, args: list[str]) -> str:
        """Map a TypeScript function call to Python.

        Handles special cases like date-fns functions.

        Args:
            func_name: Function name
            args: List of argument strings

        Returns:
            Python function call or inline expression
        """
        # Search all libraries for the function
        for lib_name, lib_data in self._libraries.items():
            if lib_name == "type_mappings":
                continue
            mappings = lib_data.get("mappings", {})
            if func_name in mappings:
                mapping = mappings[func_name]
                python_name = mapping["python_name"]
                import_stmt = mapping.get("import_stmt", "")
                
                # Handle special inline cases
                if func_name == "differenceInDays" and len(args) == 2:
                    # differenceInDays(a, b) -> (a - b).days
                    return f"({args[0]} - {args[1]}).days"
                elif func_name == "isBefore" and len(args) == 2:
                    # isBefore(a, b) -> a < b
                    return f"{args[0]} < {args[1]}"
                elif func_name == "isAfter" and len(args) == 2:
                    # isAfter(a, b) -> a > b
                    return f"{args[0]} > {args[1]}"
                elif func_name == "format" and len(args) == 2:
                    # format(date, fmt) -> date.strftime(convert_fmt(fmt))
                    if import_stmt:
                        self._needed_imports.add(import_stmt)
                    return f"{python_name}({args[0]}, {args[1]})"
                elif func_name == "parseISO" and len(args) == 1:
                    # parseISO(s) -> datetime.fromisoformat(s)
                    self._needed_imports.add("from datetime import datetime")
                    return f"datetime.fromisoformat({args[0]}.replace('Z', '+00:00'))"
                elif func_name == "isNumber" and len(args) == 1:
                    # isNumber(x) -> isinstance(x, (int, float))
                    self._needed_imports.add("from decimal import Decimal")
                    return f"isinstance({args[0]}, (int, float, Decimal))"
                elif func_name == "sortBy" and len(args) >= 2:
                    # sortBy(arr, key) -> sorted(arr, key=key)
                    return f"sorted({args[0]}, key={args[1]})"
                elif func_name == "cloneDeep" and len(args) == 1:
                    # cloneDeep(x) -> copy.deepcopy(x)
                    self._needed_imports.add("from copy import deepcopy")
                    return f"deepcopy({args[0]})"
                elif func_name == "min" and len(args) == 1:
                    # min(dates) -> min(dates)
                    return f"min({args[0]})"
                elif func_name == "sum" and len(args) == 1:
                    # sum(arr) -> sum(arr)
                    return f"sum({args[0]})"
                else:
                    # Standard function call
                    if import_stmt:
                        self._needed_imports.add(import_stmt)
                    args_str = ", ".join(args)
                    return f"{python_name}({args_str})"
        
        # No mapping found - return as-is
        args_str = ", ".join(args)
        return f"{func_name}({args_str})"

    def map_method_call(self, obj: str, method: str, args: list[str]) -> str:
        """Map a TypeScript method call to Python.

        Handles Big.js, array, string, and Map/Object methods.

        Args:
            obj: Object expression
            method: Method name
            args: List of argument strings

        Returns:
            Python method call or inline expression
        """
        args_str = ", ".join(args) if args else ""
        
        # Big.js methods
        if method == "plus":
            return f"{obj} + {args[0]}" if args else obj
        elif method == "minus":
            return f"{obj} - {args[0]}" if args else obj
        elif method == "mul":
            return f"{obj} * {args[0]}" if args else obj
        elif method == "div":
            return f"{obj} / {args[0]}" if args else obj
        elif method == "toNumber":
            return f"float({obj})"
        elif method == "toFixed" and args:
            return f"round({obj}, {args[0]})"
        elif method == "gt":
            return f"{obj} > {args[0]}" if args else obj
        elif method == "gte":
            return f"{obj} >= {args[0]}" if args else obj
        elif method == "lt":
            return f"{obj} < {args[0]}" if args else obj
        elif method == "lte":
            return f"{obj} <= {args[0]}" if args else obj
        elif method == "eq":
            return f"{obj} == {args[0]}" if args else obj
        elif method == "abs":
            return f"abs({obj})"
        
        # Array methods
        elif method == "push":
            return f"{obj}.append({args_str})"
        elif method == "filter":
            return f"[x for x in {obj} if {args[0]}(x)]" if args else f"list({obj})"
        elif method == "map":
            return f"[{args[0]}(x) for x in {obj}]" if args else f"list({obj})"
        elif method == "length":
            return f"len({obj})"
        elif method == "includes":
            return f"{args[0]} in {obj}" if args else f"False"
        elif method == "find":
            return f"next((x for x in {obj} if {args[0]}(x)), None)" if args else "None"
        elif method == "reduce":
            self._needed_imports.add("import functools")
            if len(args) >= 2:
                return f"functools.reduce({args[0]}, {obj}, {args[1]})"
            elif len(args) == 1:
                return f"functools.reduce({args[0]}, {obj})"
            else:
                return obj
        elif method == "forEach":
            # Cannot directly translate - need statement context
            return f"# TODO: forEach - convert to for loop: for x in {obj}: {args[0]}(x)"
        elif method == "some":
            return f"any({args[0]}(x) for x in {obj})" if args else f"any({obj})"
        elif method == "every":
            return f"all({args[0]}(x) for x in {obj})" if args else f"all({obj})"
        elif method == "slice":
            if len(args) == 2:
                return f"{obj}[{args[0]}:{args[1]}]"
            elif len(args) == 1:
                return f"{obj}[{args[0]}:]"
            else:
                return f"{obj}[:]"
        elif method == "splice":
            if len(args) >= 2:
                return f"del {obj}[{args[0]}:{args[0]}+{args[1]}]"
            else:
                return obj
        elif method == "join":
            return f"{args[0]}.join({obj})" if args else f"''.join({obj})"
        
        # String methods
        elif method == "toString":
            return f"str({obj})"
        elif method == "startsWith":
            return f"{obj}.startswith({args_str})"
        elif method == "endsWith":
            return f"{obj}.endswith({args_str})"
        
        # Map/Object methods (already Python-compatible in most cases)
        elif method == "keys":
            return f"{obj}.keys()"
        elif method == "values":
            return f"{obj}.values()"
        elif method == "entries":
            return f"{obj}.items()"
        elif method == "has":
            return f"{args[0]} in {obj}" if args else "False"
        elif method == "get":
            return f"{obj}.get({args_str})"
        elif method == "set":
            if len(args) >= 2:
                return f"{obj}[{args[0]}] = {args[1]}"
            else:
                return obj
        elif method == "delete":
            return f"del {obj}[{args[0]}]" if args else obj
        
        # Default: standard method call
        else:
            return f"{obj}.{method}({args_str})"

    def map_type(self, ts_type: str) -> str:
        """Map a TypeScript type to Python type hint.

        Args:
            ts_type: TypeScript type string

        Returns:
            Python type hint string
        """
        return self._type_map.get(ts_type, ts_type)

    def get_needed_imports(self) -> list[str]:
        """Get all import statements needed for mapped calls.

        Returns:
            Sorted list of import statements
        """
        return sorted(self._needed_imports)
