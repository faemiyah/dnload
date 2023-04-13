#ifndef GLSL_SHADER_SOURCE_HPP
#define GLSL_SHADER_SOURCE_HPP

#include <string>
#include <string_view>
#include <vector>

#if defined(DNLOAD_GLESV2)
#include "GLES2/gl2.h"
#else
#include "GL/glew.h"
#endif

/// Base class for shaders and shader programs.
class GlslShaderSource
{
private:
    /// Shader files.
    std::vector<std::string> m_files;

protected:
    /// OpenGL type.
    GLenum m_type;

    /// OpenGL ID.
    GLuint m_id = 0u;

protected:
    /// Constructor.
    ///
    /// \param type Shader type.
    explicit GlslShaderSource(GLenum type) :
        m_type(type)
    {
    }

public:
    /// Destructor.
    ~GlslShaderSource();

protected:
    /// Adds a file to the list of file.
    ///
    /// \param fname Filename to add.
    void addFile(std::string_view fname);

    /// Reads all source files.
    ///
    /// \return Combined preprocessed, concatenated shader content string.
    std::string read() const;

public:
    /// Gets the name by combining names of files.
    ///
    /// \return Combined name.
    std::string getName() const;

public:
    /// Get ID.
    ///
    /// \return ID or 0 if not created.
    GLuint getId() const
    {
        return m_id;
    }

    /// Get type.
    ///
    /// \return OpenGL shader type.
    GLenum getType() const
    {
        return m_type;
    }
};

/// Convert source from GLESv2 format to normal GLSL.
///
/// \param op Source to convert.
/// \return Converted source.
std::string convert_glesv2_gl(std::string_view op);

#endif
