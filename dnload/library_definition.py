from dnload.platform_var import PlatformVar
from dnload.symbol import Symbol

########################################
# Library ##############################
########################################

class LibraryDefinition:
    """Represents one library containing symbols."""

    def __init__(self, name, symbols=[]):
        """Constructor."""
        self.__name = name
        self.__symbols = []
        self.add_symbols(symbols)

    def add_symbol(self, sym):
        """Add single symbol."""
        self.__symbols += [sym]

    def add_symbols(self, lst):
        """Add a symbol listing."""
        for ii in lst:
            self.add_symbol(Symbol(ii, self))

    def find_symbol(self, op):
        """Find a symbol by name."""
        for ii in self.__symbols:
            if ii.get_name() == op:
                return ii
        return None

    def get_name(self):
        """Accessor."""
        return str(self.__name)

########################################
# Globals ##############################
########################################

g_library_definition_c = LibraryDefinition("c", (
    ("int", "fclose", "FILE*"),
    ("FILE*", "fopen", "const char*", "const char*"),
    ("void", "free", "void*"),
    ("size_t", "fwrite", "const void*", "size_t", "size_t", "FILE*"),
    ("void*", "malloc", "size_t"),
    ("void*", "memset", "void*", "int", "size_t"),
    ("int", "printf", "const char* __restrict", "..."),
    ("int", "putc", "int", "FILE*"),
    ("int", "putchar", "int"),
    ("int", "puts", "const char*"),
    ("void", "qsort", "void*", "size_t", "size_t", "int (*)(const void*, const void*)"),
    ("void*", "realloc", "void*", "size_t"),
    ("int", ("rand", PlatformVar("function_rand"))),
    ("int", "random"),
    ("unsigned", "sleep", "unsigned"),
    ("void", ("srand", PlatformVar("function_srand")), "unsigned int"),
    ("void", "srandom", "unsigned int"),
    ))

g_library_definition_bcm_host = LibraryDefinition("bcm_host", (
    ("void", "bcm_host_deinit"),
    ("void", "bcm_host_init"),
    ("DISPMANX_DISPLAY_HANDLE_T", "vc_dispmanx_display_open", "uint32_t"),
    ("DISPMANX_ELEMENT_HANDLE_T", "vc_dispmanx_element_add", "DISPMANX_UPDATE_HANDLE_T", "DISPMANX_DISPLAY_HANDLE_T", "int32_t", "const VC_RECT_T*", "DISPMANX_RESOURCE_HANDLE_T", "const VC_RECT_T*", "DISPMANX_PROTECTION_T", "VC_DISPMANX_ALPHA_T*", "DISPMANX_CLAMP_T*", "DISPMANX_TRANSFORM_T"),
    ("DISPMANX_UPDATE_HANDLE_T", "vc_dispmanx_update_start", "int32_t"),
    ("int", "vc_dispmanx_update_submit_sync", "DISPMANX_UPDATE_HANDLE_T"),
    ("int32_t", "graphics_get_display_size", "const uint16_t", "uint32_t*", "uint32_t*"),
    ))

g_library_definition_egl = LibraryDefinition("EGL", (
    ("EGLBoolean", "eglChooseConfig", "EGLDisplay", "EGLint const*", "EGLConfig*", "EGLint", "EGLint*"),
    ("EGLContext", "eglCreateContext", "EGLDisplay", "EGLConfig", "EGLContext", "EGLint const*"),
    ("EGLSurface", "eglCreateWindowSurface", "EGLDisplay", "EGLConfig", "EGLNativeWindowType", "EGLint const*"),
    ("EGLBoolean", "eglGetConfigs", "EGLDisplay", "EGLConfig*", "EGLint", "EGLint*"),
    ("EGLDisplay", "eglGetDisplay", "NativeDisplayType"),
    ("EGLBoolean", "eglInitialize", "EGLDisplay", "EGLint*", "EGLint*"),
    ("EGLBoolean", "eglMakeCurrent", "EGLDisplay", "EGLSurface", "EGLSurface", "EGLContext"),
    ("EGLBoolean", "eglSwapBuffers", "EGLDisplay", "EGLSurface"),
    ("EGLBoolean", "eglTerminate", "EGLDisplay"),
    ))

