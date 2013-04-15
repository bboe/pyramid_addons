from .helpers import DBThing
from .models import Item
from pyramid.view import view_config
from pyramid_addons.helpers import http_created, site_layout
from pyramid_addons.validation import (SOURCE_MATCHDICT, String, TextNumber,
                                       validate)


@view_config(route_name='home', renderer='templates/home.pt',
             request_method='GET')
@site_layout('example:templates/layout.pt')
def home(request):
    return {'page_title': 'Home', 'items': Item.items.values()}


@view_config(route_name='item', renderer='json', request_method='PUT')
@validate(name=String('name', min_length=1, max_length=10),
          value=String('value', min_length=5, max_length=128, optional=True,
                       default='...No value specified...'))
def item_create(request, name, value):
    item = Item(name, value)
    url = request.route_url('item_item', item_id=item.id)
    return http_created(request, redir_location=url)


@view_config(route_name='item_item', renderer='templates/item.pt',
             request_method='GET')
@validate(item=DBThing('item_id', Item,
                       TextNumber(None, min_value=0),
                       source=SOURCE_MATCHDICT))
@site_layout('example:templates/layout.pt')
def item_view(request, item):
    return {'page_title': item.name, 'item': item}
