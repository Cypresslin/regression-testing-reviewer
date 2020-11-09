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
            # find all failed test case
            for suite in report['results']['suites']:
                for item in suite['cases']:
                    sub_test = item['name']
                    if item['failedSince'] != 0:
                        try:
                            if sub_test in issues[testname][sut]:
                                for errmsg in issues[testname][sut][sub_test]:
                                    if errmsg in item['errorStackTrace']:
                                        # don't append duplicated error message
                                        if issues[testname][sut][sub_test][errmsg] not in reason:
                                            reason.append(issues[testname][sut][sub_test][errmsg])
                                        break
                                if reason == []:
                                    unused[testname] = [sut, sub_test, errmsg]
                            else:
                                print("Test failed but not record!")
                        except TypeError:
                            print("Issue {} for {} is empty, malformated database?".format(testname, sut))
    return ' '.join(reason), unused