g_library_definition_fftw = LibraryDefinition("fftw3", (
    ("void", "fftw_cleanup"),
    ("void", "fftw_destroy_plan", "fftw_plan"),
    ("void", "fftw_execute", "const fftw_plan"),
    ("void", "fftw_free", "void*"),
    ("void*", "fftw_malloc", "size_t"),
    ("fftw_plan", "fftw_plan_dft_r2c_1d", "int", "double*", "fftw_complex*", "unsigned"),
    ("fftw_plan", "fftw_plan_r2r_1d", "int", "double*", "double*", "fftw_r2r_kind", "unsigned"),
    ))

g_library_definition_freetype = LibraryDefinition("freetype", (
    ("FT_UInt", "FT_Get_Char_Index", "FT_Face", "FT_ULong"),
    ("FT_Error", "FT_Get_Kerning", "FT_Face", "FT_UInt", "FT_UInt", "FT_UInt", "FT_Vector*"),
    ("FT_Error", "FT_Init_FreeType", "FT_Library*"),
    ("FT_Error", "FT_Load_Glyph", "FT_Face", "FT_UInt", "FT_Int32"),
    ("FT_Error", "FT_New_Face", "FT_Library", "const char*", "FT_Long", "FT_Face*"),
    ("FT_Error", "FT_Render_Glyph", "FT_GlyphSlot", "FT_Render_Mode"),
    ("FT_Error", "FT_Set_Pixel_Sizes", "FT_Face", "FT_UInt", "FT_UInt"),
    ))

