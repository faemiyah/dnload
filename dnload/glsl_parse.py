from dnload.glsl_block import tokenize
from dnload.glsl_block_assignment import glsl_parse_assignment
from dnload.glsl_block_function import glsl_parse_function
from dnload.glsl_block_declaration import glsl_parse_declaration
from dnload.glsl_block_default import glsl_parse_default
from dnload.glsl_block_inout import glsl_parse_inout
from dnload.glsl_block_pervertex import glsl_parse_pervertex
from dnload.glsl_block_struct import glsl_parse_struct
from dnload.glsl_block_uniform import glsl_parse_uniform

########################################
# Functions ############################
########################################

def glsl_parse(source):
    """Parse given source."""
    content = tokenize(source)
    return glsl_parse_tokenized(content)

def glsl_parse_tokenized(source):
    """Parse tokenized source."""
    # End of input.
    if not source:
        return []
    # Try default parses for global scope.
    (block, remaining) = glsl_parse_inout(source)
    if block:
        return [block] + glsl_parse_tokenized(remaining)
    (block, remaining) = glsl_parse_struct(source)
    if block:
        return [block] + glsl_parse_tokenized(remaining)
    (block, remaining) = glsl_parse_pervertex(source)
    if block:
        return [block] + glsl_parse_tokenized(remaining)
    (block, remaining) = glsl_parse_uniform(source)
    if block:
        return [block] + glsl_parse_tokenized(remaining)
    (block, remaining) = glsl_parse_function(source)
    if block:
        return [block] + glsl_parse_tokenized(remaining)
    # Try parses normally for local scope.
    (block, remaining) = glsl_parse_declaration(source)
    if block:
        return [block] + glsl_parse_tokenized(remaining)
    (block, remaining) = glsl_parse_assignment(source)
    if block:
        return [block] + glsl_parse_tokenized(remaining)
    # Fallback, should never happen.
    return glsl_parse_default(source)
