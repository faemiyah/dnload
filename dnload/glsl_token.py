from dnload.common import is_listing
from dnload.glsl_access import is_glsl_access
from dnload.common import get_indent
from dnload.glsl_bool import interpret_bool
from dnload.glsl_bool import is_glsl_bool
from dnload.glsl_float import interpret_float
from dnload.glsl_float import is_glsl_float
from dnload.glsl_int import interpret_int
from dnload.glsl_int import is_glsl_int
from dnload.glsl_name import is_glsl_name
from dnload.glsl_operator import is_glsl_operator
from dnload.glsl_operator import interpret_operator
from dnload.glsl_paren import is_glsl_paren
from dnload.glsl_type import is_glsl_type

########################################
# Globals ##############################
########################################

g_deny_integrify_function_calls = (
    "mix",
    "smoothstep",
    )

########################################
# GlslToken ############################
########################################

class GlslToken:
    """Holds single instance of a GLSL token. Actually more of a token container."""

    def __init__(self, token):
        """Constructor."""
        self.__parent = None
        self.__left = []
        self.__middle = []
        self.__right = []
        # Prevent degeneration, collapse chains of single tokens.
        if token:
            token = token_descend(token)
            self.addMiddle(token)

    def addLeft(self, op):
        """Add left child token."""
        # List case.
        if is_listing(op):
            for ii in op:
                self.addleft(ii)
            return
        # Single case.
        if not is_glsl_token(op):
            raise RuntimeError("trying to add left non-token '%s'" % (str(left)))
        self.__left += [op]
        op.setParent(self)

    def addMiddle(self, op):
        """Add middle child token."""
        # List case.
        if is_listing(op):
            for ii in op:
                self.addMiddle(ii)
            return
        # Tokens added normally.
        if is_glsl_token(op):
            self.__middle += [op]
            op.setParent(self)
        # Non-tokens added as-is.
        else:
            self.__middle += [op]

    def addRight(self, op):
        """Add right child token."""
        # List case.
        if is_listing(op):
            for ii in op:
                self.addRight(ii)
            return
        # Single case.
        if not is_glsl_token(op):
            raise RuntimeError("trying to add right non-token '%s'" % (str(left)))
        self.__right += [op]
        op.setParent(self)

    def applyTernary(self, cmp, left, right):
        """Apply ternary operation, remove all children and replace contents with selected."""
        mid = cmp.getSingleChildMiddleNonToken()
        if (mid is None) or (not (is_glsl_bool(mid))):
            return False
        if mid.getBool():
            selected = left
        else:
            selected = right
        cmp.removeFromParent()
        left.removeFromParent()
        right.removeFromParent()
        self.replaceContents(selected)
        return True

    def clearContents(self):
        """Clear all contents."""
        while len(self.__left) > 0:
            vv = self.__left[0]
            if is_glsl_token(vv):
                vv.setParent(None)
            self.__left.pop(0)
        self.clearContentsMiddle()
        while len(self.__right) > 0:
            vv = self.__right[0]
            if is_glsl_token(vv):
                vv.setParent(None)
            self.__right.pop(0)

    def clearContentsMiddle(self):
        """Clear middle contents."""
        while len(self.__middle) > 0:
            vv = self.__middle[0]
            if is_glsl_token(vv):
                vv.setParent(None)
            self.__middle.pop(0)

    def collapse(self):
        """Collapse degenerate trees."""
        if (len(self.__left) == 0) and (len(self.__right) == 0) and (len(self.__middle) == 1):
            middle = self.__middle[0]
            if is_glsl_token(middle):
                middle.removeFromParent()
                self.replaceContents(middle)
                # Retry.
                self.collapse()
                return
        # Descend left.
        for ii in self.__left:
            ii.collapse()
        # Descend right.
        for ii in self.__right:
            ii.collapse()
        # Descend missle.
        for ii in self.__middle:
            if is_glsl_token(ii):
                ii.collapse()

    def collapseIdentity(self):
        """Collapse identity transforms that do not do anything."""
        oper = self.getSingleChildMiddleNonToken()
        if not is_glsl_operator(oper):
            raise RuntimeError("must be an operator to collapse identities")
        left_token = self.getSingleChildLeft()
        right_token = self.getSingleChildRight()
        # If right or left tokens not found, not eligible for identity collapse.
        if (not left_token) or (not right_token):
            return False
        left = left_token.getSingleChild()
        right = right_token.getSingleChild()
        # Can't collapse if either side is in itself an operator.
        if is_glsl_operator(left) or is_glsl_operator(right):
            return False
        # Multiply by one.
        if oper.getOperator() == "*":
            if is_glsl_number(left) and (left.getFloat() == 1.0):
                self.collapseMiddleLeft()
                return True
            if is_glsl_number(right) and (right.getFloat() == 1.0):
                self.collapseMiddleRight()
                return True
        # Divide by one.
        elif oper.getOperator() == "/":
            if is_glsl_number(right) and (right.getFloat() == 1.0):
                self.collapseMiddleRight()
                return True
        # Substract zero.
        elif oper.getOperator() == "-":
            if is_glsl_number(right) and (right.getFloat() == 0.0):
                self.collapseMiddleRight()
                return True
        # Add zero.
        elif oper.getOperator() == "+":
            if is_glsl_number(left) and (left.getFloat() == 0.0):
                self.collapseMiddleLeft()
                return True
            if is_glsl_number(right) and (right.getFloat() == 0.0):
                self.collapseMiddleRight()
                return True
        # No collapses found.
        return False

    def collapseMiddleLeft(self):
        """Collapse left and middle parts of this token."""
        left = self.getSingleChildLeft()
        right = self.getSingleChildRight()
        if (not left) or (not right):
            raise RuntimeError("cannot collapse if both left and right are not single tokens")
        left.removeFromParent()
        right.removeFromParent()
        self.replaceMiddle(right)

    def collapseMiddleRight(self):
        """Collapse left and middle parts of this token."""
        left = self.getSingleChildLeft()
        right = self.getSingleChildRight()
        if (not left) or (not right):
            raise RuntimeError("cannot collapse if both left and right are not single tokens")
        left.removeFromParent()
        right.removeFromParent()
        self.replaceMiddle(left)

    def collapseUp(self):
        """Collapse this token and its parent."""
        # Remove self from parent.
        parent = self.__parent
        self.removeFromParent()
        # Find remaining child of parent, remove it.
        left = parent.getSingleChildLeft()
        right = parent.getSingleChildRight()
        if left and right:
            raise RuntimeError("parent retains both children after removing child")
        remaining = left
        if not remaining:
            remaining = right
        remaining.removeFromParent()
        # Replace parent in its parent with the remaining element.
        parent.replaceInParent(remaining)

    def findEqualToken(self, orig):
        """Find a token or a number that has equal priority to given token."""
        mid = self.getSingleChildMiddleNonToken()
        if not mid:
            return (None, None)
        if is_glsl_number(mid):
            return (orig, self)
        if is_glsl_operator(mid):
            if mid.getPrecedence() is orig.getPrecedenceIfOperator():
                lt = self.getSingleChildLeft()
                if lt and lt.getSingleChildMiddleNonToken():
                    (lt_oper, lt_token) = lt.findEqualToken(self)
                    if lt_oper and lt_token:
                        return (lt_oper, lt_token)
                rt = self.getSingleChildRight()
                if rt and rt.getSingleChildMiddleNonToken():
                    (rt_oper, rt_token) = rt.findEqualToken(self)
                    if rt_oper and rt_token:
                        return (rt_oper, rt_token)
        return (None, None)

    def findEqualTokenLeft(self, orig):
        """Find a token from the left tree that has equal priority path to this operator."""
        lt = self.getSingleChildLeft()
        if lt and lt.getSingleChildMiddleNonToken():
            return lt.findEqualToken(orig)
        return (None, None)

    def findEqualTokenRight(self, orig):
        """Find a token from the right tree that has equal priority path to this operator."""
        rt = self.getSingleChildRight()
        if rt and rt.getSingleChildMiddleNonToken():
            return rt.findEqualToken(orig)
        return (None, None)

    def findHighestPrioOperatorMiddle(self):
        """Find highest priority operator from elements in the middle."""
        prio = -1
        for ii in self.__middle:
            mid = ii.getSingleChildMiddleNonToken()
            if is_glsl_operator(mid):
                prio = max(prio, mid.getPrecedence())
        return prio

    def findSiblingOperatorLeft(self):
        """Find nearest left operator."""
        if not self.__parent:
            return None
        mid = self.__parent.getSingleChildMiddleNonToken()
        if not is_glsl_operator(mid):
            return None
        if self.__parent.getSingleChildLeft() != self:
            return mid
        return self.__parent.findSiblingOperatorLeft()

    def findSiblingOperatorRight(self):
        """Find nearest right operator."""
        if not self.__parent:
            return None
        mid = self.__parent.getSingleChildMiddleNonToken()
        if not is_glsl_operator(mid):
            return None
        if self.__parent.getSingleChildRight() != self:
            return mid
        return self.__parent.findSiblingOperatorRight()

    def findRightSiblingElementFromParentTree(self, elem):
        """Find element next to given element from parent tree of this."""
        lst = self.flattenParentTree()
        for ii in range(len(lst)):
            if lst[ii] is elem:
                if ii < (len(lst) - 1):
                    return lst[ii + 1]
        return None

    def flatten(self):
        """Flatten this token into a list."""
        ret = []
        # Left
        for ii in self.__left:
            ret += ii.flatten()
        # Middle.
        ret += self.flattenMiddle()
        # Right.
        for ii in self.__right:
            ret += ii.flatten()
        return ret

    def flattenMiddle(self):
        """Flatten middle elements into a list."""
        ret = []
        for ii in self.__middle:
            # Middle may be token or element.
            if is_glsl_token(ii):
                ret += ii.flatten()
            elif ii:
                ret += [ii]
            else:
                raise RuntimeError("empty element found during flatten")
        return ret

    def flattenParentTree(self):
        """Flatten complete parent tree this node is contained in."""
        parent = self
        while parent.__parent:
            parent = parent.__parent
        return parent.flatten()

    def flattenString(self):
        """Flatten this token into a string."""
        ret = ""
        tokens = self.flatten()
        for ii in tokens:
            ret += ii.format(False)
        return ret

    def getFunctionCallNameIfFunctionCall(self):
        """Gets the name of a function call if this is a function call construct."""
        if self.__left or self.__right:
            return None
        if len(self.__middle) != 2:
            return None
        if (not is_glsl_token(self.__middle[0])) or (not is_glsl_token(self.__middle[1])):
            return None
        if self.__middle[1].getSingleChildMiddleNonToken() != "(":
            return None
        left = self.__middle[0].getSingleChildMiddleNonToken()
        if not is_glsl_name(left):
            return None
        return left.getName()

    def getPrecedenceIfOperator(self):
        """Return precedence if middle element is a single child that is an operator."""
        mid = self.getSingleChildMiddleNonToken()
        if mid and is_glsl_operator(mid):
            return mid.getPrecedence()
        return None

    def getRecursiveStringRepresentation(self, indent, indent_increment = 4):
        """Gets a recursive string representation from the current token subtree."""
        ret = get_indent(indent) + str(self) + "\n"
        if (len(self.__middle) > 1) or ((len(self.__middle) == 1) and is_glsl_token(self.__middle[0])):
            ret += get_indent(indent) + "Middle:\n"
            for ii in self.__middle:
                if is_glsl_token(ii):
                    ret += ii.getRecursiveStringRepresentation(indent + indent_increment, indent_increment)
                else:
                    ret += get_indent(indent + indent_increment) + str(ii) + "\n"
        if len(self.__left) > 0:
            ret += get_indent(indent) + "Left:\n"
            for ii in self.__left:
                if is_glsl_token(ii):
                    ret += ii.getRecursiveStringRepresentation(indent + indent_increment, indent_increment)
                else:
                    ret += get_indent(indent + indent_increment) + str(ii) + "\n"
        if len(self.__right) > 0:
            ret += get_indent(indent) + "Right:\n"
            for ii in self.__right:
                if is_glsl_token(ii):
                    ret += ii.getRecursiveStringRepresentation(indent + indent_increment, indent_increment)
                else:
                    ret += get_indent(indent + indent_increment) + str(ii) + "\n"
        return ret

    def getSingleChild(self):
        """Degeneration preventation. If token only has a single child, return that instead."""
        lr = len(self.__left) + len(self.__right)
        # If left and right exist, return node itself - there is no single child here.
        if 0 < lr:
            if not self.__middle and ((not self.__left) or (not self.__right)):
                raise RuntimeError("empty middle only allowed if bothe left and right exist")
            return self
        # If left and right did not exist, return middle.
        elif self.__middle:
            if is_listing(self.__middle):
                if 1 >= len(self.__middle):
                    return self.__middle[0]
            return self.__middle
        # Should never happen.
        raise RuntimeError("token has no content")

    def getSingleChildLeft(self):
        """Get right child if it's a single token."""
        if (len(self.__left) == 1) and is_glsl_token(self.__left[0]):
            return self.__left[0]
        return None

    def getSingleChildMiddleNonToken(self):
        """Get the single non-token middle child, even if left and right exist."""
        if (len(self.__middle) == 1) and (not is_glsl_token(self.__middle[0])):
            return self.__middle[0]
        return None

    def getSingleChildRight(self):
        """Get right child if it's a single token."""
        if (len(self.__right) == 1) and is_glsl_token(self.__right[0]):
            return self.__right[0]
        return None

    def isSingleChildRight(self):
        """Tell if this is the single, right child of its parent."""
        if self.__parent and (self.__parent.getSingleChildRight() == self):
            return True
        return False

    def getTypeFromOpeningType(self):
        """Get type of a type opening statement or None."""
        if self.__left or self.__right:
            return None
        if len(self.__middle) != 2:
            return None
        if (not is_glsl_token(self.__middle[0])) or (not is_glsl_token(self.__middle[1])):
            return None
        if self.__middle[1].getSingleChildMiddleNonToken() != "(":
            return None
        left = self.__middle[0].getSingleChildMiddleNonToken()
        if not is_glsl_type(left):
            return None
        return left

    def isSurroundedByParens(self):
        """Tell if this is a token surrounded by parens."""
        if (len(self.__left) != 1) or (len(self.__right) != 1):
            return False
        left = self.__left[0].getSingleChild()
        right = self.__right[0].getSingleChild()
        return ("(" == left) and (")" == right)

    def isParameterOfNonIntegrifyFunctionCall(self):
        """Tells if is a parameter of a function call that does not allow integrification of parameters."""
        if self.__parent:
            # Might not be the first parameter, in which case the parent is a comma and we must recurse.
            mid = self.__parent.getSingleChildMiddleNonToken()
            if mid and is_glsl_operator(mid) and (mid.getOperator() == ","):
                return self.__parent.isParameterOfNonIntegrifyFunctionCall()
            # Check function call.
            left = self.__parent.getSingleChildLeft()
            functionName = left.getFunctionCallNameIfFunctionCall()
            if functionName and (functionName in g_deny_integrify_function_calls):
                return True
        return False

    def removeChild(self, op):
        """Remove a child from this."""
        for ii in range(len(self.__left)):
            vv = self.__left[ii]
            if vv is op:
                self.__left.pop(ii)
                vv.setParent(None)
                return
        for ii in range(len(self.__middle)):
            vv = self.__middle[ii]
            if vv is op:
                self.__middle.pop(ii)
                vv.setParent(None)
                return
        for ii in range(len(self.__right)):
            vv = self.__right[ii]
            if vv is op:
                self.__right.pop(ii)
                vv.setParent(None)
                return
        raise RuntimeError("could not remove child '%s' from '%s'" % (str(op), str(self)))

    def removeFromParent(self):
        """Remove this from its parent."""
        self.__parent.removeChild(self)

    def removeParens(self):
        """Remove enclosing parens if possible."""
        if not self.isSurroundedByParens():
            return False
        # Was enclosed by parens, can remove.
        self.__left[0].removeFromParent()
        self.__right[0].removeFromParent()
        self.__left = []
        self.__right = []
        return True

    def replaceContents(self, op):
        """Replace all contents with the contents of the given token."""
        if self is op:
            raise RuntimeError("trying to have '%' replace contents with itself" % (op))
        self.clearContents()
        for ii in op.__left:
            if is_glsl_token(ii):
                ii.setParent(None)
                ii.setParent(self)
            self.__left += [ii]
        op.__left = []
        for ii in op.__middle:
            if is_glsl_token(ii):
                ii.setParent(None)
                ii.setParent(self)
            self.__middle += [ii]
        op.__middle = []
        for ii in op.__right:
            if is_glsl_token(ii):
                ii.setParent(None)
                ii.setParent(self)
            self.__right += [ii]
        op.__right = []

    def replaceMiddle(self, op):
        """Replace middle content with given single element."""
        self.clearContentsMiddle()
        self.addMiddle(op)

    def replaceInParent(self, op):
        """Replace this token in its parent with given replacement."""
        if not self.__parent:
            raise RuntimeError("no parent to replace '%s' with '%s' in" % (str(self), str(op)))
        self.__parent.replaceToken(self, op)

    def replaceToken(self, needle, replacement):
        """Replace a child token with a replacement token."""
        if replacement.getParent() is self:
            raise RuntimeError("replacement '%s' is a child of '%s'" % (str(replacement), str(self)))
        for ii in range(len(self.__left)):
            if self.__left[ii] is needle:
                needle.setParent(None)
                replacement.removeFromParent()
                self.__left[ii] = replacement
                return
        for ii in range(len(self.__middle)):
            if self.__middle[ii] is needle:
                needle.setParent(None)
                replacement.removeFromParent()
                self.__middle[ii] = replacement
                return
        for ii in range(len(self.__right)):
            if self.__right[ii] is needle:
                needle.setParent(None)
                replacement.removeFromParent()
                self.__right[ii] = replacement
                return
        raise RuntimeError("'%s' to be replaced is not a child of '%s'" % (str(needle), str(self)))

    def setParent(self, op):
        """Set parent."""
        if op and self.__parent and (self.__parent != op):
            raise RuntimeError("hierarchy inconsistency in '%s', parent '%s' over existing '%s'" %
                               (str(self), str(op), str(self.__parent)))
        self.__parent = op

    def simplify(self):
        """Perform any single simplification and stop."""
        # Remove parens.
        if self.isSurroundedByParens():
            if self.simplifyRemoveParens():
                return True
        # Recurse down.
        for ii in self.__left:
            if ii.simplify():
                return True
        for ii in self.__right:
            if ii.simplify():
                return True
        for ii in self.__middle:
            if is_glsl_token(ii):
                if ii.simplify():
                    return True
        # Perform operations only after removing any possible parens.
        mid = self.getSingleChildMiddleNonToken()
        if is_glsl_operator(mid):
            if self.simplifyApplyOperator(mid):
                return True
        # Was not an operator. Check for floating point operations.
        if is_glsl_float(mid):
            if self.simplifyIntegrify(mid):
                return True
        # Check for integer operations.
        if is_glsl_int(mid):
            if self.simplifyConversion(mid):
                return True
        return False

    def simplifyApplyOperator(self, oper):
        """Simplify by applying an operator."""
        param_count = oper.getParamCount()
        # Binary operators.
        if param_count == 2:
           # Try to remove trivial cases.
           if self.collapseIdentity():
               return True
           (left_parent, left_token) = self.findEqualTokenLeft(self)
           (right_parent, right_token) = self.findEqualTokenRight(self)
           if left_parent and left_token and right_parent and right_token:
               # Trivial case - leaf entry that can just be applied.
               if left_parent is right_parent:
                   if not (left_parent is self):
                       raise RuntimeError("left and right operator resolve as '%s' not matching self '%s'" %
                                          (str(left_parent), str(self)))
                   result = apply_operator(oper, left_token, right_token)
                   if not (result is None):
                       # Remove sides from parent.
                       left_token.removeFromParent()
                       right_token.removeFromParent()
                       self.__middle = [result]
                       return True
               # Nontrivial cases.
               left_oper = left_parent.getSingleChildMiddleNonToken()
               right_oper = right_parent.getSingleChildMiddleNonToken()
               result = None
               # Double divide -> multiply.
               if (left_oper == "/") and (right_oper == "/") and left_token.isSingleChildRight():
                   result = apply_operator(interpret_operator("*"), left_token, right_token)
               # Same operation -> can be just applied.
               elif left_parent == right_parent:
                   result = apply_operator(left_oper, left_token, right_token)
               # Substract addition: <something> - a + b => <something> + (b - a)
               elif (left_oper == "-") and (oper == "+") and (oper is right_oper):
                   result = apply_operator(left_oper, right_token, left_token)
                   # If b - a is negative, replace it with its absolute value which is going to get subtracted.
                   if result.getFloat() < 0.0:
                       right_oper.setOperator("-")
                       if is_glsl_int(result):
                           result = interpret_int(str(abs(result.getInt())))
                       elif is_glsl_float(result):
                           number_string = str(abs(result.getFloat()))
                           (integer_part, decimal_part) = number_string.split(".")
                           result = interpret_float(integer_part, decimal_part)
                       else:
                           raise RuntimeError("unknown result object '%s'" % (str(result)))
               # TODO: further cases.
               # On success, eliminate upper token (left only if necessary) and replace other token with result.
               if result:
                   if left_parent is self:
                       right_token.collapseUp()
                       left_token.replaceMiddle(result)
                   else:
                       left_token.collapseUp()
                       right_token.replaceMiddle(result)
                   return True
        # Trinary operators.
        elif param_count == 3:
            if oper.getOperator() != "?":
                return False
            # ? and : have the same precedence. Check if the parent is colon.
            if self.__parent:
                mid = self.__parent.getSingleChildMiddleNonToken()
                if is_glsl_operator(mid) and mid.getOperator() == ":":
                    cmp = self.getSingleChildLeft()
                    left = self.getSingleChildRight()
                    right = self.__parent.getSingleChildRight()
                    if self.__parent.applyTernary(cmp, left, right):
                        return True
            # TODO: ternary with ? higher than :
        return False

    def simplifyConversion(self, mid):
        """Simplify an integer value by allowing conversion to float (if possible)."""
        # Alone in float() directive.
        left = self.getSingleChildLeft()
        right = self.getSingleChildRight()
        if left and right and (right.getSingleChildMiddleNonToken() == ")"):
            opening_type = left.getTypeFromOpeningType()
            if opening_type.getType() == "float":
                float_value = interpret_float(mid.getStr(), "0")
                self.clearContents()
                self.addMiddle(float_value)
                return True
        return False

    def simplifyIntegrify(self, mid):
        """Simplify a float middle element by allowing integrification (if possible)."""
        if mid.isIntegrifyAllowed() or (abs(mid.getFloat()) > 2147483647.0):
            return False
        # No operators, left or right.
        left = self.findSiblingOperatorLeft()
        right = self.findSiblingOperatorRight()
        # Comma is not an operator.
        if left and (left.getOperator() == ","):
            left = None
        if right and (right.getOperator() == ","):
            right = None
        if (not left) and (not right):
            # Check if part of a denied function call.
            if not self.isParameterOfNonIntegrifyFunctionCall():
                mid.setAllowIntegrify(True)
                return True
        # Alone in vecN() directive.
        left = self.getSingleChildLeft()
        right = self.getSingleChildRight()
        if left and right and (right.getSingleChildMiddleNonToken() == ")"):
            opening_type = left.getTypeFromOpeningType()
            if opening_type.isVectorType():
                mid.setAllowIntegrify(True)
                return True
        # If could not be integrified, at least ensure that float precision is not exceeded.
        if mid.getPrecision() > 6:
            mid.truncatePrecision(6)
            return True
        return False

    def simplifyRemoveParens(self):
        """Simplify by removing parens (if possible)."""
        middle_lst = self.flattenMiddle()
        # Single expression.
        if len(middle_lst) == 1:
            if self.removeParens():
                return True
        # Number or name with access.
        elif len(middle_lst) == 2:
            mid_lt = middle_lst[0]
            mid_rt = middle_lst[1]
            if (is_glsl_name(mid_lt) or is_glsl_number(mid_lt)) and is_glsl_access(mid_rt):
                if self.removeParens():
                    return True
        # Single function call or indexing (with potential access).
        elif len(middle_lst) >= 3:
            mid_name = middle_lst[0]
            mid_opening = middle_lst[1]
            last_index = -1
            mid_ending = middle_lst[last_index]
            # If last part is access, try the element before that instead.
            if is_glsl_access(mid_ending) and (len(middle_lst) >= 4):
                last_index = -2
                mid_ending = middle_lst[last_index]
            # Check for function call or indexing format.
            if (is_glsl_name(mid_name) or is_glsl_type(mid_name)) and is_glsl_paren(mid_opening) and mid_opening.matches(mid_ending):
                if is_single_call_or_access_list(middle_lst[2:last_index], mid_opening):
                    if self.removeParens():
                        return True
        # Only contains lower-priority operators compared to outside.
        paren_rt = self.__right[0].getSingleChild()
        elem_rt = self.findRightSiblingElementFromParentTree(paren_rt)
        prio = self.findHighestPrioOperatorMiddle()
        # Right element cannot be access or bracket.
        if (prio >= 0) and (not is_glsl_access(elem_rt)) and (elem_rt != "["):
            left = self.findSiblingOperatorLeft()
            right = self.findSiblingOperatorRight()
            if left:
                if left.getPrecedence() > prio:
                    if right:
                        if right.getPrecedence() >= prio:
                            if self.removeParens():
                                return True
                    else:
                        if self.removeParens():
                            return True
            elif right:
                if right.getPrecedence() >= prio:
                    if self.removeParens():
                        return True
            else:
                if self.removeParens():
                    return True
        # Parens not removed.
        return False

    def __str__(self):
        """String representation."""
        if 1 == len(self.__middle):
            return "Token(%i:'%s':%i)" % (len(self.__left), str(self.__middle[0]), len(self.__right))
        return "Token(%i:%i:%i)" % (len(self.__left), len(self.__middle), len(self.__right))

