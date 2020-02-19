#include "glsl_shader.hpp"

#include "glsl_wave.hpp"

#include <boost/filesystem.hpp>

#include <fstream>
#include <iostream>
#include <sstream>

namespace fs = boost::filesystem;

//######################################
// Local ###############################
//######################################

namespace
{

/// Find a file, try several different default locations.
///
/// \param name Base name to open.
/// \return File to open or an empty string.
fs::path find_file(const std::string &name)
{
    fs::path attempt = name;
    if(fs::exists(attempt))
    {
        return attempt;
    }

    attempt = fs::path("..") / fs::path(name);
    if(fs::exists(attempt))
    {
        return attempt;
    }

    const fs::path SRC_PATH("src");
    attempt = SRC_PATH / fs::path(name);
    if(fs::exists(attempt))
    {
        return attempt;
    }

    attempt = fs::path("..") / SRC_PATH / fs::path(name);
    if(fs::exists(attempt))
    {
        return attempt;
    }

    const fs::path REL_PATH("rel");
    attempt = REL_PATH / fs::path(name);
    if(fs::exists(attempt))
    {
        return attempt;
    }

    attempt = fs::path("..") / REL_PATH / fs::path(name);
    if(fs::exists(attempt))
    {
        return attempt;
    }

    return fs::path();
}

/// Read a file.
///
/// \param name File to open.
/// \return Contents of file as a string.
std::string read_file(const fs::path &name)
{
    std::ostringstream ret;
    std::ifstream fd(name.string());

    for(;;)
    {
        char cc;
        fd.get(cc);

        if(fd.eof())
        {
            return ret.str();
        }

        ret << cc;
    }
}

/// Line comment regex on a string.
///
/// \param bb String iterator.
/// \param ee String endpoint.
/// \return Iterator to end of match or original iterator if no match.
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

/// Block comment regex on a string.
///
/// \param bb String iterator.
/// \param ee String endpoint.
/// \return Iterator to end of match or original iterator if no match.
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

/// Comment regex on a string.
///
/// \param bb String iterator.
/// \param ee String endpoint.
/// \return Iterator to end of match or original iterator if no match.
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

/// Regex for whitespace (any amount).
///
/// \param bb String iterator.
/// \param ee String endpoint.
/// \return Iterator at the end of whitespace.
static std::string::const_iterator regex_whitespace(std::string::const_iterator bb,
        const std::string::const_iterator ee)
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

/// Regex for a word and any amount of following whitespace.
///
/// \param bb String iterator.
/// \param ee String endpoint.
/// \param word Word to match.
/// \return Iterator to end of match or original iterator if no match.
static std::string::const_iterator regex_word_whitespace(std::string::const_iterator bb,
        const std::string::const_iterator ee, std::string_view word)
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

/// Regex for precision words and any amount of following whitespace.
///
/// \param bb String iterator.
/// \param ee String endpoint.
/// \return Iterator to end of match or original iterator if no match.
static std::string::const_iterator regex_precision_whitespace(std::string::const_iterator bb,
        const std::string::const_iterator ee)
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

/// Perform glsl2 regex on a string.
///
/// \param bb String iterator.
/// \param ee String endpoint.
/// \return Iterator to end of match or original iterator if no match.
static std::string::const_iterator regex_glesv2(std::string::const_iterator bb,
        const std::string::const_iterator ee)
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

}

//######################################
// Class ###############################
//######################################

GlslShaderSource::~GlslShaderSource()
{
    BOOST_ASSERT(!m_id);
}

void GlslShaderSource::addFile(std::string_view fname)
{
    m_files.emplace_back(fname);
}

std::string GlslShaderSource::read() const
{
  std::string ret;

  for(const auto& vv : m_files)
  {
    fs::path name = find_file(vv);
    if(name.empty())
    {
      std::ostringstream sstr;
      sstr << "could not find suitable file source for " << fs::path(vv);
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    // Need newline as last char if the file does do not supply one.
    if(!ret.empty() && (ret.back() != '\n') && (ret.back() != '\r'))
    {
        ret += "\n";
    }

    std::string source = read_file(name);
    ret += source;
  }

  std::string preprocessed = glsl_wave_preprocess(ret);
#if !defined(DNLOAD_GLESV2)
  return convert_glesv2_gl(preprocessed);
#else
  return preprocessed;
#endif
}

std::string GlslShaderSource::getName() const
{
  std::ostringstream ret;
  ret << "'";

  for(size_t ii = 0; (ii < m_files.size()); ++ii)
  {
    if(ii)
    {
      ret << ";";
    }
    ret << m_files[ii];
  }

  ret << "'";
  return ret.str();
}

//######################################
// Global ##############################
//######################################

std::string convert_glesv2_gl(std::string_view op)
{
  std::string ret(op);
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

