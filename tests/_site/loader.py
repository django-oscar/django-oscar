class DummyClass:
    pass


def custom_class_loader(module_label, classnames, module_prefix):
    # For testing purposes just return a dummy class
    return [DummyClass for c in classnames]
