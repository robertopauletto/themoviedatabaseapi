# genres.py

__doc__ = """Show Genres"""


class Genre:
    """Represents a genre"""
    def __init__(self, id: int, name: str):
        self._id = id
        self.name = name

    def __repr__(self) -> str:
        return f'<Genre {self._id} - {self.name}>'

    def __str__(self) -> str:
        return f'{self._id} - {self.name}'

    @classmethod
    def load(cls, genres: list) -> list:
        """Generates a list of `Genre` instances from a list of strings"""
        return [Genre(*item) for item in genres]


if __name__ == '__main__':
    pass
