# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""
Object Editor Dialog based on PyQt4
"""

from PyQt4.QtCore import QObject, SIGNAL

class DialogKeeper(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.dialogs = {}
        self.namespace = None
        
    def set_namespace(self, namespace):
        self.namespace = namespace
    
    def create_dialog(self, dialog, refname, func):
        self.dialogs[id(dialog)] = dialog, refname, func
        self.connect(dialog, SIGNAL('accepted()'),
                     lambda eid=id(dialog): self.editor_accepted(eid))
        self.connect(dialog, SIGNAL('rejected()'),
                     lambda eid=id(dialog): self.editor_rejected(eid))
        dialog.show()
        dialog.activateWindow()
        dialog.raise_()
        
    def editor_accepted(self, dialog_id):
        dialog, refname, func = self.dialogs[dialog_id]
        self.namespace[refname] = func(dialog)
        self.dialogs.pop(dialog_id)
        
    def editor_rejected(self, dialog_id):
        self.dialogs.pop(dialog_id)

keeper = DialogKeeper()

def oedit(obj, modal=True, namespace=None):
    """
    Edit the object 'obj' in a GUI-based editor and return the edited copy
    (if Cancel is pressed, return None)

    The object 'obj' is a container
    
    Supported container types:
    dict, list, tuple, str/unicode or numpy.array
    
    (instantiate a new QApplication if necessary,
    so it can be called directly from the interpreter)
    """
    # Local import
    from spyderlib.widgets.texteditor import TextEditor
    from spyderlib.widgets.dicteditor import (DictEditor, ndarray, FakeObject,
                                              Image, is_known_type)
    from spyderlib.widgets.arrayeditor import ArrayEditor
    
    from spyderlib.utils.qthelpers import qapplication, install_translators
    app = qapplication()
    install_translators(app)
    
    if modal:
        obj_name = ''
    else:
        assert isinstance(obj, basestring)
        obj_name = obj
        if namespace is None:
            namespace = globals()
        keeper.set_namespace(namespace)
        obj = namespace[obj_name]

    conv_func = lambda data: data
    readonly = not is_known_type(obj)
    if isinstance(obj, ndarray) and ndarray is not FakeObject:
        dialog = ArrayEditor()
        if not dialog.setup_and_check(obj, title=obj_name,
                                      readonly=readonly):
            return
    elif isinstance(obj, Image) and Image is not FakeObject \
         and ndarray is not FakeObject:
        dialog = ArrayEditor()
        import numpy as np
        data = np.array(obj)
        if not dialog.setup_and_check(data, title=obj_name,
                                      readonly=readonly):
            return
        import PIL.Image
        conv_func = lambda data: PIL.Image.fromarray(data, mode=obj.mode)
    elif isinstance(obj, (str, unicode)):
        dialog = TextEditor(obj, title=obj_name, readonly=readonly)
    elif isinstance(obj, (dict, tuple, list)):
        dialog = DictEditor(obj, title=obj_name, readonly=readonly)
    else:
        raise RuntimeError("Unsupported datatype")
    
    def end_func(dialog):
        return conv_func(dialog.get_value())
    
    if modal:
        dialog.exec_()
        if dialog.result():
            return end_func(dialog)
    else:
        keeper.create_dialog(dialog, obj_name, end_func)
        import os
        if os.environ.get("SPYDER_PYQT_INPUTHOOK_REMOVED", None) \
           and not os.environ.get('IPYTHON', False):
            app.exec_()


def test():
    """Run object editor test"""
    import datetime, numpy as np, PIL.Image
    image = PIL.Image.fromarray(np.random.random_integers(255, size=(100, 100)))
    example = {'str': 'kjkj kj k j j kj k jkj',
               'list': [1, 3, 4, 'kjkj', None],
               'dict': {'d': 1, 'a': np.random.rand(10, 10), 'b': [1, 2]},
               'float': 1.2233,
               'array': np.random.rand(10, 10),
               'image': image,
               'date': datetime.date(1945, 5, 8),
               'datetime': datetime.datetime(1945, 5, 8),
               }
    image = oedit(image)
    print oedit(example)
    print oedit(np.random.rand(10, 10))
    print oedit(oedit.__doc__)
    print example
    
if __name__ == "__main__":
    test()
