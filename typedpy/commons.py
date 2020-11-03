
def wrap_val(v):
    return "'{}'".format(v) if isinstance(v, str) else v
