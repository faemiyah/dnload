#include "common.hpp"
#include "compressor.hpp"

#include <iostream>

#include <boost/exception/diagnostic_information.hpp>
#include <boost/program_options.hpp>

namespace po = boost::program_options;

using namespace fcmp;

/// Extension string.
static const char *EXTENSION = ".fcmp";

/// Console output content.
static const char *g_usage = ""
"Usage: fcmp [options] <files>\n"
"'Faemiyah Context Modelling Packer' - non-serious CM (un)compressor.\n"
"\n";

/// Action.
enum Action
{
  /// No action.
  ACTION_NONE = 0,

  /// Compress a file.
  ACTION_COMPRESS,

  /// Extract a file.
  ACTION_EXTRACT
};

/// Main function.
///
/// \param argc Argument count.
/// \param argv Arguments.
/// \return Program return code.
int main(int argc, char **argv)
{
  Action action = ACTION_NONE;
  unsigned threads = 0;
  fs::path program_name = ((1 <= argc) && argv[0]) ? fs::path(argv[0]) : fs::path("fcmp");
  fs::path input_file;
  fs::path output_file;

  try
  {
    {
      po::options_description desc("Options");
      desc.add_options()
        ("compress,c", po::value<std::string>(), "Compress given file.")
        ("extract,x", po::value<std::string>(), "Decompress given file.")
        ("help,h", "Print help text.")
        ("output-file,o", po::value<std::string>(), "Write output to given file.")
        ("threads,t", po::value<unsigned>(), "Number of threads to use. (default: one thread per core)")
        ("verbose,v", "Turn on verbose reporting.")
        ("very-verbose,w", "Turn on very verbose reporting.")
        ("version,V", "Print version string.");
      bool print_help = false;
      bool print_version = false;

      if(argc > 0)
      {
        po::variables_map vmap;
        po::store(po::command_line_parser(argc, argv).options(desc).run(), vmap);
        po::notify(vmap);

        if(vmap.count("compress") && vmap.count("extract"))
        {
          std::ostringstream sstr;
          sstr << "must either compress or extract, not both";
          BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
        }
        else if(vmap.count("compress"))
        {
          action = ACTION_COMPRESS;
          input_file = fs::path(vmap["compress"].as<std::string>());
        }
        else if(vmap.count("extract"))
        {
          action = ACTION_EXTRACT;
          input_file = fs::path(vmap["extract"].as<std::string>());
        }
        
        if(vmap.count("help"))
        {
          print_help = true;
        }
        if(vmap.count("output-file"))
        {
          output_file = fs::path(vmap["output-file"].as<std::string>());
        }
        if(vmap.count("threads"))
        {
          threads = vmap["threads"].as<unsigned>();
        }
        if(vmap.count("verbose"))
        {
          if(!is_very_verbose())
          {
            set_verbosity(1);
          }
        }
        if(vmap.count("very-verbose"))
        {
          set_verbosity(2);
        }
        if(vmap.count("version"))
        {
          print_version = true;
        }
      }

      if(print_version)
      {
        std::cout << VERSION << std::endl;
      }
      if(print_help || (ACTION_NONE == action))
      {
        std::cout << g_usage << desc << std::endl;
        return 0;
      }
    }

    if(input_file.empty())
    {
      BOOST_THROW_EXCEPTION(std::runtime_error("no input file"));
    }

    if(action == ACTION_COMPRESS)
    {
      if(output_file.empty())
      {
        output_file = input_file;
        output_file += EXTENSION;
      }

      if(is_verbose())
      {
        std::cout << program_name << ": compressing " << input_file << std::endl;
      }

      DataBitsSptr content = DataBits::create(input_file);

      if(is_very_verbose())
      {
        std::cout << *content;
      }

      DataCompressedSptr compressed_content = Compressor::compress(*content, threads);

      // Perform trivial error check.
      {
        // Decompression time is insignificant compared to compression time,
        DataBitsSptr cmp = Compressor::extract(*compressed_content);

        if(*cmp != *content)
        {
          std::ostringstream sstr;
          sstr << "compressed data restores incorrectly\n" << *cmp;
          BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
        }
      }

      if(is_verbose())
      {
        size_t cbits = compressed_content->getSizeBits();
        size_t cbytes = cbits / 8;

        if(cbits % 8)
        {
          ++cbytes;
        }
        std::cout << program_name << ": wrote " << output_file << ", " << cbits << " bits, " << cbytes <<
          " bytes\n";

        if(is_very_verbose())
        {
          std::cout << *compressed_content;
        }
      }

      compressed_content->write(output_file);
    }
    else // ACTION_EXTRACT
    {
      if(output_file.empty())
      {
        if(input_file.extension() == EXTENSION)
        {
          output_file = input_file.stem();
        }
        else
        {
          std::ostringstream sstr;
          sstr << "output file not defined, cannot determine for compressed file " << input_file;
          BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
        }
      }

      if(is_verbose())
      {
        std::cout << program_name << ": extracting " << input_file << std::endl;
      }

      DataCompressedSptr content = DataCompressed::create(input_file);

      if(is_very_verbose())
      {
        std::cout << *content;
      }

      DataBitsSptr extracted_content = Compressor::extract(*content);

      if(is_verbose())
      {
        std::cout << program_name << ": wrote " << output_file << ", " <<
          extracted_content->getSizeBytes() << " bytes\n";

        if(is_very_verbose())
        {
          std::cout << *extracted_content;
        }
      }

      extracted_content->write(output_file);
    }
  }
  catch(const boost::exception &err)
  {
    std::cerr << boost::diagnostic_information(err);
    return 1;
  }

  return 0;
}

