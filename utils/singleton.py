def singleton(cls):
    """
    单例模式装饰器：确保类在整个程序中只有一个实例
    """
    _instances = {}
    def get_instance(*args, **kwargs):
        if cls not in _instances:
            _instances[cls] = cls(*args, **kwargs)
        return _instances[cls]
    return get_instance