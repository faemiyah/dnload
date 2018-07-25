#ifndef GFX_IMAGE_PNG_HPP
#define GFX_IMAGE_PNG_HPP

#include <stdint.h>
#include <string>

namespace gfx
{
  /** \brief Tell if given bit depth allowed by PNG format.
   *
   * \param op Bit depth.
   * \return True if PNG supports given bit depth, false if no.
   */
  inline bool image_png_supports_bpp(unsigned op)
  {
    return ((op == 8) || (op == 16) || (op == 24) || (op == 32));
  }

  /** \brief Probe PNG file.
   *
   * \param pfname Filename to probe.
   * \param Required to be a volume?
   * \return Bit depth found.
   */
  extern unsigned image_png_probe(const std::string &filename, bool require_volume = false);

  /** \brief Read a PNG image.
   *
   * The destination parameters are left unaltered on failure. They will only
   * be written on success.
   *
   * Throws an error on failure.
   *
   * \param pw Destination width.
   * \param ph Destination height.
   * \param pb Destiantion bit depth.
   * \param pdata Destination data.
   * \param filename Source filename.
   * \param required_bpp If set, require this bit depth.
   */
  extern void image_png_load(unsigned &pw, unsigned &ph, unsigned &pb, uint8_t *&pdata,
      const std::string &filename, unsigned required_bpp = 0);

  /** \brief Read an 'extended' PNG image with depth axis.
   *
   * The destination parameters are left unaltered on failure. They will only
   * be written on success.
   *
   * Throws an error on failure.
   *
   * \param pw Destination width.
   * \param ph Destination height.
   * \param pd Destination depth.
   * \param pb Destiantion bit depth.
   * \param pdata Destination data.
   * \param filename Source filename.
   * \param required_bpp If set, require this bit depth.
   */
  extern void image_png_load_extended(unsigned &pw, unsigned &ph, unsigned &pd, unsigned &pb, uint8_t *&pdata,
      const std::string &filename, unsigned required_bpp = 0);

  /** \brief Save a PNG image.
   *
   * Throws an error on failure.
   *
   * \param filename Destination filename.
   * \param pw Source width.
   * \param ph Source height.
   * \param pb Source bit depth.
   * \param pdata Source data.
   */
  extern void image_png_save(const std::string &filename, unsigned pw, unsigned ph, unsigned pb,
      uint8_t *pdata);

  /** \brief Save an 'extended' PNG image with depth axis.
   *
   * Throws an error on failure.
   *
   * \param filename Destination filename.
   * \param pw Source width.
   * \param ph Source height.
   * \param pd Source depth.
   * \param pb Source bit depth.
   * \param pdata Source data.
   */
  extern void image_png_save_extended(const std::string &filename, unsigned pw, unsigned ph, unsigned pd,
      unsigned pb, uint8_t *pdata);
};

#endif
