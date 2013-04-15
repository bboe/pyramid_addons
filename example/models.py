class Item(object):

    """A simple class that mimics some behavior of a database backed class.

    Note that this class is _NOT_ thread safe. It is just for demonstration
    purposes.

    """

    items = {}
    max_id = 0

    @classmethod
    def fetch_by_id(cls, item_id):
        """Return the item at id `item_id` or None."""
        return cls.items.get(item_id, None)

    def __init__(self, name, value):
        self.id = Item.max_id
        self.name = name
        self.value = value
        Item.items[self.id] = self
        Item.max_id += 1


# Prepopulate with some data since it's volatile
Item('apple', 'so many varieties')
Item('banana', 'better when slightly brown')
