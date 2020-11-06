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
import json
import re
import sys
import urllib
import analyzer
import utils

max_colspan = 7
style_arch = {'align': 'center', 'colspan': '7', 'style': 'background: #e9e7e5;'}
style_kernel = {'align': 'left', 'colspan': '7', 'width': '150'}
report = {}
url_root = "http://10.246.72.4/test-results/"
url = "http://10.246.72.4/test-results/aggregate-sru-results.json"

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
parser.add_argument('--hwe', action='store_const', dest='flag', const='-hwe',
                    help='Get only HWE kernel result')
parser.add_argument('--edge', action='store_const', dest='flag', const='-edge',
                    help='Get only Edge kernel result')
parser.add_argument('--kvm', action='store_const', dest='flag', const='-kvm',
                    help='Get only KVM kernel result')
parser.add_argument('--oem', action='store_const', dest='flag', const='-oem',
                    help='Get only OEM kernel result')
parser.add_argument('--oem-osp1', action='store_const', dest='flag', const='-oem-osp1',
                    help='Get only OEM OSP1 kernel result')
parser.add_argument('--fips', action='store_const', dest='flag', const='-fips',
                    help='Get only FIPS kernel result')
parser.add_argument('--ibm', action='store_const', dest='flag', const='-ibm-gt',
                    help='Get only IBM-GT kernel result')
#parser.add_argument('--aws', dest='kernel_filter', action='store_const', const='aws',
#                    help='Get only AWS kernel result')
#parser.add_argument('--gcp', dest='kernel_filter', action='store_const', const='gcp',
#                    help='Get only GCP kernel result')
#parser.add_argument('--gke', dest='kernel_filter', action='store_const', const='gke',
#                    help='Get only GKE kernel result')
#parser.add_argument('--azure', dest='kernel_filter', action='store_const', const='azure',
#                    help='Get only Azure kernel result')

args = parser.parse_args()
filters = {'-hwe': '~',
           '-edge': '5.4.0-.*~',
           '-kvm': ' - kvm',
           '-oem': ' - oem',
           '-oem-osp1': ' - oem-osp1',
           '-fips': ' - fips',
           '-ibm-gt': ' - ibm-gt'}
highlighted = False
target_found = False
unused_all = []

if args.all:
    url = url_root
report = json.load(urllib.request.urlopen(url))
target_distro = args.release.lower()

if target_distro not in report.keys():
    print('Requested distro "{}" was not in the report: {}'.format(target_distro, report.keys()))
    sys.exit(1)

# Print result here
fn = args.release.lower() + (args.flag if args.flag else '')
for kernel in report[target_distro]:
    # Filter out what to print here
    # If we're asking a specific kernel to check
    if args.kernel and args.kernel != kernel.split()[0]:
        continue
    # flavour filter
    if args.flag:
        if 'oem' in filters[args.flag]:
            if not kernel.endswith(filters[args.flag]):
                continue
        elif args.flag == '-edge':
            if not re.match(filters[args.flag], kernel):
                continue
        elif filters[args.flag] not in kernel:
            continue
    else:
        # case for generic kernel
        if any(_ in kernel for _ in filters.values()):
                continue
    target_found = True

    print(kernel)
    print('Regression test CMPL, RTB.')
    print()
    for arch in sorted(report[target_distro][kernel]['suites-results']):
        # Validate the test case number here
        analyzer.testsuite_validator(fn, arch.split()[0], report[target_distro][kernel]['suites-results'][arch])

        # Analyze each failure here
        print('Issue to note in {}:'.format(arch))
        detail = []
        highlighted = False
        for testcase in sorted(report[target_distro][kernel]['suites-results'][arch]):
            if report[target_distro][kernel]['suites-results'][arch][testcase]['totals'][1] > 0:
                highlighted = True
                reason = ''
                # Call the advanced test result analyzer here
                if not args.template_only:
                    link = report[target_distro][kernel]['suites-results'][arch][testcase]['link'].replace("index.html", "suite-results.json")
                    reason, unused = analyzer.analyze_that(url_root + link, testcase, fn)
                    if unused != {}:
                        unused_all.append(unused)
                print('  {} - {}'.format(testcase, reason))
                # advanced test result analyzer
                detail.append(report[target_distro][kernel]['suites-results'][arch][testcase]['link'])
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