########################################
# Functions ############################
########################################

def apply_operator(oper, left_token, right_token):
    """Apply operator, collapsing into one number if possible."""
    left = left_token.getSingleChild()
    right = right_token.getSingleChild()
    # Numbers must be valid
    left_number = get_contained_glsl_number(left)
    right_number = get_contained_glsl_number(right)
    if (left_number is None) or (right_number is None):
        return None
    both_are_int = is_glsl_int(left) and is_glsl_int(right)
    # Perform operation.
    result_number = oper.applyOperator(left_number, right_number)
    # Replace content of this with the result number
    if isinstance(result_number, bool):
        result_number = interpret_bool(str(result_number).lower())
    elif both_are_int:
        int_number = interpret_int(str(result_number))
        if int_number is None:
            result_number = interpret_int(str(int(float(result_number))))
        else:
            result_number = int_number
    else:
        number_string = str(float(result_number))
        (integer_part, decimal_part) = number_string.split(".")
        result_number = interpret_float(integer_part, decimal_part)
    # Not all operations require truncation afterwards.
    if oper.requiresTruncation() and (left.requiresTruncation() or right.requiresTruncation()):
        lower_precision = min(left.getPrecision(), right.getPrecision()) + 1
        precision = max(max(left.getPrecision(), right.getPrecision()), lower_precision)
        result_number.truncatePrecision(precision)
    return result_number

