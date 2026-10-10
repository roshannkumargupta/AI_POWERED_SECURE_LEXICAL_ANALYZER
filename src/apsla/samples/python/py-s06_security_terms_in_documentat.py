def inspect_model(model):
    """Words eval, exec and os.system describe APIs, not calls."""
    # eval(user_text), exec(code), os.system(command)
    note = 'eval and exec are documentation terms'
    return model.eval()
