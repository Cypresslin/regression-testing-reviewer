# Regression-testing result reviewer

## What is this?
An ugly parser with Beautifulsoup to help you review the Ubuntu Kernel SRU regression-testing test result.

## Why a web parser?
This was designed to run on the every corner in this world, so that the reviewer does not required to run it on the jenkins server.

## How to use it?
For a generic kernel, run the parser with:
    ./reviewer.py --release xenial

For a hwe / edge kernel, run it with:
    ./reviewer.py --release xenial --hwe

If you want to get the link of a failed test case, just simply add --link to the command. The link will be appended to the bottom of the result.

### Example output ###
    $ ./reviewer.py --release trusty
    3.13.0-146.195 - generic
    Regression test CMPL, RTB.
    
    Issue to note in amd64:
      ubuntu_kvm_smoke_test -
      ubuntu_kvm_unit_tests -

    Issue to note in arm64:
      hwclock - issue for HP m400 (bug 1716603)
      libhugetlbfs - noresv-preserve-resv-page failed (bug 1747823) chunk-overcommit failed (bug 1747828)
      ubuntu_cts_kernel - lp1262692 failed, bug for iproute2 (bug 1715376)
      ubuntu_kvm_smoke_test -
      ubuntu_qrt_apparmor - test_old_trusty_regression_testsuite failed to build (bug 1699987)
      ubuntu_qrt_kernel_security - test 060 should be skipped (bug 1712038) test 021, 022 (bug 1747847) test 050 (bug 1684776) test 072 (bug 1747850) test 075 (bug 1712007) test 82 (bug 1747853)

    Issue to note in i386:
      ubuntu_kvm_smoke_test -
      ubuntu_kvm_unit_tests -

    Issue to note in ppc64le:
      ubuntu_cts_kernel - lp1262692 failed, bug for iproute2 (bug 1715376)
      ubuntu_kvm_smoke_test - no supported architecture for 'hvm' (bug 1752550)

The next thing to do is to fill in those missing results, and you're ready to go.

### Special case: Parse result from the "Past & Current" page ###
Sometimes the "Current cycle" result page, tracker-index.html, might be empty. Or if you just want to get the history test result from the "Past & Current" page, in this case, use the "--all" flag to access the date from the "Past & Current" result page.

As there will be a pile of kernels in the report, it's better to use it along with the "--kernel KERNEL_VERSION" argument to print only the wanted result.
