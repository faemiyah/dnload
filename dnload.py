import os
import sys

if __name__ == "__main__":
    (pathname, basename) = os.path.split(__file__)
    sys.path.append(pathname)
    from dnload.__main__ import main
    sys.exit(main())
