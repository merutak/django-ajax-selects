import json
from django.http import HttpResponse
from django.utils.encoding import force_text
from django.utils.html import conditional_escape

from ajax_select import registry


def ajax_lookup(request, channel):

    """Load the named lookup channel and lookup matching models.

    GET or POST should contain 'term'

    Returns:
        HttpResponse - JSON: `[{pk: value: match: repr:}, ...]`
    Raises:
        PermissionDenied - depending on the LookupChannel's implementation of check_auth
    """
    query = request.GET.get('term') or request.GET.get('q') or request.POST.get('term') or request.POST.get('q')
    if not query:
        return HttpResponse('[]', content_type='application/json')


    lookup = registry.get(channel)
    if hasattr(lookup, 'check_auth'):
        lookup.check_auth(request)

    if len(query) >= getattr(lookup, 'min_length', 1):
        instances = lookup.get_query(query, request)
    else:
        instances = []

    def origin(item):
        origlu = getattr(item, 'origin', None)
        if not origlu:
            return None
        return origlu.model.__name__

    results = json.dumps([
        {
            lookup.id_field_name: force_text(getattr(item, 'pk', None)),
            'value': conditional_escape(lookup.get_result(item)),
            'match': conditional_escape(lookup.format_match(item)),
            'repr': conditional_escape(lookup.format_item_display(item)),
            'link': safe_link(lookup.get_link(item)) if request.user.is_authenticated() and request.user.is_staff else '',
            'origin': conditional_escape(origin(item)),
        } for item in instances
    ])

    response = HttpResponse(results, content_type='application/json')
    response['Cache-Control'] = 'max-age=0, must-revalidate, no-store, no-cache;'
    return response


def safe_link(l):
    assert '<' not in l
    return l
