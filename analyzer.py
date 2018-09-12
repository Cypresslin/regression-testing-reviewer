import os
import yaml
import utils

# format:
# test-suite: {sut: {sub-test-case1: {errmsg:'', reason:''},
#                    sub-test-case2: {errmsg:'', reason:''},
def testsuite_validator(fullname, arch, testcases):
    try:
        with open('db-testcases.yaml', 'r') as stream:
            db = yaml.load(stream)
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
            issues = yaml.load(stream)
    except FileNotFoundError:
        print("database file {} does not exist".format(fn))
        raise SystemExit

    if testname not in issues:
        return '', unused

    soup_summary = utils.soup_generator(link)
    reason = []
    # Parse the failed nodes first
    for sut in _node_parser(soup_summary):
        # get the failed page for the sut
        if sut in issues[testname]:
            # jump to the sut
            suthtml = sut + '.html'
            try:
                #### FIXME, if there are multiple test results, this one will fail, especially with the first one passed, the second one failed
                head = soup_summary.find('a', {'href': suthtml}).parent
                ####
            except:
                pass
            report = head.find_next('td', {'align': 'center'}).find_next('td', {'align': 'center'}).next_element.get('href')
            baseurl = os.path.dirname(link)
            target = baseurl + '/' + report
            # parse the target page
            soup = utils.soup_generator(target)
            # jump to the test, and update the report link
            head = soup.find('div', {'class': 'dash-section'}).find_next('div')
            # update the baseurl for those sub-pages here, as the target will be updated later
            baseurl = os.path.dirname(target)
            # find all failed test case by using the color, the link before the color is what we want
            for sub_head in head.find_all('td', {'style': "color: red"}):
                # push the head back to the hyperlink from the font style
                sub_head = sub_head.find_previous('a')
                sub_test = sub_head.text
                # check the sub-test-case name here
                if sub_test in issues[testname][sut]:
                    report = sub_head.get('href')
                    target = baseurl + '/' + report
                    # finally we can parse the real test report
                    soup = utils.soup_generator(target)
                    for item in soup.find_all('td', {'valign': 'top'}):
                        # filter out the column number section
                        if item.has_attr('width'):
                            continue
                        # check the error from all the message
                        # tried to focus on stdout/stderr before, but some error will be in Traceback
                        # tried to focus on message without stdout/stderr, but if the test times out this will not work
                        text = item.get_text()
                        for errmsg in issues[testname][sut][sub_test]:
                            if errmsg in text:
                                # don't append duplicated error message
                                if issues[testname][sut][sub_test][errmsg] not in reason:
                                    reason.append(issues[testname][sut][sub_test][errmsg])
                    if reason == []:
                        unused[testname] = [sut, sub_test, errmsg]
#                    The following check is not valid, sometime a same bug report will be used for different err msg
#                    if len(set(reason)) != len(issues[testname][sut][sub_test]):
#                        reason.append("SOME ERROR DID NOT MATCH, PLZ CHECK")
    return ' '.join(reason), unused
