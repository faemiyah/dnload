#ifndef GLSL_WAVE_HPP
#define GLSL_WAVE_HPP

#include <string>

/// Preprocess GLSL with wave.
///
/// This is a separate function only due to Boost::Wave problems with C++ standard versions.
///
/// \parmam op Raw source to process.
/// \ŗeturn Source that can be given to shader compilers.
extern std::string glsl_wave_preprocess(const std::string &op);

#endif
