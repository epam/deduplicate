#  Copyright (c) 2023 EPAM Systems
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License

import difflib
import re


def tokenize(s):
    return re.split('\s+', s)


def untokenize(ts):
    return ' '.join(ts)


def equalize(s1, s2):
    l1 = tokenize(s1)
    l2 = tokenize(s2)
    res1 = []
    res2 = []
    prev = difflib.Match(0, 0, 0)

    for match in difflib.SequenceMatcher(a=l1, b=l2).get_matching_blocks():
        if prev.a + prev.size != match.a:
            res2.append('[[ ' + untokenize(l1[prev.a + prev.size:match.a]) + ' ]]')
        if prev.b + prev.size != match.b:
            res1.append('[[ ' + untokenize(l2[prev.b + prev.size:match.b]) + ' ]]')

        res1.extend(l1[match.a:match.a + match.size])
        res2.extend(l2[match.b:match.b + match.size])

        prev = match

    return untokenize(res1), untokenize(res2)
