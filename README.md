# Regression-testing result reviewer

## What is this?

This is a tool that I wrote to help me to review Ubuntu Kernel SRU regression
testing test result. It's a json parser for the bare-metal raw test output file:
aggregate-sru-results.json (it used to be a HTML parser for the bare-metal SRU
test report, which is a bit hard to maintain) with a kernel-specific database.
Review history will be stored in the log directory.


## What is in the database

Since the test results on bare-metal are pretty hardware-dependent, thus the
database is composed with sut node name. The dictionary format as follows:

    test-suite name:
        sut node name:
            sub-test-case1:
            "errmsg":
                failed reason


## How to use it

For a generic kernel, run the parser with:
    ./reviewer.py --release xenial

For a hwe / edge kernel, run it with:
    ./reviewer.py --release xenial --hwe

If you want to get the links of failed test cases, just simply add --link to
the command. Links will be appended to the bottom of the result.

An output example (normally you don't need to use the ``--kernel`` flag, just
run ``./reviewer.py --release bionic --kvm`` should give you the test result
for the current cycle):

.. code-block:: console

    $ time ./reviewer.py --release bionic --kvm --kernel 4.15.0-1009.9
    4.15.0-1009.9 - kvm

    Issue to note in amd64:
      libhugetlbfs - Unable to build libghugetlbfs test on 4.15 KVM (bug 1765279)
      ubuntu_blktrace_smoke_test - ubuntu_blktrace_smoke_test failed with 4.4 / 4.15 kvm kernel (bug 1760636)
      ubuntu_fan_smoke_test - ubuntu_fan_smoke_test failed on 4.4/4.15 kvm kernel (bug 1763323)
      ubuntu_kvm_unit_tests -
      ubuntu_ltp - inotify08 in ubuntu_ltp test failed on 4.15 kvm (bug 1770334) ar test failed with 4.15 KVM (bug 1765331)
      ubuntu_lttng_smoke_test - Unable to build lttng module on 4.4/4.15 KVM kernel (bug 1760647)
      ubuntu_lxc - lxc-tests package removed on bionic (bug 1758255)
      ubuntu_qrt_kernel_security - test_182_config_hardened_usercopy (bug 1766777) test_190_config_kernel_fortify (bug 1766774) test_250_config_security_perf_events_restrict (bug 1766780)
      ubuntu_stress_smoke_test - af-alg failed with 4.4/4.15 KVM kernel (bug 1760637) dccp failed with 4.4/4.15 KVM kernel (bug 1760638)
      ubuntu_sysdig_smoke_test - Unable to insert sysdig_probe module on B-KVM kernel (bug 1766565)
      ubuntu_unionmount_overlayfs_suite - File unexpectedly on union layer (bug 1751243)
      ubuntu_zram_smoke_test - zram module not found (bug 1766823)


    real        9m54.622s
    user        3m18.710s
    sys 0m7.046s

Next thing to do is to handle exceptions described below, after that the report
is ready.


### Exceptions Explained

Take the following output for example::

    5.10.0-1017.18 - oem

    Test case ubuntu_kernel_selftests, ubuntu_ltp_stable does not exist in the database, please check
    Issue to note in amd64:
      ubuntu_boot - kernel tainted because of workaround for bug in platform firmware applied (bug 1912316)
    Test failed for ubuntu_kernel_selftests on spitfire but not recorded!
      ubuntu_kernel_selftests -
      ubuntu_ltp -

    == Some expected errors were not found in the report, please check:
    {'ubuntu_kernel_selftests': ['kili', 'net', 'Cannot find a vmlinux for VMLINUX_BTF ']}

- ``Test case ubuntu_kernel_selftests, ubuntu_ltp_stable does not exist in the
  database, please check``

  - This means the test case was not written in db-testcases.yaml, it might be
    that the test case was just added recently.

- ``Test failed for ubuntu_kernel_selftests on spitfire but not recorded!``

  - This means we have failure recorded for ubuntu_kernel_selftests, but not
    for this node "spitfire". It could be that this node was not tested before
    (especially after we migrated the infrastructure code from KT to CKCT, the
    test case and testing node are no longer bound together, we won't run the
    same test on the same node.)

- ``ubuntu_ltp -``

  - This means the ubuntu_ltp test has failed but it is not record in the
    database at all

- ``== Some expected errors were not found in the report, please check:``

  - This means the following error message was expected to be found in the
    report, but it's not. It could be that the issue has been fixed, or maybe
    the error message has been changed due to test case changes or something
    else.


This output is what I'm using as a comment when flipping regression-testing
task to Fix-Released on the tracking bug.

I will save a copy to the log directory as well, so when you run this tool
again in the next cycle, you get something to compare with.


### Special case: Parse result from the "Past & Current" page ###
Sometimes the "Current cycle" result page, tracker-index.html, might be empty. Or if you just want to get the history test result from the "Past & Current" page, in this case, use the "--all" flag to access the date from the "Past & Current" result page.

As there will be a pile of kernels in the report, it's better to use it along with the "--kernel KERNEL_VERSION" flag to print only the wanted result.


## Limitations

There are still some limitations for this tool now, like it can't catch new
failures. This needs to be fixed from the tool and the testsuite.
