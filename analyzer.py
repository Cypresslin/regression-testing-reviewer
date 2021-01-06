import os
import json
import yaml
import urllib
import utils

# format:
# test-suite: {sut: {sub-test-case1: {errmsg:'', reason:''},
#                    sub-test-case2: {errmsg:'', reason:''},
def testsuite_validator(fullname, arch, testcases):
    try:
        with open('db-testcases.yaml', 'r') as stream:
            db = yaml.load(stream, Loader=yaml.SafeLoader)
            expected = db['full-list']
    except FileNotFoundError:
        print("db-testcases.yaml does not exist")
        raise SystemExit
    # Compose the database for each arch from the full test list
    if fullname in db:
        if arch in db[fullname]:
            exclude = db[fullname][arch].keys()
            expected = list(set(expected) - set(exclude))
    total = len(expected)
    tested = len(testcases)
    extra = list(set(testcases) - set(expected))
    missing = list(set(expected) - set(testcases))
    if extra:
        extra.sort()
        print('Test case {} does not exist in the database, please check'.format(', '.join(extra)))
    if missing:
        missing.sort()
        print('{} / {} tests were run, missing: {}'.format(tested, total, ', '.join(missing)))


def _node_parser(soup):
    '''Parser to print failed nodes'''
    nodes = []
    # jump to test results summary list
    try:
        raw_node = soup.find('tbody').find('tr').find_next_siblings()
        for item in raw_node:
            # check if this node has failed, the fourth td is the failed count
            # format: timestamp, total, passed, failed
            fail = item.findChildren('td', {'align': 'center'})[3].get_text()
            if int(fail) > 0:
                nodes.append(item.find('td').get_text())
    except AttributeError:
        print("Something bad happened, web page not rendered properly?")
    return nodes


def analyze_that(link, testname, distro):
    '''Load known issue database for error analysis'''
    fn = "db-" + distro + ".yaml"
    unused = {}
    try:
        with open(fn, 'r') as stream:
            issues = yaml.load(stream, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print("database file {} does not exist".format(fn))
        raise SystemExit

    if testname not in issues:
        return '', unused

    summary = json.load(urllib.request.urlopen(link))
    reason = []
    # Parse the failed nodes first
    for job in summary["jobs"]:
        sut = job[1]
        # get the failed page for the sut
        if sut in issues[testname]:
            # Get the summary page for SUT
            suthtml = sut + '.html'
            target = os.path.dirname(link) + '/' + job[0] + '/' + 'results.json'
            report = json.load(urllib.request.urlopen(target))
            # iterate through all failed test suites, only process it when the test name matches
            for suite in report['results']['suites']:
                if suite['name'].replace('autotest.', '') != testname:
                    continue
                for item in suite['cases']:
                    sub_test = item['name']
                    if 'errorStackTrace' in item:
                        try:
                            if sub_test in issues[testname][sut]:
                                # Do not use errorStackTrace content here, as it probably does not contain the complete output
                                _fullname = testname + '.' + sub_test
                                debug_link = os.path.dirname(target) + '/' + testname + '/results/' + _fullname + '/debug/' + _fullname + '.DEBUG'
                                debug_link.replace(' ', '%20')
                                try:
                                    urllib.request.urlopen(debug_link)
                                except urllib.error.HTTPError:
                                    _fullname = testname
                                    debug_link = os.path.dirname(target) + '/' + testname + '/results/' + _fullname + '/debug/' + _fullname + '.DEBUG'
                                debug_link.replace(' ', '%20')
                                for errmsg in issues[testname][sut][sub_test]:
                                    debug_txt = urllib.request.urlopen(debug_link)
                                    if any(errmsg in _line.decode("utf-8") for _line in debug_txt):
                                        # don't append duplicated error message
                                        if issues[testname][sut][sub_test][errmsg] not in reason:
                                            reason.append(issues[testname][sut][sub_test][errmsg])
                                if reason == []:
                                    unused[testname] = [sut, sub_test, errmsg]
                            else:
                                print("Test failed for {}/{} on {} but not recorded!".format(testname, sub_test, sut))
                        except TypeError:
                            print("Issue {} for {} is empty, malformated database?".format(testname, sut))
        else:
            print("Test failed for {} on {} but not recorded!".format(testname, sut))
    return ' '.join(reason), unused
