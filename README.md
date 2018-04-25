# Regression-testing result reviewer

## What is this?
An ugly parser with Beautifulsoup to help you review the Ubuntu Kernel SRU regression-testing test result.

## How to use it?
For a generic kernel, run the parser with:
    ./reviewer.py --release xenial

For a hwe / edge kernel, run it with:
    ./reviewer.py --release xenial --hwe

If you want to get the link of a failed test case, just simply add --link to the command. The link will be
appended on bottom.
