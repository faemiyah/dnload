#ifndef GLSL_SHADER_HPP
#define GLSL_SHADER_HPP

#include <memory>
#include <string>
#include <vector>

#if defined(DNLOAD_GLESV2)
#include "GLES2/gl2.h"
#else
#include "GL/glew.h"
#endif

// Forward declaration.
class GlslShader;

/// Convenience typedef.
typedef std::unique_ptr<GlslShader> GlslShaderUptr;

/// Shader abstraction.
class GlslShader
{
  private:
    /// OpenGL type.
    GLenum m_type;

    /// OpenGL ID.
    GLuint m_id;

    /// Pipeline ID.
    GLuint m_pipeline_id;

    /// Shader files.
    std::vector<std::string> m_files;

  public:
    /// Constructor.
    ///
    /// \param type Shader type.
    /// \param src1 Source file.
    GlslShader(GLenum type, const char *src1);

    /// Constructor.
    ///
    /// \param type Shader type.
    /// \param src1 Source file.
    /// \param src2 Source file.
    GlslShader(GLenum type, const char *src1, const char *src2);

    /// Destructor.
    ~GlslShader();

  private:
    /// Clean up generated IDs.
    void cleanup();

  public:
    /// Load files and (re)compile source.
    ///
    /// \param pipeline True to create pipeline program as opposed to shader.
    /// \return True if compilation successful, false otherwise.
    bool compile(bool pipeline = false);

    /// Get stage for pipeline ID.
    ///
    /// \return Attachment stage.
    GLuint getStage() const;

  public:
    /// Get ID.
    ///
    /// \return ID or 0 if not created.
    GLuint getId() const
    {
      return m_id;
    }

    /// Get pipeline ID.
    ///
    /// \return Pipeline ID or 0 if not created.
    GLuint getPipelineId() const
    {
      return m_pipeline_id;
    }

    /// Get type.
    ///
    /// \return OpenGL shader type.
    GLenum getType() const
    {
      return m_type;
    }

  public:
    /// Create a new shader.
    ///
    /// \param type Shader type.
    /// \param src1 Source file.
    static GlslShaderUptr create(GLenum type, const char *src1)
    {
      return GlslShaderUptr(new GlslShader(type, src1));
    }

    /// Create a new shader.
    ///
    /// \param type Shader type.
    /// \param src1 Source file.
    /// \param src2 Source file.
    static GlslShaderUptr create(GLenum type, const char *src1, const char *src2)
    {
      return GlslShaderUptr(new GlslShader(type, src1, src2));
    }
};

#endif
