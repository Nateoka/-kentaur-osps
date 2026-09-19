"""Resolve the actual generator configuration; never ignore frozen weights/bounds."""
from copy import deepcopy as cp
from math import factorial
from .errors import Failure


def resolve_options(config,family,difficulty):
    options=config["generator_options"];value=cp(difficulty)
    if family=="SYMBOLIC_PIPELINE":
        defaults=dict(weights=options["operation_weights"],max_abs=options["max_abs_intermediate"],max_attempts=options["max_attempts"])
        allowed={"n","length",*defaults}
    else:
        if factorial(value["n"])**value["k"]>options["max_grid_assignments"]:raise Failure("CONFIGURATION_FAILURE","GRID_ASSIGNMENT_CONFIG_BOUND")
        defaults=dict(weights=options["constraint_weights"],min_clues=options["min_clue_factor"]*value["n"],
            max_clues=options["max_clue_factor"]*value["n"]*value["k"],max_attempts=options["max_attempts"])
        allowed={"n","k",*defaults}
    if set(value)-allowed:raise Failure("CONFIGURATION_FAILURE","UNKNOWN_DIFFICULTY_FIELD")
    for name,default in defaults.items():
        if name in value and value[name]!=default:raise Failure("CONFIGURATION_FAILURE","TUPLE_CONFIG_OPTION_CONFLICT")
        value[name]=cp(default)
    return value
