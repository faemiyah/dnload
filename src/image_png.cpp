#include "png.h"

#include <map>
#include <sstream>
#include <stdexcept>
#include <stdint.h>
#include <string>

#include <boost/lexical_cast.hpp>
#include <boost/scoped_array.hpp>
#include <boost/throw_exception.hpp>
#include "zlib.h"
      
/* Keyword to store depth info under. */
static const std::string PNG_TEXT_DEPTH_KEYWORD("depth");

/** \brief Transform a bpp value into a PNG color type.
 *
 * \param bpp Bit depth.
 * \return Corresponding color type.
 */
static uint8_t bpp_to_png_color_type(unsigned bpp)
{
  switch(bpp)
  {
    case 8:
      break;

    case 16:
      return PNG_COLOR_TYPE_GRAY_ALPHA;

    case 24:
      return PNG_COLOR_TYPE_RGB;

    case 32:
      return PNG_COLOR_TYPE_RGB_ALPHA;

    default:
      {
        std::stringstream sstr;
        sstr << "invalid bit depth: " << bpp;
        BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
      }
      break;
  }

  return PNG_COLOR_TYPE_GRAY;
}

/** \brief Read PNG header.
 *
 * \param filename Filename to open.
 * \return File stream to after the header.
 */
static FILE* png_read_header(const std::string &filename)
{
    FILE *fd = fopen(filename.c_str(), "rb");
    if(!fd)
    {
      std::stringstream sstr;
      sstr << "could not open '" << filename << '\'';
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    {
      uint8_t header[8];
      fread(header, 1, 8, fd);
      if(png_sig_cmp(header, 0, 8))
      {
        fclose(fd);
        std::stringstream sstr;
        sstr << "not a PNG file: " << filename;
        BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
      }
    }

    return fd;
}

/** Wrapper for png_set_text.
 *
 * \param png_ptr PNG pointer.
 * \param info_ptr PNG info pointer.
 * \param ptext Text map.
 */
static void png_set_text_map(png_structp png_ptr, png_infop info_ptr,
    const std::map<std::string, std::string> &ptext)
{
  png_textp text_array = new png_text[ptext.size()];
  png_textp iter = text_array;

  for(std::map<std::string, std::string>::const_iterator ii = ptext.begin(), ee = ptext.end();
      (ii != ee);
      ++ii)
  {
    const std::string &key = (*ii).first;
    const std::string &value = (*ii).second;

    memset(iter, 0, sizeof(png_text));

    iter->compression = PNG_TEXT_COMPRESSION_NONE;
    iter->key = const_cast<char*>(key.c_str());
    iter->text = const_cast<char*>(value.c_str());
    iter->text_length = value.length();

    ++iter;
  }

  png_set_text(png_ptr, info_ptr, text_array, static_cast<int>(ptext.size()));
  delete[] text_array;
}

/** Hold contents of PNG read structs safely. */
class PngReader
{
  private:
    /** File handle. */
    FILE *m_fd;

    /** PNG read struct. */
    png_struct *m_png;

    /** PNG info struct. */
    png_info *m_info;

    /** PNG end info struct. */
    png_info *m_end;

    /** Data block.
     *
     * The data block will be deleted on exit if it is non-NULL. It is used to
     * store reference to the image data which is alter given away from this
     * function.
     */
    uint8_t *m_block;

  public:
    /** \brief Constructor.
     *
     * \param fd File handle to adapt.
     * \param skip How many bytes of file have already been read
     */
    PngReader(FILE *fd, unsigned skip) :
      m_fd(fd),
      m_png(NULL),
      m_info(NULL),
      m_end(NULL),
      m_block(NULL)
    {
      m_png = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
      if(!m_png)
      {
        std::stringstream sstr;
        sstr << "could not create a PNG read struct";
        BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
      }
      m_info = png_create_info_struct(m_png);
      if(!m_info)
      {
        std::stringstream sstr;
        sstr << "could not create a PNG info struct";
        BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
      }
      m_end = png_create_info_struct(m_png);
      if(!m_end)
      {
        std::stringstream sstr;
        sstr << "could not create a PNG end info struct";
        BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
      }

      png_byte keep_chunks[] = { 0 };
      png_set_keep_unknown_chunks(m_png, PNG_HANDLE_CHUNK_NEVER, keep_chunks, 0);

      png_init_io(m_png, m_fd); 
      png_set_sig_bytes(m_png, static_cast<int>(skip));
    }

    /** \brief Destructor. */
    ~PngReader()
    {
      delete[] m_block;
      png_destroy_read_struct(&m_png, &m_info, &m_end);
      fclose(m_fd);
    }

  public:
    /** \brief Get color depth.
     *
     * Transform the color depth accordingly.
     *
     * On unacceptable color type, 0 is returned.
     *
     * \return Color depth dependant on actual color depth and model.
     */
    unsigned getBpp() const
    {
      uint8_t bpp = png_get_bit_depth(m_png, m_info);
      if(8 != bpp)
      {
        return 0;
      }
      switch(png_get_color_type(m_png, m_info))
      {
        case PNG_COLOR_TYPE_GRAY:
          return 8;

        case PNG_COLOR_TYPE_GRAY_ALPHA:
          return 16;

        case PNG_COLOR_TYPE_RGB:
          return 24;

        case PNG_COLOR_TYPE_RGB_ALPHA:
          return 32;

        default:
          return 0;
      }
    }

    /** \brief Get depth.
     *
     * Note that this function is expensive as depth is stored in comments.
     *
     * \return Depth as unsigned or 0.
     */
    unsigned getDepth() const
    {
      png_textp text_array;
      int text_count;

      if(png_get_text(m_png, m_info, &text_array, &text_count) > 0)
      {
        for(int ii = 0; (ii < text_count); ++ii)
        {
          png_textp text = text_array + ii;

          if(PNG_TEXT_DEPTH_KEYWORD.compare(text->key) == 0)
          {
            return boost::lexical_cast<unsigned>(text->text);
          }
        }
      }

      return 0; // No depth available equals 0.
    }

    /** \brief Read actual file contents.
     *
     * \param row_pointers Row pointer input.
     */
    void read(uint8_t **row_pointers)
    {
      png_read_image(m_png, row_pointers);
      png_read_end(m_png, m_end);
    }

    /** \brief Read header.
     */
    void readHeader()
    {
      png_read_info(m_png, m_info);
    }

  public:
    /** \brief Get data block.
     *
     * \return Data pointer.
     */
    uint8_t* getBlock()
    {
      return m_block;
    }

    /** \brief Get height.
     *
     * \return Height as unsigned.
     */
    unsigned getHeight() const
    {
      return static_cast<unsigned>(png_get_image_height(m_png, m_info));
    }

    /** \brief Get the PNG object..
     *
     * \return PNG object.
     */
    png_struct* getPng()
    {
      return m_png;
    }

    /** \brief Get width.
     *
     * \return Width as unsigned.
     */
    unsigned getWidth() const
    {
      return static_cast<unsigned>(png_get_image_width(m_png, m_info));
    }

    /** \brief Set the contents of the block.
     *
     * \param op New block pointer.
     */
    void setBlock(uint8_t *op)
    {
      m_block = op;
    }
};

/** Hold contents of PNG write structs safely. */
class PngWriter
{
  private:
    /** File handle. */
    FILE *m_fd;

    /** PNG read struct. */
    png_struct *m_png;

    /** PNG info struct. */
    png_info *m_info;

  public:
    /** \brief Constructor.
     *
     * \param fd File handle to adapt.
     * \param skip How many bytes of file have already been read
     */
    PngWriter(FILE *fd) :
      m_fd(fd),
      m_png(NULL),
      m_info(NULL)
    {
      m_png = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
      if(!m_png)
      {
        std::stringstream sstr;
        sstr << "could not create a PNG read struct";
        BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
      }
      m_info = png_create_info_struct(m_png);
      if(!m_info)
      {
        std::stringstream sstr;
        sstr << "could not create a PNG info struct";
        BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
      }

      png_init_io(m_png, m_fd); // read header
      png_set_compression_buffer_size(m_png, 8192);
      png_set_compression_level(m_png, Z_BEST_COMPRESSION);
      png_set_compression_mem_level(m_png, Z_BEST_COMPRESSION);
      png_set_compression_window_bits(m_png, 15);
    }

    /** \brief Destructor. */
    ~PngWriter()
    {
      png_destroy_write_struct(&m_png, &m_info);
      fclose(m_fd);
    }

  public:
    /** \brief Write actual file contents.
     *
     * \param pw Width.
     * \param ph Height.
     * \param pd Depth.
     * \param color_type PNG color type.
     * \param row_pointers Row pointer input.
     */
    void write(unsigned pw, unsigned ph, unsigned pd, uint8_t color_type, uint8_t **row_pointers)
    {
      png_set_IHDR(m_png, m_info, pw, ph, 8, color_type, PNG_INTERLACE_NONE,
          PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);

      if(pd > 0)
      {
        std::map<std::string, std::string> text_map;

        text_map[PNG_TEXT_DEPTH_KEYWORD] = boost::lexical_cast<std::string>(pd);

        png_set_text_map(m_png, m_info, text_map);
      }

      png_write_info(m_png, m_info);
      png_write_image(m_png, row_pointers);
      png_write_end(m_png, NULL);
    }

  public:
    /** \brief Get the PNG object..
     *
     * \return PNG object.
     */
    png_struct* getPng()
    {
      return m_png;
    }
};

namespace gfx
{
  unsigned image_png_probe(const std::string &filename, bool require_volume)
  {
    FILE *fd = png_read_header(filename);
    PngReader reader(fd, 8);

    // error handling in libpng is retarded
    if(setjmp(png_jmpbuf(reader.getPng())))
    {
      std::stringstream sstr;
      sstr << "could not set longjmp";
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    reader.readHeader();

    if(require_volume)
    {
      if(reader.getDepth() <= 0)
      {
        std::stringstream sstr;
        sstr << '\'' << filename << "' is an image, excepted a volume";
        BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
      }
    }
    else if(reader.getDepth() > 0)
    {
      std::stringstream sstr;
      sstr << '\'' << filename << "' is a volume, excepted an image";
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    return reader.getBpp();
  }

  void image_png_load_extended(unsigned &pw, unsigned &ph, unsigned &pd, unsigned &pb, uint8_t *&pdata,
      const std::string &filename, unsigned required_bpp)
  {
    FILE *fd = png_read_header(filename);
    PngReader reader(fd, 8);

    // error handling in libpng is still retarded
    if(setjmp(png_jmpbuf(reader.getPng())))
    {
      std::stringstream sstr;
      sstr << "could not set longjmp";
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    reader.readHeader();
    unsigned width = reader.getWidth(),
             height = reader.getHeight(),
             depth = reader.getDepth(),
             bpp = reader.getBpp();
    if(bpp != required_bpp)
    {
      std::stringstream sstr;
      sstr << '\'' << filename << "' has bit depth " << bpp << ", excepted " << required_bpp;
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    unsigned data_size = width * height * bpp / 8;
    reader.setBlock(new uint8_t[data_size]);
    boost::scoped_array<uint8_t*> row_pointers(new uint8_t*[height]);
    {
      uint8_t *iter = reader.getBlock() + data_size;
      unsigned iter_sub = (width * bpp / 8);

      // PNG and OpenGL scanlines are in different order
      for(ptrdiff_t ii = 0; (ii < static_cast<ptrdiff_t>(height)); ++ii)
      {
        iter -= iter_sub;
        row_pointers[ii] = iter;
      }
    }

    reader.read(row_pointers.get());

    if(depth > 0)
    {
      height /= depth;
    }

    pw = width;
    ph = height;
    pd = depth;
    pb = bpp;

    // yield ownership of block
    pdata = reader.getBlock();
    reader.setBlock(NULL);
  }

  void image_png_load(unsigned &pw, unsigned &ph, unsigned &pb, uint8_t *&pdata, const std::string &filename,
      unsigned required_bpp)
  {
    unsigned depth;

    image_png_load_extended(pw, ph, depth, pb, pdata, filename, required_bpp);

    if(depth != 0)
    {
      std::stringstream sstr;
      sstr << '\'' << filename << "' is a volume, excepted an image";
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }
  }

  void image_png_save_extended(const std::string &filename, unsigned pw, unsigned ph, unsigned pd, unsigned pb,
      uint8_t *pdata)
  {
    if((0 >= pw) || (0 >= ph))
    {
      std::stringstream sstr;
      sstr << "invalid image dimensions: " << pw << "x" << ph;
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    uint8_t color_type = bpp_to_png_color_type(pb);
    unsigned logical_height = ph;
    if(pd > 0)
    {
      logical_height *= ph;
    }

    FILE *fd = fopen(filename.c_str(), "wb");
    if(!fd)
    {
      std::stringstream sstr;
      sstr << "could not open '" << filename << '\'';
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    PngWriter writer(fd);
    boost::scoped_array<uint8_t*> row_pointers(new uint8_t*[logical_height]);
    {
      uint8_t *iter = pdata + pw * logical_height * pb / 8;
      unsigned iter_sub = (pw * pb / 8);

      // PNG and OpenGL scanlines are in different order
      for(ptrdiff_t ii = 0; (static_cast<ptrdiff_t>(logical_height) > ii); ++ii)
      {
        iter -= iter_sub;
        row_pointers[ii] = iter;
      }
    }

    // error handling in libpng is still retarded
    if(setjmp(png_jmpbuf(writer.getPng())))
    {
      std::stringstream sstr;
      sstr << "could not set longjmp";
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    // Multiply ph again to prevent it being clobbered by longjmp.
    writer.write(pw, ph * ((pd <= 0) ? 1 : pd), pd, color_type, row_pointers.get());
  }

  void image_png_save(const std::string &filename, unsigned pw, unsigned ph, unsigned pb, uint8_t *pdata)
  {
    image_png_save_extended(filename, pw, ph, 0, pb, pdata);
  }
}

