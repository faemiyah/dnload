#include "glsl_shader_source.hpp"

#include <cctype>
#include <cstring>
#include <iostream>

#if defined(DNLOAD_GLESV2)
/** \cond */
#define GL_GLEXT_PROTOTYPES
/** \endcond */
#include "GLES2/gl2ext.h"
#endif

/** \brief Generate an indent.
 *
 * \param op Indent length.
 */
static std::string create_indent(unsigned op)
{
  std::ostringstream ret;

  for(unsigned ii = 0; (ii < op); ++ii)
  {
    ret << "  ";
  }
  return ret.str();
}

/** \brief Regex for whitespace (any amount).
 *
 * \param bb String iterator.
 * \param ee String endpoint.
 * \return Iterator at the end of whitespace.
 */
static std::string::const_iterator regex_whitespace(std::string::const_iterator bb,
    const std::string::const_iterator &ee)
{
  for(std::string::const_iterator ii = bb; (ii != ee); ++ii)
  {
    if(!isspace(static_cast<int>(*ii)))
    {
      return ii;
    }
  }
  return ee;
}

/** \brief Regex for a word and any amount of following whitespace.
 *
 * \param bb String iterator.
 * \param ee String endpoint.
 * \param word Word to match.
 * \return Iterator to end of match or original iterator if no match.
 */
static std::string::const_iterator regex_word_whitespace(std::string::const_iterator bb,
    const std::string::const_iterator &ee, const std::string &word)
{
  std::string::const_iterator ii = bb;
  unsigned jj = 0;

  while(word.length() > jj)
  {
    if(ii == ee)
    {
      return bb;
    }
    int lhs = tolower(static_cast<int>(*ii));
    int rhs = tolower(static_cast<int>(word[jj]));
    if(lhs != rhs)
    {
      return bb;
    }
    ++ii;
    ++jj;
  }
  return regex_whitespace(ii, ee);
}

/** \brief Regex for precision words and any amount of following whitespace.
 *
 * \param bb String iterator.
 * \param ee String endpoint.
 * \return Iterator to end of match or original iterator if no match.
 */
static std::string::const_iterator regex_precision_whitespace(std::string::const_iterator bb,
    const std::string::const_iterator &ee)
{
  std::string::const_iterator ii = regex_word_whitespace(bb, ee, "lowp");
  if(ii != bb)
  {
    return regex_whitespace(ii, ee);
  }
  ii = regex_word_whitespace(bb, ee, "mediump");
  if(ii != bb)
  {
    return regex_whitespace(ii, ee);
  }
  ii = regex_word_whitespace(bb, ee, "highp");
  if(ii != bb)
  {
    return regex_whitespace(ii, ee);
  }

  return bb;
}

/** \brief Perform glsl2 regex on a string.
 *
 * \param bb String iterator.
 * \param ee String endpoint.
 * \return Iterator to end of match or original iterator if no match.
 */
static std::string::const_iterator regex_glesv2(std::string::const_iterator bb,
    const std::string::const_iterator &ee)
{
  std::string::const_iterator ii = bb;

  // Try "precision" statement."
  std::string::const_iterator jj = regex_word_whitespace(ii, ee, "precision");
  if(jj != ii)
  {
    std::string::const_iterator kk = jj;
    jj = regex_precision_whitespace(kk, ee);
    if(jj != kk)
    {
      kk = jj;
      jj = regex_word_whitespace(kk, ee, "float");
      if(jj != kk)
      {
        kk = jj;
        jj = regex_word_whitespace(kk, ee, ";");
        if(jj != kk)
        {
          return jj;
        }
      }
    }
  }

  // Try precision statement otherwise.
  jj = regex_precision_whitespace(ii, ee);
  if(jj != ii)
  {
    return jj;
  }

  return bb;
}

/** \brief Line comment regex on a string.
 *
 * \param bb String iterator.
 * \param ee String endpoint.
 * \return Iterator to end of match or original iterator if no match.
 */
static std::string::const_iterator regex_line_comment(std::string::const_iterator bb,
    const std::string::const_iterator &ee)
{
  std::string::const_iterator ii = bb;

  if((ii == ee) || ('/' != *ii))
  {
    return bb;
  }
  ++ii;
  if((ii == ee) || ('/' != *ii))
  {
    return bb;
  }

  for(;;)
  {
    ++ii;
    if(ii == ee)
    {
      return ii;
    }
    if('\n' == *ii)
    {
      ++ii;
      return ii;
    }
  }
}

/** \brief Block comment regex on a string.
 *
 * \param bb String iterator.
 * \param ee String endpoint.
 * \return Iterator to end of match or original iterator if no match.
 */
static std::string::const_iterator regex_block_comment(std::string::const_iterator bb,
    const std::string::const_iterator &ee)
{
  std::string::const_iterator ii = bb;
  bool allow_return = false;

  if((ii == ee) || ('/' != *ii))
  {
    return bb;
  }
  ++ii;
  if((ii == ee) || ('*' != *ii))
  {
    return bb;
  }

  for(;;)
  {
    ++ii;
    if(ii == ee)
    {
      return bb;
    }
    if(allow_return)
    {
      if('/' == *ii)
      {
        ++ii;
        return ii;
      }
      allow_return = false;
    }
    else if('*' == *ii)
    {
      allow_return = true;
    }
  }
}