g_library_definition_gl = LibraryDefinition(PlatformVar("gl_library"), (
    ("void", "glActiveTexture", "GLenum"),
    ("void", "glAttachShader", "GLuint", "GLuint"),
    ("void", "glBindBuffer", "GLenum", "GLuint"),
    ("void", "glBindFramebuffer", "GLenum", "GLuint"),
    ("void", "glBindProgramPipeline", "GLuint"),
    ("void", "glBindRenderbuffer", "GLenum", "GLuint"),
    ("void", "glBindTexture", "GLenum", "GLuint"),
    ("void", "glBindTextureUnit", "GLuint", "GLuint"),
    ("void", "glBindTextures", "GLuint", "GLsizei", "const GLuint*"),
    ("void", "glBindVertexArray", "GLuint"),
    ("void", "glBlendFunc", "GLenum", "GLenum"),
    ("void", "glBlendFuncSeparate", "GLenum", "GLenum", "GLenum", "GLenum"),
    ("void", "glBufferData", "GLenum", "GLsizeiptr", "const GLvoid*", "GLenum"),
    ("void", "glBufferSubData", "GLenum", "GLintptr", "GLsizeiptr", "const void*"),
    ("void", "glClear", "GLbitfield"),
    ("void", "glClearColor", "GLfloat", "GLfloat", "GLfloat", "GLfloat"),
    ("void", "glClearDepthf", "GLfloat"),
    ("void", "glClearStencil", "GLint"),
    ("void", "glColorMask", "GLboolean", "GLboolean", "GLboolean", "GLboolean"),
    ("void", "glCompileShader", "GLuint"),
    ("void", "glCreateFramebuffers", "GLsizei", "GLuint*"),
    ("GLuint", "glCreateProgram"),
    ("GLuint", "glCreateShader", "GLenum"),
    ("GLuint", "glCreateShaderProgramv", "GLenum", "GLsizei", "const char**"),
    ("void", "glCreateTextures", "GLenum", "GLsizei", "GLuint*"),
    ("void", "glCullFace", "GLenum"),
    ("void", "glDeleteBuffers", "GLsizei", "const GLuint*"),
    ("void", "glDeleteFramebuffers", "GLsizei", "GLuint*"),
    ("void", "glDeleteProgram", "GLuint"),
    ("void", "glDeleteProgramPipelines", "GLsizei", "GLuint*"),
    ("void", "glDeleteRenderbuffers", "GLsizei", "GLuint*"),
    ("void", "glDeleteShader", "GLuint"),
    ("void", "glDeleteTextures", "GLsizei", "const GLuint*"),
    ("void", "glDeleteVertexArrays", "GLsizei", "const GLuint*"),
    ("void", "glDepthFunc", "GLenum"),
    ("void", "glDepthMask", "GLboolean"),
    ("void", "glDisable", "GLenum"),
    ("void", "glDisableVertexAttribArray", "GLuint"),
    ("void", "glDrawArrays", "GLenum", "GLint", "GLsizei"),
    ("void", "glDrawArraysInstanced", "GLenum", "GLint", "GLsizei, GLsizei"),
    ("void", "glDrawElements", "GLenum", "GLsizei", "GLenum", "const GLvoid*"),
    ("void", "glEnable", "GLenum"),
    ("void", "glEnableVertexAttribArray", "GLuint"),
    ("void", "glFramebufferTexture", "GLenum", "GLenum", "GLuint", "GLint"),
    ("void", "glFramebufferTexture2D", "GLenum", "GLenum", "GLenum", "GLuint", "GLint"),
    ("void", "glFramebufferRenderbuffer", "GLenum", "GLenum", "GLint", "GLuint"),
    ("void", "glGenerateMipmap", "GLenum"),
    ("void", "glGenerateTextureMipmap", "GLuint"),
    ("void", "glGenBuffers", "GLsizei", "GLuint*"),
    ("void", "glGenFramebuffers", "GLsizei", "GLuint*"),
    ("void", "glGenProgramPipelines", "GLsizei", "GLuint*"),
    ("void", "glGenRenderbuffers", "GLsizei", "GLuint*"),
    ("void", "glGenTextures", "GLsizei", "GLuint*"),
    ("void", "glGenVertexArrays", "GLsizei", "GLuint*"),
    ("void", "glDrawMeshTasksNV", "GLuint", "GLuint"),
    ("GLint", "glGetAttribLocation", "GLuint", "const GLchar*"),
    ("GLenum", "glGetError", "void"),
    ("void", "glGetProgramInfoLog", "GLuint", "GLsizei", "GLsizei*", "GLchar*"),
    ("void", "glGetProgramiv", "GLuint", "GLenum", "GLint*"),
    ("void", "glGetShaderInfoLog", "GLuint", "GLsizei", "GLsizei*", "GLchar*"),
    ("void", "glGetShaderiv", "GLuint", "GLenum", "GLint*"),
    ("GLint", "glGetUniformLocation", "GLuint", "const GLchar*"),
    ("void", "glLineWidth", "GLfloat"),
    ("void", "glLinkProgram", "GLuint"),
    ("void", "glNamedFramebufferTexture", "GLuint", "GLenum", "GLuint", "GLint"),
    ("void", "glPolygonOffset", "GLfloat", "GLfloat"),
    ("void", "glProgramUniform1f", "GLuint", "GLint", "GLfloat"),
    ("void", "glProgramUniform1i", "GLuint", "GLint", "GLint"),
    ("void", "glProgramUniform1fv", "GLuint", "GLint", "GLsizei", "const GLfloat*"),
    ("void", "glProgramUniform1iv", "GLuint", "GLint", "GLsizei", "const GLint*"),
    ("void", "glProgramUniform2fv", "GLuint", "GLint", "GLsizei", "const GLfloat*"),
    ("void", "glProgramUniform3fv", "GLuint", "GLint", "GLsizei", "const GLfloat*"),
    ("void", "glProgramUniform3iv", "GLuint", "GLint", "GLsizei", "const GLint*"),
    ("void", "glProgramUniform4fv", "GLuint", "GLint", "GLsizei", "const GLfloat*"),
    ("void", "glProgramUniformMatrix2fv", "GLuint", "GLint", "GLsizei", "GLboolean", "const GLfloat*"),
    ("void", "glProgramUniformMatrix3fv", "GLuint", "GLint", "GLsizei", "GLboolean", "const GLfloat*"),
    ("void", "glProgramUniformMatrix4fv", "GLuint", "GLint", "GLsizei", "GLboolean", "const GLfloat*"),
    ("void", "glReadPixels", "GLint", "GLint", "GLsizei", "GLsizei", "GLenum", "GLenum", "GLvoid*"),
    ("void", "glRectf", "GLfloat", "GLfloat", "GLfloat", "GLfloat"),
    ("void", "glRecti", "GLint", "GLint", "GLint", "GLint"),
    ("void", "glRects", "GLshort", "GLshort", "GLshort", "GLshort"),
    ("void", "glRenderbufferStorage", "GLenum", "GLenum", "GLsizei", "GLsizei"),
    ("void", "glRotatef", "GLfloat", "GLfloat", "GLfloat", "GLfloat"),
    ("void", "glShaderSource", "GLuint", "GLsizei", "const GLchar**", "const GLint*"),
    ("void", "glStencilFunc", "GLenum", "GLint", "GLuint"),
    ("void", "glStencilMask", "GLuint"),
    ("void", "glStencilOp", "GLenum", "GLenum", "GLenum"),
    ("void", "glStencilOpSeparate", "GLenum", "GLenum", "GLenum", "GLenum"),
    ("void", "glTexImage1D", "GLenum", "GLint", "GLint", "GLsizei", "GLint", "GLenum", "GLenum", "const GLvoid*"),
    ("void", "glTexImage2D", "GLenum", "GLint", "GLint", "GLsizei", "GLsizei", "GLint", "GLenum", "GLenum", "const GLvoid*"),
    ("void", "glTexImage2DMultisample", "GLenum", "GLsizei", "GLint", "GLsizei", "GLsizei", "GLboolean"),
    ("void", "glTexImage3D", "GLenum", "GLint", "GLint", "GLsizei", "GLsizei", "GLsizei", "GLint", "GLenum", "GLenum", "const GLvoid*"),
    ("void", "glTexStorage2D", "GLenum", "GLsizei", "GLenum", "GLsizei", "GLsizei"),
    ("void", "glTexStorage3D", "GLenum", "GLsizei", "GLenum", "GLsizei", "GLsizei", "GLsizei"),
    ("void", "glTexSubImage2D", "GLenum", "GLint", "GLint", "GLint", "GLsizei", "GLsizei", "GLenum", "GLenum", "const GLvoid*"),
    ("void", "glTexSubImage3D", "GLenum", "GLint", "GLint", "GLint", "GLint", "GLsizei", "GLsizei", "GLsizei", "GLenum", "GLenum", "const GLvoid*"),
    ("void", "glTexParameterf", "GLenum", "GLenum", "GLfloat"),
    ("void", "glTexParameteri", "GLenum", "GLenum", "GLint"),
    ("void", "glTextureParameterf", "GLuint", "GLenum", "GLfloat"),
    ("void", "glTextureParameteri", "GLuint", "GLenum", "GLint"),
    ("void", "glTextureStorage2D", "GLuint", "GLsizei", "GLenum", "GLsizei", "GLsizei"),
    ("void", "glTextureStorage3D", "GLuint", "GLsizei", "GLenum", "GLsizei", "GLsizei", "GLsizei"),
    ("void", "glTextureSubImage3D", "GLuint", "GLint", "GLint", "GLint", "GLint", "GLsizei", "GLsizei", "GLsizei", "GLenum", "GLenum", "const void*"),
    ("void", "glUseProgram", "GLuint"),
    ("void", "glUseProgramStages", "GLuint", "GLbitfield", "GLuint"),
    ("void", "glUniform1f", "GLint", "GLfloat"),
    ("void", "glUniform1i", "GLint", "GLint"),
    ("void", "glUniform2f", "GLint", "GLfloat", "GLfloat"),
    ("void", "glUniform2i", "GLint", "GLint", "GLint"),
    ("void", "glUniform3f", "GLint", "GLfloat", "GLfloat", "GLfloat"),
    ("void", "glUniform3i", "GLint", "GLint", "GLint", "GLint"),
    ("void", "glUniform4f", "GLint", "GLfloat", "GLfloat", "GLfloat", "GLfloat"),
    ("void", "glUniform4i", "GLint", "GLint", "GLint", "GLint", "GLint"),
    ("void", "glUniform1iv", "GLint", "GLsizei", "const GLint*"),
    ("void", "glUniform1fv", "GLint", "GLsizei", "const GLfloat*"),
    ("void", "glUniform2fv", "GLint", "GLsizei", "const GLfloat*"),
    ("void", "glUniform2iv", "GLint", "GLsizei", "const GLint*"),
    ("void", "glUniform3fv", "GLint", "GLsizei", "const GLfloat*"),
    ("void", "glUniform3iv", "GLint", "GLsizei", "const GLint*"),
    ("void", "glUniform4fv", "GLint", "GLsizei", "const GLfloat*"),
    ("void", "glUniform4iv", "GLint", "GLsizei", "const GLint*"),
    ("void", "glUniformMatrix2fv", "GLint", "GLsizei", "GLboolean", "const GLfloat*"),
    ("void", "glUniformMatrix3fv", "GLint", "GLsizei", "GLboolean", "const GLfloat*"),
    ("void", "glUniformMatrix4fv", "GLint", "GLsizei", "GLboolean", "const GLfloat*"),
    ("void", "glVertexAttribIPointer", "GLuint", "GLint", "GLenum", "GLsizei", "const GLvoid*"),
    ("void", "glVertexAttribPointer", "GLuint", "GLint", "GLenum", "GLboolean", "GLsizei", "const GLvoid*"),
    ("void", "glViewport", "GLint", "GLint", "GLsizei", "GLsizei"),
    ))

