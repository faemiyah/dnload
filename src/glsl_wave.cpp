#include "glsl_wave.hpp"

#include <boost/algorithm/string.hpp>
#include <boost/foreach.hpp>
#include <boost/tuple/tuple.hpp>
#include <boost/wave/cpp_context.hpp>
#include <boost/wave/cpplexer/cpp_lex_iterator.hpp>

typedef boost::wave::cpplexer::lex_iterator<boost::wave::cpplexer::lex_token<> > wave_cpplex_iterator;
typedef boost::wave::context<std::string::const_iterator, wave_cpplex_iterator> wave_context;

//######################################
// Local ###############################
//######################################

namespace
{

/// Split GLSL source to onward-passed preprocessor definitions and the rest.
///
/// \param source Source input.
/// \return Tuple of GLSL shader compiler preprocessor input and rest of the source.
boost::tuple<std::string, std::string> glsl_split(const std::string &source)
{
  std::vector<std::string> lines;

  boost::split(lines, source, boost::is_any_of("\n"));

  std::vector<std::string> glsl_list;
  std::vector<std::string> cpp_list;

  BOOST_FOREACH(const std::string &vv, lines)
  {
    std::string ii = boost::trim_copy(vv);

    if(boost::starts_with(ii, "#"))
    {
      ii = boost::trim_copy(ii.substr(1));

      if(boost::starts_with(ii, "define") ||
          boost::starts_with(ii, "version"))
      {
        glsl_list.push_back(vv);
        continue;
      }
    }

    cpp_list.push_back(vv);
  }

  std::string glsl_ret = boost::algorithm::join(glsl_list, "\n");
  std::string cpp_ret = boost::algorithm::join(cpp_list, "\n");

  if(!glsl_ret.empty())
  {
    glsl_ret += "\n";
  }

  return boost::make_tuple(glsl_ret, cpp_ret);
}

/// Tidy up given source, remove all preprocess lines.
///
/// \prarm source Source input.
/// \return Source with preprocessor lines removed.
std::string glsl_tidy(const std::string &source)
{
  std::vector<std::string> lines;

  boost::split(lines, source, boost::is_any_of("\n"));

  std::vector<std::string> accepted;

  BOOST_FOREACH(const std::string &vv, lines)
  {
    std::string ii = boost::trim_copy(vv);

    if(!boost::starts_with(ii, "#"))
    {
      accepted.push_back(ii);
    }
  }

  std::string ret = boost::algorithm::join(accepted, "\n");

  return ret;
}

}

//######################################
// Global ##############################
//######################################

std::string glsl_wave_preprocess(const std::string &op)
{
  // Split into GLSL preprocess code and the rest.
  std::string removed;
  std::string source;
  boost::tie(removed, source) = glsl_split(op);

  // Preprocess with wave.
  std::ostringstream preprocessed;
  wave_context ctx(source.cbegin(), source.cend(), "Boost::Wave GLSL;");
  for(wave_context::iterator_type ii = ctx.begin(), ee = ctx.end(); (ii != ee); ++ii)
  {
    preprocessed << ii->get_value();
  }

  return removed + glsl_tidy(preprocessed.str());
}

