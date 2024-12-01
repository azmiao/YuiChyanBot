import os


class ResObj:
    def __init__(self, res_path):
        self.res_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'yuiChyan', 'res')
        self.__path = os.path.normpath(res_path)

    @property
    def path(self):
        return os.path.join(self.res_dir, self.__path)

    @property
    def exist(self):
        return os.path.exists(self.path)


def img(path, *paths):
    return ResObj(os.path.join('img', path, *paths))
