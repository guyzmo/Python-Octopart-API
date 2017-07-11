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

class OctopartException(Exception):
    """Various errors that can be raised by the Octopart API."""
    __slots__ = ["arguments", "arg_types", "arg_ranges", "code"]
    def __init__(self, args, arg_types, arg_ranges, error_message):
        self.arguments = args
        self.arg_types = arg_types
        self.arg_ranges = arg_ranges
        self.message = error_message

    def __str__(self):
        args = ' '.join(('\nPassed arguments:', str(self.arguments)))
        argt = ' '.join(('\nArgument types:', str(self.arg_types)))
        argr = ' '.join(('\nArgument ranges:', str(self.arg_ranges)))
        string = self.message + args + argt + argr
        return string

class OctopartInvalidApiKeyError(OctopartException):
    def __init__(self, apikey):
        OctopartException.__init__(self, [], [], [], "")
        self.apikey = apikey

    def __str__(self):
        return "Api key '{}' is invalid! Please set it up!".format(self.apikey)

class OctopartArgumentMissingError(OctopartException):
    def __init__(self, args, arg_types, arg_ranges):
        OctopartException.__init__(self,
            args,
            arg_types,
            arg_ranges,
            'Required argument missing from method call.')

class OctopartArgumentInvalidError(OctopartException):
    def __init__(self, args, arg_types, arg_ranges):
        OctopartException.__init__(self,
            args,
            arg_types,
            arg_ranges,
            'Passed an invalid argument for this method.')

class OctopartTypeArgumentError(OctopartException):
    def __init__(self, args, arg_types, arg_ranges):
        OctopartException.__init__(self,
            args,
            arg_types,
            arg_ranges,
            'Argument type mismatch.')

class OctopartRangeArgumentError(OctopartException):
    def __init__(self, args, arg_types, arg_ranges):
        OctopartException.__init__(self,
            args,
            arg_types,
            arg_ranges,
            'Numeric argument value out of valid range.')

class OctopartStringLengthError(OctopartException):
    def __init__(self, args, arg_types, arg_ranges):
        OctopartException.__init__(self,
            args,
            arg_types,
            arg_ranges,
            'String argument outside of allowed length.')

class OctopartLimitExceededError(OctopartException):
    def __init__(self, args, arg_types, arg_ranges):
        OctopartException.__init__(self,
            args,
            arg_types,
            arg_ranges,
            'Value of (start+limit) in a bom/match line argument exceeds 100.')

class Octopart404Error(OctopartException):
    def __init__(self, args, arg_types, arg_ranges):
        OctopartException.__init__(self,
            args,
            arg_types,
            arg_ranges,
            'Unexpected HTTP Error 404.')

class Octopart503Error(OctopartException):
    def __init__(self, args, arg_types, arg_ranges):
        OctopartException.__init__(self,
            args,
            arg_types,
            arg_ranges,
            'Unexpected HTTP Error 503.')

class OctopartNonJsonArgumentError(OctopartException):
    def __init__(self, args, arg_types, arg_ranges):
        OctopartException.__init__(self,
            args,
            arg_types,
            arg_ranges,
            'Argument is not a JSON-encoded list of pairs.')

class OctopartInvalidSortError(OctopartException):
    def __init__(self, args, arg_types, arg_ranges):
        OctopartException.__init__(self,
            args,
            arg_types,
            arg_ranges,
            'Invalid sort order. Valid sort order strings are "asc" and "desc".')

class OctopartTooLongListError(OctopartException):
    def __init__(self, args, arg_types, arg_ranges):
        OctopartException.__init__(self,
            args,
            arg_types,
            arg_ranges,
            'List argument outside of allowed length.')

class OctopartApiThrottleError(OctopartException):
    def __init__(self, args, arg_types, arg_ranges):
        OctopartException.__init__(self,
            args,
            arg_types,
            arg_ranges,
            'Throttled by Octopart API.')


