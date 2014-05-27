def bar():
    return 3

def foo():
    ret_val = 1
    try:
        ret_val = bar()
    except Exception:
        ret_val = 2
    finally:
        return ret_val

print foo()
