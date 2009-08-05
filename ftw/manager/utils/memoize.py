

def memoize(func):
    def _mem(*args, **kwargs):
        key = (args, tuple(kwargs.items()))
        dic = getattr(func, '_memoize_dict', {})
        if key not in dic.keys():
            dic[key] = func(*args, **kwargs)
            setattr(func, '_memoize_dict', dic)
        return dic[key]
    return _mem