def is_glsl_number(op):
    """Tell if given object is a number."""
    if is_glsl_bool(op) or is_glsl_float(op) or is_glsl_int(op):
        return True
    return False

def is_glsl_token(op):
    """Tell if given object is a GLSL token."""
    return isinstance(op, GlslToken)

def is_minus_collapsible(left, mid, right):
    """Tell if given triplet of elements is minus-collapsible."""
    if not (is_glsl_float(right) or is_glsl_int(right)):
        return False
    if not (is_glsl_operator(mid) and (mid.getOperator() == "-")):
        return False
    if is_glsl_paren(left):
        return left.isOpening()
    if is_glsl_operator(left):
        return True
    return left is None

def is_single_call_or_access_list(lst, opening_paren):
    """Tell if given list is a single call or access."""
    parens = 1
    simplify_allowed = True
    for ii in lst:
        if 0 >= parens:
            if "(" == opening_paren:
                return False
            # Chaining brackets is ok.
            if "[" == opening_paren:
                if opening_paren != ii:
                    return False
        # Keep track of paren count.
        if opening_paren == ii:
            parens += 1
        elif opening_paren.matches(ii):
            parens -= 1
    return (0 < parens)

def get_contained_glsl_number(op):
    """Gets internal contained GLSL number or None."""
    if is_glsl_bool(op):
        return op.getBool()
    if is_glsl_float(op):
        return op.getFloat()
    if is_glsl_int(op):
        return op.getInt()
    return None

