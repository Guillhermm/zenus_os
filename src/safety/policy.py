def check_step(step):
    if step.risk >= 3:
        raise PermissionError("High-risk operation blocked")

    return True
