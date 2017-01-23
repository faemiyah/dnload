import re

from dnload.common import is_verbose

########################################
# Template #############################
########################################

class Template:
  """Class for templated string generation."""

  def __init__(self, content):
    """Constructor."""
    self.__content = content

  def format(self, substitutions = None):
    """Return formatted output."""
    ret = self.__content
    if substitutions:
      for kk in substitutions:
        vv = substitutions[kk].replace("\\", "\\\\")
        (ret, num) = re.subn(r'\[\[\s*%s\s*\]\]' % (kk), vv, ret)
        if not num:
          print("WARNING: substitution '%s' has no matches" % (kk))
    unmatched = list(set(re.findall(r'\[\[([^\]]+)\]\]', ret)))
    (ret, num) = re.subn(r'\[\[[^\]]+\]\]', "", ret)
    if num and is_verbose():
      print("Template substitutions not matched: %s (%i)" % (str(unmatched), num))
    return ret

  def __str__(self):
    """String representation."""
    return self.__content