def token_descend(token):
    """Descend token or token list."""
    # Single element case.
    if is_glsl_token(token):
        token.setParent(None)
        single = token.getSingleChild()
        if single == token:
            return token
        return token_descend(single)
    # Listing case.
    if is_listing(token):
        for ii in token:
            ii.setParent(None)
            if not is_glsl_token(ii):
                raise RuntimeError("non-token '%s' found in descend" % (str(ii)))
        if len(token) == 1:
            return token_descend(token[0])
    # Could not descend.
    return token

def token_list_collapse_negative_numbers(lst):
    """Collapse minuses with numbers into a proper negative numbers as necessary."""
    prev2 = None
    prev2_content = None
    prev1 = None
    prev1_content = None
    for ii in range(len(lst)):
        curr = lst[ii]
        curr_content = curr.getSingleChildMiddleNonToken()
        if curr_content is None:
            raise RuntimeError("complex token structure detected in list collapse phase")
        # Can only collapse if middle operator is minus.
        if is_minus_collapsible(prev2_content, prev1_content, curr_content):
            ret = lst[:ii - 1] + [GlslToken(curr_content.getNegatedNumber())] + lst[ii + 1:]
            #print(str(list(map(str, lst))))
            return token_list_collapse_negative_numbers(ret)
        # Continue.
        prev2 = prev1
        prev2_content = prev1_content
        prev1 = curr
        prev1_content = curr_content
    # No modifications.
    return lst

