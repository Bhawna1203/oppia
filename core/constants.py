# coding: utf-8
#
# Copyright 2017 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Loads constants for backend use."""

from __future__ import annotations

import io
import json
import os
import pkgutil
import re

from typing import Any, Dict


# Here we use Dict[str, Any] as return type because we need to parse and return
# generic JSON objects.
def parse_json_from_ts(ts_file_contents: str) -> Dict[str, Any]:
    """Extracts JSON object from TS file.

    Args:
        ts_file_contents: str. The contents of the TS file containing JSON that
            needs to be parsed.

    Returns:
        dict. The dict representation of JSON object in the TS file.
    """
    text_without_comments = remove_comments(ts_file_contents)
    json_start = text_without_comments.find('{\n')
    # Add 1 to index returned because the '}' is part of the JSON object.
    json_end = text_without_comments.rfind('}') + 1
    json_dict: Dict[str, Any] = (
        json.loads(text_without_comments[json_start:json_end]))
    return json_dict


def remove_comments(text: str) -> str:
    """Removes comments from given text.

    Args:
        text: str. The text from which comments should be removed.

    Returns:
        str. Text with all its comments removed.
    """
    return re.sub(r'  //.*\n', r'', text)


# This function could be in utils but a race conditions happens because of
# the chronology of our files execution. utils imports constants and constants
# need utils.get_package_file_contents but it does not have it loaded to memory
# yet. If called from utils we get error as `module has no attribute`.
def get_package_file_contents(package: str, filepath: str) -> str:
    """Open file and return its contents. This needs to be used for files that
    are loaded by the Python code directly, like constants.ts or
    rich_text_components.json. This function is needed to make loading these
    files work even when Oppia is packaged.

    Args:
        package: str. The package where the file is located.
            For Oppia the package is usually the folder in the root folder,
            like 'core' or 'extensions'.
        filepath: str. The path to the file in the package.

    Returns:
        str. The contents of the file.

    Raises:
        FileNotFoundError. The file does not exist.
    """
    try:
        with io.open(
            os.path.join(package, filepath), 'r', encoding='utf-8'
        ) as file:
            return file.read()
    except FileNotFoundError as e:
        file_data = pkgutil.get_data(package, filepath)
        if file_data is None:
            raise e
        return file_data.decode('utf-8')


class Constants(dict):  # type: ignore[type-arg]
    """Transforms dict to object, attributes can be accessed by dot notation."""

    # Here `value` has the type Any because it parses and stores the values of
    # contants defined in constants.ts file and we cannot define a single type
    # which works for all of them.
    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    # The return value here refers to the `value` in the above method, hence the
    # type Any is used for it.
    def __getattr__(self, name: str) -> Any:
        return self[name]


constants = Constants(parse_json_from_ts(  # pylint:disable=invalid-name
    get_package_file_contents('assets', 'constants.ts')))

release_constants = Constants( # pylint:disable=invalid-name
    json.loads(get_package_file_contents('assets', 'release_constants.json'))
)