g_library_definition_glu = LibraryDefinition("GLU", (
    ("GLint", "gluBuild3DMipmaps", "GLenum", "GLint", "GLsizei", "GLsizei", "GLsizei", "GLenum", "GLenum", "const void*"),
    ))

g_library_definition_m = LibraryDefinition("m", (
    ("double", "acos", "double"),
    ("float", "acosf", "float"),
    ("double", "asin", "double"),
    ("float", "asinf", "float"),
    ("float", "atan2f", "float", "float"),
    ("float", "atanf", "float"),
    ("float", ("ceilf", PlatformVar("function_ceilf")), "float"),
    ("double", "cos", "double"),
    ("float", "cosf", "float"),
    ("float", "expf", "float"),
    ("float", "exp2f", "float"),
    ("float", ("fabsf", None), "float"),
    ("float", ("floorf", PlatformVar("function_floorf")), "float"),
    ("float", ("fmaxf", None), "float", "float"),
    ("float", ("fminf", None), "float", "float"),
    ("float", "fmodf", "float", "float"),
    ("float", "logf", "float"),
    ("float", "log2f", "float"),
    ("long", "lrintf", "float"),
    ("float", "powf", "float", "float"),
    ("float", "roundf", "float"),
    ("double", "sin", "double"),
    ("float", "sinf", "float"),
    ("void", "sincosf", "float", "float*", "float*"),
    ("double", ("sqrt", None), "double"),
    ("float", ("sqrtf", None), "float"),
    ("float", "tanf", "float"),
    ("float", "tanhf", "float"),
    ))

