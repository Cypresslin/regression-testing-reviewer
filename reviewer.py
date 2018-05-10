#!/usr/bin/env python3
'''Ubuntu kernel SRU regression-testing result review tool.

A small tool to make reviewer's life easier.
Author: Po-Hsu Lin <po-hsu.lin@canonical.com>
'''
# TODO
# decide what to review
# 1. test cases that will be tested
# 2. test that expected to fail, including further parsing
# compare the failed / passed number for first check
# Structure:
#   div-dash-section-table-tbody-tr-td-
#     table-tbody-tr-td
#                   <strong> release title </strong>
#                 tr-td-table-tbody-tr-td
#                   kernel ver
#                                   tr-td
#                   arch
#                                   tr-td
#                   test results
#                 tr-td
#                   <strong> release title </strong>

import argparse
import sys
from urllib import request
from bs4 import BeautifulSoup
import analyzer

max_colspan = 7
style_arch = {'align': 'center', 'colspan': '7', 'style': 'background: #e9e7e5;'}
style_kernel = {'align': 'left', 'colspan': '7', 'width': '150'}
report = {}
url_root = "http://10.246.72.4/test-results/"
url = "http://10.246.72.4/test-results/tracker-index.html"

parser = argparse.ArgumentParser(description='Test report reviewer')
parser.add_argument('--release', type=str, required=True,
                    help='The desired release(s)')
parser.add_argument('--all', action='store_true',
                    help='Use the result page for all test results, not the current cycle')
parser.add_argument('--template-only', action='store_true',
                    help='Do not analyze the result, just print a template')
parser.add_argument('--link', action='store_true',
                    help='Print test case links')
parser.add_argument('--kernel',
                    help='Review a specific kernel')
parser.add_argument('--hwe', action='store_true',
                    help='Get only HWE kernel result')
parser.add_argument('--edge', action='store_true',
                    help='Get only Edge kernel result')
parser.add_argument('--kvm', action='store_true',
                    help='Get only KVM kernel result')
#parser.add_argument('--aws', dest='kernel_filter', action='store_const', const='aws',
#                    help='Get only AWS kernel result')
#parser.add_argument('--gcp', dest='kernel_filter', action='store_const', const='gcp',
#                    help='Get only GCP kernel result')
#parser.add_argument('--gke', dest='kernel_filter', action='store_const', const='gke',
#                    help='Get only GKE kernel result')
#parser.add_argument('--azure', dest='kernel_filter', action='store_const', const='azure',
#                    help='Get only Azure kernel result')

args = parser.parse_args()

hwe_filter = '~'
kvm_filter = ' - kvm'
edge_filter = '4.15.0'
highlighted = False
target_found = False
unused_all = []

if args.all:
    url = url_root

page = request.urlopen(url).read()
soup = BeautifulSoup(page, "lxml")
# Jump to the correct strong tag, for release
try:
    head = soup.find("td", {"style": "background: #ffff99;"}).next_element
except AttributeError:
    print("Report seems to be empty, please try again later.")
    sys.exit(1)
# Jump to the table contains all SRU results
head = soup.find("table", {"width": "100%", "style": "font-size: 0.9em"})

# Compose data fetched from the result page
# Get the available distro first, so we can make a quick check for the existence
target_distro = args.release.lower()
for td in head.findChildren('td', {'style': 'background: #ffff99;'}):
    # Releases
    if td.findChild('strong'):
        distro = td.findChild('strong').text
        report[distro] = {}

if target_distro not in report:
    print('Requested distro "{}" was not in the report: {}'.format(target_distro, report.keys()))
    sys.exit(1)
'''
# This is a stupid bug in the report, the relase name comes with a trailing whitespace
# Can't just use the target_distro as key, it won't fit in the dict.
found = False
for distro in report:
    if target_distro == distro.rstrip():
        # replace the target_distro with the actual distro (buggy one) for future key search
        target_distro = distro
        found = True
        break

if not found:
    print('Requested distro "{}" was not in the report: {}'.format(target_distro, report.keys()))
    sys.exit(1)
'''

# Now compose the database only for the targeted release
# The table next to the tr that contains the release name will be the target
for data in head.find(string=target_distro).find_parent('tr').find_next('tbody').findChildren('tr'):
    if data.findChild('td', style_kernel):
        kernel = data.findChild('td', style_kernel).text
        # kernel version prettifier
        report[target_distro][kernel] = {}
    elif data.findChild('td', style_arch):
        arch = data.find_next('td', style_arch).text.rstrip()
        report[target_distro][kernel][arch] = {}
    elif data.findChildren('td', {'align': 'left'}):
        # result structure: test case / passed / failed, separate by td
        for result in data.findChildren('td', {'align': 'left'}):
            ptr = result.next_element
            testcase = ptr.text
            ptr = ptr.find_next().next_element
            passed = int(ptr.text)
            ptr = ptr.find_next().next_element
            failed = int(ptr.text)
            # replace special characters in hyperlink with %-format string
            detail = ptr.get('href').replace(' ', '%20')
            detail = detail.replace('(', '%28')
            detail = detail.replace(')', '%29')
            report[target_distro][kernel][arch][testcase] = {'pass': passed,
                                                             'fail': failed,
                                                             'link': detail}
    #else:
        # All trash, do nothing

# Print result here
for kernel in report[target_distro]:
    # No filter was set, print only everything except from the exclusion list
    # If we're asking a specific kernel to check
    if args.kernel and args.kernel != kernel.split()[0]:
        continue
    # flavour filter
    if args.hwe:
        if hwe_filter not in kernel or edge_filter in kernel:
            continue
    elif args.edge:
        if edge_filter not in kernel:
            continue
    elif args.kvm:
        if kvm_filter not in kernel:
             continue
    elif hwe_filter in kernel or kvm_filter in kernel:
        continue
    target_found = True

    print(kernel)
    print('Regression test CMPL, RTB.')
    print()
    for arch in sorted(report[target_distro][kernel]):
        print('Issue to note in {}:'.format(arch))
        detail = []
        highlighted = False
        for testcase in sorted(report[target_distro][kernel][arch]):
            if report[target_distro][kernel][arch][testcase]['fail'] > 0:
                highlighted = True
                reason = ''
                # Call the advanced test result analyzer here
                if not args.template_only:
                    fn = target_distro
                    if args.hwe:
                        fn += '-hwe'
                    elif args.edge:
                        fn += '-edge'
                    elif args.kvm:
                        fn += '-kvm'
                    reason, unused = analyzer.analyze_that(url_root + report[target_distro][kernel][arch][testcase]['link'], testcase, fn)
                    if unused != {}:
                        unused_all.append(unused)
                print('  {} - {}'.format(testcase, reason))
                # advanced test result analyzer
                detail.append(report[target_distro][kernel][arch][testcase]['link'])
        if not highlighted:
            print("  None")
        elif args.link:
            for item in detail:
                print(url_root + item)
        print()

if not target_found:
    print("Desired kernel was not found")
    print("Maybe the report hasn't refreshed yet or you have asked for an invalid kernel.")

if unused_all != []:
    print("== Some expected errors were not found in the report, please check:")
    for items in unused_all:
        print(items)