/** \brief Comment regex on a string.
 *
 * \param bb String iterator.
 * \param ee String endpoint.
 * \return Iterator to end of match or original iterator if no match.
 */
static std::string::const_iterator regex_comment(std::string::const_iterator bb,
    const std::string::const_iterator &ee)
{
  std::string::const_iterator ii = regex_line_comment(bb, ee);
  if(ii != bb)
  {
    return ii;
  }
  return regex_block_comment(bb, ee);
}

/** \brief Perform a set regex on a string.
 *
 * \param ii String iterator.
 * \return True if matches, false if not.
 */
static bool regex_space_plus_alpha_plus_semicolon(std::string::const_iterator ii,
    const std::string::const_iterator &ee)
{
  for(++ii; (ii != ee); ++ii)
  {
    if(' ' != *ii)
    {
      for(; (ii != ee); ++ii)
      {
        if(!isalpha(*ii))
        {
          for(; (ii != ee); ++ii)
          {
            char cc = *ii;

            if(' ' != cc)
            {
              return (';' == cc);
            }
          }
        }
      }
    }
  }
  return false;
}

GlslShaderSource::GlslShaderSource(const char *str1) :
  m_indent(0)
{
  this->add(str1);
}

void GlslShaderSource::add(const std::string &op)
{
  for(std::string::const_iterator ii = op.begin(), ee = op.end(); (ii != ee); ++ii)
  {		
    char cc = *ii;

    switch(cc)
    {
      case ';':
        m_source << ";\n" << create_indent(m_indent);
        break;

      case '{':
        m_source << std::endl << create_indent(m_indent) << "{\n";
        ++m_indent;
        m_source << create_indent(m_indent);
        break;

      case '}':
        --m_indent;
        m_source << '\r' << create_indent(m_indent) << "}";
        if(!regex_space_plus_alpha_plus_semicolon(ii + 1, ee) && (ii + 1 != ee))
        {
          m_source << std::endl << create_indent(m_indent);
        }
        break;

      default:
        m_source << cc;
        break;
    }
  }
}

std::string GlslShaderSource::convert_glesv2_gl(const std::string &op)
{
  std::string ret = op;
  std::string::const_iterator ii = ret.begin();
  std::string::const_iterator ee = ret.end();

  while(ii != ee)
  {
    std::string::const_iterator jj = regex_glesv2(ii, ee);
    if(jj != ii)
    {
      // TODO: Erase with iterators when C++11.
      std::string::difference_type erase_start = ii - ret.begin();
      std::string::difference_type erase_count = jj - ret.begin() - erase_start;
      ret = ret.erase(static_cast<size_t>(erase_start), static_cast<size_t>(erase_count));
      ii = ret.begin() + erase_start;
      ee = ret.end();
      continue;
    }
    jj = regex_comment(ii, ee);
    if(jj != ii)
    {
      ii = jj;
      continue;
    }
    ++ii;
  }

  return ret;
}

std::string GlslShaderSource::get_pipeline_info_log(GLuint op)
{
#if defined(DNLOAD_GLESV2)
  (void)op;
  return std::string();
#else
  std::string ret;
  GLint len;

  glGetProgramPipelineiv(op, GL_INFO_LOG_LENGTH, &len);
  if(len)
  {
    GLchar *log = new GLchar[len];
    GLsizei acquired;

    glGetProgramPipelineInfoLog(op, len, &acquired, log);

    ret.assign(log);
    delete[] log;
  }

  return ret;
#endif
}

std::string GlslShaderSource::get_program_info_log(GLuint op)
{
  std::string ret;
  GLint len;

  glGetProgramiv(op, GL_INFO_LOG_LENGTH, &len);
  if(len)
  {
    GLchar *log = new GLchar[len];
    GLsizei acquired;

    glGetProgramInfoLog(op, len, &acquired, log);

    ret.assign(log);
    delete[] log;
  }

  return ret;
}

bool GlslShaderSource::get_program_link_status(GLuint op)
{
  GLint ret;

  glGetProgramiv(op, GL_LINK_STATUS, &ret);

  return (ret != 0);
}

bool GlslShaderSource::get_shader_compile_status(GLuint op)
{
  GLint ret;

  glGetShaderiv(op, GL_COMPILE_STATUS, &ret);

  return (ret != 0);
}

std::string GlslShaderSource::get_shader_info_log(GLuint op)
{
  std::string ret;
  GLint len;

  glGetShaderiv(op, GL_INFO_LOG_LENGTH, &len);
  if(len)
  {
    GLchar *log = new GLchar[len];
    GLsizei acquired;

    glGetShaderInfoLog(op, len, &acquired, log);

    ret.assign(log);
    delete[] log;
  }

  return ret;
}

