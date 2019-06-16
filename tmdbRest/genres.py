# genres.py

__doc__ = """genres.py"""
__version__ = "0.1"
__changelog__ = """

"""


class Genre:
    """Represents a genre"""
    def __init__(self, id, name):
        self._id = id
        self._name = name

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return f'{self._id} - {self.name}'

    @staticmethod
    def load(genres):
        """Generates a genres list from a list of strings"""
        return [Genre(*item) for item in genres]


if __name__ == '__main__':
    pass