def token_list_create(lst):
    """Build a token list from a given listing, ensuring every element is a token."""
    ret = []
    for ii in lst:
        if not is_glsl_token(ii):
            ret += [GlslToken(ii)]
        elif ii:
            ret += [ii]
    return token_list_collapse_negative_numbers(ret)

def token_tree_build(lst):
    """Builds and balances a token tree from given list."""
    # Might be that everything is lost at this point.
    if not lst:
        return None
    # Ensure all list elements are tokens.
    for ii in lst:
        if not is_glsl_token(ii):
            raise RuntimeError("non-token object '%s' detected while building token tree" % str(ii))
    # Start iteration over tokenized list.
    bracket_count = 0
    paren_count = 0
    first_bracket_index = -1
    first_paren_index = -1
    lowest_operator = None
    lowest_operator_index = -1
    for ii in range(len(lst)):
        vv = lst[ii].getSingleChild()
        # Count parens.
        if is_glsl_paren(vv):
            # Bracket case.
            if vv.isBracket():
                new_bracket_count = vv.updateBracket(bracket_count)
                if new_bracket_count == bracket_count:
                    raise RuntimeError("wut?")
                bracket_count = new_bracket_count
                # Split on brackets reaching 0.
                if 0 >= bracket_count:
                    if 0 > first_bracket_index:
                        raise RuntimeError("bracket inconsistency")
                    return token_tree_split_paren(lst, first_bracket_index, ii)
                elif (1 == bracket_count) and (0 > first_bracket_index):
                    first_bracket_index = ii
            # Paren case.
            elif vv.isParen():
                new_paren_count = vv.updateParen(paren_count)
                if new_paren_count == paren_count:
                    raise RuntimeError("wut?")
                paren_count = new_paren_count
                # Split on parens reaching 0.
                if 0 >= paren_count:
                    if 0 > first_paren_index:
                        raise RuntimeError("paren inconsistency")
                    return token_tree_split_paren(lst, first_paren_index, ii)
                elif (1 == paren_count) and (0 > first_paren_index):
                    first_paren_index = ii
            # Curly braces impossible.
            else:
                raise RuntimeError("unknown paren object '%s'" % (str(vv)))
        # If we're not within parens, consider operators.
        if is_glsl_operator(vv) and (0 >= bracket_count) and (0 >= paren_count):
            if (not lowest_operator) or (vv < lowest_operator):
                lowest_operator = vv
                lowest_operator_index = ii
    # Iteration done. Make a tiny subtree on the lowest operator position and continue.
    if lowest_operator:
        ret = GlslToken(lowest_operator)
        left_block = []
        right_block = []
        left = None
        right = None
        # Get extending list left and right.
        if lowest_operator_index >= 2:
            left_block = lst[:(lowest_operator_index - 1)]
        if lowest_operator_index <= len(lst) - 3:
            right_block = lst[(lowest_operator_index + 2):]
        # Check for left existing.
        if lowest_operator_index >= 1:
            left = lst[lowest_operator_index - 1]
            ret.addLeft(left)
        elif not (lowest_operator in ("-", "++", "--", "!")):
            raise RuntimeError("left component nonexistent for operator '%s'" % (str(lowest_operator)))
        # Check for right existing.
        if lowest_operator_index <= len(lst) - 2:
            right = lst[lowest_operator_index + 1]
            ret.addRight(right)
        elif not (lowest_operator in ("++", "--")):
            raise RuntimeError("right component nonexistent for operator '%s'" % (str(lowest_operator)))
        return token_tree_build(left_block + [ret] + right_block)
    # Only option at this point is that the list has no operators and no parens - return as itself.
    return GlslToken(lst)

def token_tree_simplify(op):
    """Perform first found simplify operation for given tree."""
    op.collapse()
    if op.simplify():
        return True
    return False

def token_tree_split_paren(lst, first, last):
    """Split token tree for parens."""
    # Read types, names or accesses left.
    left = [lst[first]]
    iter_left = first - 1
    while iter_left >= 0:
        prospect = lst[iter_left].getSingleChild()
        if is_glsl_access(prospect) or is_glsl_name(prospect) or is_glsl_type(prospect):
            left = [lst[iter_left]] + left
            iter_left -= 1
        else:
            break
    # Left may be multiple elements.
    if 1 < len(left):
        left = GlslToken(left)
    else:
        left = left[0]
    # It's ok to have empty parens, as opposed to empty brackets.
    middle = token_tree_build(lst[first + 1:last])
    right = lst[last]
    # Create split.
    ret = GlslToken(middle)
    ret.addLeft(left)
    ret.addRight(right)
    return token_tree_build(lst[:iter_left + 1] + [ret] + lst[last + 1:])