g_library_definition_ncurses = LibraryDefinition("ncurses", (
    ("NCURSES_EXPORT(int)", "addch", "const chtype"),
    ("NCURSES_EXPORT(int)", "chgat", "int", "attr_t", "NCURSES_PAIRS_T", "const void*"),
    ("NCURSES_EXPORT(int)", "curs_set", "int"),
    ("NCURSES_EXPORT(int)", "getch"),
    ("NCURSES_EXPORT(int)", "getmaxx", "const WINDOW*"),
    ("NCURSES_EXPORT(int)", "getmaxy", "const WINDOW*"),
    ("NCURSES_EXPORT(int)", "init_pair", "NCURSES_PAIRS_T", "NCURSES_COLOR_T", "NCURSES_COLOR_T"),
    ("NCURSES_EXPORT(WINDOW*)", "initscr"),
    ("NCURSES_EXPORT(int)", "endwin"),
    ("NCURSES_EXPORT(int)", "move", "int", "int"),
    ("NCURSES_EXPORT(int)", "mvaddch", "int", "int", "const chtype"),
    ("NCURSES_EXPORT(int)", "mvchgat", "int", "int", "int", "attr_t", "NCURSES_PAIRS_T", "const void*"),
    ("NCURSES_EXPORT(int)", "mvwaddch", "WINDOW*", "int", "int", "const chtype"),
    ("NCURSES_EXPORT(int)", "refresh"),
    ("NCURSES_EXPORT(int)", "start_color"),
    ("NCURSES_EXPORT(int)", "wmove", "WINDOW*", "int", "int"),
    ))

