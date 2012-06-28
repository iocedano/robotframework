#  Copyright 2008-2012 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from __future__ import with_statement

import re
from functools import partial

from robot.utils import ET, ETSource
from robot.libraries.BuiltIn import BuiltIn


class XML(object):
    """
    Supported xpath is documented here: http://effbot.org/zone/element-xpath.htm
    Notice that support for predicates (e.g. tag[@id="1"]) is supported
    only in 1.3 i.e in Python 2.7!
    """

    _should_be_equal = partial(BuiltIn().should_be_equal, values=False)
    _should_match = partial(BuiltIn().should_match, values=False)
    _normalize_whitespace = partial(re.compile('\s+').sub, ' ')

    def parse_xml(self, source):
        with ETSource(source) as source:
            return ET.parse(source).getroot()

    def _get_parent(self, source):
        if isinstance(source, basestring):
            return self.parse_xml(source)
        return source

    def get_element(self, source, xpath):
        if xpath == '.':  # TODO: Is this good workaround for ET 1.2 not supporting '.'?
            return self._get_parent(source)
        elements = self.get_elements(source, xpath)
        if not elements:
            raise RuntimeError("No element matching '%s' found." % xpath)
        if len(elements) > 1:
            raise RuntimeError("Multiple elements (%d) matching '%s' found."
                               % (len(elements), xpath))
        return elements[0]

    def get_elements(self, source, xpath):
        return self._get_parent(source).findall(xpath)

    def get_element_text(self, source, xpath='.', normalize_whitespace=False):
        element = self.get_element(source, xpath)
        text = ''.join(self._yield_texts(element))
        if normalize_whitespace:
            text = self._normalize_whitespace(text).strip()
        return text

    def _yield_texts(self, element, top=True):
        if element.text:
            yield element.text
        for child in element:
            for text in self._yield_texts(child, top=False):
                yield text
        if element.tail and not top:
            yield element.tail

    def get_elements_texts(self, source, xpath, normalize_whitespace=False):
        return [self.get_element_text(elem, normalize_whitespace=normalize_whitespace)
                for elem in self.get_elements(source, xpath)]

    def element_text_should_be(self, source, expected, xpath='.',
                               normalize_whitespace=False, message=None):
        text = self.get_element_text(source, xpath, normalize_whitespace)
        self._should_be_equal(text, expected, message)

    def element_text_should_match(self, source, pattern, xpath='.',
                                  normalize_whitespace=False, message=None):
        text = self.get_element_text(source, xpath, normalize_whitespace)
        self._should_match(text, pattern, message)

    def get_element_attribute(self, source, name, xpath='.', default=None):
        return self.get_element(source, xpath).get(name, default)

    def get_element_attributes(self, source, xpath='.'):
        return self.get_element(source, xpath).attrib.copy()

    def element_attribute_should_be(self, source, name, expected, xpath='.',
                                    message=None):
        attr = self.get_element_attribute(source, name, xpath)
        self._should_be_equal(attr, expected, message)

    def element_attribute_should_match(self, source, name, pattern, xpath='.',
                                       message=None):
        attr = self.get_element_attribute(source, name, xpath)
        if attr is None:
            raise AssertionError("Attribute '%s' does not exist." % name)
        self._should_match(attr, pattern, message)
