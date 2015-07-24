#ifndef INTRO_HPP
#define INTRO_HPP

#if defined(HAVE_INTTYPES_H)
#include <inttypes.h>
#elif defined(HAVE_STDINT_H)
#include <stdint.h>
#else // default
#include <stdint.h>
#endif

#if defined(USE_LD)

#include <string>

/// Get 10-base number count of a number.
///
/// \param op Number to investigate.
/// \return 10-base number count.
extern size_t base10_magnitude(size_t op);

/// Get string representation of a number with indent to given value.
///
/// \param num Number to get.
/// \param indent Number to indent to.
/// \return String representation.
extern std::string string_format_zero_padded_number(size_t num, size_t indent);

/// \brief Audio writing callback.
///
/// \param data Raw audio data.
/// \param size Audio data size (in samples).
extern void write_audio_callback(void *data, unsigned size);

/// \brief Image writing callback.
///
/// \param screen_w Screen width.
/// \param screen_h Screen height.
/// \param idx Frame index to write.
extern void write_frame_callback(unsigned screen_w, unsigned screen_h, unsigned idx);

/// Intro call to make.
///
/// \param screen_w Window width.
/// \param screen_h Window height.
/// \param flag_developer True to turn on developer mode.
/// \param flag_fullscreen Enable fullscreen?
/// \param flag_record Do not play intro normally, record it to disk instead.
extern int intro(unsigned screen_w, unsigned screen_h, uint8_t flag_developer, uint8_t flag_fullscreen,
    uint8_t flag_record);

#endif

#endif
