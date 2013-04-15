from pyramid.config import Configurator


def add_routes(config):
    """Add the routes to the pyramid configuration."""
    config.add_route('form_item', '/form_item')
    config.add_route('home', '/')
    config.add_route('item', '/item')
    config.add_route('item_item', '/item/{item_id}')


def main():
    """Build and return the Pyramid WSGI application."""
    config = Configurator()
    add_routes(config)
    config.scan()
    return config.make_wsgi_app()
