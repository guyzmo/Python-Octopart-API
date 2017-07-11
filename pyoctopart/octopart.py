#!/usr/bin/env python
"""
pyoctopart: A simple Python client library to the Octopart public REST API.

author: Bernard `Guyzmo` Pratz <octopart@m0g.net>
author: Joe Baker <jbaker@alum.wpi.edu>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import copy
import json
import requests
import datetime
import pkg_resources

from pprint import pprint

from .exceptions import OctopartArgumentMissingError
from .exceptions import OctopartArgumentInvalidError
from .exceptions import OctopartTypeArgumentError
from .exceptions import OctopartRangeArgumentError
from .exceptions import OctopartStringLengthError
from .exceptions import OctopartLimitExceededError
from .exceptions import Octopart404Error
from .exceptions import Octopart503Error
from .exceptions import OctopartNonJsonArgumentError
from .exceptions import OctopartInvalidSortError
from .exceptions import OctopartTooLongListError
from .exceptions import OctopartInvalidApiKeyError
from .exceptions import OctopartApiThrottleError

__version__ = pkg_resources.require('pyoctopart')[0].version
__author__ = 'Joe Baker <jbaker at alum.wpi.edu>'
__contributors__ = ['Bernard `Guyzmo` Pratz <pyoctopart at m0g dot net>']

''' Utility features '''

class curry:
    def __init__(self, fun, *args, **kwargs):
        self.fun = fun
        self.pending = args[:]
        self.kwargs = kwargs.copy()

    def __call__(self, *args, **kwargs):
        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs

        return self.fun(*(self.pending + args), **kw)


def select(param, d):
    return {k: v for k, v in d.items() if param in k}

select_incls=curry(select, 'include_')
select_shows=curry(select, 'show_')
select_hides=curry(select, 'hide_')


''' Octopart Data maps '''

class OctopartBrand(object):
    def __init__(self, id, dispname, homepage):
        self._id = id
        self.displayname = dispname
        self.homepage_url = homepage

    @classmethod
    def new_from_dict(cls, brand_dict):
        new = cls(brand_dict['id'], brand_dict['displayname'], brand_dict['homepage_url'])
        return new

    @property
    def id(self):
        return self._id

    def equals_json(self, resource):
        """Checks the object for data equivalence to a JSON Brand resource."""

        if isinstance(resource, dict) and resource.get('__class__') == 'Brand':
            if self.id != resource.get('id'):
                return False
            if self.displayname != resource.get('displayname'):
                return False
            if self.homepage_url != resource.get('homepage_url'):
                return False
        else:
            return False
        return True

    def __eq__(self, b):
        if isinstance(b, OctopartBrand):
            try:
                if self.id != b.id:
                    return False
                if self.displayname != b.displayname:
                    return False
                if self.homepage_url != b.homepage_url:
                    return False
            except AttributeError:
                return False
        else:
            return False
        return True

    def __ne__(self, b):
        return not self.__eq__(b)

    def __hash__(self):
        return (hash(self.__class__), hash(self.id))

    def __str__(self):
        return ''.join(('Brand ', str(self.id), ': ', self.displayname, ' (', self.homepage_url, ')'))

class OctopartCategory(object):

    @classmethod
    def new_from_dict(cls, category_dict):
        new_dict = copy.deepcopy(category_dict)
        new = cls(new_dict['id'], new_dict['parent_id'], new_dict['nodename'], \
                            new_dict['images'], new_dict['children_ids'], new_dict['ancestor_ids'], \
                            new_dict.get('ancestors', []), new_dict['num_parts'])
        return new

    def __init__(self, id, parent_id, nodename, images, children_ids, ancestor_ids, ancestors, num_parts):
        self._id = id
        self.parent_id = parent_id
        self.nodename = nodename
        self.images = images    # List of dicts of URLs
        self.children_ids = children_ids    # List of child node ids
        self.ancestor_ids = ancestor_ids    # Sorted list of ancestor node ids (immediate parent first)
        self.ancestors = ancestors    # Sorted list of category objects
        self.num_parts = num_parts

    @property
    def id(self):
        return self._id

    def equals_json(self, resource):
        """Checks the object for data equivalence to a JSON Category resource."""

        if isinstance(resource, dict) and resource.get('__class__') == 'Category':
            if self.id != resource.get('id'):
                return False
            if self.parent_id != resource.get('parent_id'):
                return False
            if self.nodename != resource.get('nodename'):
                return False
            if sorted(self.images) != sorted(resource.get('images')):
                return False
            if sorted(self.children_ids) != sorted(resource.get('children_ids')):
                return False
            if sorted(self.ancestor_ids) != sorted(resource.get('ancestor_ids')):
                return False
            if set(self.ancestors) != set(resource.get('ancestors', [])):
                return False
            if self.num_parts != resource.get('num_parts'):
                return False
        else:
            return False
        return True

    def __eq__(self, c):
        if isinstance(c, OctopartCategory):
            try:
                if self.id != c.id:
                    return False
                if self.parent_id != c.parent_id:
                    return False
                if self.nodename != c.nodename:
                    return False
                if sorted(self.images != c.images):
                    return False
                if sorted(self.children_ids) != sorted(c.children_ids):
                    return False
                if sorted(self.ancestor_ids) != sorted(c.ancestor_ids):
                    return False
                if set(self.ancestors) != set(c.ancestors):
                    return False
                if self.num_parts != c.num_parts:
                    return False
            except AttributeError:
                return False
        else:
            return False
        return True

    def __ne__(self, c):
        return not self.__eq__(c)

    def __hash__(self):
        return (hash(self.__class__), hash(self.id))

    def __str__(self):
        return ''.join(('Category ', str(self.id), ': ', self.nodename))


class OctopartManufacturer(object):
    pass

class OctopartPart(object):
    @classmethod
    def includes(cls,
                 include_short_description: bool = False,
                 include_datasheets: bool = False,
                 include_compliance_documents: bool = False,
                 include_descriptions: bool = False,
                 include_imagesets: bool = False,
                 include_specs: bool = False,
                 include_category_uids: bool = False,
                 include_external_links: bool = False,
                 include_reference_designs: bool = False,
                 include_cad_models: bool = False):
        args = {'include[]':[]}
        if include_short_description is True:     args['include[]']+=['short_description']
        if include_datasheets is True:            args['include[]']+=['datasheets']
        if include_compliance_documents is True:  args['include[]']+=['compliante_documents']
        if include_descriptions is True:          args['include[]']+=['descriptions']
        if include_imagesets is True:             args['include[]']+=['imagesets']
        if include_specs is True:                 args['include[]']+=['specs']
        if include_category_uids is True:         args['include[]']+=['category_uids']
        if include_external_links is True:        args['include[]']+=['external_links']
        if include_reference_designs is True:     args['include[]']+=['reference_designs']
        if include_cad_models is True:            args['include[]']+=['cad_models']
        return args

    @classmethod
    def shows(cls,
              show_uid: bool = False,
              show_mpn: bool = False,
              show_manufacturer: bool = False,
              show_brand: bool = False,
              show_octopart_url: bool = False,
              show_external_links: bool = False,
              show_offers: bool = False,
              show_broker_listings: bool = False,
              show_short_description: bool = False,
              show_descriptions: bool = False,
              show_imagesets: bool = False,
              show_datasheets: bool = False,
              show_compliance_documents: bool = False,
              show_reference_designs: bool = False,
              show_cad_models: bool = False,
              show_specs: bool = False,
              show_category_uids:bool = False):
        args = {'show[]':[]}
        if show_uid is True:                   args['show[]']+=['uid']
        if show_mpn is True:                   args['show[]']+=['mpn']
        if show_manufacturer is True:          args['show[]']+=['manufacturer']
        if show_brand is True:                 args['show[]']+=['brand']
        if show_octopart_url is True:          args['show[]']+=['octopart_url']
        if show_offers is True:                args['show[]']+=['offers']
        if show_broker_listings is True:       args['show[]']+=['broker_listings']
        if show_short_description is True:     args['show[]']+=['short_description']
        if show_datasheets is True:            args['show[]']+=['datasheets']
        if show_compliance_documents is True:  args['show[]']+=['compliante_documents']
        if show_descriptions is True:          args['show[]']+=['descriptions']
        if show_imagesets is True:             args['show[]']+=['imagesets']
        if show_specs is True:                 args['show[]']+=['specs']
        if show_category_uids is True:         args['show[]']+=['category_uids']
        if show_external_links is True:        args['show[]']+=['external_links']
        if show_reference_designs is True:     args['show[]']+=['reference_designs']
        if show_cad_models is True:            args['show[]']+=['cad_models']
        return args

    @classmethod
    def hides(cls,
              hide_uid: bool = False,
              hide_mpn: bool = False,
              hide_manufacturer: bool = False,
              hide_brand: bool = False,
              hide_octopart_url: bool = False,
              hide_external_links: bool = False,
              hide_offers: bool = False,
              hide_broker_listings: bool = False,
              hide_short_description: bool = False,
              hide_descriptions: bool = False,
              hide_imagesets: bool = False,
              hide_datasheets: bool = False,
              hide_compliance_documents: bool = False,
              hide_reference_designs: bool = False,
              hide_cad_models: bool = False,
              hide_specs: bool = False,
              hide_category_uids:bool = False):
        args = {'hide[]':[]}
        if hide_uid is True:                   args['hide[]']+=['uid']
        if hide_mpn is True:                   args['hide[]']+=['mpn']
        if hide_manufacturer is True:          args['hide[]']+=['manufacturer']
        if hide_brand is True:                 args['hide[]']+=['brand']
        if hide_octopart_url is True:          args['hide[]']+=['octopart_url']
        if hide_offers is True:                args['hide[]']+=['offers']
        if hide_broker_listings is True:       args['hide[]']+=['broker_listings']
        if hide_short_description is True:     args['hide[]']+=['short_description']
        if hide_datasheets is True:            args['hide[]']+=['datasheets']
        if hide_compliance_documents is True:  args['hide[]']+=['compliante_documents']
        if hide_descriptions is True:          args['hide[]']+=['descriptions']
        if hide_imagesets is True:             args['hide[]']+=['imagesets']
        if hide_specs is True:                 args['hide[]']+=['specs']
        if hide_category_uids is True:         args['hide[]']+=['category_uids']
        if hide_external_links is True:        args['hide[]']+=['external_links']
        if hide_reference_designs is True:     args['hide[]']+=['reference_designs']
        if hide_cad_models is True:            args['hide[]']+=['cad_models']
        return args


    @classmethod
    def new_from_dict(cls, part_dict):
        """Constructor for use with JSON resource dictionaries."""

        copied_dict = part_dict.copy()
        uid = copied_dict.pop('uid')
        mpn = copied_dict.pop('mpn')
        manufacturer = copied_dict.pop('manufacturer')
        detail_url = copied_dict.pop('detail_url')
        return cls(uid, mpn, manufacturer, detail_url, **copied_dict)

    def __init__(self, uid, mpn, manufacturer, detail_url, **kwargs):
        # If class data is in dictionary format, convert everything to class instances
        # Otherwise, assume it is already in class format and do nothing
        args = copy.deepcopy(kwargs)
        if type(manufacturer) is dict:
            manufacturer = OctopartBrand.new_from_dict(copy.deepcopy(manufacturer))
        for offer in args.get('offers', []):
            if type(offer['supplier']) is dict:
                offer['supplier'] = OctopartBrand.new_from_dict(offer['supplier'])
            # Convert ISO 8601 datetime strings to datetime objects
            if 'update_ts' in offer:
                # Strip 'Z' UTC notation that can't be parsed
                if offer['update_ts'][-1] == 'Z':
                    offer['update_ts'] = offer['update_ts'][0:-1]
                offer['update_ts'] = datetime.datetime.strptime(offer['update_ts'], '%Y-%m-%dT%H:%M:%S')

        for spec in args.get('specs', []):
            if type(spec['attribute']) is dict:
                spec['attribute'] = OctopartPartAttribute.new_from_dict(spec['attribute'])

        self._uid = uid
        self._mpn = mpn
        self.manufacturer = manufacturer
        self.detail_url = detail_url
        self.avg_price = args.get('avg_price')
        self.avg_avail = args.get('avg_avail')
        self.market_status = args.get('market_status')
        self.num_suppliers = args.get('num_suppliers')
        self.num_authsuppliers = args.get('num_authsuppliers')
        self.short_description = args.get('short_description', '')
        self.category_ids = args.get('category_ids', [])
        self.images = args.get('images', [])
        self.datasheets = args.get('datasheets', [])
        self.descriptions = args.get('descriptions', [])
        self.hyperlinks = args.get('hyperlinks', {})
        self.offers = args.get('offers', [])
        self.specs = args.get('specs', [])

    @property
    def uid(self):
        return self._uid

    @property
    def mpn(self):
        return self._mpn

    def get_authorized_offers(self):
        return [o for o in self.offers if o['is_authorized'] is True]

    def get_unauthorized_offers(self):
        return [o for o in self.offers if o['is_authorized'] is False]

    def equals_json(self, resource, hide_datasheets=False, hide_descriptions=False, hide_images=False, \
                hide_offers=False, hide_unauthorized_offers=False, hide_specs=False):
        """Checks the object for data equivalence to a JSON Part resource."""

        def compare_offers(class_offer, json_offer):
            """
            Compares two offers.
            class_offer: An offer from an OctopartPart instance.
            json_offer: An offer from a JSON Part resource.
            """

            class_attribs = (class_offer['sku'], class_offer['avail'], class_offer['prices'], \
                            class_offer['is_authorized'], class_offer.get('clickthrough_url'), \
                            class_offer.get('buynow_url'), class_offer.get('sendrfq_url'))
            json_attribs = (json_offer['sku'], json_offer['avail'], json_offer['prices'], \
                            json_offer['is_authorized'], json_offer.get('clickthrough_url'), \
                            json_offer.get('buynow_url'), json_offer.get('sendrfq_url'))
            if class_attribs != json_attribs:
                return False
            if not class_offer['supplier'].equals_json(json_offer['supplier']):
                return False
            return True

        def compare_specs(class_spec, json_spec):
            """
            Compares two specs.
            class_spec: A spec from an OctopartPart instance.
            json_spec: A spec from a JSON Part resource.
            """

            if not class_spec['attribute'].equals_json(json_spec['attribute']):
                return False
            if sorted(class_spec['values']) != sorted(json_spec['values']):
                return False
            return True

        if isinstance(resource, dict) and resource.get('__class__') == 'Part':
            if self.uid != resource.get('uid'):
                return False
            if self.mpn != resource.get('mpn'):
                return False
            if not self.manufacturer.equals_json(resource.get('manufacturer')):
                return False
            if self.detail_url != resource.get('detail_url'):
                return False
            if self.avg_price != resource.get('avg_price'):
                return False
            if self.avg_avail != resource.get('avg_avail'):
                return False
            if self.market_status != resource.get('market_status'):
                return False
            if self.num_suppliers != resource.get('num_suppliers'):
                return False
            if self.num_authsuppliers != resource.get('num_authsuppliers'):
                return False
            if self.short_description != resource.get('short_description', ''):
                return False
            if sorted(self.category_ids) != sorted(resource.get('category_ids', [])):
                return False
            if hide_images is False and sorted(self.images) != sorted(resource.get('images', [])):
                return False
            if hide_datasheets is False and sorted(self.datasheets) != sorted(resource.get('datasheets', [])):
                return False
            if hide_descriptions is False and sorted(self.descriptions) != sorted(resource.get('descriptions', [])):
                return False
            if self.hyperlinks != resource.get('hyperlinks', {}):
                return False
            if hide_offers is False:
                checked_offers = []
                if hide_unauthorized_offers:
                    checked_offers = sorted(self.get_unauthorized_offers())
                else:
                    checked_offers = sorted(self.offers)
                for offer in checked_offers:
                    truth = [compare_offers(offer, other) for other in sorted(resource.get('offers', []))]
                    if True not in truth:
                        return False
            if not hide_specs:
                for spec in sorted(self.specs):
                    truth = [compare_specs(spec, other) for other in sorted(resource.get('specs', []))]
                    if True not in truth:
                        return False
        else:
            return False
        return True

    def __eq__(self, p):
        if isinstance(p, OctopartPart):
            try:
                if self.uid != p.uid:
                    return False
                if self.mpn != p.mpn:
                    return False
                if self.manufacturer != p.manufacturer:
                    return False
                if self.detail_url != p.detail_url:
                    return False
                if self.avg_price != p.avg_price:
                    return False
                if self.avg_avail != p.avg_avail:
                    return False
                if self.market_status != p.market_status:
                    return False
                if self.num_suppliers != p.num_suppliers:
                    return False
                if self.num_authsuppliers != p.num_authsuppliers:
                    return False
                if self.short_description != p.short_description:
                    return False
                if self.category_ids != p.category_ids:
                    return False
                if self.images != p.images:
                    return False
                if self.datasheets != p.datasheets:
                    return False
                if self.descriptions != p.descriptions:
                    return False
                if self.hyperlinks != p.hyperlinks:
                    return False
                if self.offers != p.offers:
                    return False
                if self.specs != p.specs:
                    return False
            except AttributeError:
                return False
        else:
            return False
        return True

    def __ne__(self, p):
        return not self.__eq__(p)

    def __hash__(self):
        return (hash(self.__class__), hash(self.uid), hash(self.mpn))

    def __str__(self):
        return ''.join(('Part ', str(self.uid), ': ', str(self.manufacturer), ' ', self.mpn))

class OctopartPartAttribute(object):
    TYPE_TEXT = 'text'
    TYPE_NUMBER = 'number'

    @classmethod
    def new_from_dict(cls, attribute_dict):
        new = cls(attribute_dict['fieldname'], attribute_dict['displayname'], attribute_dict['type'], attribute_dict.get('metadata', {}))
        return new

    def __init__(self, fieldname, displayname, attribute_type, metadata):
        self._fieldname = fieldname
        self.displayname = displayname
        self.type = attribute_type
        self.metadata = metadata

    @property
    def fieldname(self):
        return self._fieldname

    def equals_json(self, resource):
        """Checks the object for data equivalence to a JSON PartAttribute resource."""

        if isinstance(resource, dict) and resource.get('__class__') == 'PartAttribute':
            if self.fieldname != resource.get('fieldname'):
                return False
            if self.displayname != resource.get('displayname'):
                return False
            if self.type != resource.get('type'):
                return False
            if self.metadata != resource.get('metadata', {}):
                return False
        else:
            return False
        return True

    def __eq__(self, pa):
        if isinstance(pa, OctopartPartAttribute):
            try:
                if self.fieldname != pa.fieldname:
                    return False
                if self.displayname != pa.displayname:
                    return False
                if self.type != pa.type:
                    return False
                if self.metadata != pa.metadata:
                    return False
            except AttributeError:
                return False
        else:
            return False
        return True

    def __ne__(self, pa):
        return not self.__eq__(pa)

    def __hash__(self):
        return (hash(self.__class__), hash(self.fieldname))

    def __str__(self):
        if self.type == 'number':
            return ''.join((self.displayname, 'attribute: ', self.metadata['datatype'], ' (', self.metadata['unit']['name'], ')'))
        elif self.type == 'text':
            return ''.join((self.displayname, 'attribute: ', self.type))
        else:    # Note: 'else' is not a valid state in the API resource definition
            return self.displayname


''' Octopart API proxy '''

class Octopart(object):

    """A simple client frontend to tho Octopart public REST API.

    For detailed API documentation, refer to https://octopart.com/api/docs/v2/rest-api.
    """

    api_url = 'http://octopart.com/api/v%d/'
    __slots__ = ['apikey', 'callback', 'pretty_print', 'verbose']

    def __init__(self, apikey=None, callback=None, pretty_print=False, verbose=False):
        self.apikey = apikey
        self.callback = callback
        self.pretty_print = pretty_print
        self.verbose = verbose


    def _get_data(self, method, args, payload=dict(), ver=2, wait=1, attempts=1, maxattempts=1):
        """Constructs the URL to pass to _get().

        param method: String containing the method path, such as 'parts/search'.
        param args: Dictionary of arguments to pass to the API method.
        returns: Complete request URL string.
        """
        req_url = Octopart.api_url % ver + method

        if self.apikey:
            payload['apikey'] = self.apikey
        if self.callback:
            payload['callback'] = self.callback

        for arg, val in args.items():
            if type(val) is bool:
                v = int(val)
            elif type(val) is list:
                v = json.dumps(val)
            else:
                v = val
            payload[arg] = v

        r = requests.get(req_url, params=payload)
        if r.status_code == 404:
            return None
        if r.status_code == 429:
            if attempts < maxattempts:
                time.sleep(wait)
                self._get_data(method, args, payload=payload, ver=ver, wait=wait*2, attempts=attempts+1, maxattempts=maxattempts)
            else:
                raise OctopartApiThrottleError(args, [], [])
        elif r.status_code == 503:
            raise Octopart503Error(args, [], [])

        r = r.json()

        if self.verbose:
            if self.pretty_print:
                pprint(r)
            else:
                print(r)

        if 'message' in r.keys() and r['message'] == 'Invalid API key':
            raise OctopartInvalidApiKeyError(self.apikey)

        return r


    ''' API v3 Methods '''

    def parts_search(self,
                     q: str = "",
                     start: int = 0,
                     limit: int = 10,
                     sortby: str = "score desc",
                     maxattempts = 1,
                     **show_hide
                     ):
        # filter[fields][<fieldname>][]: string = "",
        # filter[queries][]: string = "",
        # facet[fields][<fieldname>][include]: boolean = false,
        # facet[fields][<fieldname>][exclude_filter]: boolean = false,
        # facet[fields][<fieldname>][start]: integer = 0,
        # facet[fields][<fieldname>][limit]: integer = 10,
        # facet[queries][]: string = "",
        # stats[<fieldname>][include]: boolean = false,
        # stats[<fieldname>][exclude_filter]: boolean = false,
        # spec_drilldown[include]: boolean = false,
        # spec_drilldown[exclude_filter]: boolean = false,
        # spec_drilldown[limit]: integer = 10
        method = 'parts/search'
        args = { 'q': q, 'limit': limit, 'start': start}
        params = {}

        params.update(OctopartPart.includes(**select_incls(show_hide)))
        params.update(OctopartPart.shows(**select_shows(show_hide)))
        params.update(OctopartPart.hides(**select_hides(show_hide)))

        if not len(q) >= 2:
            raise OctopartRangeArgumentError(['q'], [int], [2,float('inf')])
        if limit not in range(0,101):
            raise OctopartRangeArgumentError(['limit'], [int], [0,100])
        if start not in range(0,1001):
            raise OctopartRangeArgumentError(['limit'], [int], [0,1000])

        json_obj = self._get_data(method, args, params, ver=3, maxattempts=maxattempts)

        if json_obj:
            return json_obj, json_obj['results']
        else:
            return None

    def parts_match(self,
                    queries: list,
                    exact_only: bool = False,
                    maxattempts = 1,
                    **show_hide):

        method = 'parts/match'

        args = { 'queries': queries, 'exact_only': exact_only}
        params = {}

        params.update(OctopartPart.includes(**select_incls(show_hide)))
        params.update(OctopartPart.shows(**select_shows(show_hide)))
        params.update(OctopartPart.hides(**select_hides(show_hide)))

        for q in queries:
            if type(q) != dict:
                raise OctopartTypeArgumentError(['queries'], ['str'], [])

        json_obj = self._get_data(method, args, params, ver=3, maxattempts=maxattempts)

        # XXX consider using the following?
        # items = [OctopartPart.new_from_dict(item) for item in json_obj['results']['items']]

        if json_obj:
            return json_obj, json_obj['results']
        else:
            return None

    def parts_get(self, uid: int, maxattempts = 1, **show_hide):
        method = 'parts/{:s}'.format(uid)
        params = {}

        params.update(OctopartPart.includes(**select_incls(show_hide)))
        params.update(OctopartPart.shows(**select_shows(show_hide)))
        params.update(OctopartPart.hides(**select_hides(show_hide)))

        json_obj = self._get_data(method, {}, params, ver=3, maxattempts=maxattempts)

        if json_obj:
            return json_obj
        else:
            return None


    ''' API v2 Methods '''

    def parts_suggest_v2(self,
                      q: str,
                      limit: int = 25,
                      start: int = 0):
        """Suggest a part search query string.

        Optimized for speed (useful for auto-complete features).

        returns A pair containing:
        - The raw JSON result dictionary.
        - A list of manufacturer part number strings.
        If no JSON object is found without an Exception being raised, returns None.
        """

        method = 'parts/suggest'

        if not len(q) >= 2:
            raise OctopartRangeArgumentError(['q'], [int], [2,float('inf')])
        if limit not in range(0,26):
            raise OctopartRangeArgumentError(['limit'], [int], [0,25])

        json_obj = self._get_data(method, { 'q': q, 'limit': limit, 'start': start}, ver=2)

        if json_obj:
            return json_obj, json_obj['results']
        else:
            return None

    def parts_match_v2(self, manufacturer_name: str, mpn: str):
        """Match (manufacturer name, mpn) to part uid.

        returns a list of (part uid, manufacturer displayname, mpn) tuples.
        If no JSON object is found without an Exception being raised, returns None.
        """

        method = 'parts/match'
        args = {
            'mpn': mpn,
            'manufacturer_name': manufacturer_name
        }
        json_obj = self._get_data(method, args, ver=2)

        if json_obj:
            return json_obj
        else:
            return None

    def partattributes_get(self, fieldname: str):
        """Fetch a PartAttribute object by its fieldname.

        returns A pair containing:
            -The raw JSON result dictionary.
            -An OctopartPartAttribute object.
        If no JSON object is found without an Exception being raised, returns None.
        """

        method = 'partattributes/get'
        args = {
            'fieldname': fieldname
        }
        json_obj = self._get_data(method, args)

        if json_obj:
            return json_obj, OctopartPartAttribute.new_from_dict(json_obj)
        else:
            return None

    def partattributes_get_multi(self, fieldnames: list):
        """Fetch multiple PartAttribute objects by their fieldnames.

        returns A pair containing:
            -The raw JSON result dictionary.
            -A list of OctopartPartAttribute objects.
        If no JSON object is found without an Exception being raised, returns None.
        """
        method = 'partattributes/get_multi'
        for name in fieldnames:
            if isinstance(name, str) is False:
                raise OctopartTypeArgumentError(args, [], [])

        args = {
            'fieldnames': fieldnames
        }
        json_obj = self._get_data(method, args, ver=2)

        if json_obj:
            return json_obj, [OctopartPartAttribute.new_from_dict(attrib) for attrib in json_obj]
        else:
            return None

    def bom_match(self,
                  lines: list,
                  optimize_return_stubs : bool = False,
                  optimize_hide_datasheets : bool = False,
                  optimize_hide_descriptions : bool = False,
                  optimize_hide_images : bool = False,
                  optimize_hide_hide_offers : bool = False,
                  optimize_hide_hide_unauthorized_offers : bool = False,
                  optimize_hide_specs : bool = False):
        """Match a list of part numbers to Octopart part objects.

        returns A pair containing:
            -The raw JSON result dictionary.
            -A list of dicts containing:
                -A list of OctopartParts.
                -A reference string.
                -A status string.
                -Optionally, the number of search hits.
        If no JSON object is found without an Exception being raised, returns None.
        """

        method = 'bom/match'

        def check_line(q: str,
                       mpn : str = None,
                       manufacturer : str = None,
                       sku : str = None,
                       supplier : str = None,
                       mpn_or_sku : str = None,
                       start : int = 0,
                       limit : int = 0,
                       reference : str = None):
            if limit < 0 and limit > 20:
                raise OctopartArgumentMissingError([], [], [])

        for line in lines:
            check_line(line)

        args = {
            'lines': lines,
            'optimize.return.stubs' :                  optimize_return_stubs,
            'optimize.hide.datasheets' :               optimize_hide_datasheets,
            'optimize.hide.descriptions' :             optimize_hide_descriptions,
            'optimize.hide.images' :                   optimize_hide_images,
            'optimize.hide.hide_offers' :              optimize_hide_hide_offers,
            'optimize.hide.hide_unauthorized_offers' : optimize_hide_hide_unauthorized_offers,
            'optimize.hide.specs' :                    optimize_hide_specs,
        }

        json_obj = self._get_data(method, args, ver=2)

        results = []
        if json_obj:
            for result in json_obj['results']:
                items = [OctopartPart.new_from_dict(item) for item in result['items']]
                new_result = {'items' : items, 'reference' : result.get('reference', ''), 'status' : result['status']}
                if result.get('hits') is not None:
                    new_result['hits'] = result.get('hits')
                results.append(new_result)

            return json_obj, results
        else:
            return None