g_library_definition_ogg = LibraryDefinition("ogg", (
    ("int", "ogg_page_serialno", "ogg_page*"),
    ("int", "ogg_stream_init", "ogg_stream_state*", "int"),
    ("int", "ogg_stream_pagein", "ogg_stream_state*", "ogg_page*"),
    ("int", "ogg_stream_packetout", "ogg_stream_state*", "ogg_packet*"),
    ("char*", "ogg_sync_buffer", "ogg_sync_state*", "long"),
    ("int", "ogg_sync_init", "ogg_sync_state*"),
    ("int", "ogg_sync_pageout", "ogg_sync_state*", "ogg_page*"),
    ))

g_library_definition_opus = LibraryDefinition("opus", (
    ("OpusDecoder*", "opus_decoder_create", "opus_int32", "int", "int*"),
    ("int", "opus_decoder_init", "OpusDecoder*", "opus_int32", "int"),
    ("int", "opus_decode_float", "OpusDecoder*", "const unsigned char*", "opus_int32", "float*", "int", "int"),
    ))

g_library_definition_opusfile = LibraryDefinition("opusfile", (
    ("void", "op_free", "OggOpusFile*"),
    ("OggOpusFile*", "op_open_memory", "const unsigned char*", "size_t", "int*"),
    ("int", "op_read_float", "OggOpusFile*", "float*", "int", "int*"),
    ))

g_library_definition_png = LibraryDefinition("png", (
    ("png_infop", "png_create_info_struct", "png_const_structrp"),
    ("png_structp", "png_create_read_struct", "png_const_charp", "png_voidp", "png_error_ptr", "png_error_ptr"),
    ("png_uint_32", "png_get_IHDR", "png_const_structrp", "png_const_inforp", "png_uint_32*", "png_uint_32*", "int*", "int*", "int*", "int*", "int*"),
    ("png_uint_32", "png_get_valid", "png_const_structrp", "png_const_inforp", "png_uint_32"),
    ("void", "png_read_info", "png_structrp", "png_inforp"),
    ("void", "png_read_row", "png_structrp", "png_bytep", "png_bytep"),
    ("void", "png_set_expand", "png_structrp"),
    ("void", "png_set_read_fn", "png_structrp", "png_voidp", "png_rw_ptr"),
    ("void", "png_set_tRNS_to_alpha", "png_structrp"),
    ))

g_library_definition_sdl = LibraryDefinition("SDL", (
    ("SDL_cond*", "SDL_CreateCond"),
    ("SDL_mutex*", "SDL_CreateMutex"),
    ("SDL_Thread*", "SDL_CreateThread", "int (*)(void*)", "void*"),
    ("int", "SDL_CondBroadcast", "SDL_cond*"),
    ("int", "SDL_CondSignal", "SDL_cond*"),
    ("int", "SDL_CondWait", "SDL_cond*", "SDL_mutex*"),
    ("void", "SDL_Delay", "Uint32"),
    ("void", "SDL_DestroyCond", "SDL_cond*"),
    ("void", "SDL_DestroyMutex", "SDL_mutex*"),
    ("int", "SDL_mutexP", "SDL_mutex*"),
    ("int", "SDL_mutexV", "SDL_mutex*"),
    ("SDL_threadID", "SDL_ThreadID"),
    ("SDL_threadID", "SDL_GetThreadID", "SDL_Thread*"),
    ("uint32_t", "SDL_GetTicks"),
    ("void", "SDL_GL_SwapBuffers"),
    ("int", "SDL_Init", "Uint32"),
    ("int", "SDL_OpenAudio", "SDL_AudioSpec*", "SDL_AudioSpec*"),
    ("void", "SDL_PauseAudio", "int"),
    ("int", "SDL_PollEvent", "SDL_Event*"),
    ("void", "SDL_Quit"),
    ("SDL_Surface*", "SDL_SetVideoMode", "int", "int", "int", "Uint32"),
    ("int", "SDL_ShowCursor", "int"),
    ("void*", "SDL_TLSGet", "SDL_TLSID"),
    ("int", "SDL_TLSSet", "SDL_TLSID", "const void*", "void (*)(void*)"),
    ("void", "SDL_WaitThread", "SDL_Thread*", "int*"),
    ))

g_library_definition_sdl2 = LibraryDefinition("SDL2", (
    ("SDL_Renderer*", "SDL_CreateRenderer", "SDL_Window*", "int", "Uint32"),
    ("SDL_Thread*", "SDL_CreateThread", "int (*)(void*)", "const char*", "void*"),
    ("SDL_Window*", "SDL_CreateWindow", "const char*", "int", "int", "int", "int", "Uint32"),
    ("int", "SDL_CreateWindowAndRenderer", "int", "int", "Uint32", "SDL_Window**", "SDL_Renderer**"),
    ("SDL_GLContext", "SDL_GL_CreateContext", "SDL_Window*"),
    ("int", "SDL_GL_SetAttribute", "SDL_GLattr", "int"),
    ("int", "SDL_GL_SetSwapInterval", "int"),
    ("void", "SDL_GL_SwapWindow", "SDL_Window*"),
    ("int", "SDL_LockMutex", "SDL_mutex*"),
    ("int", "SDL_RenderSetLogicalSize", "SDL_Renderer*", "int", "int"),
    ("int", "SDL_UnlockMutex", "SDL_mutex*"),
    ))

g_library_definition_sndfile = LibraryDefinition("sndfile", (
    ("int", "sf_close", "SNDFILE*"),
    ("SNDFILE*", "sf_open", "const char*", "int", "SF_INFO*"),
    ("sf_count_t", "sf_writef_float", "SNDFILE*", "const float*", "sf_count_t"),
    ))

g_library_definitions = (
    g_library_definition_c,
    g_library_definition_bcm_host,
    g_library_definition_egl,
    g_library_definition_fftw,
    g_library_definition_freetype,
    g_library_definition_gl,
    g_library_definition_glu,
    g_library_definition_m,
    g_library_definition_ncurses,
    g_library_definition_ogg,
    g_library_definition_opusfile,
    g_library_definition_opus,
    g_library_definition_png,
    g_library_definition_sdl,
    g_library_definition_sdl2,
    g_library_definition_sndfile,
    )
